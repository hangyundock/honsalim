"""cli 키워드 큐 명령 회귀 테스트 (세션 #25) — add·generate(dry)·list·reject.

LLM·외부 API는 호출하지 않는 경로만 (dry_run·검증·반려·목록).
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
        "INSERT INTO personas (slug, title_ko, description) VALUES ('jachi', '자취생', 'd');"
        "INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);"
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


def _add_kw(keyword: str = "자취생 전자레인지 추천", channel: str = "ali") -> int:
    return cli.cmd_keyword_add(
        _ns(
            keyword=keyword,
            channel=channel,
            slug=None,
            budget_min=None,
            budget_max=None,
            note=None,
            score=0.0,
        )
    )


class TestKeywordAdd:
    def test_add_pending(self, migrated_db: Path) -> None:
        assert _add_kw() == 0
        conn = db.connect(migrated_db)
        n = conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE status='pending'").fetchone()[0]
        conn.close()
        assert n == 1

    def test_bad_channel_returns_2(self, migrated_db: Path) -> None:
        assert _add_kw(channel="naver") == 2


class TestKeywordGenerateDryRun:
    def test_dry_run_no_writes(self, migrated_db: Path) -> None:
        _add_kw("원룸 가습기")
        conn = db.connect(migrated_db)
        kid = conn.execute("SELECT id FROM keyword_queue").fetchone()[0]
        scen_before = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        conn.close()

        rc = cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=True))
        assert rc == 0

        conn = db.connect(migrated_db)
        # dry_run은 쓰기 없음: 새 시나리오·draft 미생성, 상태 pending 유지
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == scen_before
        assert conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == 0
        assert (
            conn.execute("SELECT status FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0]
            == "pending"
        )
        conn.close()

    def test_missing_id_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_keyword_generate(_ns(id=999, page_size=20, dry_run=True)) == 2


class TestKeywordList:
    def test_list_prints(self, migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _add_kw("선풍기")
        rc = cli.cmd_keyword_list(_ns(status=None))
        assert rc == 0
        assert "선풍기" in capsys.readouterr().out

    def test_list_empty(self, migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.cmd_keyword_list(_ns(status=None)) == 0
        assert "없음" in capsys.readouterr().out


class TestReject:
    def _draft(self, dbpath: Path, status: str) -> int:
        conn = db.connect(dbpath)
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (1, ?)", (status,))
        conn.commit()
        did = conn.execute("SELECT id FROM drafts ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.close()
        return int(did)

    def test_reject_validated(self, migrated_db: Path) -> None:
        did = self._draft(migrated_db, "validated")
        assert cli.cmd_reject(_ns(draft=did, note="테스트")) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT status FROM drafts WHERE id=?", (did,)).fetchone()[0] == "rejected"
        )
        conn.close()

    def test_reject_approved_two_step(self, migrated_db: Path) -> None:
        did = self._draft(migrated_db, "approved")
        assert cli.cmd_reject(_ns(draft=did, note=None)) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT status FROM drafts WHERE id=?", (did,)).fetchone()[0] == "rejected"
        )
        conn.close()

    def test_reject_missing_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_reject(_ns(draft=999, note=None)) == 2


class TestParserRegistration:
    def test_new_commands_registered(self) -> None:
        parser = cli.build_parser()
        # subparsers 액션에서 등록된 명령 이름 수집
        names: set[str] = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                names |= set(action.choices)
        assert {"keyword-add", "keyword-generate", "keyword-list", "reject"} <= names
