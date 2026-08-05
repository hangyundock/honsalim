"""writer.keyword_recommender 회귀 테스트 — 추천 키워드 (세션 #26).

정의된 선정 방식(keyword_research)을 씨앗에 적용 → 검색량순·중복제외·자가복원 검증.
라이브 네트워크 없이 fetch 의존성 주입 + :memory: DB(실 마이그레이션 001~007).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, ClassVar

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
        {"keyword": "공부의자", "volume": 900, "competition": "중간"},
        {"keyword": "게이밍의자", "volume": 1900, "competition": "높음"},
        {"keyword": "책상의자", "volume": 1500, "competition": "중간"},
        {"keyword": "듀오백의자", "volume": 850, "competition": "중간"},  # 브랜드 → 제외
        {"keyword": "중고의자", "volume": 500, "competition": "중간"},  # 거래성 → 제외
        {"keyword": "사무용 의자", "volume": 1600, "competition": "중간"},  # == seed → 제외
        {"keyword": "접이식테이블", "volume": 1800, "competition": "중간"},  # no_core → 제외
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
        assert recs[0]["volume"] == 1500
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
            return [{"keyword": "원룸 수납장", "volume": 1500, "competition": "중간"}]

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

    def test_publishable_keyword_preferred_over_unmapped(self) -> None:
        # 세션 #39 후순위 강등: 미매핑(고점수)보다 매핑된(저점수) 키워드를 우선 집는다.
        conn = _db()
        kq.add_keyword(conn, "양자역학교재", channel="ali", score=99999.0)  # 미매핑
        kq.add_keyword(conn, "컴퓨터의자", channel="ali", score=10.0)  # office-chair 매핑
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "컴퓨터의자"  # 발행가능(매핑) 우선 — 고점수 미매핑보다 먼저

    def test_all_unmapped_falls_back_to_top_not_none(self) -> None:
        # 전부 미매핑이면 멈추지 않고 맨 위 1건(기존 정렬 보존) — skip·None 아님(digest가 사유 보고).
        conn = _db()
        kq.add_keyword(conn, "양자역학교재", channel="ali", score=10.0)
        kq.add_keyword(conn, "상대성이론책", channel="ali", score=9999.0)
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["source"] == "queue"
        assert picked["keyword"] == "상대성이론책"  # score 최고(기존 정렬 보존)


class TestRefillPublishableOnly:
    """★세션 #45: 추천 자동 보충(refill)은 '매핑 + 공개 카테고리' 후보만 큐에 넣는다.

    미매핑 추천을 넣으면 ali 수집 skip→상품 0→failed = 그날 무인 발행 0(여름이불 실사고),
    draft 카테고리 추천은 공개 허브 없는 고아 글이 된다. 사람 경로(수동 추가)는 제한 없음.
    """

    def test_refill_skips_unmapped_picks_mapped(self) -> None:
        conn = _db()
        seeds: list[dict[str, Any]] = [
            {
                "seed": "잡동사니",
                "core": None,
                "exclude_terms": (),
                "require_terms": (),
                "category": None,
                "cached_secondary": [],
            }
        ]
        rows = {
            "잡동사니": [
                # winnable 1위지만 미매핑 — 큐 투입 금지(여름이불류 데드엔드)
                {"keyword": "여름이불", "volume": 1900, "competition": "낮음"},
                # 매핑(office-chair·행 없음=fail-open) — 이것이 선택돼야
                {"keyword": "컴퓨터의자", "volume": 1000, "competition": "중간"},
            ]
        }
        picked = kr.auto_pick_keyword(
            conn, seeds=seeds, fetch=lambda s, dry_run=False: list(rows.get(s, []))
        )
        assert picked is not None
        assert picked["keyword"] == "컴퓨터의자"
        assert picked["source"] == "recommend"
        # 미매핑 추천이 큐에 추가되지 않았는지(부작용 0)
        kws = [r[0] for r in conn.execute("SELECT keyword FROM keyword_queue").fetchall()]
        assert "여름이불" not in kws

    def test_refill_none_when_all_unmapped(self) -> None:
        conn = _db()
        seeds: list[dict[str, Any]] = [
            {
                "seed": "잡동사니",
                "core": None,
                "exclude_terms": (),
                "require_terms": (),
                "category": None,
                "cached_secondary": [],
            }
        ]
        rows = {"잡동사니": [{"keyword": "여름이불", "volume": 1900, "competition": "낮음"}]}
        picked = kr.auto_pick_keyword(
            conn, seeds=seeds, fetch=lambda s, dry_run=False: list(rows.get(s, []))
        )
        assert picked is None  # auto-cycle이 '생성 0'으로 abnormal→경보(fail-loud)
        assert conn.execute("SELECT COUNT(*) FROM keyword_queue").fetchone()[0] == 0

    def test_refill_skips_draft_category(self) -> None:
        # 행이 있는데 draft(비공개) — laptop-stand 실사례형. 자동 경로에선 건너뛴다.
        conn = _db()
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) VALUES ('office-chair','의자','draft')"
        )
        conn.commit()
        assert kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch) is None

    def test_refill_allows_published_category_row(self) -> None:
        conn = _db()
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) "
            "VALUES ('office-chair','의자','published')"
        )
        conn.commit()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "책상의자"  # 기존 winnable 1위 그대로(공개면 제한 없음)

    def test_refill_scans_beyond_display_limit(self) -> None:
        """★#45 적대검증: 상위 20이 전부 미매핑이어도 21위+의 매핑 후보를 찾아낸다.

        미매핑 후보는 큐에 안 들어가 dedup에 안 걸려 매일 상위에 잔류 — 표시용 limit(20)로
        자른 뒤 가드를 걸면 매핑 후보를 영영 못 집는 래칫이 된다(스캔 폭 분리로 해소).
        """
        conn = _db()
        seeds: list[dict[str, Any]] = [
            {
                "seed": "잡동사니",
                "core": None,
                "exclude_terms": (),
                "require_terms": (),
                "category": None,
                "cached_secondary": [],
            }
        ]
        rows = [
            # 미매핑 25건 — 전부 winnable 상위(검색량 9만~)
            {"keyword": f"미매핑키워드{i}", "volume": 1900 - i, "competition": "낮음"}
            for i in range(25)
        ] + [
            # 매핑 후보 1건 — winnable 최하위(26위)
            {"keyword": "컴퓨터의자", "volume": 1000, "competition": "높음"}
        ]
        picked = kr.auto_pick_keyword(
            conn, seeds=seeds, fetch=lambda s, dry_run=False: [dict(r) for r in rows]
        )
        assert picked is not None
        assert picked["keyword"] == "컴퓨터의자"  # 26위여도 스캔 폭 안에서 발견

    def test_pending_draft_category_deprioritized(self) -> None:
        """#45: pending 큐에서도 draft 카테고리 매핑은 후순위 — 생성 비용 후 보류되는 어긋남 방지."""
        conn = _db()
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) VALUES "
            "('office-chair','의자','draft'), ('desk','책상','published')"
        )
        conn.commit()
        kq.add_keyword(conn, "컴퓨터의자", channel="ali", score=9999.0)  # draft 카테고리 — 강등
        kq.add_keyword(conn, "컴퓨터 책상", channel="ali", score=10.0)  # published — 우선
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "컴퓨터 책상"


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


