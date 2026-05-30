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
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import validator

from . import state_machine

# POLICY §2-2 [확정] — 첫머리 disclosure 키워드 (두 단어 모두 포함 필수)
DISCLOSURE_FIRST_KEYWORDS: tuple[str, ...] = ("쿠팡 파트너스", "수수료")
# POLICY §2-3 [확정] — 푸터 disclosure 키워드 (validator.disclosure FOOTER_REQUIRED 일치)
DISCLOSURE_FOOTER_KEYWORDS: tuple[str, ...] = ("쿠팡 파트너스", "AliExpress", "본인")

# POLICY §2-2 표준 첫머리 문구 — 제휴처 인지형 [확정 2026-05-30, 공정위 정확성].
# 글이 실제 추천한 상품의 제휴처를 첫머리에 정확히 공시. 문구 패턴은 동일, 제휴처명만 교체.
FIRST_DISCLOSURE_COUPANG = (
    "이 글에는 쿠팡 파트너스 활동의 일환으로 일정 수수료를 제공받습니다. "
    "(구매자에게 추가 비용은 발생하지 않습니다.)"
)
FIRST_DISCLOSURE_ALI = (
    "이 글에는 AliExpress 어필리에이트 활동의 일환으로 일정 수수료를 제공받습니다. "
    "(구매자에게 추가 비용은 발생하지 않습니다.)"
)
FIRST_DISCLOSURE_BOTH = (
    "이 글에는 쿠팡 파트너스 및 AliExpress 어필리에이트 활동의 일환으로 일정 수수료를 "
    "제공받습니다. (구매자에게 추가 비용은 발생하지 않습니다.)"
)
# 하위호환 기본값 (제휴처 불명 시) — 쿠팡(메인)
FIRST_DISCLOSURE = FIRST_DISCLOSURE_COUPANG
# POLICY §2-3 표준 푸터 풀 문구 (verbatim)
FOOTER_DISCLOSURE = (
    "혼살림은 쿠팡 파트너스 및 AliExpress Portals 어필리에이트 활동의 일환으로, "
    "독자가 본 사이트의 추천 링크를 통해 상품을 구매할 경우 일정 수수료를 받습니다. "
    "수수료는 구매자가 지불하는 가격에 추가되지 않으며, 본 사이트는 수수료 여부와 "
    "무관하게 추천 기준을 적용합니다. 본인 및 가족 구매 금지·자동 실행 광고 미사용 "
    "등 어필리에이트 정책을 준수합니다."
)

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

    첫 단락(\\n\\n 전) 또는 처음 300자 안에서 표준 disclosure를 추출해 반환.
    찾지 못하면 None.

    판정 기준 (제휴처 무관 — 공정위 정확성):
    1) 표준 첫머리 마커 ``일정 수수료를 제공받습니다`` 존재 (쿠팡·알리·both 모든
       변형 공통, apply_disclosure가 보장) — **또는**
    2) (하위호환) "쿠팡 파트너스" + "수수료" 키워드 둘 다 존재.

    이전엔 (2)만 검사해 AliExpress 첫머리(쿠팡 미포함)가 None으로 빠졌고,
    promote 시 disclosure_first NOT NULL 위반을 유발했다 — 마커 기준으로 근본 수정.

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
    if _FIRST_MARK in first_para or all(k in first_para for k in DISCLOSURE_FIRST_KEYWORDS):
        return first_para
    return None


# 표준 문구 식별용 distinctive 구절 (POLICY §2-4 "표준 문구" 일치 여부 판정 — 키워드가 아니라
# 표준 문구 자체의 존재로 멱등 판정해야 모델이 임의로 쓴 비표준 disclosure를 표준으로 교체 보강).
_FIRST_MARK = "일정 수수료를 제공받습니다"
_FOOTER_MARK = "어필리에이트 정책을 준수합니다"


def first_disclosure_for(sources: Iterable[str] | None) -> str:
    """featured 상품 제휴처 집합 → 첫머리 표준 문구 (제휴처 인지형, 공정위 정확성).

    sources: {'aliexpress', 'coupang', ...}. 알리만→알리, 쿠팡만/불명→쿠팡, 둘 다→both.
    """
    src = {str(s).lower() for s in (sources or [])}
    has_ali = "aliexpress" in src
    has_coupang = "coupang" in src
    if has_ali and has_coupang:
        return FIRST_DISCLOSURE_BOTH
    if has_ali:
        return FIRST_DISCLOSURE_ALI
    return FIRST_DISCLOSURE_COUPANG  # 쿠팡 또는 제휴처 불명(하위호환 기본)


