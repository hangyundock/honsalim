"""auto-cycle (B-i 무인 사이클) — auto_mode 게이트 안전 기본값 + 파서 + 오케스트레이션 (세션 #29).

핵심 안전: auto_mode OFF(기본)면 자동 사이클이 아무것도 하지 않는다(사람 게이트 E7 유지).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

import cli


class TestAutoCycleGate:
    def test_off_by_default_does_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # auto_mode OFF → DB·LLM·배포 일절 없이 즉시 0 반환(안전 기본값)
        monkeypatch.setattr(
            cli.settings, "get", lambda k, *a, **kw: False if k == "auto_mode" else None
        )
        rc = cli.cmd_auto_cycle(argparse.Namespace(count=None, dry_run=True, no_deploy=False))
        assert rc == 0


class TestAutoCycleParser:
    def test_subcommand_parses_dry_run_default(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["auto-cycle"])
        assert args.command == "auto-cycle"
        assert args.func == cli.cmd_auto_cycle
        assert args.dry_run is True  # 기본 dry_run

    def test_no_dry_run_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["auto-cycle", "--no-dry-run", "--count", "3"])
        assert args.dry_run is False
        assert args.count == 3


class TestAutoModeDefault:
    def test_auto_mode_default_off(self) -> None:
        from common import settings

        assert settings.DEFAULTS["auto_mode"] is False  # 기본 OFF (E7 유지)


class TestAutoCycleOrchestration:
    def test_live_calls_generate_and_publish(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # auto_mode ON 라이브 → 대기 키워드는 생성 호출, 승인된 글은 publish-queue 호출(배선 검증)
        from common import db
        from writer import article_writer, state_machine
        from writer import keyword_queue as kq

        p = tmp_path / "t.db"
        db.migrate(db_path=p)
        db.seed(db_path=p)
        conn = db.connect(p)
        kid = kq.get_or_create(conn, "컴퓨터의자", channel="ali")  # 기본 status=pending
        sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]
        did = article_writer.create_draft(conn, scenario_id=sid)
        for st in ("enriched", "validated", "approved"):  # 발행 대상 approved 1개
            state_machine.transition(conn, did, st)
        conn.commit()
        conn.close()

        monkeypatch.setattr(cli.db, "DB_PATH", p)
        monkeypatch.setattr(
            cli.settings,
            "get",
            lambda k, d=None, **kw: (
                True if k == "auto_mode" else (1 if k == "publish_per_day" else d)
            ),
        )
        gen: list[int] = []
        pub: list[int] = []

        def fake_gen(ns: argparse.Namespace) -> int:
            gen.append(ns.id)
            return 0

        def fake_pub(ns: argparse.Namespace) -> int:
            pub.append(ns.count)
            return 0

        monkeypatch.setattr(cli, "cmd_keyword_generate", fake_gen)
        monkeypatch.setattr(cli, "cmd_publish_queue", fake_pub)

        rc = cli.cmd_auto_cycle(argparse.Namespace(count=1, dry_run=False, no_deploy=True))
        assert rc == 0
        assert kid in gen  # 대기 키워드 → 생성 호출
        assert pub == [1]  # 승인된 글 → publish-queue 호출(count=1)


class TestAutoApproveSafetyGate:
    """④ 세션 #33 — 초기 검수→자동 전환 안전장치: 발행 이력 N편 미만이면 자동 승인 보류."""

    def _validated_draft(self, p: Path) -> Any:
        from common import db
        from writer import article_writer, state_machine

        db.migrate(db_path=p)
        db.seed(db_path=p)
        conn = db.connect(p)
        sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]
        did = article_writer.create_draft(conn, scenario_id=sid)
        for st in ("enriched", "validated"):
            state_machine.transition(conn, did, st)
        conn.commit()
        return conn

    def test_holds_until_min_published(self, tmp_path: Path) -> None:
        from writer import auto_approve as aa

        conn = self._validated_draft(tmp_path / "t.db")
        # published 0 < min_published 5 → 전체 보류(자동 승인 0), 사유는 초기 검수
        res = aa.auto_approve(conn, apply=False, min_published=5)
        assert res["approved"] == []
        assert len(res["held"]) == 1
        assert "초기 검수" in res["held"][0]["reason"]
        conn.close()

    def test_gate_off_when_min_zero(self, tmp_path: Path) -> None:
        from writer import auto_approve as aa

        conn = self._validated_draft(tmp_path / "t.db")
        # min_published=0 → 게이트 없음(하위호환): eligible 단계로 진행, '초기 검수' 보류 아님
        res = aa.auto_approve(conn, apply=False, min_published=0)
        assert all("초기 검수" not in h["reason"] for h in res["held"])
        conn.close()
