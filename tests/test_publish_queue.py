"""cli publish-queue 회귀 테스트 (세션 #25) — dry-run·선택·빈 큐.

라이브(promote·git push)는 외부 영향이라 실행하지 않는다 — dry-run·선택 로직만 검증.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pytest

import cli
from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.executescript(
        "INSERT INTO personas (slug, title_ko, description) VALUES ('p', 'P', 'd');"
        "INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s', 'S', 'd', 1);"
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def migrated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    p = tmp_path / "honsalim.db"
    _make_db(p)
    monkeypatch.setattr(db, "DB_PATH", p)
    return p


def _ns(**kw: object) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def _approved(dbpath: Path, title: str) -> None:
    conn = db.connect(dbpath)
    conn.execute(
        "INSERT INTO drafts (scenario_id, working_title, status) VALUES (1, ?, 'approved')",
        (title,),
    )
    conn.commit()
    conn.close()


def test_empty_queue_returns_0(migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.cmd_publish_queue(_ns(count=None, no_deploy=False, dry_run=True)) == 0
    assert "없습니다" in capsys.readouterr().out


def test_dry_run_lists_and_no_promote(
    migrated_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _approved(migrated_db, "글A")
    _approved(migrated_db, "글B")
    rc = cli.cmd_publish_queue(_ns(count=5, no_deploy=False, dry_run=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "글A" in out and "글B" in out and "DRY" in out
    # dry-run은 promote 안 함 — 여전히 approved 2건
    conn = db.connect(migrated_db)
    n = conn.execute("SELECT COUNT(*) FROM drafts WHERE status='approved'").fetchone()[0]
    conn.close()
    assert n == 2


def test_count_limits_selection(migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for t in ("A", "B", "C"):
        _approved(migrated_db, t)
    cli.cmd_publish_queue(_ns(count=2, no_deploy=False, dry_run=True))
    out = capsys.readouterr().out
    assert "상한 2" in out


def test_default_count_from_settings(migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """count 미지정 → config publish_per_day(기본 1)."""
    _approved(migrated_db, "글A")
    _approved(migrated_db, "글B")
    cli.cmd_publish_queue(_ns(count=None, no_deploy=False, dry_run=True))
    out = capsys.readouterr().out
    assert "상한 1" in out  # 기본 publish_per_day=1


def test_live_publish_uses_refresh_cycle_commit(
    migrated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """★EVENTS #30 재발 방지: 라이브 발행은 build/site를 commit하는 refresh_cycle을 거쳐야 한다.

    옛 버그는 cmd_deploy(git push만·commit 없음)라 새 글이 라이브 미반영(404·무인 치명).
    promote·refresh_cycle을 모킹(외부 영향 없음)해, cmd_publish_queue 라이브 경로가
    refresh_cycle.run_refresh_cycle을 do_build+do_deploy(+refresh=False)로 호출함을 보장.
    """
    from types import SimpleNamespace

    _approved(migrated_db, "글A")
    calls: dict[str, object] = {}

    def fake_refresh(conn: object, **kw: object) -> object:
        calls["refresh_kw"] = kw
        return SimpleNamespace(built=True, deployed=True, changed=True, go_count=3, notes=[])

    monkeypatch.setattr(cli, "cmd_promote", lambda args: 0)
    monkeypatch.setattr("deployer.refresh_cycle.run_refresh_cycle", fake_refresh)

    rc = cli.cmd_publish_queue(_ns(count=1, no_deploy=False, dry_run=False))
    assert rc == 0
    kw = calls["refresh_kw"]
    assert isinstance(kw, dict)
    assert kw["do_build"] is True
    assert kw["do_deploy"] is True
    assert kw["refresh"] is False  # 콘텐츠 수집 안 함 — 이미 생성·승인된 글만 발행
    assert kw["dry_run"] is False
    assert "발행·배포 완료" in capsys.readouterr().out


def test_live_publish_no_deploy_builds_only(
    migrated_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--no-deploy면 빌드만(do_deploy=False) — 배포(외부 게시) 생략."""
    from types import SimpleNamespace

    _approved(migrated_db, "글A")
    calls: dict[str, object] = {}

    monkeypatch.setattr(cli, "cmd_promote", lambda args: 0)

    def fake_refresh(conn: object, **kw: object) -> object:
        calls["refresh_kw"] = kw
        return SimpleNamespace(built=True, deployed=False, changed=False, go_count=0, notes=[])

    monkeypatch.setattr("deployer.refresh_cycle.run_refresh_cycle", fake_refresh)

    rc = cli.cmd_publish_queue(_ns(count=1, no_deploy=True, dry_run=False))
    assert rc == 0
    kw = calls["refresh_kw"]
    assert isinstance(kw, dict)
    assert kw["do_deploy"] is False
    assert "배포 생략" in capsys.readouterr().out
