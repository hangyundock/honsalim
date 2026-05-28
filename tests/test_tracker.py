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
    conn.executescript("""
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
        """)
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
            conn.executescript("""
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
                """)
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


# ─── 세션 #5 — tracker.report (BACKEND §2-8 진입점) ─────────────────────


def _seeded_clicks_db() -> sqlite3.Connection:
    """in-memory DB + clicks_daily 시드."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    rows = [
        ("2026-05-25", "wonroom-30", 10, 8, "KR"),
        ("2026-05-26", "wonroom-30", 20, 15, "KR"),
        ("2026-05-27", "wonroom-30", 5, 5, "KR"),
        ("2026-05-26", "homeoffice-50", 15, 12, "KR"),
        ("2026-05-28", "homeoffice-50", 30, 25, "KR"),
        ("2026-04-15", "gaeul-30", 8, 7, "JP"),
    ]
    for date_, slug, c, uu, country in rows:
        conn.execute(
            "INSERT INTO clicks_daily (date, slug, click_count, unique_ua_count, top_country) "
            "VALUES (?, ?, ?, ?, ?)",
            (date_, slug, c, uu, country),
        )
    conn.commit()
    return conn


class TestAggregateWeekly:
    def test_weekly_range_includes_end(self) -> None:
        from tracker.report import aggregate_weekly

        conn = _seeded_clicks_db()
        try:
            data = aggregate_weekly(conn, end_date="2026-05-28")
            assert data.period == "weekly"
            assert data.start_date == "2026-05-22"
            assert data.end_date == "2026-05-28"
            # 7일 범위 합산: wonroom-30 = 10+20+5 = 35, homeoffice-50 = 15+30 = 45
            assert data.total_clicks == 35 + 45
            assert data.by_slug[0].slug == "homeoffice-50"  # clicks DESC
            assert data.by_slug[0].click_count == 45
            assert data.top_country == "KR"
        finally:
            conn.close()

    def test_weekly_excludes_out_of_range(self) -> None:
        from tracker.report import aggregate_weekly

        conn = _seeded_clicks_db()
        try:
            data = aggregate_weekly(conn, end_date="2026-05-28")
            slugs = {a.slug for a in data.by_slug}
            assert "gaeul-30" not in slugs
        finally:
            conn.close()

    def test_weekly_bad_date_rejected(self) -> None:
        from tracker.report import aggregate_weekly

        conn = _seeded_clicks_db()
        try:
            with raises(ValueError):
                aggregate_weekly(conn, end_date="2026/05/28")
        finally:
            conn.close()


class TestAggregateMonthly:
    def test_monthly_includes_full_month(self) -> None:
        from tracker.report import aggregate_monthly

        conn = _seeded_clicks_db()
        try:
            data = aggregate_monthly(conn, year_month="2026-05")
            assert data.period == "monthly"
            assert data.start_date == "2026-05-01"
            assert data.end_date == "2026-05-31"
            # 5월: wonroom 35 + homeoffice 45 = 80
            assert data.total_clicks == 80
        finally:
            conn.close()

    def test_monthly_excludes_other_month(self) -> None:
        from tracker.report import aggregate_monthly

        conn = _seeded_clicks_db()
        try:
            data = aggregate_monthly(conn, year_month="2026-04")
            assert data.total_clicks == 8  # gaeul-30만
            assert len(data.by_slug) == 1
            assert data.by_slug[0].slug == "gaeul-30"
        finally:
            conn.close()

    def test_monthly_december_handles_year_end(self) -> None:
        from tracker.report import aggregate_monthly

        conn = _seeded_clicks_db()
        try:
            data = aggregate_monthly(conn, year_month="2026-12")
            assert data.start_date == "2026-12-01"
            assert data.end_date == "2026-12-31"
        finally:
            conn.close()

    def test_monthly_bad_format_rejected(self) -> None:
        from tracker.report import aggregate_monthly

        conn = _seeded_clicks_db()
        try:
            with raises(ValueError):
                aggregate_monthly(conn, year_month="2026/05")
            with raises(ValueError):
                aggregate_monthly(conn, year_month="2026-13")
        finally:
            conn.close()


class TestTopArticles:
    def test_top_articles_by_clicks_desc(self) -> None:
        from tracker.report import top_articles_by_clicks

        conn = _seeded_clicks_db()
        try:
            top = top_articles_by_clicks(conn, since_date="2026-05-01", limit=10)
            assert top[0].slug == "homeoffice-50"
            assert top[0].click_count == 45
            assert top[1].slug == "wonroom-30"
            assert top[1].click_count == 35
        finally:
            conn.close()

    def test_top_articles_limit_respected(self) -> None:
        from tracker.report import top_articles_by_clicks

        conn = _seeded_clicks_db()
        try:
            top = top_articles_by_clicks(conn, since_date="2026-05-01", limit=1)
            assert len(top) == 1
            assert top[0].slug == "homeoffice-50"
        finally:
            conn.close()

    def test_top_articles_invalid_limit(self) -> None:
        from tracker.report import top_articles_by_clicks

        conn = _seeded_clicks_db()
        try:
            with raises(ValueError):
                top_articles_by_clicks(conn, since_date="2026-05-01", limit=0)
        finally:
            conn.close()


class TestWeeklyMonthlyEntrypoints:
    def test_weekly_entrypoint_with_render(self) -> None:
        from tracker.report import weekly

        conn = _seeded_clicks_db()
        try:
            result = weekly(conn, end_date="2026-05-28", render=True)
            assert result["data"].period == "weekly"
            assert result["html"] is not None
            assert "[STUB]" in result["html"]
            assert "weekly" in result["html"]
        finally:
            conn.close()

    def test_monthly_entrypoint_without_render(self) -> None:
        from tracker.report import monthly

        conn = _seeded_clicks_db()
        try:
            result = monthly(conn, year_month="2026-05", render=False)
            assert result["data"].period == "monthly"
            assert result["html"] is None
        finally:
            conn.close()


class TestRenderHtmlStub:
    def test_stub_includes_summary_fields(self) -> None:
        from tracker.report import aggregate_weekly, render_html_stub

        conn = _seeded_clicks_db()
        try:
            data = aggregate_weekly(conn, end_date="2026-05-28")
            html = render_html_stub(data)
            assert "[STUB]" in html
            assert "weekly" in html
            assert "2026-05-22~2026-05-28" in html
            assert "total_clicks=" in html
            assert "homeoffice-50" in html
        finally:
            conn.close()


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
