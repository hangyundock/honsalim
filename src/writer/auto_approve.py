"""writer.auto_approve — 검증 통과 글의 자동 승인 (세션 #29, B-i 사람 게이트 자동화).

E7(사람 1클릭 승인)을 'fail-closed 자동 승인'으로 대체 — **auto_mode ON일 때만** 호출된다.
자동 승인 조건(전부 충족해야 approved 전이):
  1. status='validated' (5게이트 truth/schema/disclosure/links/seo 전부 통과)
  2. 키워드가 카테고리에 매핑됨 — 매핑 없으면 적합성 검증 불가 → 보류(사람)
  3. featured 상품이 전부 키워드-카테고리 적합(off-target 0)
하나라도 불충족이면 보류(validated 유지·사람 검토). 미탐<오탐 — 나쁜 글 자동발행보다 좋은 글 보류.

비용 0(DB·문자열만). 자동 승인된 글은 publish-queue가 promote→build→deploy 한다.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from collector import keyword_relevance, product_filter
from writer import state_machine


def _draft_keyword(conn: sqlite3.Connection, keyword_id: int | None) -> str | None:
    """draft가 파생된 키워드 (keyword_queue). 없으면 None."""
    if keyword_id is None:
        return None
    has_kw = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='keyword_queue'"
    ).fetchone()
    if has_kw is None:
        return None
    row = conn.execute("SELECT keyword FROM keyword_queue WHERE id = ?", (keyword_id,)).fetchone()
    return str(row[0]) if row and row[0] else None


def eligible(conn: sqlite3.Connection, draft_id: int) -> tuple[bool, str]:
    """draft가 자동 승인 가능한지 (validated + 키워드 매핑 + featured 적합). 반환: (ok, reason)."""
    row = conn.execute(
        "SELECT status, keyword_id, enriched_payload FROM drafts WHERE id = ?", (draft_id,)
    ).fetchone()
    if row is None:
        return False, "draft 없음"
    status, keyword_id, ep_json = row[0], row[1], row[2]
    if status != "validated":
        return False, f"상태 {status!r}(validated 아님)"
    keyword = _draft_keyword(conn, keyword_id)
    if not keyword:
        return False, "키워드 추적 불가(검증 불가→보류)"
    terms = keyword_relevance.relevance_terms(keyword)
    if terms is None:
        return False, f"키워드 {keyword!r} 카테고리 미매핑(적합성 검증 불가→보류)"
    require_any, require_all, exclude, _slug = terms
    try:
        ep = json.loads(ep_json) if ep_json else {}
    except (json.JSONDecodeError, TypeError):
        return False, "enriched_payload 파싱 불가"
    featured = ep.get("products") or []
    if not featured:
        return False, "featured 상품 0개"
    offtarget = [
        str(p.get("name") or "")
        for p in featured
        if not product_filter.is_relevant(
            str(p.get("name") or ""),
            require_any=require_any,
            require_all=require_all,
            exclude_terms=exclude,
        )
    ]
    if offtarget:
        return False, f"featured off-target {len(offtarget)}개: {offtarget[0][:30]}"
    return True, "적합(게이트+적합성 통과)"


def auto_approve(
    conn: sqlite3.Connection, *, apply: bool = True, min_published: int = 0
) -> dict[str, Any]:
    """validated draft 전체 판정 → 적합한 것만 approved 전이(apply). 미달은 validated 유지(보류).

    min_published: 발행 이력(published)이 이 수 미만이면 자동 승인 전체 보류 — 초기 사람 검수
    단계(세션 #33 안전장치·autonomous-safe-system). 0이면 게이트 없음(하위호환). 사람이 N편
    직접 승인·발행해 품질을 눈으로 확인한 뒤에만 자동 승인으로 전환(미탐<오탐).

    반환: {approved:[id], held:[{draft,reason}]}. 실패 격리 — 한 건이 다음을 막지 않는다.
    """
    rows = conn.execute("SELECT id FROM drafts WHERE status = 'validated' ORDER BY id").fetchall()
    approved: list[int] = []
    held: list[dict[str, Any]] = []
    if min_published > 0:
        pub = int(
            conn.execute("SELECT COUNT(*) FROM drafts WHERE status = 'published'").fetchone()[0]
        )
        if pub < min_published:
            reason = f"초기 검수 단계(발행 {pub}/{min_published}편) — 사람 승인 필요"
            return {"approved": [], "held": [{"draft": int(r[0]), "reason": reason} for r in rows]}
    for r in rows:
        did = int(r[0])
        ok, reason = eligible(conn, did)
        if not ok:
            held.append({"draft": did, "reason": reason})
            continue
        if apply:
            try:
                state_machine.transition(conn, did, "approved", reason="auto-approve (B-i)")
            except (state_machine.IllegalStateError, ValueError) as e:  # 전이 실패 격리
                held.append({"draft": did, "reason": f"전이 실패: {e}"})
                continue
        approved.append(did)
    return {"approved": approved, "held": held}
