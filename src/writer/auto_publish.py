"""writer.auto_publish — 가드레일 통과 카테고리 자동 게시 (세션 #22).

각 카테고리에 category_guardrail.check를 돌려 **통과면** category_state.approve(draft→published),
**보류면** draft 유지 + 사유 보고. E7의 '사람이 매 건 승인'을 'fail-closed 가드레일 +
사후 킬스위치'로 대체한다(§0 무인 자율). 게시 후 문제는 monitor()가 재검수로 가시화하고,
category_state.unapprove(킬스위치)로 즉시 비공개한다.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from writer import category_guardrail, category_state


def auto_publish_one(
    conn: sqlite3.Connection,
    slug: str,
    client: Any | None = None,
    *,
    use_llm: bool = True,
    apply: bool = True,
) -> dict[str, Any]:
    """카테고리 1개 가드레일 판정 + (통과·apply 시) 공개. 반환에 판정·사유 포함."""
    gr = category_guardrail.check(conn, slug, client, use_llm=use_llm)
    published = False
    if gr.passed and apply:
        try:
            category_state.approve(conn, slug)
            published = True
        except category_state.CategoryStateError:
            published = True  # 이미 published — 통과 상태로 간주(멱등)
    return {
        "slug": slug,
        "passed": gr.passed,
        "published": published,
        "reasons": gr.reasons,
        "flagged": gr.flagged_products,
        "checks": gr.checks,
    }


def auto_publish(
    conn: sqlite3.Connection,
    slugs: list[str],
    client: Any | None = None,
    *,
    use_llm: bool = True,
    apply: bool = True,
) -> list[dict[str, Any]]:
    """여러 카테고리 순차 자동 게시. 실패 격리 — 한 건 보류가 다음 진행을 막지 않는다."""
    return [auto_publish_one(conn, s, client, use_llm=use_llm, apply=apply) for s in slugs]


def monitor(
    conn: sqlite3.Connection, client: Any | None = None, *, use_llm: bool = False
) -> list[dict[str, Any]]:
    """게시(published) 카테고리를 재검수해 '지금은 가드레일 미달'인 것을 가시화(킬스위치 후보).

    사후 감시용 — 기본 use_llm=False(비용 0 휴리스틱)로 빠르게 훑고, 의심 건만 LLM 재확인.
    반환: 미달 카테고리들의 판정(사유 포함). 자동 비공개는 하지 않는다(보고만 — 사람/상위 결정).
    """
    conn.row_factory = sqlite3.Row
    pub = conn.execute("SELECT slug FROM categories WHERE status = 'published'").fetchall()
    out: list[dict[str, Any]] = []
    for row in pub:
        gr = category_guardrail.check(conn, row["slug"], client, use_llm=use_llm)
        if not gr.passed:
            out.append({"slug": row["slug"], "reasons": gr.reasons, "flagged": gr.flagged_products})
    return out
