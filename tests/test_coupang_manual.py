"""collector.coupang_manual + cli coupang-add 회귀 테스트 (세션 #25)."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pytest

import cli
from collector import coupang_manual as cm
from common import db
from writer import keyword_queue as kq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _apply_migrations(conn: sqlite3.Connection) -> None:
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.executescript("INSERT INTO personas (slug, title_ko, description) VALUES ('p', 'P', 'd');")
    conn.commit()


def _mem_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    _apply_migrations(conn)
    return conn


class TestBuildManualProduct:
    def test_fields(self) -> None:
        p = cm.build_manual_product(
            "쿠팡 선풍기", "https://link.coupang.com/a/xyz", price_krw=12900
        )
        assert p["source"] == "coupang"
        assert p["deeplink_url"] == "https://link.coupang.com/a/xyz"
        assert p["deeplink_slug"].startswith("coupang-")
        assert p["name"] == "쿠팡 선풍기"
        assert p["price_krw"] == 12900
        assert p["affiliate_tag"]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            cm.build_manual_product("  ", "https://x")

    def test_empty_url_raises(self) -> None:
        with pytest.raises(ValueError):
            cm.build_manual_product("선풍기", "  ")

    def test_deterministic_slug_by_url(self) -> None:
        a = cm.build_manual_product("A", "https://link.coupang.com/x")
        b = cm.build_manual_product("B", "https://link.coupang.com/x")
        assert a["deeplink_slug"] == b["deeplink_slug"]


class TestAddToKeyword:
    def test_appends(self) -> None:
        conn = _mem_db()
        kid = kq.add_keyword(conn, "선풍기", channel="coupang")
        p = cm.build_manual_product("쿠팡 선풍기", "https://link.coupang.com/a")
        assert cm.add_to_keyword(conn, kid, p) == 1
        raw = conn.execute(
            "SELECT target_products FROM keyword_queue WHERE id=?", (kid,)
        ).fetchone()[0]
        assert json.loads(raw)[0]["name"] == "쿠팡 선풍기"

    def test_dedup_by_slug(self) -> None:
        conn = _mem_db()
        kid = kq.add_keyword(conn, "선풍기", channel="coupang")
        p = cm.build_manual_product("쿠팡 선풍기", "https://link.coupang.com/a")
        cm.add_to_keyword(conn, kid, p)
        assert cm.add_to_keyword(conn, kid, p) == 1  # 같은 url→같은 slug→교체

    def test_two_distinct(self) -> None:
        conn = _mem_db()
        kid = kq.add_keyword(conn, "선풍기", channel="coupang")
        cm.add_to_keyword(conn, kid, cm.build_manual_product("A", "https://link.coupang.com/a"))
        assert (
            cm.add_to_keyword(conn, kid, cm.build_manual_product("B", "https://link.coupang.com/b"))
            == 2
        )

    def test_missing_keyword_raises(self) -> None:
        conn = _mem_db()
        p = cm.build_manual_product("x", "https://x")
        with pytest.raises(ValueError):
            cm.add_to_keyword(conn, 999, p)


class TestCmdCoupangAdd:
    @pytest.fixture()
    def migrated_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        p = tmp_path / "honsalim.db"
        conn = sqlite3.connect(str(p))
        _apply_migrations(conn)
        conn.close()
        monkeypatch.setattr(db, "DB_PATH", p)
        return p

    def test_add_success(self, migrated_db: Path) -> None:
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "선풍기", channel="coupang")
        conn.close()
        rc = cli.cmd_coupang_add(
            argparse.Namespace(
                keyword_id=kid,
                name="쿠팡 선풍기",
                url="https://link.coupang.com/a",
                price=12900,
                widget=None,
            )
        )
        assert rc == 0
        conn = db.connect(migrated_db)
        raw = conn.execute(
            "SELECT target_products FROM keyword_queue WHERE id=?", (kid,)
        ).fetchone()[0]
        conn.close()
        assert len(json.loads(raw)) == 1

    def test_missing_keyword_returns_2(self, migrated_db: Path) -> None:
        rc = cli.cmd_coupang_add(
            argparse.Namespace(keyword_id=999, name="x", url="https://x", price=None, widget=None)
        )
        assert rc == 2

    def test_empty_name_returns_2(self, migrated_db: Path) -> None:
        rc = cli.cmd_coupang_add(
            argparse.Namespace(keyword_id=1, name="  ", url="https://x", price=None, widget=None)
        )
        assert rc == 2
