"""dashboard.queries 회귀 테스트 — 운영 대시보드 읽기 데이터 레이어 (세션 #25).

테이블 미존재 안전성·통계 카운트·키워드/큐 목록·카테고리 건강.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import ClassVar

from dashboard import queries

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _full_db() -> sqlite3.Connection:
    """001~007 적용 + 페르소나/시나리오 시드."""
    conn = sqlite3.connect(":memory:")
    for version in ("001", "002", "003", "004", "005", "006", "007"):
        sql = next(MIGRATIONS.glob(f"{version}_*.sql")).read_text(encoding="utf-8")
        conn.executescript(sql)
    conn.executescript("""
        INSERT INTO personas (slug, title_ko, description) VALUES ('p1', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);
        """)
    conn.commit()
    return conn


def _bare_db() -> sqlite3.Connection:
    """001만 적용 (keyword_queue·categories 없음) — 미존재 안전성 검증용."""
    conn = sqlite3.connect(":memory:")
    sql = next(MIGRATIONS.glob("001_*.sql")).read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
    return conn


class TestSafetyMissingTables:
    def test_stats_on_bare_db(self) -> None:
        conn = _bare_db()
        stats = queries.dashboard_stats(conn)
        # keyword_queue·categories 미존재 → 0, drafts·articles 존재 → 0
        assert stats["keywords_pending"] == 0
        assert stats["categories_published"] == 0
        assert stats["articles_published"] == 0

    def test_list_keywords_on_bare_db(self) -> None:
        assert queries.list_keywords(_bare_db()) == []

    def test_category_health_on_bare_db(self) -> None:
        assert queries.category_health(_bare_db()) == []

    def test_list_queue_on_bare_db_without_keyword_table(self) -> None:
        conn = _bare_db()
        conn.executescript(
            "INSERT INTO personas (slug, title_ko, description) VALUES ('p1','P','d');"
            "INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1','S','d',1);"
            "INSERT INTO drafts (scenario_id, working_title, status) VALUES (1,'T','validated');"
        )
        conn.commit()
        q = queries.list_queue(conn)
        assert len(q) == 1
        assert q[0]["status"] == "validated"
        assert q[0]["keyword"] is None  # keyword_queue 없음 → NULL


class TestStats:
    def test_counts_reflect_inserts(self) -> None:
        conn = _full_db()
        conn.executescript("""
            INSERT INTO keyword_queue (keyword, slug, status) VALUES ('a','a','pending');
            INSERT INTO keyword_queue (keyword, slug, status) VALUES ('b','b','disabled');
            INSERT INTO drafts (scenario_id, status) VALUES (1,'validated');
            INSERT INTO drafts (scenario_id, status) VALUES (1,'approved');
            """)
        conn.commit()
        stats = queries.dashboard_stats(conn)
        assert stats["keywords_pending"] == 1
        assert stats["keywords_total"] == 2
        assert stats["drafts_validated"] == 1
        assert stats["drafts_approved"] == 1

    def test_gate_failed_and_unpublished_counters(self) -> None:
        """★세션 #41 — 반려/미발행 가시화: 게이트 반려 격리·재생성 대기·미발행 글 카운트."""
        conn = _full_db()
        conn.executescript("""
            INSERT INTO keyword_queue (keyword, slug, status, status_reason, fail_count)
              VALUES ('gf','gf','failed','검증 반려 3회(상한 도달) — 수동 검토 필요',3);
            INSERT INTO keyword_queue (keyword, slug, status, status_reason)
              VALUES ('he','he','failed','상품 확보 실패: x');
            INSERT INTO keyword_queue (keyword, slug, status, fail_count)
              VALUES ('rt','rt','pending',1);
            INSERT INTO articles (slug, scenario_id, title, summary, body_md, body_html,
              meta_description, schema_jsonld, disclosure_first, content_hash,
              truth_check_passed_at, user_approved_at, status)
              VALUES ('u1',1,'T','s','m','h','d','{}','disc','hash','2026-01-01','2026-01-01',
                      'unpublished');
            """)
        conn.commit()
        stats = queries.dashboard_stats(conn)
        assert stats["keywords_gate_failed"] == 1  # '반려' 격리만(상품확보 실패 failed는 제외)
        assert stats["keywords_retrying"] == 1  # pending + fail_count>0
        assert stats["articles_unpublished"] == 1


