"""tracker.gsc_store — GSC 검색어 적립·조회 (세션 #52).

왜 적립하는가: GSC는 **최근 16개월만** 보관하고, 우리가 궁금한 건 "구글에서 실제로 검색되는
우리 주제어"다. 지금 표본은 28일 노출 66 중 82%가 익명화라 판단 불가지만, 주 1회 쌓아두면
몇 달 뒤 **네이버 신호 vs 구글 실수요**를 데이터로 비교할 수 있다(#52 재평가 기준: 월 노출
500+ 또는 비익명 쿼리 30+).

멱등: 같은 (창, 쿼리, 페이지)를 다시 적립하면 최신 수치로 갱신한다 — 무인 훅이 두 번 돌아도
행이 늘지 않는다. 저장은 read-only 조회 결과를 넣는 것뿐이라 발행 파이프라인과 무관하다.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Any


def _norm_page(value: Any) -> str:
    """page는 NULL 대신 '' — SQLite가 NULL을 유니크 비교에서 제외해 중복이 생기는 것을 막는다."""
    return str(value or "").strip()


def save_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    *,
    period_start: str,
    period_end: str,
    captured_at: str | None = None,
) -> int:
    """gsc.query() 결과를 적립. 반환 = 저장(갱신 포함)된 행 수.

    rows의 keys는 ``[query]`` 또는 ``[query, page]``(dimensions에 page를 넣은 경우).
    """
    stamp = captured_at or dt.datetime.now().isoformat(timespec="seconds")
    saved = 0
    for r in rows:
        keys = list(r.get("keys") or [])
        if not keys or not str(keys[0]).strip():
            continue  # 쿼리 없는 행은 적립 대상이 아니다
        query = str(keys[0]).strip()
        page = _norm_page(keys[1] if len(keys) > 1 else "")
        conn.execute(
            """
            INSERT INTO gsc_queries
                (captured_at, period_start, period_end, query, page,
                 clicks, impressions, ctr, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (period_start, period_end, query, page) DO UPDATE SET
                captured_at = excluded.captured_at,
                clicks      = excluded.clicks,
                impressions = excluded.impressions,
                ctr         = excluded.ctr,
                position    = excluded.position
            """,
            (
                stamp,
                period_start,
                period_end,
                query,
                page,
                int(r.get("clicks") or 0),
                int(r.get("impressions") or 0),
                float(r.get("ctr") or 0.0),
                float(r.get("position") or 0.0),
            ),
        )
        saved += 1
    conn.commit()
    return saved


def dictionary(
    conn: sqlite3.Connection, *, limit: int = 100, min_impressions: int = 1
) -> list[dict[str, Any]]:
    """구글 실수요 사전 — 쿼리별 누적 집계.

    ★창이 겹치면 노출이 중복 계산된다(28일 창을 매주 적립하면 같은 노출이 4번 잡힌다).
    그래서 합이 아니라 **창 하나당 최대값**을 쓴다: 쿼리별 max(impressions)는 "이 쿼리가 한
    조회 창에서 최대 몇 번 노출됐나"로, 중복 없이 규모를 비교할 수 있는 보수적 지표다.
    """
    sql = """
        SELECT query,
               MAX(impressions) AS peak_impressions,
               MAX(clicks)      AS peak_clicks,
               MIN(position)    AS best_position,
               COUNT(DISTINCT period_start || '~' || period_end) AS windows,
               MAX(period_end)  AS last_seen
        FROM gsc_queries
        WHERE page = ''
        GROUP BY query
        HAVING peak_impressions >= ?
        ORDER BY peak_impressions DESC, best_position ASC
        LIMIT ?
    """
    cur = conn.execute(sql, (int(min_impressions), int(limit)))
    return [
        {
            "query": r[0],
            "peak_impressions": int(r[1] or 0),
            "peak_clicks": int(r[2] or 0),
            "best_position": float(r[3] or 0.0),
            "windows": int(r[4] or 0),
            "last_seen": r[5] or "",
        }
        for r in cur.fetchall()
    ]


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    """적립 현황 — 재평가 기준(비익명 쿼리 30+) 도달 여부 판단용."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT query), COUNT(*), MIN(period_start), MAX(period_end), "
        "COUNT(DISTINCT period_start || '~' || period_end) FROM gsc_queries"
    ).fetchone()
    return {
        "unique_queries": int(row[0] or 0),
        "rows": int(row[1] or 0),
        "first_period": row[2] or "",
        "last_period": row[3] or "",
        "windows": int(row[4] or 0),
    }


def normalize(text: str) -> str:
    """비교용 정규화 — 공백 제거 + 소문자. 구글은 'tpu 도마 추천'처럼 띄어 검색한다."""
    return "".join(str(text or "").split()).lower()


def is_covered_by_seeds(query: str, seeds_ns: set[str]) -> bool:
    """이 쿼리를 기존 씨앗이 이미 커버하는가.

    ★정확 일치로 보면 안 된다: 한국어 검색은 '~추천'을 붙이는 일이 흔해서, 씨앗 '서재책상'이
    있는데도 '서재 책상 추천'이 매번 '새 후보'로 잡힌다(라이브 실측 — 9개 쿼리 전부 오검출).
    그런 근친 변형은 등재 금지 대상이므로(DECISIONS JJ3) 후보에서 빼는 게 맞다.
    → **포함 관계**로 판정한다: 씨앗이 쿼리에 들어 있거나(서재책상 ⊂ 서재책상추천) 그 반대면 커버됨.
    """
    q = normalize(query)
    if not q:
        return True  # 빈 쿼리는 후보가 아니다
    return any(s and (s in q or q in s) for s in seeds_ns)


def unmapped_candidates(
    conn: sqlite3.Connection, seed_terms: set[str], *, limit: int = 30
) -> list[dict[str, Any]]:
    """어떤 씨앗도 커버하지 않는 실수요 쿼리 — 씨앗 보강 후보(구글 실측 기반).

    ★자동 등재하지 않는다 — 후보 제시까지만(JJ3 근친 변형 금지·컨셉 정합 판단은 사람 몫).
    """
    seeds_ns = {normalize(s) for s in seed_terms if s}
    out = []
    for row in dictionary(conn, limit=limit * 4):
        if is_covered_by_seeds(row["query"], seeds_ns):
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
