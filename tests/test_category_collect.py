"""category_collect 회귀 — yml 로딩 + dry_run 안전 + (모킹) 수집·정제·티어·연결·정가저장.

라이브 HTTP는 호출하지 않는다(ali.query_products를 모킹). 실제 마이그레이션을 in-memory에
적용해 categories/category_products/products 스키마를 그대로 검증한다.
"""

from __future__ import annotations

import sqlite3
from typing import Any

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

from collector import aliexpress as ali
from collector import category_collect as cc
from common import db as _db


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO categories (slug, name_ko, status) VALUES ('office-chair', '사무용 의자', 'draft')"
    )
    conn.commit()
    return conn


def _item(pid: str, name: str, **extra: Any) -> dict[str, Any]:
    row = {
        "source": "aliexpress",
        "source_product_id": pid,
        "name": name,
        "price_krw": 50000,
        "deeplink_url": f"https://s.click.aliexpress.com/{pid}",
        "deeplink_slug": f"ali-{pid}",
        "affiliate_tag": "TRACK",
        "availability": "unknown",
    }
    row.update(extra)
    return row


class TestLoadSources:
    def test_office_chair_and_desk_defined(self) -> None:
        s = cc.load_sources()
        assert "office-chair" in s and "desk" in s
        oc = s["office-chair"]
        assert "의자" in oc.require_any
        assert set(oc.tiers) == {"budget", "premium"}
        assert oc.tiers["budget"].q == "office chair"
        assert oc.tiers["premium"].min_price == 100000


class TestDryRun:
    def test_dry_run_no_db_write(self) -> None:
        conn = _conn()
        res = cc.collect_category(conn, "office-chair", dry_run=True)
        assert res.dry_run is True
        assert res.linked == 0
        assert len(res.terms) == 2
        assert conn.execute("SELECT COUNT(*) FROM category_products").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0

    def test_unknown_slug_raises(self) -> None:
        conn = _conn()
        try:
            cc.collect_category(conn, "no-such-cat", dry_run=True)
            raise AssertionError("KeyError 기대")
        except KeyError:
            pass


class TestLiveMocked:
    def test_collect_filters_links_and_persists_discount(self, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            if "ergonomic" in q:  # premium 티어
                items = [
                    _item(
                        "P1",
                        "인체공학 사무용 의자",
                        price_krw=150000,
                        original_price_krw=200000,
                        discount_pct=25,
                    ),
                    _item("X1", "의자 발받침 쿠션", price_krw=120000),  # '발받침' exclude
                ]
            else:  # budget 티어
                items = [
                    _item("P2", "메쉬 컴퓨터 의자", price_krw=50000),
                    _item("Z1", "노트북 거치대", price_krw=40000),  # '의자' 미포함 → 제외
                ]
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        res = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        # P1(premium)·P2(budget) 통과. X1(발받침 exclude)·Z1(의자 미포함) 제외.
        assert res.relevant == 2
        assert res.linked == 2
        rows = conn.execute(
            "SELECT p.source_product_id, cp.tier FROM category_products cp "
            "JOIN products p ON p.id = cp.product_id ORDER BY cp.display_order"
        ).fetchall()
        assert {r[0]: r[1] for r in rows} == {"P2": "budget", "P1": "premium"}
        # 정가/할인 영속화 (products_store 정합)
        op = conn.execute(
            "SELECT original_price_krw, discount_pct FROM products WHERE source_product_id = 'P1'"
        ).fetchone()
        assert tuple(op) == (200000, 25)

    def test_dedup_same_product_across_tiers(self, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            # 동일 제품 P1이 두 티어 검색에 모두 등장
            return ali.QueryResult(
                dry_run=False,
                request={},
                products=[_item("P1", "메쉬 사무용 의자")],
                resp_code="200",
            )

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        res = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        assert res.linked == 1  # 중복 제외 — 한 번만 연결
        assert conn.execute("SELECT COUNT(*) FROM category_products").fetchone()[0] == 1


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
