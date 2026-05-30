"""tracker.slug_map 회귀 — published 상품 → D1 slug_map UPSERT (DB §11-2).

published article에 연결된 상품만 노출 + SQL escape + dry_run 기본 검증.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tracker import slug_map
from writer import article_writer
from writer.state_machine import transition

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"


def _base_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    conn.executescript(
        "INSERT INTO personas (slug, title_ko, description) VALUES ('p1', 'P', 'd');"
        "INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1','S','d',1);"
    )
    conn.commit()
    return conn


def _insert_product(conn: sqlite3.Connection, spid: str, *, deeplink: str | None = None) -> int:
    url = deeplink or f"https://s.click.aliexpress.com/{spid}"
    conn.execute(
        "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
        "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
        "VALUES ('aliexpress', ?, '상품', 'KRW', 10000, ?, ?, 'honsalim', "
        "datetime('now'), datetime('now'), datetime('now'))",
        (spid, url, f"ali-{spid}"),
    )
    conn.commit()
    return int(
        conn.execute(
            "SELECT id FROM products WHERE source_product_id = ?", (str(spid),)
        ).fetchone()[0]
    )


def _publish_article(conn: sqlite3.Connection, slug: str = "art") -> int:
    did = article_writer.create_draft(conn, scenario_id=1)
    transition(conn, did, "enriched")
    transition(conn, did, "validated")
    transition(conn, did, "approved")
    fields = {
        "slug": slug,
        "scenario_id": 1,
        "title": "T",
        "summary": "S",
        "body_md": "# 본문",
        "body_html": "<h1>본문</h1>",
        "meta_description": "메타",
        "schema_jsonld": '{"@type":"Article"}',
        "disclosure_first": "수수료 안내",
        "content_hash": "sha256:x",
        "truth_check_passed_at": "2026-05-30T00:00:00Z",
        "user_approved_at": "2026-05-30T00:00:00Z",
    }
    return article_writer.promote_to_article(conn, did, fields)


class TestCollectSlugMapEntries:
    def test_published_article_products_collected(self) -> None:
        conn = _base_db()
        _insert_product(conn, "111")
        _insert_product(conn, "222")
        aid = _publish_article(conn)
        article_writer.link_article_products(
            conn,
            aid,
            [
                {"source": "aliexpress", "source_product_id": "111"},
                {"source": "aliexpress", "source_product_id": "222"},
            ],
        )
        entries = slug_map.collect_slug_map_entries(conn)
        slugs = {e["slug"] for e in entries}
        assert slugs == {"ali-111", "ali-222"}
        e0 = next(e for e in entries if e["slug"] == "ali-111")
        assert e0["source"] == "aliexpress"
        assert e0["deeplink_url"].startswith("https://s.click.aliexpress.com/")
        assert isinstance(e0["product_id_local"], int)

    def test_unlinked_product_excluded(self) -> None:
        """게시 글에 연결 안 된 상품은 slug_map에서 제외 (미게시 딥링크 비노출)."""
        conn = _base_db()
        _insert_product(conn, "111")
        _insert_product(conn, "999")  # 어떤 글에도 미연결
        aid = _publish_article(conn)
        article_writer.link_article_products(
            conn, aid, [{"source": "aliexpress", "source_product_id": "111"}]
        )
        slugs = {e["slug"] for e in slug_map.collect_slug_map_entries(conn)}
        assert slugs == {"ali-111"}
        assert "ali-999" not in slugs

    def test_no_published_articles_returns_empty(self) -> None:
        conn = _base_db()
        _insert_product(conn, "111")
        assert slug_map.collect_slug_map_entries(conn) == []


class TestBuildUpsertSql:
    def test_structure_and_conflict_clause(self) -> None:
        entries = [
            {
                "slug": "ali-1",
                "deeplink_url": "https://x/1",
                "source": "aliexpress",
                "product_id_local": 7,
            }
        ]
        sql = slug_map.build_upsert_sql(entries, now="2026-05-30T00:00:00+00:00")
        assert sql.startswith("INSERT INTO slug_map (slug, deeplink_url, source")
        assert "ON CONFLICT(slug) DO UPDATE SET" in sql
        assert "'ali-1'" in sql
        assert "'https://x/1'" in sql
        assert ", 7, " in sql  # product_id_local 정수 그대로
        assert sql.rstrip().endswith(";")

    def test_escapes_single_quote_injection(self) -> None:
        """딥링크에 작은따옴표가 있어도 doubling으로 escape (인젝션 차단)."""
        entries = [
            {
                "slug": "ali-x",
                "deeplink_url": "https://x/'; DROP TABLE slug_map;--",
                "source": "aliexpress",
                "product_id_local": 1,
            }
        ]
        sql = slug_map.build_upsert_sql(entries, now="t")
        assert "''; DROP TABLE slug_map;--" in sql  # 작은따옴표 doubling됨
        assert "'https://x/''; DROP TABLE slug_map;--'" in sql

    def test_null_product_id(self) -> None:
        entries = [
            {
                "slug": "ali-n",
                "deeplink_url": "https://x/n",
                "source": "coupang",
                "product_id_local": None,
            }
        ]
        sql = slug_map.build_upsert_sql(entries, now="t")
        assert ", NULL, " in sql

    def test_multiple_rows_comma_joined(self) -> None:
        entries = [
            {"slug": "a", "deeplink_url": "u1", "source": "aliexpress", "product_id_local": 1},
            {"slug": "b", "deeplink_url": "u2", "source": "aliexpress", "product_id_local": 2},
        ]
        sql = slug_map.build_upsert_sql(entries, now="t")
        assert sql.count("(") >= 2
        assert "'a'" in sql and "'b'" in sql


class TestSyncSlugMap:
    def test_dry_run_builds_command_no_execution(self) -> None:
        conn = _base_db()
        _insert_product(conn, "111")
        aid = _publish_article(conn)
        article_writer.link_article_products(
            conn, aid, [{"source": "aliexpress", "source_product_id": "111"}]
        )
        result = slug_map.sync_slug_map(conn, dry_run=True)
        assert result.dry_run is True
        assert len(result.entries) == 1
        assert result.command[:3] == ["wrangler", "d1", "execute"]
        assert "honsalim-clicks" in result.command
        assert "--remote" in result.command
        assert "INSERT INTO slug_map" in result.sql

    def test_empty_returns_no_command(self) -> None:
        conn = _base_db()
        result = slug_map.sync_slug_map(conn, dry_run=True)
        assert result.entries == []
        assert result.command == []
        assert "0개" in result.stdout

    def test_custom_database_name(self) -> None:
        conn = _base_db()
        _insert_product(conn, "111")
        aid = _publish_article(conn)
        article_writer.link_article_products(
            conn, aid, [{"source": "aliexpress", "source_product_id": "111"}]
        )
        result = slug_map.sync_slug_map(conn, database_name="custom-db", dry_run=True)
        assert "custom-db" in result.command


def test_sql_str_escaping() -> None:
    assert slug_map._sql_str("abc") == "'abc'"
    assert slug_map._sql_str("a'b") == "'a''b'"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
