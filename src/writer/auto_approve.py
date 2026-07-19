"""writer.auto_approve — 검증 통과 글의 자동 승인 (세션 #29, B-i 사람 게이트 자동화).

E7(사람 1클릭 승인)을 'fail-closed 자동 승인'으로 대체 — **auto_mode ON일 때만** 호출된다.
자동 승인 조건(전부 충족해야 approved 전이):
  1. status='validated' (5게이트 truth/schema/disclosure/links/seo 전부 통과)
  2. 키워드가 카테고리에 매핑됨 — 매핑 없으면 적합성 검증 불가 → 보류(사람)
  3. 자동수집(ali) featured 상품이 전부 키워드-카테고리 적합(off-target 0).
     수동 쿠팡 배너는 사람이 고른 것이라 적합성 검사 면제(수집 단계 정책과 일치, 세션 #39).
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


def eligible(conn: sqlite3.Connection, draft_id: int) -> tuple[bool, str, str]:
    """draft가 자동 승인 가능한지. 반환: (ok, reason, code).

    code = machine-readable 보류 사유(영문 enum) — 무인 가시화·알림이 '문제 보류'를 분류·집계하는
    단일 소스(세션 #39). 사람용 reason과 분리해 로그 문자열 파싱 없이 코드로 판정한다.
    값: ok / no_draft / not_validated / no_keyword / unmapped / category_draft / payload_error /
    featured_zero / offtarget.
    """
    row = conn.execute(
        "SELECT status, keyword_id, enriched_payload FROM drafts WHERE id = ?", (draft_id,)
    ).fetchone()
    if row is None:
        return False, "draft 없음", "no_draft"
    status, keyword_id, ep_json = row[0], row[1], row[2]
    if status != "validated":
        return False, f"상태 {status!r}(validated 아님)", "not_validated"
    keyword = _draft_keyword(conn, keyword_id)
    if not keyword:
        return False, "키워드 추적 불가(검증 불가→보류)", "no_keyword"
    terms = keyword_relevance.relevance_terms(keyword)
    if terms is None:
        return False, f"키워드 {keyword!r} 카테고리 미매핑(적합성 검증 불가→보류)", "unmapped"
    require_any, require_all, exclude, slug = terms
    # ★세션 #45: 매핑됐어도 카테고리가 비공개(draft)면 보류 — 공개 허브 없는 고아 글(빵부스러기·
    # 내부링크 폴백 강등)이 완전무인으로 발행되는 것을 차단. 카테고리를 공개 승인하면 자동 해소.
    # 행 없음·구 스키마는 막지 않음(fail-open — category_blocked 참조).
    if keyword_relevance.category_blocked(conn, slug):
        return (
            False,
            f"카테고리 {slug!r} 비공개(draft) — 카테고리 공개 승인 후 자동 발행",
            "category_draft",
        )
    try:
        ep = json.loads(ep_json) if ep_json else {}
    except (json.JSONDecodeError, TypeError):
        return False, "enriched_payload 파싱 불가", "payload_error"
    featured = ep.get("products") or []
    if not featured:
        return False, "featured 상품 0개", "featured_zero"
    offtarget = [
        str(p.get("name") or "")
        for p in featured
        # 수동 쿠팡 배너(source='coupang')는 사람이 직접 고른 것이라 적합성 필터 면제 —
        # 수집 단계(_gather_keyword_candidates·keyword_relevance.filter_products)와 동일 정책.
        # 무중력의자·리클라이너처럼 카테고리 exclude_terms와 충돌하는 키워드의 주인 큐레이션
        # 상품이 거부돼 무인 발행이 막히던 문제를 근본 해결(세션 #39). ali 자동수집은 그대로 검사.
        if str(p.get("source") or "").lower() != "coupang"
        and not product_filter.is_relevant(
            str(p.get("name") or ""),
            require_any=require_any,
            require_all=require_all,
            exclude_terms=exclude,
        )
    ]
    if offtarget:
        return False, f"featured off-target {len(offtarget)}개: {offtarget[0][:30]}", "offtarget"
    return True, "적합(게이트+적합성 통과)", "ok"


def auto_approve(
    conn: sqlite3.Connection, *, apply: bool = True, min_published: int = 0
) -> dict[str, Any]:
    """validated draft 전체 판정 → 적합한 것만 approved 전이(apply). 미달은 validated 유지(보류).

    min_published: 발행 이력(published)이 이 수 미만이면 자동 승인 전체 보류 — 초기 사람 검수
    단계(세션 #33 안전장치·autonomous-safe-system). 0이면 게이트 없음(하위호환). 사람이 N편
    직접 승인·발행해 품질을 눈으로 확인한 뒤에만 자동 승인으로 전환(미탐<오탐).

    반환: {approved:[id], held:[{draft,reason,code}]}. code는 eligible의 machine-readable 사유
    (min_published 의도적 보류는 code='min_published' — 무인 알림이 '정상 보류 vs 문제 보류'를
    코드로 구분해 오경보를 막는다, 세션 #39). 실패 격리 — 한 건이 다음을 막지 않는다.
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
            # code='min_published' = 의도된 정상 보류(첫 N편 사람검수) — 알림에서 '문제'로 안 침.
            return {
                "approved": [],
                "held": [
                    {"draft": int(r[0]), "reason": reason, "code": "min_published"} for r in rows
                ],
            }
    for r in rows:
        did = int(r[0])
        ok, reason, code = eligible(conn, did)
        if not ok:
            held.append({"draft": did, "reason": reason, "code": code})
            continue
        if apply:
            try:
                state_machine.transition(conn, did, "approved", reason="auto-approve (B-i)")
            except (state_machine.IllegalStateError, ValueError) as e:  # 전이 실패 격리
                held.append({"draft": did, "reason": f"전이 실패: {e}", "code": "transition_error"})
                continue
        approved.append(did)
    return {"approved": approved, "held": held}
