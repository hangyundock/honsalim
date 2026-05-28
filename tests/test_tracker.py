"""tracker.d1_aggregator 회귀 — BACKEND §2-8 + DB §11 [확정].

dry_run 모드 우선 — wrangler·D1 실호출 없이 명령 빌드·인자 검증.
실제 SQLite 동기화는 in-memory DB로 검증.
"""

from __future__ import annotations

import sqlite3
import tempfile
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


from tracker.d1_aggregator import aggregate, export_to_sqlite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"


# ─── aggregate (wrangler d1 execute) ──────────────────────────────────


class TestAggregate:
    def test_dry_run_default(self) -> None:
        result = aggregate("2026-05-28")
        assert result.dry_run is True
        assert result.date == "2026-05-28"
        assert "wrangler" in result.command
        assert "d1" in result.command
        assert "execute" in result.command

    def test_command_includes_database_id(self) -> None:
        result = aggregate("2026-05-28", database_id="honsalim-clicks")
        assert "honsalim-clicks" in result.command

    def test_remote_flag_present(self) -> None:
        """D1 원격 DB 지정 필수."""
        result = aggregate("2026-05-28")
        assert "--remote" in result.command

    def test_sql_includes_upsert_pattern(self) -> None:
        """ON CONFLICT UPSERT 패턴 — 재실행 안전성."""
        result = aggregate("2026-05-28")
        sql = " ".join(result.command)
        assert "INSERT INTO clicks_daily" in sql
        assert "ON CONFLICT" in sql

    def test_invalid_date_format_raises(self) -> None:
        with raises(ValueError):
            aggregate("2026/05/28")
        with raises(ValueError):
            aggregate("28-05-2026")
        with raises(ValueError):
            aggregate("2026-05")

    def test_non_numeric_date_raises(self) -> None:
        with raises(ValueError):
            aggregate("ABCD-EF-GH")

    def test_empty_database_id_raises(self) -> None:
        with raises(ValueError):
            aggregate("2026-05-28", database_id="")


# ─── export_to_sqlite (D1 결과 → articles.view_count_cached) ──────────


def _seeded_db_with_article() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    conn.executescript(
        """
        INSERT INTO personas (slug, title_ko, description) VALUES ('p', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s', 'S', 'd', 1);
        INSERT INTO articles (
            slug, scenario_id, title, summary, body_md, body_html,
            meta_description, schema_jsonld, disclosure_first,
            status, published_at, content_hash,
            truth_check_passed_at, user_approved_at
        ) VALUES (
            'test-slug', 1, 'T', 's', 'b', '<p>b</p>',
            'md', '{}', 'd',
            'published', '2026-05-28', 'sha256:abc',
            '2026-05-28T11:00:00Z', '2026-05-28T11:05:00Z'
        );
        """
    )
    conn.commit()
    return conn


class TestExportToSqlite:
    def test_dry_run_default(self) -> None:
        result = export_to_sqlite([{"slug": "x", "clicks": 5}])
        assert result.dry_run is True
        assert result.articles_updated == 1
        assert result.aggregates_loaded == [{"slug": "x", "clicks": 5}]

    def test_empty_aggregates_dry_run(self) -> None:
        result = export_to_sqlite()
        assert result.dry_run is True
        assert result.articles_updated == 0

    def test_missing_keys_raises(self) -> None:
        with raises(ValueError):
            export_to_sqlite([{"slug": "x"}])  # clicks 누락
        with raises(ValueError):
            export_to_sqlite([{"clicks": 5}])  # slug 누락

    def _setup_file_db(self, db_path: Path) -> None:
        """파일 SQLite에 마이그레이션 + 1 article 직접 시드."""
        conn = sqlite3.connect(str(db_path))
        try:
            conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
            conn.executescript(
                """
                INSERT INTO personas (slug, title_ko, description) VALUES ('p', 'P', 'd');
                INSERT INTO scenarios (slug, title_ko, description, persona_id)
                VALUES ('s', 'S', 'd', 1);
                INSERT INTO articles (
                    slug, scenario_id, title, summary, body_md, body_html,
                    meta_description, schema_jsonld, disclosure_first,
                    status, published_at, content_hash,
                    truth_check_passed_at, user_approved_at
                ) VALUES (
                    'test-slug', 1, 'T', 's', 'b', '<p>b</p>',
                    'md', '{}', 'd',
                    'published', '2026-05-28', 'sha256:abc',
                    '2026-05-28T11:00:00Z', '2026-05-28T11:05:00Z'
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def test_actual_update(self) -> None:
        """dry_run=False — articles.view_count_cached 실제 UPDATE."""
        with tempfile.TemporaryDirectory() as d:
            db_path = Path(d) / "honsalim.db"
            self._setup_file_db(db_path)

            result = export_to_sqlite(
                [{"slug": "test-slug", "clicks": 42}],
                db_path=db_path,
                dry_run=False,
            )
            assert result.dry_run is False
            assert result.articles_updated == 1

            check = sqlite3.connect(str(db_path))
            row = check.execute(
                "SELECT view_count_cached FROM articles WHERE slug = 'test-slug'"
            ).fetchone()
            check.close()
            assert row[0] == 42

    def test_no_matching_slug_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            db_path = Path(d) / "honsalim.db"
            self._setup_file_db(db_path)

            result = export_to_sqlite(
                [{"slug": "nonexistent", "clicks": 99}],
                db_path=db_path,
                dry_run=False,
            )
            assert result.articles_updated == 0


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
