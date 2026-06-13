"""dashboard.queries 회귀 테스트 — 운영 대시보드 읽기 데이터 레이어 (세션 #25).

테이블 미존재 안전성·통계 카운트·키워드/큐 목록·카테고리 건강.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

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
