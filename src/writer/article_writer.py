"""writer.article_writer — drafts INSERT·UPDATE 및 articles 승격.

출처: BACKEND §2-4 + DB §4·§5·§8 [확정].

함수:
- create_draft        : collector 결과를 drafts INSERT (status='collected')
- save_enriched       : Claude 결과를 drafts.enriched_payload에 저장
- save_validation_report : validator 결과를 drafts.validation_report에 저장
- validate_and_save   : validator 4 게이트 호출 → report 저장 + 상태 전이 (BACKEND §2-3 흐름)
- promote_to_article  : approved draft → articles INSERT + 상태 published 전이

payload는 dict로 받아 JSON 문자열로 저장 (DB §5).
모듈 의존: writer → validator (단방향).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

import validator

from . import state_machine

# POLICY §2-2 [확정] — 첫머리 disclosure 키워드 (두 단어 모두 포함 필수)
DISCLOSURE_FIRST_KEYWORDS: tuple[str, ...] = ("쿠팡 파트너스", "수수료")

# 첫머리 검사 범위 — POLICY §2-4 명시 200자보다 약간 여유 (단락 종료 우선)
DISCLOSURE_SCAN_HEAD_LEN = 300

# DB §4-1 / manifest 일관 — "sha256:" prefix + hex digest
CONTENT_HASH_PREFIX = "sha256:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compute_content_hash(body_md: str) -> str:
    """본문 SHA256 — DB §4-1 + manifest §10 일관.

    형식: 'sha256:' + 64자 hex digest. UTF-8 인코딩.
    같은 body_md → 같은 hash (결정적). 빈 문자열도 처리.

    용도: articles.content_hash 컬럼 + manifest articles[*].content_hash.
    """
    digest = hashlib.sha256(body_md.encode("utf-8")).hexdigest()
    return f"{CONTENT_HASH_PREFIX}{digest}"


def extract_disclosure_first(body_md: str) -> str | None:
    """본문 첫머리에서 disclosure 문구 추출 (POLICY §2-2 표준 문구).

    첫 단락(\\n\\n 전) 또는 처음 300자 안에서 "쿠팡 파트너스" + "수수료"
    키워드 둘 다 포함된 텍스트를 추출해 반환. 찾지 못하면 None.

    반환된 문자열은 articles.disclosure_first 컬럼에 그대로 저장 가능.
    validator.disclosure 게이트는 별도로 본문 첫 200자 안의 키워드 존재를
    검증 — 본 함수는 추출 헬퍼이고 검증 책임은 없음.
    """
    if not body_md:
        return None
    head = body_md[:DISCLOSURE_SCAN_HEAD_LEN]
    # 첫 단락(빈 줄로 구분된 첫 블록) 또는 전체 head
    para_end = head.find("\n\n")
    first_para = head if para_end == -1 else head[:para_end]
    first_para = first_para.strip()
    if not first_para:
        return None
    if all(keyword in first_para for keyword in DISCLOSURE_FIRST_KEYWORDS):
        return first_para
    return None


def create_draft(
    conn: sqlite3.Connection,
    scenario_id: int,
    raw_payload: dict[str, Any] | None = None,
    working_title: str | None = None,
) -> int:
    """수집된 시나리오 → drafts INSERT (status='collected'). 반환: 새 draft id.

    raw_payload: collector.coupang 등의 출력 — dict → JSON 직렬화.
    """
    raw_json = json.dumps(raw_payload, ensure_ascii=False) if raw_payload is not None else None
    cur = conn.execute(
        """
        INSERT INTO drafts (scenario_id, working_title, status, raw_payload)
        VALUES (?, ?, 'collected', ?)
        """,
        (scenario_id, working_title, raw_json),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def save_enriched(
    conn: sqlite3.Connection,
    draft_id: int,
    enriched_payload: dict[str, Any],
) -> None:
    """Claude 결과 저장 — drafts.enriched_payload UPDATE.

    상태 전이는 호출자가 state_machine.transition으로 분리 수행 (collected→enriched).
    """
    conn.execute(
        "UPDATE drafts SET enriched_payload = ? WHERE id = ?",
        (json.dumps(enriched_payload, ensure_ascii=False), draft_id),
    )
    conn.commit()


def save_validation_report(
    conn: sqlite3.Connection,
    draft_id: int,
    report: dict[str, Any],
) -> None:
    """validator 4 게이트 결과 저장 — drafts.validation_report UPDATE."""
    conn.execute(
        "UPDATE drafts SET validation_report = ? WHERE id = ?",
        (json.dumps(report, ensure_ascii=False), draft_id),
    )
    conn.commit()


def validate_and_save(
    conn: sqlite3.Connection,
    draft_id: int,
    payload: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """validator 4 게이트 호출 → validation_report 저장 + 상태 전이 (BACKEND §2-3 흐름).

    호출 전제: draft가 'enriched' 상태여야 함 (state_machine 매트릭스).

    payload 기대 키 (validator.validate_all 호환):
    - body_md       : 본문 Markdown
    - schema_jsonld : Schema.org JSON-LD 문자열
    - products      : [{id, price_krw, ...}, ...] (선택)
    - photos        : 1인칭 게이트용 (선택)

    동작:
    1. validator.validate_all(payload) 호출
    2. serialize_report로 JSON 직렬화 가능 형태 변환
    3. drafts.validation_report 저장
    4. 전체 pass → state_machine.transition('validated')
       하나라도 fail → state_machine.transition('rejected')

    반환: (overall_pass, serialized_report)
    """
    results = validator.validate_all(payload)
    report = validator.serialize_report(results)
    save_validation_report(conn, draft_id, report)

    next_status = "validated" if report["overall_pass"] else "rejected"
    state_machine.transition(
        conn,
        draft_id,
        next_status,
        reason=f"validate_and_save → {next_status}",
    )
    return report["overall_pass"], report


def promote_to_article(
    conn: sqlite3.Connection,
    draft_id: int,
    article_fields: dict[str, Any],
) -> int:
    """approved draft → articles INSERT + drafts.promoted_article_id + status published.

    article_fields 필수 키 (DB §4-1):
    - slug · scenario_id · title · summary · body_md · body_html
    - meta_description · schema_jsonld · disclosure_first
    - content_hash · truth_check_passed_at · user_approved_at
    선택: meta_keywords · user_approved_note · published_at (없으면 now)

    반환: 새 articles.id
    """
    required = (
        "slug",
        "scenario_id",
        "title",
        "summary",
        "body_md",
        "body_html",
        "meta_description",
        "schema_jsonld",
        "disclosure_first",
        "content_hash",
        "truth_check_passed_at",
        "user_approved_at",
    )
    missing = [k for k in required if k not in article_fields]
    if missing:
        raise ValueError(f"article_fields 누락: {missing}")

    # 현재 상태가 approved여야 함 (DB §12)
    cur_status = state_machine.current_status(conn, draft_id)
    if cur_status != "approved":
        raise state_machine.IllegalStateError(
            f"promote_to_article requires approved status, got: {cur_status}"
        )

    published_at = article_fields.get("published_at") or _now_iso()

    cur = conn.execute(
        """
        INSERT INTO articles (
            slug, scenario_id, title, summary, body_md, body_html,
            meta_description, meta_keywords, schema_jsonld, disclosure_first,
            status, published_at, content_hash,
            truth_check_passed_at, user_approved_at, user_approved_note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', ?, ?, ?, ?, ?)
        """,
        (
            article_fields["slug"],
            article_fields["scenario_id"],
            article_fields["title"],
            article_fields["summary"],
            article_fields["body_md"],
            article_fields["body_html"],
            article_fields["meta_description"],
            article_fields.get("meta_keywords"),
            article_fields["schema_jsonld"],
            article_fields["disclosure_first"],
            published_at,
            article_fields["content_hash"],
            article_fields["truth_check_passed_at"],
            article_fields["user_approved_at"],
            article_fields.get("user_approved_note"),
        ),
    )
    article_id = int(cur.lastrowid or 0)

    # drafts → published 상태 전이 (state_machine 사용 — 매트릭스 검증)
    state_machine.transition(conn, draft_id, "published", reason="promoted to articles")

    # drafts.promoted_article_id 설정
    conn.execute(
        "UPDATE drafts SET promoted_article_id = ? WHERE id = ?",
        (article_id, draft_id),
    )
    conn.commit()

    # article_history 감사 로그 (DB §8-4)
    conn.execute(
        """
        INSERT INTO article_history (article_id, event_type, actor, diff_summary)
        VALUES (?, 'created', 'user', ?)
        """,
        (article_id, f"promoted from draft_id={draft_id}"),
    )
    conn.commit()

    return article_id
