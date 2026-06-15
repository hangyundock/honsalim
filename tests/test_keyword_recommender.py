"""writer.keyword_recommender 회귀 테스트 — 추천 키워드 (세션 #26).

정의된 선정 방식(keyword_research)을 씨앗에 적용 → 검색량순·중복제외·자가복원 검증.
라이브 네트워크 없이 fetch 의존성 주입 + :memory: DB(실 마이그레이션 001~007).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from writer import keyword_queue as kq
from writer import keyword_recommender as kr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.commit()
    return conn


# 씨앗 1개(사무용 의자) + 캐시 보조키워드 — 실데이터 모방 (세션 #15 값 기반)
SEED: list[dict[str, Any]] = [
    {
        "seed": "사무용 의자",
        "core": "의자",
        "exclude_terms": (),
        "category": "office-chair",
        "cached_secondary": ["메쉬의자", "중역의자"],
    }
]

ROWS: dict[str, list[dict[str, Any]]] = {
    "사무용 의자": [
        {"keyword": "공부의자", "volume": 9000, "competition": "중간"},
        {"keyword": "게이밍의자", "volume": 30100, "competition": "높음"},
        {"keyword": "책상의자", "volume": 20620, "competition": "중간"},
        {"keyword": "듀오백의자", "volume": 8590, "competition": "중간"},  # 브랜드 → 제외
        {"keyword": "중고의자", "volume": 5000, "competition": "중간"},  # 거래성 → 제외
        {"keyword": "사무용 의자", "volume": 26100, "competition": "중간"},  # == seed → 제외
        {"keyword": "접이식테이블", "volume": 41810, "competition": "중간"},  # no_core → 제외
    ],
}


def _fetch(seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
    return [dict(r) for r in ROWS.get(seed, [])]


class TestRecommend:
    def test_ranked_by_winnable_and_filtered(self) -> None:
        conn = _db()
        recs = kr.recommend(conn, seeds=SEED, fetch=_fetch)
        kws = [r["keyword"] for r in recs]
        # winnable 정렬(세션 #33): 경쟁 낮은 '틈' 우선 — 책상의자(중간·20620) > 게이밍의자(높음·30100,
        # 검색량 1위지만 경쟁 높아 후순위) > 공부의자(중간·9000). 브랜드/거래성/seed/no_core 제외.
        assert kws == ["책상의자", "게이밍의자", "공부의자"]
        assert recs[0]["source"] == "naver"
        assert recs[0]["channel"] == "ali"
        assert recs[0]["keyword"] == "책상의자"
        assert recs[0]["volume"] == 20620
        assert recs[0]["category"] == "office-chair"

    def test_dedupe_against_queue(self) -> None:
        conn = _db()
        kq.add_keyword(conn, "게이밍의자", channel="ali")
        recs = kr.recommend(conn, seeds=SEED, fetch=_fetch)
        assert "게이밍의자" not in [r["keyword"] for r in recs]

    def test_dedupe_against_scenarios(self) -> None:
        conn = _db()
        conn.execute("INSERT INTO personas (slug, title_ko, description) VALUES ('p','자취','d')")
        pid = conn.execute("SELECT id FROM personas LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO scenarios (slug, title_ko, description, persona_id, active) "
            "VALUES ('s1','책상의자','d',?,1)",
            (pid,),
        )
        conn.commit()
        recs = kr.recommend(conn, seeds=SEED, fetch=_fetch)
        assert "책상의자" not in [r["keyword"] for r in recs]

    def test_fallback_to_cache_on_naver_failure(self) -> None:
        conn = _db()

        def boom(seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
            raise RuntimeError("naver down")

        recs = kr.recommend(conn, seeds=SEED, fetch=boom)
        assert [r["keyword"] for r in recs] == ["메쉬의자", "중역의자"]
        assert all(r["source"] == "cached" and r["volume"] is None for r in recs)

    def test_live_false_uses_cache_only(self) -> None:
        conn = _db()
        recs = kr.recommend(conn, seeds=SEED, live=False)
        assert [r["keyword"] for r in recs] == ["메쉬의자", "중역의자"]
        assert all(r["source"] == "cached" for r in recs)

    def test_custom_seed_no_core_filter(self) -> None:
        conn = _db()

        def fetch(seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
            assert seed == "원룸 수납"
            return [{"keyword": "원룸 수납장", "volume": 3000, "competition": "중간"}]

        recs = kr.recommend(conn, custom_seed="원룸 수납", fetch=fetch)
        assert recs[0]["keyword"] == "원룸 수납장"
        assert recs[0]["category"] is None

    def test_limit(self) -> None:
        conn = _db()
        recs = kr.recommend(conn, seeds=SEED, fetch=_fetch, limit=2)
        assert [r["keyword"] for r in recs] == ["책상의자", "게이밍의자"]

    def test_top_recommendation(self) -> None:
        conn = _db()
        top = kr.top_recommendation(conn, seeds=SEED, fetch=_fetch)
        assert top is not None
        assert top["keyword"] == "책상의자"  # winnable 1위(경쟁 낮은 틈)

    def test_top_recommendation_none_when_empty(self) -> None:
        conn = _db()
        assert kr.top_recommendation(conn, seeds=[], live=False) is None


class TestAutoPick:
    def test_uses_pending_first(self) -> None:
        conn = _db()
        kq.add_keyword(conn, "기존키워드", channel="ali", score=100.0)
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["source"] == "queue"
        assert picked["keyword"] == "기존키워드"

    def test_pending_priority_by_score(self) -> None:
        conn = _db()
        kq.add_keyword(conn, "낮은점수", channel="ali", score=10.0)
        kq.add_keyword(conn, "높은점수", channel="ali", score=9999.0)
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "높은점수"  # score 내림차순

    def test_auto_pick_matches_display_top(self) -> None:
        # 자동 선정 = 대시보드 목록 맨 위 행과 동일해야 함(정렬 일치)
        from dashboard import queries

        conn = _db()
        for name, sc in [("에이", 100.0), ("비이", 5000.0), ("씨이", 300.0)]:
            kq.add_keyword(conn, name, channel="ali", score=sc)
        display_top = queries.list_keywords(conn, status="pending")[0]["keyword"]
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == display_top == "비이"  # 최고 score = 맨 위

    def test_recommends_and_adds_when_empty(self) -> None:
        conn = _db()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["source"] == "recommend"
        assert picked["keyword"] == "책상의자"  # winnable 1위(경쟁 낮은 틈)
        # 큐에 실제로 추가됐는지(이후 generate가 쓸 수 있게)
        row = conn.execute(
            "SELECT keyword, status FROM keyword_queue WHERE id = ?", (picked["keyword_id"],)
        ).fetchone()
        assert row[0] == "책상의자"
        assert row[1] == "pending"

    def test_none_when_no_recommendations(self) -> None:
        conn = _db()
        assert kr.auto_pick_keyword(conn, seeds=[], live=False) is None

    def test_target_products_keyword_prioritized(self) -> None:
        # 미리선택(쿠팡)이 세팅된 키워드는 검색량 높은 알리 키워드보다 우선 (Part2)
        from collector import coupang_manual as cm

        conn = _db()
        kq.add_keyword(conn, "고검색알리", channel="ali", score=99999.0)
        kid = kq.add_keyword(conn, "쿠팡세팅", channel="coupang", score=0.0)
        cm.add_to_keyword(
            conn, kid, cm.build_manual_product("쿠팡상품", "https://link.coupang.com/a/Z")
        )
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "쿠팡세팅"  # target_products 있는 키워드 우선
        assert picked["source"] == "queue"

    def test_display_lists_target_products_first(self) -> None:
        from collector import coupang_manual as cm
        from dashboard import queries

        conn = _db()
        kq.add_keyword(conn, "고검색", channel="ali", score=99999.0)
        kid = kq.add_keyword(conn, "쿠팡세팅", channel="coupang", score=0.0)
        cm.add_to_keyword(conn, kid, cm.build_manual_product("P", "https://link.coupang.com/a/Z"))
        rows = queries.list_keywords(conn, status="pending")
        assert rows[0]["keyword"] == "쿠팡세팅"  # 미리선택 있는 것 맨 위 (자동 선정과 일치)


class TestWinnableScore:
    def test_lower_competition_ranks_higher(self) -> None:
        # 같은 검색량이면 경쟁 낮을수록 '틈' 점수가 높다(낮음 > 중간 > 높음).
        assert kr.winnable_score(10000, "낮음") > kr.winnable_score(10000, "중간")
        assert kr.winnable_score(10000, "중간") > kr.winnable_score(10000, "높음")

    def test_volume_capped(self) -> None:
        # 상한 이상 검색량은 동일 취급 — head 키워드 과가중 억제.
        assert kr.winnable_score(30000, "중간") == kr.winnable_score(99999, "중간")

    def test_cached_volume_none_is_lowest(self) -> None:
        # 캐시(검색량 미상)는 최하 — 실데이터 키워드가 항상 우선.
        assert kr.winnable_score(None, "낮음") == -1.0
        assert kr.winnable_score(None, "낮음") < kr.winnable_score(1, "높음")

    def test_unknown_competition_is_middle(self) -> None:
        # 미상 경쟁도는 중간(0.5) — 낮음(1.0)과 높음(0.3) 사이.
        s = kr.winnable_score(10000, "unknown")
        assert kr.winnable_score(10000, "높음") < s < kr.winnable_score(10000, "낮음")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
