"""tracker.gsc_store 단위 테스트 — GSC 검색어 적립·사전 (세션 #52). 네트워크 0."""

from __future__ import annotations

import sqlite3

import pytest

from tracker import gsc_store

SCHEMA = """
CREATE TABLE gsc_queries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at   TEXT    NOT NULL,
    period_start  TEXT    NOT NULL,
    period_end    TEXT    NOT NULL,
    query         TEXT    NOT NULL,
    page          TEXT    NOT NULL DEFAULT '',
    clicks        INTEGER NOT NULL DEFAULT 0,
    impressions   INTEGER NOT NULL DEFAULT 0,
    ctr           REAL    NOT NULL DEFAULT 0,
    position      REAL    NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX idx_gsc_queries_window
    ON gsc_queries (period_start, period_end, query, page);
"""


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.executescript(SCHEMA)
    yield c
    c.close()


def _row(q, imp, clicks=0, pos=10.0, page=None):
    keys = [q] if page is None else [q, page]
    return {"keys": keys, "clicks": clicks, "impressions": imp, "ctr": 0.0, "position": pos}


def test_save_rows_inserts(conn):
    n = gsc_store.save_rows(
        conn,
        [_row("나무도마", 5), _row("자취방 책상", 3)],
        period_start="2026-07-09",
        period_end="2026-08-05",
    )
    assert n == 2
    assert conn.execute("SELECT COUNT(*) FROM gsc_queries").fetchone()[0] == 2


def test_save_rows_is_idempotent_and_updates(conn):
    """★같은 창을 다시 적립해도 행이 늘지 않고 최신 수치로 갱신 — 무인 훅 재실행 안전."""
    w = {"period_start": "2026-07-09", "period_end": "2026-08-05"}
    gsc_store.save_rows(conn, [_row("나무도마", 5)], **w)
    gsc_store.save_rows(conn, [_row("나무도마", 9, clicks=1, pos=7.5)], **w)
    rows = conn.execute("SELECT impressions, clicks, position FROM gsc_queries").fetchall()
    assert rows == [(9, 1, 7.5)]


def test_save_rows_different_window_is_new_row(conn):
    gsc_store.save_rows(
        conn, [_row("나무도마", 5)], period_start="2026-07-01", period_end="2026-07-28"
    )
    gsc_store.save_rows(
        conn, [_row("나무도마", 8)], period_start="2026-07-09", period_end="2026-08-05"
    )
    assert conn.execute("SELECT COUNT(*) FROM gsc_queries").fetchone()[0] == 2


def test_save_rows_skips_blank_query(conn):
    n = gsc_store.save_rows(
        conn,
        [{"keys": [], "impressions": 3}, {"keys": ["  "], "impressions": 2}],
        period_start="a",
        period_end="b",
    )
    assert n == 0


def test_save_rows_normalizes_page_to_empty_string(conn):
    """page가 NULL이면 SQLite 유니크가 안 걸려 중복이 쌓인다 — ''로 정규화해야 멱등이 성립."""
    w = {"period_start": "s", "period_end": "e"}
    gsc_store.save_rows(conn, [_row("q", 1)], **w)
    gsc_store.save_rows(conn, [_row("q", 2)], **w)
    assert conn.execute("SELECT COUNT(*) FROM gsc_queries").fetchone()[0] == 1
    assert conn.execute("SELECT page FROM gsc_queries").fetchone()[0] == ""


def test_dictionary_uses_peak_not_sum(conn):
    """★겹치는 창을 합산하면 같은 노출이 여러 번 세어진다 — 최대값이 보수적 지표."""
    gsc_store.save_rows(
        conn, [_row("도마", 5, pos=12.0)], period_start="2026-07-01", period_end="2026-07-28"
    )
    gsc_store.save_rows(
        conn, [_row("도마", 7, pos=8.0)], period_start="2026-07-09", period_end="2026-08-05"
    )
    d = gsc_store.dictionary(conn)
    assert len(d) == 1
    assert d[0]["peak_impressions"] == 7  # 5+7=12이 아니다
    assert d[0]["best_position"] == 8.0
    assert d[0]["windows"] == 2
    assert d[0]["last_seen"] == "2026-08-05"


