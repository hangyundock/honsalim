"""collector.category_coupang + cli category-coupang-* 회귀 테스트 (세션 #32).

쿠팡 공식 배너 → products 업서트 → category_products 링크(운영자추천 zone). 외부 호출 없음.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pytest

from collector import category_coupang
from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"

BANNER = (
    '<a href="https://link.coupang.com/a/ABC123">'
    '<img src="https://static.coupangcdn.com/image/affiliate/banner/x@2x.jpg" '
    'alt="라보토리 사무용 의자, 베이지"></a>'
)
BANNER2 = (
    '<a href="https://link.coupang.com/a/DEF456">'
    '<img src="https://static.coupangcdn.com/image/affiliate/banner/y@2x.jpg" '
    'alt="시디즈 T50 메쉬 의자"></a>'
)


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.executescript(
        "INSERT INTO categories (slug, name_ko, status) VALUES ('office-chair', '의자', 'published');"
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def cat_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    p = tmp_path / "honsalim.db"
    _make_db(p)
    monkeypatch.setattr(db, "DB_PATH", p)
    return p


class TestModule:
    def test_add_banner_links_product(self, cat_db: Path) -> None:
        conn = db.connect(cat_db)
        res = category_coupang.add_banners(conn, "office-chair", BANNER)
        conn.close()
        assert res["added"] == 1
        assert "라보토리" in res["names"][0]
        conn = db.connect(cat_db)
        rows = category_coupang.list_coupang(conn, "office-chair")
        conn.close()
        assert len(rows) == 1
        assert rows[0]["image_url_external"].endswith("x@2x.jpg")

    def test_add_multiple_banners(self, cat_db: Path) -> None:
        conn = db.connect(cat_db)
        res = category_coupang.add_banners(conn, "office-chair", BANNER + "\n" + BANNER2)
        conn.close()
        assert res["added"] == 2
        conn = db.connect(cat_db)
        assert len(category_coupang.list_coupang(conn, "office-chair")) == 2
        conn.close()

    def test_add_idempotent(self, cat_db: Path) -> None:
        conn = db.connect(cat_db)
        category_coupang.add_banners(conn, "office-chair", BANNER)
        category_coupang.add_banners(conn, "office-chair", BANNER)  # 같은 배너 재추가
        conn.close()
        conn = db.connect(cat_db)
        assert len(category_coupang.list_coupang(conn, "office-chair")) == 1  # 중복 링크 안 됨
        conn.close()

    def test_add_unknown_category_raises(self, cat_db: Path) -> None:
        conn = db.connect(cat_db)
        with pytest.raises(ValueError):
            category_coupang.add_banners(conn, "no-such", BANNER)
        conn.close()

    def test_remove_unlinks_keeps_product(self, cat_db: Path) -> None:
        conn = db.connect(cat_db)
        category_coupang.add_banners(conn, "office-chair", BANNER)
        pid = category_coupang.list_coupang(conn, "office-chair")[0]["id"]
        n = category_coupang.remove(conn, "office-chair", pid)
        conn.close()
        assert n == 1
        conn = db.connect(cat_db)
        assert category_coupang.list_coupang(conn, "office-chair") == []
        assert conn.execute("SELECT COUNT(*) FROM products WHERE id=?", (pid,)).fetchone()[0] == 1
        conn.close()


class TestCli:
    def test_add_list_remove(self, cat_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
        import cli

        ns = argparse.Namespace
        assert cli.cmd_category_coupang_add(ns(slug="office-chair", banner=BANNER)) == 0
        assert cli.cmd_category_coupang_list(ns(slug="office-chair")) == 0
        assert "라보토리" in capsys.readouterr().out
        conn = db.connect(cat_db)
        pid = category_coupang.list_coupang(conn, "office-chair")[0]["id"]
        conn.close()
        assert cli.cmd_category_coupang_remove(ns(slug="office-chair", product_id=pid)) == 0

    def test_add_unknown_returns_2(self, cat_db: Path) -> None:
        import cli

        assert cli.cmd_category_coupang_add(argparse.Namespace(slug="no-such", banner=BANNER)) == 2

    def test_parsers_registered(self) -> None:
        import cli

        parser = cli.build_parser()
        names: set[str] = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                names |= set(action.choices)
        assert {
            "category-coupang-add",
            "category-coupang-list",
            "category-coupang-remove",
            "build-deploy",
        } <= names


class TestBuildDeploy:
    def test_calls_refresh_cycle_with_safe_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """빌드·배포는 refresh·killswitch 끄고 build+deploy만 — 카테고리 임의 비공개 방지(§0)."""
        import cli
        from deployer import refresh_cycle

        captured: dict[str, object] = {}

        class _Res:
            deployed = True
            changed = True
            go_count = 5
            notes = ()

        def _fake(conn: object, **kw: object) -> _Res:
            captured.update(kw)
            return _Res()

        monkeypatch.setattr(refresh_cycle, "run_refresh_cycle", _fake)
        rc = cli.cmd_build_deploy(argparse.Namespace(dry_run=False, message="x"))
        assert rc == 0
        assert captured["refresh"] is False  # 가격 새로고침 안 함
        assert captured["auto_killswitch"] is False  # 카테고리 임의 비공개 안 함
        assert captured["do_build"] is True
        assert captured["do_deploy"] is True

    def test_no_changes_returns_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import cli
        from deployer import refresh_cycle

        class _Res:
            deployed = False
            changed = False
            go_count = 0
            notes = ()

        monkeypatch.setattr(refresh_cycle, "run_refresh_cycle", lambda *a, **k: _Res())
        assert cli.cmd_build_deploy(argparse.Namespace(dry_run=False, message=None)) == 0