def apply_disclosure(body_md: str, sources: Iterable[str] | None = None) -> str:
    """POLICY §2-2 첫머리 + §2-3 푸터 **표준** disclosure를 본문에 자동 삽입 (system_base §2 '자동 삽입').

    sources: featured 상품 제휴처 집합 — 첫머리를 제휴처 인지형으로 선택(알리 글엔 알리 명시).
    모델은 disclosure를 쓰지 않도록 지시받으므로(프롬프트) 생성 후 시스템이 표준 문구를 삽입한다.
    멱등 판정은 **표준 문구 존재**(공통 구절) 기준 — 모델이 임의로 쓴 비표준 disclosure가 있어도
    표준 문구가 없으면 삽입한다(POLICY §2-4 표준 문구 보장). 결과는 validator.check_disclosure 통과.
    """
    body = body_md or ""
    head = body[:300]  # 표준 첫머리는 본문 맨 앞이나 모델 서두 직후일 수 있어 약간 여유
    tail = body[-1000:]
    need_first = _FIRST_MARK not in head
    need_footer = _FOOTER_MARK not in tail

    parts: list[str] = []
    if need_first:
        parts.append(first_disclosure_for(sources))
    if body:
        parts.append(body)
    if need_footer:
        parts.append(FOOTER_DISCLOSURE)
    return "\n\n".join(parts)


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


def record_scenario_candidates(
    conn: sqlite3.Connection,
    scenario_id: int,
    candidates: list[dict[str, Any]],
    working_title: str | None = None,
) -> int:
    """수집된 상품 후보를 시나리오의 collected draft.raw_payload에 기록 (DB §5 collector 결과).

    같은 시나리오에 'collected' 상태 draft가 있으면 그 raw_payload를 갱신,
    없으면 새 draft 생성 — 반복 수집 시 draft 난립 방지(멱등). 반환: draft id.

    raw_payload 형식: {"source": "collect-products", "candidate_count": N,
                       "candidates": [후보 dict, ...]}.
    enrich/큐레이션 단계가 이 후보 풀에서 article_products로 선별한다.
    """
    payload = {
        "source": "collect-products",
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    raw_json = json.dumps(payload, ensure_ascii=False)
    row = conn.execute(
        "SELECT id FROM drafts WHERE scenario_id = ? AND status = 'collected' "
        "ORDER BY id DESC LIMIT 1",
        (scenario_id,),
    ).fetchone()
    if row is not None:
        draft_id = int(row[0])
        conn.execute("UPDATE drafts SET raw_payload = ? WHERE id = ?", (raw_json, draft_id))
        conn.commit()
        return draft_id
    cur = conn.execute(
        "INSERT INTO drafts (scenario_id, working_title, status, raw_payload) "
        "VALUES (?, ?, 'collected', ?)",
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


def unique_article_slug(conn: sqlite3.Connection, base_slug: str) -> str:
    """articles.slug 충돌 시 ``-2``, ``-3`` … 접미사로 유일 slug 반환.

    같은 시나리오로 두 번째 글을 게시할 때 slug 충돌(UNIQUE)을 피한다.
    """
    slug = base_slug
    n = 2
    while conn.execute("SELECT 1 FROM articles WHERE slug = ?", (slug,)).fetchone():
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


def link_article_products(
    conn: sqlite3.Connection,
    article_id: int,
    featured: Iterable[dict[str, Any]],
    *,
    replace: bool = True,
) -> tuple[int, int]:
    """featured 상품(enriched_payload['products'])을 article_products에 연결 (DB §5).

    각 featured 항목의 source_product_id(+source)로 products.id를 찾아
    article_products(article_id, product_id, display_order, recommendation_note)
    INSERT. display_order는 입력 순서(0-base). products에 없는 항목은 건너뛴다
    (link 0개여도 게시는 막지 않되 호출자가 경고).

    replace=True: 기존 연결을 먼저 삭제 후 재삽입 (재게시 멱등).
    반환: (linked, skipped) 카운트.
    """
    if replace:
        conn.execute("DELETE FROM article_products WHERE article_id = ?", (article_id,))
    linked = 0
    skipped = 0
    for order, f in enumerate(featured):
        spid = f.get("source_product_id")
        if not spid:
            skipped += 1
            continue
        src = f.get("source")
        if src:
            prow = conn.execute(
                "SELECT id FROM products WHERE source_product_id = ? AND source = ?",
                (str(spid), str(src)),
            ).fetchone()
        else:
            prow = conn.execute(
                "SELECT id FROM products WHERE source_product_id = ?", (str(spid),)
            ).fetchone()
        if prow is None:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO article_products "
            "(article_id, product_id, display_order, recommendation_note) "
            "VALUES (?, ?, ?, ?)",
            (article_id, int(prow[0]), order, f.get("recommendation_note")),
        )
        linked += 1
    conn.commit()
    return linked, skipped