class TestAutoForecastAndBanner:
    """★세션 #41 — 무인 발행 예측(쿠팡 재고 런웨이) + 3줄 안내 배너 (naver_blog UX 미러)."""

    CFG: ClassVar[dict[str, object]] = {
        "auto_mode": True,
        "publish_per_day": 1,
        "schedule_time": "11:11",
        "coupang_mode": "manual",
        "coupang_low_threshold": 2,
    }

    def _seed(self, conn: sqlite3.Connection) -> None:
        # 쿠팡 첨부 2개('의자' = office-chair 매핑) + 미첨부 1개
        conn.executescript("""
            INSERT INTO keyword_queue (keyword, slug, status, score, target_products)
              VALUES ('등받이의자','a','pending',500,'[{"source":"coupang"}]');
            INSERT INTO keyword_queue (keyword, slug, status, score, target_products)
              VALUES ('메쉬의자','b','pending',300,'[{"source":"coupang"}]');
            INSERT INTO keyword_queue (keyword, slug, status, score, fail_count)
              VALUES ('서재책상','c','pending',100,1);
            """)
        conn.commit()

    def test_forecast_counts_and_order(self) -> None:
        from datetime import datetime

        conn = _full_db()
        self._seed(conn)
        now = datetime(2026, 7, 3, 9, 0)  # 예약(11:11) 전 → 오늘부터
        fc = queries.auto_forecast(conn, self.CFG, now)
        assert fc["pending"] == 3
        assert fc["coupang_pending"] == 2
        assert fc["retrying"] == 1
        # 소비 순서: 쿠팡 첨부(점수순) 먼저 → 미첨부
        names = [p["keyword"] for p in fc["picks"]]
        assert names[:2] == ["등받이의자", "메쉬의자"]
        # 예약 전이므로 첫 발행일 = 오늘
        assert fc["dates"][0].date() == now.date()

    def test_forecast_after_schedule_starts_tomorrow(self) -> None:
        from datetime import datetime, timedelta

        conn = _full_db()
        self._seed(conn)
        now = datetime(2026, 7, 3, 12, 0)  # 예약(11:11) 지남 → 내일부터
        fc = queries.auto_forecast(conn, self.CFG, now)
        assert fc["dates"][0].date() == (now + timedelta(days=1)).date()

    def test_banner_ok_when_stock_sufficient(self) -> None:
        from datetime import datetime

        conn = _full_db()
        self._seed(conn)
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, status, score, target_products) "
            "VALUES ('허리편한의자','d','pending',200,'[{\"source\":\"coupang\"}]')"
        )
        conn.commit()  # 쿠팡 3편 > 기준 2 → ok
        lines, level = queries.banner_lines(conn, self.CFG, datetime(2026, 7, 3, 9, 0))
        assert level == "ok"
        assert len(lines) == 3
        assert "완전 무인 ON" in lines[0]
        assert "3편" in lines[1] and "수익 링크" in lines[1]
        assert "충분" in lines[2]

    def test_banner_caution_when_stock_low(self) -> None:
        from datetime import datetime

        conn = _full_db()
        self._seed(conn)  # 쿠팡 2편 <= 기준 2 → caution
        lines, level = queries.banner_lines(conn, self.CFG, datetime(2026, 7, 3, 9, 0))
        assert level == "caution"
        assert "쿠팡 첨부(저장)" in lines[2]

    def test_banner_alert_when_no_coupang(self) -> None:
        from datetime import datetime

        conn = _full_db()
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, status, score) "
            "VALUES ('서재책상','x','pending',100)"
        )
        conn.commit()
        lines, level = queries.banner_lines(conn, self.CFG, datetime(2026, 7, 3, 9, 0))
        assert level == "alert"
        assert "쿠팡" in lines[2]

    def test_banner_alert_on_gate_failed(self) -> None:
        from datetime import datetime

        conn = _full_db()
        self._seed(conn)
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, status, status_reason) "
            "VALUES ('게이밍책상','y','failed','검증 반려 3회(상한 도달) — 수동 검토 필요')"
        )
        conn.commit()
        lines, level = queries.banner_lines(conn, self.CFG, datetime(2026, 7, 3, 9, 0))
        assert level == "alert"
        assert "반려" in lines[2] and "재시도" in lines[2]

    def test_banner_off_mode(self) -> None:
        from datetime import datetime

        conn = _full_db()
        cfg = dict(self.CFG, auto_mode=False)
        lines, level = queries.banner_lines(conn, cfg, datetime(2026, 7, 3, 9, 0))
        assert level == "caution"
        assert "무인 OFF" in lines[0]


