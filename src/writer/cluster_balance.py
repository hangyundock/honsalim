"""writer.cluster_balance — 클러스터(카테고리) 포화도 판정·추천 정렬 (세션 #52).

왜 필요한가: 추천 창이 **검색량순**이라 맨 위가 미매핑(발행 불가)이고, 어느 클러스터가
이미 포화인지는 화면에 없었다. 그래서 운영자가 "이 키워드가 포화 주제인가"를 머리로
판단해야 했는데, 그건 키워드 선정을 자동화한 취지와 정면으로 어긋난다(주인 지적 #52).

실측 근거(2026-08-07): 발행 24편이 의자 7 · 도마 6 · 책상 5에 몰려 전체의 75%였고,
게이밍의자 글은 구글이 크롤까지 하고도 **색인을 거부**했다(Crawled - not indexed).
유사 주제 과밀이 색인 가치 판단에 불리하게 작용한다는 신호다.

설계: GUI에서 분리(테스트 가능·CI 안전, C14 원칙). 화면은 이 모듈의 판정 결과만 표시한다.
정렬 사상은 무인 리필(HH3: 카테고리 균형)과 같게 맞춰 자동/수동 판단이 어긋나지 않게 한다.
"""

from __future__ import annotations

import sqlite3
from typing import Any

# 포화 배수 — 평균 편수의 이 배를 넘으면 '포화'. 절대 편수(예: 5편)로 잡으면 사이트가
# 커질수록 전부 포화로 잡히므로 **상대 기준**을 쓴다(규모에 따라 자동으로 올라간다).
SATURATION_RATIO = 1.5
# 클러스터가 이 편수 미만이면 평균과 무관하게 포화로 보지 않는다 — 표본이 적을 때
# (예: 전 카테고리 1편, 평균 1.0) 2편짜리가 '포화'로 잡히는 것을 막는다.
SATURATION_MIN_ARTICLES = 3


def published_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """카테고리별 발행 글 수. 키워드→카테고리는 운영 경로와 **같은 함수**로 해석한다."""
    from collector.keyword_relevance import resolve_category

    counts: dict[str, int] = {}
    rows = conn.execute(
        "SELECT kq.keyword FROM keyword_queue kq "
        "JOIN articles a ON a.slug = kq.slug WHERE a.status = 'published'"
    ).fetchall()
    for (kw,) in rows:
        cat = resolve_category(str(kw or ""))
        if cat:
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def saturation_threshold(counts: dict[str, int]) -> float:
    """포화 경계 편수 — 평균 곱하기 SATURATION_RATIO (최소 SATURATION_MIN_ARTICLES)."""
    if not counts:
        return float(SATURATION_MIN_ARTICLES)
    avg = sum(counts.values()) / len(counts)
    return max(float(SATURATION_MIN_ARTICLES), avg * SATURATION_RATIO)


def annotate(recs: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    """각 추천에 cluster / cluster_count / saturated 를 채워 넣는다(원본 dict 갱신).

    카테고리를 못 찾는 키워드(미매핑)는 cluster=None·saturated=False — 포화로 취급하지
    않는다. 그런 키워드는 이미 '발행 불가'로 걸러지므로 이중으로 벌주지 않는다.
    """
    from collector.keyword_relevance import resolve_category

    limit = saturation_threshold(counts)
    for r in recs:
        cat = resolve_category(str(r.get("keyword") or ""))
        r["cluster"] = cat
        r["cluster_count"] = counts.get(cat, 0) if cat else 0
        r["saturated"] = bool(cat and counts.get(cat, 0) >= limit)
    return recs


def sort_key(rec: dict[str, Any]) -> tuple[int, int, int, float]:
    """정렬 키 — ①발행 가능 ②포화 아님 ③글 적은 클러스터 ④점수 높은 순.

    ★맨 위가 항상 '지금 넣기 가장 좋은 키워드'가 되게 한다. 기존엔 검색량순이라 맨 위가
    미매핑이었고, '⭐1순위만 추가' 버튼이 발행 불가 키워드를 큐에 넣는 함정이 있었다.
    """
    publishable = rec.get("publishable")
    # publishable 키가 없으면(구 호출부·테스트) 중립 취급 — 없는 정보로 벌주지 않는다.
    rank_pub = 0 if publishable is None or publishable else 1
    rank_sat = 1 if rec.get("saturated") else 0
    count = int(rec.get("cluster_count") or 0)
    score = float(rec.get("score") or 0.0)
    return (rank_pub, rank_sat, count, -score)


def prepare(
    recs: list[dict[str, Any]],
    counts: dict[str, int],
    *,
    show_unpublishable: bool = False,
    show_saturated: bool = False,
) -> dict[str, Any]:
    """추천 목록을 화면에 그대로 쓸 수 있는 형태로 정리.

    반환 {rows, hidden_unpublishable, hidden_saturated, total, threshold}.
    ★숨김은 기본값일 뿐 **차단이 아니다** — 화면 토글로 언제든 펼칠 수 있어야 한다
    (주인 결정을 막지 않는다·[[feedback_assist_not_overstep]]).
    """
    annotate(recs, counts)
    ordered = sorted(recs, key=sort_key)
    rows = []
    hid_unpub = 0
    hid_sat = 0
    for r in ordered:
        unpub = r.get("publishable") is False
        if unpub and not show_unpublishable:
            hid_unpub += 1
            continue
        if r.get("saturated") and not show_saturated:
            hid_sat += 1
            continue
        rows.append(r)
    return {
        "rows": rows,
        "hidden_unpublishable": hid_unpub,
        "hidden_saturated": hid_sat,
        "total": len(recs),
        "threshold": saturation_threshold(counts),
    }


def summary_line(prepared: dict[str, Any]) -> str:
    """목록 위에 띄울 한 줄 — 왜 적게 보이는지 설명한다(빈 화면 오해 방지)."""
    parts = [f"표시 {len(prepared['rows'])}건"]
    hid = []
    if prepared["hidden_unpublishable"]:
        hid.append(f"발행 불가 {prepared['hidden_unpublishable']}건")
    if prepared["hidden_saturated"]:
        hid.append(f"포화 클러스터 {prepared['hidden_saturated']}건")
    if hid:
        parts.append("숨김: " + " · ".join(hid))
    parts.append(f"포화 기준 {prepared['threshold']:.1f}편 이상")
    return " · ".join(parts)
