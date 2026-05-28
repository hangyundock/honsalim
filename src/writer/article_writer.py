"""writer.article_writer — drafts INSERT·UPDATE 및 articles 승격.

출처: BACKEND §2-4 + DB §4·§5·§8 [확정].

함수:
- create_draft        : collector 결과를 drafts INSERT (status='collected')
- save_enriched       : Claude 결과를 drafts.enriched_payload에 저장
- save_validation_report : validator 결과를 drafts.validation_report에 저장
- promote_to_article  : approved draft → articles INSERT + 상태 published 전이

payload는 dict로 받아 JSON 문자열로 저장 (DB §5).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from . import state_machine


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
