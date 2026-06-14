"""writer.article_guardrail — 발행된 시나리오 글 사후 점검 (세션 #29, B-i 발행후 안전망).

``category_guardrail``(카테고리)와 대칭. B 자동발행 후, 사람 없이도 '지금 문제 있는 글'을 자동
판정·자동 비공개(fail-closed·미탐<오탐)한다. 비용 0 — DB·문자열만(네트워크·LLM 없음):
  1. **무결성**: 글의 추천 상품이 딥링크·트래킹태그·가격을 갖췄는가(깨진 제휴 페이지 방지).
  2. **적합성**: 글 키워드 기준 상품 관련성을 keyword_relevance로 재적용(off-target 사후 적발).
판정 실패 글은 article_state.unpublish로 자동 비공개. monitor()가 published 전체를 일괄 처리.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from collector import keyword_relevance
from writer import article_state

_PRODUCTS_SQL = """
    SELECT pr.name, pr.deeplink_url, pr.deeplink_slug, pr.affiliate_tag, pr.price_krw
    FROM article_products ap JOIN products pr ON pr.id = ap.product_id
    WHERE ap.article_id = ? ORDER BY ap.display_order, ap.product_id
"""

_KEYWORD_SQL = """
    SELECT k.keyword FROM drafts d JOIN keyword_queue k ON k.id = d.keyword_id
    WHERE d.promoted_article_id = ? AND k.keyword IS NOT NULL LIMIT 1
"""


@dataclass
class ArticleGuardResult:
    """글 1개 사후 판정 — passed + 사유·플래그(가시화·킬스위치 근거)."""

    slug: str
    passed: bool = True
    reasons: list[str] = field(default_factory=list)
    flagged_products: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)


def _article_keyword(conn: sqlite3.Connection, article_id: int) -> str | None:
    """글이 파생된 키워드 (drafts.promoted_article_id → keyword_queue). 없으면 None."""
    has_kw = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='keyword_queue'"
    ).fetchone()
    if has_kw is None:
        return None
    row = conn.execute(_KEYWORD_SQL, (article_id,)).fetchone()
    return str(row[0]) if row and row[0] else None


def check(conn: sqlite3.Connection, slug: str) -> ArticleGuardResult:
    """published 글 1개 사후 판정 (무결성 + 적합성). 비용 0."""
    conn.row_factory = sqlite3.Row
    arow = conn.execute(
        "SELECT id FROM articles WHERE slug = ? AND status = 'published'", (slug,)
    ).fetchone()
    res = ArticleGuardResult(slug=slug)
    if arow is None:
        res.passed = False
        res.checks["exists"] = False
        res.reasons.append("published 글 없음")
        return res
    aid = int(arow["id"])
    prods = conn.execute(_PRODUCTS_SQL, (aid,)).fetchall()

    # 1. 무결성 — 유효 제휴 상품(딥링크 + 트래킹태그 + 가격)이 최소 1개
    valid = [
        p
        for p in prods
        if (p["deeplink_url"] or p["deeplink_slug"]) and p["affiliate_tag"] and p["price_krw"]
    ]
    res.checks["integrity"] = bool(valid)
    if not valid:
        res.reasons.append(f"유효 제휴 상품 0개(전체 {len(prods)}) — 딥링크/태그/가격 누락")

    # 2. 적합성 — 키워드 기준 상품 관련성 재적용(keyword_relevance). 매핑 없으면 kept=전체(판단 보류=통과).
    keyword = _article_keyword(conn, aid)
    if keyword and prods:
        items = [{"name": str(p["name"] or "")} for p in prods]
        kept, dropped = keyword_relevance.filter_products(keyword, items)
        res.checks["relevance"] = bool(kept)  # 매핑 있고 전량 탈락이면 False
        if not kept:
            res.reasons.append(f"상품 전량 off-target(키워드 {keyword!r})")
        if dropped:
            res.flagged_products += [str(p["name"])[:30] for p in dropped[:3]]

    res.passed = all(res.checks.values()) if res.checks else True
    return res


def monitor(conn: sqlite3.Connection, *, auto_unpublish: bool = False) -> dict[str, Any]:
    """published 글 전체 사후 점검. auto_unpublish=True면 미달 글 자동 비공개(fail-closed).

    반환: {checked, failed:[{slug,reasons,flagged}], unpublished:[slug...]}. 실패 격리 —
    한 글 처리 실패가 다음을 막지 않는다. 자동 비공개 후 라이브 반영은 호출자가 build+deploy.
    """
    rows = article_state.list_published(conn)
    failed: list[dict[str, Any]] = []
    unpublished: list[str] = []
    for r in rows:
        slug = str(r["slug"])
        gr = check(conn, slug)
        if gr.passed:
            continue
        failed.append({"slug": slug, "reasons": gr.reasons, "flagged": gr.flagged_products})
        if auto_unpublish:
            try:
                article_state.unpublish(conn, slug, reason="; ".join(gr.reasons)[:200])
                unpublished.append(slug)
            except article_state.ArticleStateError:
                pass  # 이미 비공개 등 — 격리
    return {"checked": len(rows), "failed": failed, "unpublished": unpublished}