class TestListKeywords:
    def test_filter_by_status(self) -> None:
        conn = _full_db()
        conn.executescript("""
            INSERT INTO keyword_queue (keyword, slug, status, score) VALUES ('a','a','pending',5);
            INSERT INTO keyword_queue (keyword, slug, status, score) VALUES ('b','b','pending',9);
            INSERT INTO keyword_queue (keyword, slug, status) VALUES ('c','c','disabled');
            """)
        conn.commit()
        pending = queries.list_keywords(conn, status="pending")
        assert [k["slug"] for k in pending] == ["b", "a"]  # score 내림차순
        assert len(queries.list_keywords(conn)) == 3


class TestListQueue:
    def test_only_target_statuses_and_keyword_join(self) -> None:
        conn = _full_db()
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, scenario_id) VALUES ('전자레인지','micro',1)"
        )
        kid = conn.execute("SELECT id FROM keyword_queue WHERE slug='micro'").fetchone()[0]
        conn.execute(
            "INSERT INTO drafts (scenario_id, keyword_id, working_title, status) "
            "VALUES (1, ?, '글', 'validated')",
            (kid,),
        )
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (1,'collected')")
        conn.commit()
        q = queries.list_queue(conn)
        assert len(q) == 1  # collected 제외
        assert q[0]["keyword"] == "전자레인지"


class TestCategoryHealth:
    def test_empty_when_no_published(self) -> None:
        conn = _full_db()  # categories 테이블 있으나 published 없음
        assert queries.category_health(conn) == []


class TestListArticles:
    _COLS = (
        "slug, scenario_id, title, summary, body_md, body_html, meta_description, "
        "schema_jsonld, disclosure_first, status, published_at, content_hash, "
        "truth_check_passed_at, user_approved_at"
    )

    def test_no_articles_table_is_safe(self) -> None:
        conn = sqlite3.connect(":memory:")  # 테이블 전무 → [] (마이그레이션 전 안전·§0)
        assert queries.list_articles(conn) == []

    def test_empty_when_no_rows(self) -> None:
        assert queries.list_articles(_full_db()) == []  # articles 있으나 0편

    def test_published_first_then_unpublished_with_live_url(self) -> None:
        conn = _full_db()
        conn.execute(
            f"INSERT INTO articles ({self._COLS}) VALUES "  # noqa: S608
            "('pub-a', 1, '공개글', '요', '본', '<p>본</p>', '메', '{}', '고', "
            "'published', '2026-06-20T00:00:00Z', 'h1', '2026-06-20T00:00:00Z', "
            "'2026-06-20T00:00:00Z')"
        )
        conn.execute(
            f"INSERT INTO articles ({self._COLS}) VALUES "  # noqa: S608
            "('unp-b', 1, '비공개글', '요', '본', '<p>본</p>', '메', '{}', '고', "
            "'unpublished', NULL, 'h2', '2026-06-19T00:00:00Z', '2026-06-19T00:00:00Z')"
        )
        conn.commit()
        arts = queries.list_articles(conn)
        assert [a["slug"] for a in arts] == ["pub-a", "unp-b"]  # published 먼저
        assert arts[0]["status"] == "published"
        assert arts[0]["live_url"] == "https://honsallim.com/articles/pub-a/"
        # 상태 필터 — 비공개만
        only_unp = queries.list_articles(conn, statuses=("unpublished",))
        assert [a["slug"] for a in only_unp] == ["unp-b"]
