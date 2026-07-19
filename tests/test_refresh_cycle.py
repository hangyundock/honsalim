"""deployer.refresh_cycle — 무인 일일 새로고침·자가복원·빌드·배포 사이클 회귀 (세션 #23, A안).

published 선택·새로고침 실패 격리·가드레일 자가복원(fail-closed 킬스위치)·변경분만 배포·
dry_run 외부영향 차단을 검증. 외부 호출(알리·git)은 monkeypatch로 오프라인 보장.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from common import db
from deployer import refresh_cycle as rc


@pytest.fixture()
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    c = db.connect(db_path)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()


def _publish(conn: sqlite3.Connection, slug: str, *, with_guide: bool = True) -> None:
    """카테고리를 published로 — 글 유무 선택(글 없으면 가드레일 미달로 monitor가 플래그)."""
    if with_guide:
        conn.execute(
            "UPDATE categories SET status='published', guide_generated_at=CURRENT_TIMESTAMP, "
            "guide_md='가이드', guide_title='제목' WHERE slug=?",
            (slug,),
        )
    else:
        conn.execute("UPDATE categories SET status='published' WHERE slug=?", (slug,))
    conn.commit()


@dataclass
class _FakeCollect:
    received: int = 12
    relevant: int = 10
    linked: int = 6
    removed_stale: int = 1


class TestPublishedSelection:
    def test_only_published_selected(self, conn: sqlite3.Connection) -> None:
        _publish(conn, "office-chair")
        _publish(conn, "desk")
        # monitor-stand는 draft로 둠
        res = rc.run_refresh_cycle(
            conn, project_root=Path("."), refresh=False, do_build=False, do_deploy=False
        )
        assert set(res.published) == {"office-chair", "desk"}
        assert "monitor-stand" not in res.published

    def test_no_published_no_crash(self, conn: sqlite3.Connection) -> None:
        res = rc.run_refresh_cycle(
            conn, project_root=Path("."), refresh=False, do_build=False, do_deploy=False
        )
        assert res.published == []
        assert res.killswitched == []


class TestRefresh:
    def test_refresh_calls_collect_for_each(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _publish(conn, "office-chair")
        _publish(conn, "desk")
        called: list[str] = []

        def fake(c: object, slug: str, *, dry_run: bool, page_size: int) -> _FakeCollect:
            called.append(slug)
            return _FakeCollect()

        monkeypatch.setattr(rc.category_collect, "collect_category", fake)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=True,
            do_build=False,
            do_deploy=False,
            dry_run=True,
        )
        assert set(called) == {"office-chair", "desk"}
        assert all(r.ok for r in res.refreshed)
        assert res.refreshed[0].received == 12 and res.refreshed[0].linked == 6

    def test_refresh_error_isolated(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _publish(conn, "office-chair")
        _publish(conn, "desk")

        def fake(c: object, slug: str, *, dry_run: bool, page_size: int) -> _FakeCollect:
            if slug == "office-chair":
                raise ValueError("API 실패")
            return _FakeCollect()

        monkeypatch.setattr(rc.category_collect, "collect_category", fake)
        res = rc.run_refresh_cycle(
            conn, project_root=Path("."), refresh=True, do_build=False, do_deploy=False
        )
        by_slug = {r.slug: r for r in res.refreshed}
        assert by_slug["office-chair"].ok is False
        assert "API 실패" in (by_slug["office-chair"].error or "")
        assert by_slug["desk"].ok is True  # 한 건 실패가 다음을 막지 않음
        assert len(res.refresh_errors) == 1


class TestSelfHeal:
    def test_killswitch_unapproves_failing(self, conn: sqlite3.Connection) -> None:
        # 글 없는 published → 가드레일 '가이드 글 없음' 미달 → 자동 비공개
        _publish(conn, "office-chair", with_guide=False)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=False,
            auto_killswitch=True,
            dry_run=False,
        )
        assert "office-chair" in res.killswitched
        row = conn.execute("SELECT status FROM categories WHERE slug='office-chair'").fetchone()
        assert row[0] == "draft"  # 비공개로 복원됨(fail-closed)

    def test_dry_run_does_not_killswitch(self, conn: sqlite3.Connection) -> None:
        _publish(conn, "office-chair", with_guide=False)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=False,
            auto_killswitch=True,
            dry_run=True,
        )
        assert res.killswitched == []  # dry_run은 적용 안 함
        row = conn.execute("SELECT status FROM categories WHERE slug='office-chair'").fetchone()
        assert row[0] == "published"  # 변경 없음
        assert res.flagged  # 그래도 미달은 가시화

    def test_report_only_when_killswitch_off(self, conn: sqlite3.Connection) -> None:
        _publish(conn, "office-chair", with_guide=False)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=False,
            auto_killswitch=False,
            dry_run=False,
        )
        assert res.killswitched == []  # 끄면 비공개 안 함
        assert any(f["slug"] == "office-chair" for f in res.flagged)
        row = conn.execute("SELECT status FROM categories WHERE slug='office-chair'").fetchone()
        assert row[0] == "published"  # 보고만


class TestDeploy:
    def test_deploy_skips_when_no_change(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _no_push(**kw: object) -> None:
            pytest.fail("변경 없으면 push 안 함")

        monkeypatch.setattr(rc, "detect_changes", lambda root, paths=rc.DEPLOY_PATHS: (False, ""))
        monkeypatch.setattr(rc, "git_push", _no_push)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.deployed is False  # 변경 없으면 push 안 함(_no_push 미호출)
        assert any("스킵" in n for n in res.notes)

    def test_deploy_pushes_when_changed(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        @dataclass
        class _Push:
            returncode: int = 0
            stderr: str = ""

        @dataclass
        class _Git:
            returncode: int = 0
            stdout: str = ""
            stderr: str = ""

        monkeypatch.setattr(
            rc, "detect_changes", lambda root, paths=rc.DEPLOY_PATHS: (True, " M x")
        )
        monkeypatch.setattr(rc, "_git", lambda args, **kw: _Git())
        monkeypatch.setattr(rc, "git_push", lambda **kw: _Push())
        # #45: 배포 성공 후속 IndexNow 통지는 별도 테스트에서 검증 — 여기선 차단(외부 호출 0)
        monkeypatch.setattr(rc, "_notify_indexnow", lambda result, root: None)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.changed is True
        assert res.deployed is True
        assert res.push_rc == 0

    def test_dry_run_never_deploys(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            rc, "detect_changes", lambda root, paths=rc.DEPLOY_PATHS: (True, " M x")
        )
        monkeypatch.setattr(rc, "git_push", lambda **kw: pytest.fail("dry_run은 push 금지"))
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=True,
        )
        assert res.deployed is False


class TestIndexnowWiring:
    """★세션 #45 — 배포 성공 후 IndexNow 통지 배선 + §0 격리(핑 실패가 배포 결과 불변)."""

    @staticmethod
    def _fake_git(monkeypatch: pytest.MonkeyPatch) -> None:
        from dataclasses import dataclass

        @dataclass
        class _Ok:
            returncode: int = 0
            stdout: str = ""
            stderr: str = ""

        monkeypatch.setattr(
            rc, "detect_changes", lambda root, paths=rc.DEPLOY_PATHS: (True, " M x")
        )
        monkeypatch.setattr(rc, "_git", lambda args, **kw: _Ok())
        monkeypatch.setattr(rc, "git_push", lambda **kw: _Ok())

    def test_deploy_success_pings_sitemap_urls(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from deployer import indexnow as ixn

        self._fake_git(monkeypatch)
        calls: dict[str, object] = {}
        monkeypatch.setattr(ixn, "indexnow_ready", lambda: True)
        monkeypatch.setattr(
            ixn, "sitemap_urls", lambda p: ["https://honsallim.com/", "https://honsallim.com/a/"]
        )

        def fake_ping(urls: list[str]) -> bool:
            calls["urls"] = list(urls)
            return True

        monkeypatch.setattr(ixn, "ping", fake_ping)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.deployed is True
        assert calls["urls"] == ["https://honsallim.com/", "https://honsallim.com/a/"]
        assert any("IndexNow 통지 성공" in n for n in res.notes)

    def test_push_failure_never_pings(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from dataclasses import dataclass

        from deployer import indexnow as ixn

        @dataclass
        class _Ok:
            returncode: int = 0
            stdout: str = ""
            stderr: str = ""

        @dataclass
        class _Fail:
            returncode: int = 1
            stdout: str = ""
            stderr: str = "denied"

        monkeypatch.setattr(
            rc, "detect_changes", lambda root, paths=rc.DEPLOY_PATHS: (True, " M x")
        )
        monkeypatch.setattr(rc, "_git", lambda args, **kw: _Ok())
        monkeypatch.setattr(rc, "git_push", lambda **kw: _Fail())
        monkeypatch.setattr(
            ixn, "indexnow_ready", lambda: pytest.fail("push 실패 시 IndexNow 호출 금지")
        )
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.deployed is False

    def test_ping_exception_does_not_affect_deploy(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """§0: 통지 코드가 예외를 던져도 deployed=True 유지·notes에만 기록."""
        from deployer import indexnow as ixn

        self._fake_git(monkeypatch)
        monkeypatch.setattr(
            ixn, "indexnow_ready", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.deployed is True  # 핑 실패는 배포 결과를 절대 오염시키지 않음
        assert any("IndexNow 오류(무시)" in n for n in res.notes)

    def test_not_ready_notes_and_skips(
        self, conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from deployer import indexnow as ixn

        self._fake_git(monkeypatch)
        monkeypatch.setattr(ixn, "indexnow_ready", lambda: False)
        monkeypatch.setattr(ixn, "ping", lambda urls: pytest.fail("미설정이면 핑 금지"))
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=True,
            dry_run=False,
        )
        assert res.deployed is True
        assert any("IndexNow 미설정" in n for n in res.notes)


class TestReport:
    def test_cycle_report_dict_captures_killswitch(self, conn: sqlite3.Connection) -> None:
        _publish(conn, "office-chair", with_guide=False)
        res = rc.run_refresh_cycle(
            conn,
            project_root=Path("."),
            refresh=False,
            do_build=False,
            do_deploy=False,
            auto_killswitch=True,
            dry_run=False,
        )
        rep = rc.cycle_report(res, ran_at="2026-06-03T11:00:00+09:00")
        assert rep["ran_at"] == "2026-06-03T11:00:00+09:00"
        assert rep["dry_run"] is False
        assert "office-chair" in rep["killswitched"]
        assert rep["had_issue"] is True
        assert isinstance(rep["refreshed"], list)

    def test_write_and_reload_cycle_report(self, conn: sqlite3.Connection, tmp_path: Path) -> None:
        res = rc.run_refresh_cycle(
            conn, project_root=Path("."), refresh=False, do_build=False, do_deploy=False
        )
        p = tmp_path / "data" / "refresh_cycle_last.json"
        out = rc.write_cycle_report(res, p, ran_at="2026-06-03T11:00:00+09:00")
        assert out.exists()
        from dashboard import render as dash_render

        loaded = dash_render.load_last_cycle(p)
        assert loaded is not None
        assert loaded["ran_at"] == "2026-06-03T11:00:00+09:00"