def test_dictionary_excludes_page_rows(conn):
    """page 차원 행은 사전 집계에서 제외 — 쿼리 단독 집계와 이중 계산되지 않게."""
    w = {"period_start": "s", "period_end": "e"}
    gsc_store.save_rows(conn, [_row("도마", 5), _row("도마", 5, page="https://x/a/")], **w)
    d = gsc_store.dictionary(conn)
    assert [x["query"] for x in d] == ["도마"]
    assert d[0]["windows"] == 1


def test_dictionary_min_impressions_filter(conn):
    w = {"period_start": "s", "period_end": "e"}
    gsc_store.save_rows(conn, [_row("a", 1), _row("b", 9)], **w)
    assert [x["query"] for x in gsc_store.dictionary(conn, min_impressions=5)] == ["b"]


def test_stats_reports_windows_and_uniques(conn):
    gsc_store.save_rows(
        conn, [_row("a", 1), _row("b", 2)], period_start="2026-07-01", period_end="2026-07-28"
    )
    gsc_store.save_rows(conn, [_row("a", 3)], period_start="2026-07-09", period_end="2026-08-05")
    st = gsc_store.stats(conn)
    assert st["unique_queries"] == 2 and st["rows"] == 3 and st["windows"] == 2
    assert st["first_period"] == "2026-07-01" and st["last_period"] == "2026-08-05"


def test_stats_empty(conn):
    assert gsc_store.stats(conn) == {
        "unique_queries": 0,
        "rows": 0,
        "first_period": "",
        "last_period": "",
        "windows": 0,
    }


def test_unmapped_candidates_ignores_spacing(conn):
    """구글은 'tpu 도마 추천'처럼 띄어 검색한다 — 공백만 다른 건 '새 후보'가 아니다."""
    w = {"period_start": "s", "period_end": "e"}
    gsc_store.save_rows(conn, [_row("나무 도마", 9), _row("접이식 도마", 4)], **w)
    got = gsc_store.unmapped_candidates(conn, {"나무도마", "스텐도마"})
    assert [x["query"] for x in got] == ["접이식 도마"]


def test_unmapped_candidates_excludes_recommend_suffix(conn):
    """★라이브 적발: 씨앗 '서재책상'이 있는데 '서재 책상 추천'이 새 후보로 잡히던 오검출.

    한국어 검색은 '~추천'을 붙이는 일이 흔하고, 그런 근친 변형은 등재 금지(JJ3)라 후보가 아니다.
    """
    w = {"period_start": "s", "period_end": "e"}
    gsc_store.save_rows(
        conn,
        [_row("서재 책상 추천", 7), _row("고등학생 자취", 5), _row("인체 공학 의자", 3)],
        **w,
    )
    got = [x["query"] for x in gsc_store.unmapped_candidates(conn, {"서재책상", "사무용 의자"})]
    assert "서재 책상 추천" not in got  # 씨앗이 부분문자열로 커버
    assert got == ["고등학생 자취", "인체 공학 의자"]


def test_is_covered_by_seeds_both_directions():
    seeds = {gsc_store.normalize(s) for s in ("서재책상", "TPU도마")}
    assert gsc_store.is_covered_by_seeds("서재 책상 추천", seeds)  # 씨앗 ⊂ 쿼리
    assert gsc_store.is_covered_by_seeds("tpu도마", seeds)  # 대소문자 무시
    assert gsc_store.is_covered_by_seeds("도마", {gsc_store.normalize("TPU도마")})  # 쿼리 ⊂ 씨앗
    assert not gsc_store.is_covered_by_seeds("고등학생 자취", seeds)
    assert gsc_store.is_covered_by_seeds("   ", seeds)  # 빈 쿼리는 후보 아님
