"""products_store 회귀 테스트 — upsert 신규/갱신/스킵 + map_product 연동 + CLI dry_run.

products 테이블 DDL은 sql/migrations/001_initial_schema.sql §products와 동일하게 재현해
NOT NULL·CHECK·UNIQUE 제약까지 실제와 같은 조건에서 검증한다. 라이브 HTTP는 호출하지 않는다.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from collector import aliexpress as ali
from collector import products_store
from common import db as _db


def _new_conn() -> sqlite3.Connection:
    """실제 sql/migrations/*.sql 전체를 in-memory DB에 적용.

    products DDL을 하드코딩 재현하지 않고 마이그레이션을 단일 소스로 적용한다 —
    새 migration(002 정가·할인 컬럼·categories 등) 추가 시 자동 정합(재발 방지 가드).
    NOT NULL·CHECK·UNIQUE 등 실제 제약을 그대로 검증한다.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    return conn


def _sample(pid: str = "100500", **overrides: Any) -> dict[str, Any]:
    row = {
        "source": "aliexpress",
        "source_product_id": pid,
        "name": "LED 스탠드",
        "category_path": "조명",
        "price_krw": 12000,
        "currency": "KRW",
        "image_url_external": "https://img/x.jpg",
        "deeplink_url": f"https://s.click.aliexpress.com/{pid}",
        "deeplink_slug": f"ali-{pid}",
        "affiliate_tag": "TRACK",
        "availability": "unknown",
    }
    row.update(overrides)
    return row


class TestInsert:
    def test_insert_new_counts_and_row(self) -> None:
        conn = _new_conn()
        res = products_store.upsert_products(conn, [_sample()])
        assert (res.inserted, res.updated, res.skipped) == (1, 0, 0)
        assert res.total_written == 1
        row = conn.execute(
            "SELECT name, price_krw, deeplink_slug, affiliate_tag, availability,"
            " price_checked_at FROM products WHERE source_product_id = '100500'"
        ).fetchone()
        assert row[0] == "LED 스탠드"
        assert row[1] == 12000
        assert row[2] == "ali-100500"
        assert row[3] == "TRACK"
        assert row[4] == "unknown"
        assert row[5] is not None  # 가격 있으면 price_checked_at 기록

    def test_defaults_when_optional_missing(self) -> None:
        conn = _new_conn()
        minimal = {
            "source": "aliexpress",
            "source_product_id": "1",
            "name": "x",
            "deeplink_url": "https://s.click/1",
            "deeplink_slug": "ali-1",
            "affiliate_tag": "T",
        }
        res = products_store.upsert_products(conn, [minimal])
        assert res.inserted == 1
        row = conn.execute(
            "SELECT currency, availability, price_krw, price_checked_at"
            " FROM products WHERE source_product_id = '1'"
        ).fetchone()
        assert row[0] == "KRW"  # currency 기본
        assert row[1] == "unknown"  # availability 기본
        assert row[2] is None  # 가격 없음
        assert row[3] is None  # 가격 없으면 price_checked_at NULL


class TestUpdate:
    def test_existing_is_updated_not_duplicated(self) -> None:
        conn = _new_conn()
        products_store.upsert_products(conn, [_sample(price_krw=12000, name="구형")])
        res = products_store.upsert_products(
            conn, [_sample(price_krw=9900, name="신형", availability="in_stock")]
        )
        assert (res.inserted, res.updated, res.skipped) == (0, 1, 0)
        rows = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        assert rows[0] == 1  # 중복 행 없음
        row = conn.execute(
            "SELECT name, price_krw, availability FROM products WHERE source_product_id = '100500'"
        ).fetchone()
        assert row == ("신형", 9900, "in_stock")

    def test_created_at_preserved_on_update(self) -> None:
        conn = _new_conn()
        products_store.upsert_products(conn, [_sample()])
        created = conn.execute(
            "SELECT created_at FROM products WHERE source_product_id = '100500'"
        ).fetchone()[0]
        products_store.upsert_products(conn, [_sample(name="갱신")])
        after = conn.execute(
            "SELECT created_at FROM products WHERE source_product_id = '100500'"
        ).fetchone()[0]
        assert created == after  # created_at 보존


class TestSkip:
    def test_missing_required_skipped(self) -> None:
        conn = _new_conn()
        bad = _sample()
        bad["deeplink_url"] = None  # NOT NULL 필수 누락
        res = products_store.upsert_products(conn, [bad])
        assert (res.inserted, res.updated, res.skipped) == (0, 0, 1)
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0

    def test_empty_string_required_skipped(self) -> None:
        conn = _new_conn()
        bad = _sample()
        bad["source_product_id"] = ""
        res = products_store.upsert_products(conn, [bad])
        assert res.skipped == 1

    def test_is_valid_helper(self) -> None:
        assert products_store.is_valid(_sample()) is True
        assert products_store.is_valid({**_sample(), "name": ""}) is False


class TestBatchMixed:
    def test_counts_split_correctly(self) -> None:
        conn = _new_conn()
        rows = [
            _sample("1"),
            _sample("2"),
            {**_sample("3"), "deeplink_url": None},  # skip
        ]
        res = products_store.upsert_products(conn, rows)
        assert (res.inserted, res.updated, res.skipped) == (2, 0, 1)
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2


class TestMapProductIntegration:
    def test_map_product_output_upserts(self) -> None:
        item = {
            "product_id": "777",
            "product_title": "원룸 무드등",
            "target_sale_price": "8.50",
            "target_sale_price_currency": "KRW",
            "product_main_image_url": "https://img/m.jpg",
            "promotion_link": "https://s.click.aliexpress.com/777",
            "second_level_category_name": "조명",
        }
        mapped = ali.map_product(item, "TRACK")
        conn = _new_conn()
        res = products_store.upsert_products(conn, [mapped])
        assert res.inserted == 1
        row = conn.execute(
            "SELECT name, deeplink_url, deeplink_slug FROM products WHERE source_product_id = '777'"
        ).fetchone()
        assert row == ("원룸 무드등", "https://s.click.aliexpress.com/777", "ali-777")


class TestCliDryRun:
    """collect-products dry_run은 키·네트워크·DB 없이 요청 빌드만 — exit 0."""

    def test_cli_dry_run_returns_zero(self) -> None:
        import cli

        rc = cli.main(["collect-products", "--keywords", "원룸 조명"])
        assert rc == 0
