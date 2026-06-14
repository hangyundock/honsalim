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
    def test_ranked_by_volume_and_filtered(self) -> None:
        conn = _db()
        recs = kr.recommend(conn, seeds=SEED, fetch=_fetch)
        kws = [r["keyword"] for r in recs]
        # 검색량 내림차순, 브랜드/거래성/seed/no_core 제외
        assert kws == ["게이밍의자", "책상의자", "공부의자"]
        assert recs[0]["source"] == "naver"
        assert recs[0]["channel"] == "ali"
        assert recs[0]["volume"] == 30100
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
        assert [r["keyword"] for r in recs] == ["게이밍의자", "책상의자"]

    def test_top_recommendation(self) -> None:
        conn = _db()
        top = kr.top_recommendation(conn, seeds=SEED, fetch=_fetch)
        assert top is not None
        assert top["keyword"] == "게이밍의자"

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

    def test_recommends_and_adds_when_empty(self) -> None:
        conn = _db()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["source"] == "recommend"
        assert picked["keyword"] == "게이밍의자"  # 검색량 1위
        # 큐에 실제로 추가됐는지(이후 generate가 쓸 수 있게)
        row = conn.execute(
            "SELECT keyword, status FROM keyword_queue WHERE id = ?", (picked["keyword_id"],)
        ).fetchone()
        assert row[0] == "게이밍의자"
        assert row[1] == "pending"

    def test_none_when_no_recommendations(self) -> None:
        conn = _db()
        assert kr.auto_pick_keyword(conn, seeds=[], live=False) is None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
