"""마이그레이션 007 회귀 테스트 — keyword_queue 발행 큐 + drafts.keyword_id (세션 #25).

스키마 존재·컬럼·CHECK·UNIQUE·schema_version·키워드↔draft 링크 검증.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _migrated_db() -> sqlite3.Connection:
    """001~007 적용 + 페르소나/시나리오 1건 시드한 in-memory DB."""
    conn = sqlite3.connect(":memory:")
    for version in ("001", "002", "003", "004", "005", "006", "007"):
        sql = next(MIGRATIONS.glob(f"{version}_*.sql")).read_text(encoding="utf-8")
        conn.executescript(sql)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        INSERT INTO personas (slug, title_ko, description) VALUES ('p1', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);
        """)
    conn.commit()
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


class TestSchemaShape:
    def test_keyword_queue_table_exists(self) -> None:
        conn = _migrated_db()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='keyword_queue'"
        ).fetchone()
        assert row is not None

    def test_keyword_queue_has_expected_columns(self) -> None:
        conn = _migrated_db()
        cols = _columns(conn, "keyword_queue")
        expected = {
            "id",
            "keyword",
            "slug",
            "channel",
            "status",
            "status_reason",
            "persona_id",
            "budget_min_krw",
            "budget_max_krw",
            "target_products",
            "notes",
            "score",
            "priority",
            "scenario_id",
            "times_used",
            "fail_count",
            "created_at",
            "updated_at",
        }
        assert expected <= cols

    def test_drafts_has_keyword_id(self) -> None:
        conn = _migrated_db()
        assert "keyword_id" in _columns(conn, "drafts")

    def test_schema_version_is_7(self) -> None:
        conn = _migrated_db()
        v = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert v == 7


class TestConstraints:
    def test_channel_check_rejects_bad_value(self) -> None:
        conn = _migrated_db()
        with raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO keyword_queue (keyword, slug, channel) VALUES ('k', 'k1', 'naver')"
            )

    def test_status_check_rejects_bad_value(self) -> None:
        conn = _migrated_db()
        with raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO keyword_queue (keyword, slug, status) VALUES ('k', 'k1', 'bogus')"
            )

    def test_slug_unique(self) -> None:
        conn = _migrated_db()
        conn.execute("INSERT INTO keyword_queue (keyword, slug) VALUES ('a', 'dup')")
        with raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO keyword_queue (keyword, slug) VALUES ('b', 'dup')")

    def test_defaults_applied(self) -> None:
        conn = _migrated_db()
        conn.execute("INSERT INTO keyword_queue (keyword, slug) VALUES ('a', 'k1')")
        row = conn.execute(
            "SELECT channel, status, score, priority, times_used, fail_count "
            "FROM keyword_queue WHERE slug='k1'"
        ).fetchone()
        assert row == ("ali", "pending", 0, 0, 0, 0)


class TestKeywordDraftLink:
    def test_draft_links_to_keyword(self) -> None:
        conn = _migrated_db()
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, scenario_id) VALUES ('전자레인지', 'micro', 1)"
        )
        kid = conn.execute("SELECT id FROM keyword_queue WHERE slug='micro'").fetchone()[0]
        conn.execute(
            "INSERT INTO drafts (scenario_id, keyword_id, status) VALUES (1, ?, 'collected')",
            (kid,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT d.keyword_id, k.keyword FROM drafts d "
            "JOIN keyword_queue k ON k.id = d.keyword_id"
        ).fetchone()
        assert row[0] == kid
        assert row[1] == "전자레인지"

    def test_updated_at_trigger_fires(self) -> None:
        conn = _migrated_db()
        conn.execute(
            "INSERT INTO keyword_queue (keyword, slug, created_at, updated_at) "
            "VALUES ('a', 'k1', '2020-01-01', '2020-01-01')"
        )
        conn.commit()
        conn.execute("UPDATE keyword_queue SET status='drafted' WHERE slug='k1'")
        conn.commit()
        upd = conn.execute("SELECT updated_at FROM keyword_queue WHERE slug='k1'").fetchone()[0]
        assert upd != "2020-01-01"  # 트리거가 갱신


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