class TestVolumeBand:
    """세션 #51 근본수정 — 공략 구간 [floor, ceiling]. 검색량을 난이도 지표로 사용.

    ★회귀 배경(라이브 실측): 하한 2000이 네이버 후보의 94.8%(1,878/1,980)를 잘라, 시스템이
    가장 경쟁이 심한 상위 5%에서만 키워드를 골랐다 → 발행 22편 전부 head, GSC 평균 18.2위.
    ★1차안 기각도 함께 고정: '상한(cap)을 낮춰 경쟁도를 결정자로' 안은 네이버 경쟁도 분포
    (300~2000 구간 305개 중 '낮음' 1개)가 변별력이 없어 폐기했다. cap은 원래대로 30000.
    """

    BAND_SEED: ClassVar[list[dict[str, Any]]] = [
        {
            "seed": "사무용 의자",
            "core": "의자",
            "exclude_terms": (),
            "require_terms": (),
            "category": "office-chair",
            "cached_secondary": [],
        }
    ]
    BAND_ROWS: ClassVar[list[dict[str, Any]]] = [
        {"keyword": "고검색의자", "volume": 25000, "competition": "중간"},  # 상한 초과 → 제외
        {"keyword": "구간내의자", "volume": 1500, "competition": "중간"},  # 구간 내 → 통과
        {"keyword": "저검색의자", "volume": 50, "competition": "낮음"},  # 하한 미만 → 제외
    ]

    def _fetch_band(self, seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
        return [dict(r) for r in self.BAND_ROWS]

    def test_ceiling_excludes_head_keywords(self) -> None:
        """상한 초과 = 기존 강자 점유 구간 → 신규 도메인은 못 이기므로 후보에서 제외."""
        recs = kr.recommend(
            _db(),
            seeds=self.BAND_SEED,
            fetch=self._fetch_band,
            volume_floor=300,
            volume_ceiling=2000,
        )
        kws = [r["keyword"] for r in recs]
        assert "고검색의자" not in kws, "상한 초과 head가 후보에 남음 — 구간 제한 무효"
        assert "구간내의자" in kws

    def test_floor_still_excludes_no_traffic(self) -> None:
        """하한 미만은 계속 배제 — 검색량 0에 가까운 키워드는 글을 써도 트래픽이 없다."""
        recs = kr.recommend(
            _db(),
            seeds=self.BAND_SEED,
            fetch=self._fetch_band,
            volume_floor=300,
            volume_ceiling=2000,
        )
        assert "저검색의자" not in [r["keyword"] for r in recs]

    def test_ceiling_zero_means_no_upper_limit(self) -> None:
        """ceiling=0 = 상한 없음(옛 동작) — 사이트가 성숙하면 head로 확장하는 경로."""
        recs = kr.recommend(
            _db(),
            seeds=self.BAND_SEED,
            fetch=self._fetch_band,
            volume_floor=300,
            volume_ceiling=0,
        )
        assert "고검색의자" in [r["keyword"] for r in recs]

    def test_cached_degraded_rows_survive_ceiling(self) -> None:
        """캐시 강등분(volume=None)은 판정 불가라 상한에 걸려 사라지면 안 된다(#50 경로 보존).

        네이버 실패 시 yml secondary로 강등되는데, 여기서 전멸하면 무인 리필이 0건이 되어
        발행이 멈춘다. 검색량 미상은 통과시키고 winnable에서 최하위로 밀리게만 한다.
        """
        recs = kr.recommend(
            _db(),
            seeds=[{**self.BAND_SEED[0], "cached_secondary": ["메쉬의자", "중역의자"]}],
            fetch=lambda s, dry_run=False: [],  # 라이브 0건 → 캐시 강등
            volume_floor=300,
            volume_ceiling=2000,
        )
        assert [r["keyword"] for r in recs] == ["메쉬의자", "중역의자"]
        assert all(r["source"] == "cached" for r in recs)

    def test_defaults_come_from_settings(self) -> None:
        """인자 미지정이면 설정값 — 주인이 config로 조정 가능(상수 하드코딩 아님)."""
        assert kr._volume_floor() >= 0
        assert kr._volume_ceiling() >= 0
        # 기본 정책상 상한이 하한보다 커야 후보가 존재한다(설정 오기입 조기 발견).
        if kr._volume_ceiling():
            assert kr._volume_ceiling() > kr._volume_floor()


class TestCategoryBalance:
    """★세션 #50: 무인 리필의 카테고리 균형(라운드로빈) — 한 카테고리 연속 소진 방지.

    실사고: 07-20~27 큐 이력이 cutting-board **6일 연속**(나무도마·스텐도마·도마추천·
    엔드그레인도마·실리콘도마·TPU도마). 리필이 winnable 전역 1위만 집으므로 한 카테고리가
    상위를 점유하면 씨앗 소진까지 같은 주제만 나간다. GSC 실측으로 그 6편은 상위 노출 0편.
    """

    @staticmethod
    def _cat(keyword: str) -> str | None:
        from collector import keyword_relevance

        return keyword_relevance.resolve_category(keyword)

    @staticmethod
    def _fetch_of(rows: dict[str, list[dict[str, Any]]]) -> Any:
        return lambda s, dry_run=False: [dict(r) for r in rows.get(s, [])]

    # 카테고리 무관 씨앗 1개(추천 후보로 여러 카테고리를 섞기 위함)
    SEED_MIX: ClassVar[list[dict[str, Any]]] = [
        {
            "seed": "살림",
            "core": None,
            "exclude_terms": (),
            "require_terms": (),
            "category": None,
            "cached_secondary": [],
        }
    ]

    def _drain(self, conn: sqlite3.Connection, picked: dict[str, Any]) -> None:
        """리필 후 글 생성돼 pending을 벗어난 상태 모사 — 다음 호출이 다시 리필을 타게 한다."""
        conn.execute(
            "UPDATE keyword_queue SET status = 'drafted' WHERE id = ?", (picked["keyword_id"],)
        )
        conn.commit()

    def test_no_consecutive_same_category(self) -> None:
        """★도마 6연속 재현 방지 — 한 카테고리가 점수 상위를 독식해도 연속으로 뽑지 않는다."""
        conn = _db()
        rows = {
            "살림": [
                # cutting-board가 winnable 1~3위 독식(07-20~27 실제 상황 재현)
                {"keyword": "나무도마", "volume": 1900, "competition": "낮음"},
                {"keyword": "스텐도마", "volume": 1850, "competition": "낮음"},
                {"keyword": "원목도마", "volume": 1800, "competition": "낮음"},
                # 다른 카테고리는 점수가 한참 낮다
                {"keyword": "컴퓨터의자", "volume": 1000, "competition": "중간"},
                {"keyword": "서재책상", "volume": 900, "competition": "중간"},
            ]
        }
        cats: list[str | None] = []
        for _ in range(3):
            picked = kr.auto_pick_keyword(conn, seeds=self.SEED_MIX, fetch=self._fetch_of(rows))
            assert picked is not None
            cats.append(self._cat(picked["keyword"]))
            self._drain(conn, picked)

        # 수정 전이었다면 ['cutting-board'] * 3 (점수 1·2·3위가 전부 도마)
        assert cats != ["cutting-board", "cutting-board", "cutting-board"]
        assert cats[0] != cats[1] and cats[1] != cats[2]  # 직전 연속 회피
        assert len(set(cats)) >= 2

    def test_least_used_category_first(self) -> None:
        """사용 횟수가 적은 카테고리를 우선 — 점수 1위라도 이미 많이 쓴 카테고리는 후순위."""
        conn = _db()
        for kw in ("컴퓨터의자", "메쉬의자", "책상의자"):  # office-chair 3회 소비 이력
            kid = kq.add_keyword(conn, kw, channel="ali", score=1.0)
            conn.execute("UPDATE keyword_queue SET status = 'drafted' WHERE id = ?", (kid,))
        conn.commit()

        rows = {
            "살림": [
                {"keyword": "중역의자", "volume": 1900, "competition": "낮음"},  # 많이 쓴 카테고리
                {"keyword": "나무도마", "volume": 1000, "competition": "중간"},  # 안 쓴 카테고리
            ]
        }
        picked = kr.auto_pick_keyword(conn, seeds=self.SEED_MIX, fetch=self._fetch_of(rows))
        assert picked is not None
        assert picked["keyword"] == "나무도마"  # 점수 6배 차이를 균형이 이긴다

    def test_single_eligible_category_still_picks(self) -> None:
        """★멈추지 않음(§0) — 적격이 한 카테고리뿐이면 균형과 무관하게 그것을 고른다."""
        conn = _db()
        kid = kq.add_keyword(conn, "나무도마", channel="ali", score=1.0)  # 같은 카테고리 이력
        conn.execute("UPDATE keyword_queue SET status = 'drafted' WHERE id = ?", (kid,))
        conn.commit()
        rows = {
            "살림": [
                {"keyword": "여름이불", "volume": 1900, "competition": "낮음"},  # 미매핑
                {"keyword": "스텐도마", "volume": 1000, "competition": "중간"},  # 유일 적격
            ]
        }
        picked = kr.auto_pick_keyword(conn, seeds=self.SEED_MIX, fetch=self._fetch_of(rows))
        assert picked is not None
        assert picked["keyword"] == "스텐도마"  # 직전과 같은 카테고리여도 선택(멈추면 발행 0)

    def test_empty_history_keeps_score_order(self) -> None:
        """이력이 없으면 기존 winnable 순서 그대로 — 신규 DB·구 스키마 동작 보존."""
        conn = _db()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["keyword"] == "책상의자"  # 기존 winnable 1위

    def test_balance_sorted_preserves_candidate_set(self) -> None:
        """재배열일 뿐 후보 집합은 불변 — 균형이 후보를 '버리지' 않는다."""
        recs: list[dict[str, Any]] = [
            {"keyword": "나무도마", "volume": 100, "competition": "낮음"},
            {"keyword": "컴퓨터의자", "volume": 200, "competition": "낮음"},
            {"keyword": "여름이불", "volume": 300, "competition": "낮음"},  # 미매핑
        ]
        out = kr.balance_sorted(recs, {"cutting-board": 5}, "cutting-board")
        assert len(out) == len(recs)
        assert sorted(r["keyword"] for r in out) == sorted(r["keyword"] for r in recs)
        assert out[-1]["keyword"] == "여름이불"  # 미매핑은 맨 뒤

    def test_category_usage_ignores_unmapped(self) -> None:
        """미매핑 키워드는 어느 카테고리도 소비하지 않는다 — 횟수·'직전' 판정 모두 제외."""
        conn = _db()
        kq.add_keyword(conn, "나무도마", channel="ali")
        kq.add_keyword(conn, "여름이불", channel="ali")  # 가장 최근이지만 미매핑
        counts, last = kr.category_usage(conn)
        assert counts == {"cutting-board": 1}
        assert last == "cutting-board"

    def test_category_usage_missing_table_is_safe(self) -> None:
        """구 스키마(큐 테이블 없음)에서도 죽지 않고 균형 판정만 생략 — 점수순 폴백."""
        conn = sqlite3.connect(":memory:")
        counts, last = kr.category_usage(conn)
        assert counts == {}
        assert last is None

    def test_balance_works_when_cache_degraded(self) -> None:
        """★실운영 조건 — 캐시 강등(volume=None)으로 점수가 전부 동률일 때도 균형이 작동한다.

        07-20~27 도마 6연속이 정확히 이 상태였다: 리필이 네이버 자격증명 없이 돌아 캐시로
        강등 → winnable 점수가 전부 -1.0 동률 → **yml secondary에 적힌 순서 그대로** 한
        카테고리를 통째로 소진(나무도마→스텐도마→도마추천→엔드그레인도마→실리콘도마→TPU도마).
        점수가 무력한 조건이므로 균형 키(사용 횟수·직전 회피)만으로 순환해야 한다.
        """
        conn = _db()
        seeds: list[dict[str, Any]] = [
            {
                "seed": "도마",
                "core": None,
                "exclude_terms": (),
                "require_terms": (),
                "category": "cutting-board",
                "cached_secondary": ["나무도마", "스텐도마", "원목도마"],
            },
            {
                "seed": "컴퓨터 책상",
                "core": None,
                "exclude_terms": (),
                "require_terms": (),
                "category": "desk",
                "cached_secondary": ["서재책상", "미니책상"],
            },
        ]
        cats: list[str | None] = []
        for _ in range(3):
            picked = kr.auto_pick_keyword(conn, seeds=seeds, live=False)  # 캐시만 = 강등 재현
            assert picked is not None
            cats.append(self._cat(picked["keyword"]))
            self._drain(conn, picked)

        # 수정 전이었다면 yml 순서 그대로 ['cutting-board'] * 3
        assert cats != ["cutting-board", "cutting-board", "cutting-board"]
        assert cats[0] != cats[1] and cats[1] != cats[2]


class TestRefillDegradedSignal:
    """★세션 #50 fail-loud — '검색량 없이 캐시로 골랐다'가 호출부로 새어나가야 한다.

    recommend는 네이버 실패를 예외로 올리지 않고 캐시로 자가강등한다(§0 멈추지 않음). 그
    자체는 옳지만 **사실이 보고되지 않으면** 선정 품질이 무너진 채로 조용히 계속 돈다 —
    실제로 07-01~27 리필 10건이 전부 캐시였는데 글은 매일 나가 한 달간 아무도 몰랐다.
    """

    def test_degraded_true_on_cache_fallback(self) -> None:
        conn = _db()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, live=False)  # 캐시만 = 강등
        assert picked is not None
        assert picked["source"] == "recommend"
        assert picked["degraded"] is True

    def test_degraded_false_on_live_success(self) -> None:
        conn = _db()
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)  # 네이버 성공
        assert picked is not None
        assert picked["degraded"] is False

    def test_queue_reuse_is_not_degraded(self) -> None:
        # 큐 재사용은 검색량 조회와 무관 — 오경보 금지
        conn = _db()
        kq.add_keyword(conn, "컴퓨터의자", channel="ali", score=10.0)
        picked = kr.auto_pick_keyword(conn, seeds=SEED, fetch=_fetch)
        assert picked is not None
        assert picked["source"] == "queue"
        assert picked["degraded"] is False


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
