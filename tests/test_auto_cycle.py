"""auto-cycle (B-i 무인 사이클) — auto_mode 게이트 안전 기본값 + 파서 + 오케스트레이션 (세션 #29).

핵심 안전: auto_mode OFF(기본)면 자동 사이클이 아무것도 하지 않는다(사람 게이트 E7 유지).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

import cli


@pytest.fixture(autouse=True)
def _no_real_notify(monkeypatch: pytest.MonkeyPatch) -> None:
    """★실발송·실 secrets 격리 (세션 #45 적대검증 적발 — §0 테스트 위생).

    오케스트레이션 테스트가 cmd_auto_cycle 라이브 경로를 돌 때 _auto_cycle_notify가 실
    config.load_secrets()→notify.send_telegram()까지 도달해, telegram.env가 설정된 운영
    머신에서는 **pytest 실행마다 주인 폰으로 가짜 '무인 사이클' 리포트가 실발송**되고
    실 시크릿 4종이 os.environ에 유입돼 이후 테스트가 머신·순서 의존이 되던 결함의 차단.
    알림 내용 자체는 digest 단위 테스트가 검증한다.
    """
    monkeypatch.setattr(cli, "_auto_cycle_notify", lambda *a, **k: None)
    monkeypatch.setattr("common.notify.send_telegram", lambda *a, **k: False)
    monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: {})


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

    def test_empty_queue_autopicks_from_recommender(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ★완전 무인(세션 #34): 대기 키워드가 0개여도 winnable 추천에서 자동 보충→생성 호출.
        # 옛 코드는 pending만 소비해 빈 큐면 0편 생성(EVENTS #33 갭). auto_pick_keyword 배선 검증.
        from common import db
        from writer import keyword_recommender as kr_mod

        p = tmp_path / "t.db"
        db.migrate(db_path=p)
        db.seed(db_path=p)  # 대기 키워드는 추가하지 않음 — 큐 비어 있음

        monkeypatch.setattr(cli.db, "DB_PATH", p)
        monkeypatch.setattr(
            cli.settings,
            "get",
            lambda k, d=None, **kw: (
                True if k == "auto_mode" else (1 if k == "publish_per_day" else d)
            ),
        )
        # 추천 경로(네이버 조회·LLM)는 모킹 — 빈 큐→추천 키워드 1건 반환만 검증.
        monkeypatch.setattr(
            kr_mod,
            "auto_pick_keyword",
            lambda conn, **kw: {"keyword_id": 99, "keyword": "원룸 수납", "source": "recommend"},
        )
        gen: list[int] = []

        def fake_gen(ns: argparse.Namespace) -> int:
            gen.append(ns.id)
            return 0

        monkeypatch.setattr(cli, "cmd_keyword_generate", fake_gen)
        monkeypatch.setattr(cli, "cmd_publish_queue", lambda ns: 0)

        rc = cli.cmd_auto_cycle(argparse.Namespace(count=1, dry_run=False, no_deploy=True))
        assert rc == 0
        assert gen == [99]  # 빈 큐인데도 추천 키워드로 생성 호출됨(완전 무인 핵심)


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


class TestAutoCycleDigest:
    """세션 #39 무인 자기보고: 사이클 health 다이제스트 + '조용한 정지' 비정상 판정.

    무인 운영 중 대시보드는 안 열리므로 결과를 파일/로그로 자기보고. min_published(의도된 보류)는
    '문제'로 안 쳐 오경보를 막고, 발행 0 + (문제보류 or 큐 발행가능 0)일 때만 abnormal(ALERT)."""

    def _conn(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
        from common import db

        p = tmp_path / "t.db"
        db.migrate(db_path=p)
        db.seed(db_path=p)
        monkeypatch.setattr(cli.db, "DB_PATH", p)  # 다이제스트 파일이 tmp에 쓰이도록
        conn = db.connect(p)
        # #45: seed는 §2-마에 따라 전부 draft — 운영 현실(매핑 카테고리=published)을 반영해
        # 공개로 올린다(publishability(conn)의 category_draft 판정과 기존 테스트 의도 정합).
        conn.execute("UPDATE categories SET status='published'")
        conn.commit()
        return conn

    def test_healthy_not_abnormal(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from writer import keyword_queue as kq

        conn = self._conn(tmp_path, monkeypatch)
        kq.add_keyword(conn, "컴퓨터의자", channel="ali")  # 매핑 → publishable
        d = cli._auto_cycle_digest_and_alert(
            conn, made=1, ar={"approved": [1], "held": []}, approved_n=1
        )
        assert d["abnormal"] is False
        assert d["queue_publishable"] == 1
        conn.close()

    def test_problem_hold_zero_publish_is_abnormal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = self._conn(tmp_path, monkeypatch)
        ar = {"approved": [], "held": [{"draft": 5, "reason": "x", "code": "unmapped"}]}
        d = cli._auto_cycle_digest_and_alert(conn, made=1, ar=ar, approved_n=0)
        assert d["abnormal"] is True
        assert d["held_by_code"]["unmapped"] == 1
        conn.close()

    def test_min_published_hold_not_abnormal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from writer import keyword_queue as kq

        conn = self._conn(tmp_path, monkeypatch)
        kq.add_keyword(conn, "컴퓨터의자", channel="ali")  # 발행가능 큐 존재
        ar = {
            "approved": [],
            "held": [{"draft": 5, "reason": "초기 검수", "code": "min_published"}],
        }
        d = cli._auto_cycle_digest_and_alert(conn, made=1, ar=ar, approved_n=0)
        assert d["abnormal"] is False  # 의도된 보류는 ALERT 아님(오경보 방지)
        conn.close()

    def test_all_unmapped_queue_is_abnormal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from writer import keyword_queue as kq

        conn = self._conn(tmp_path, monkeypatch)
        kq.add_keyword(conn, "양자역학교재", channel="ali")  # 미매핑 → 큐 발행가능 0
        d = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"approved": [], "held": []}, approved_n=0
        )
        assert d["abnormal"] is True
        assert d["queue_blocked_by_code"]["unmapped"] == 1
        conn.close()

    def test_zero_made_with_target_is_abnormal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★세션 #45: 생성 목표(target>0)인데 made=0 — 큐 비고 보류 없어도 abnormal(경보).

        옛 식은 '문제보류·큐 막힘'만 봐서 refill 고갈·전건 failed(상품 0)의 '조용한 0편'을
        놓쳤다(pend=0·held=0이면 무경보). 발행할 것도 없으면(approved_n=0) 그날 발행 0 확정."""
        conn = self._conn(tmp_path, monkeypatch)
        d = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"approved": [], "held": []}, approved_n=0, target=1
        )
        assert d["abnormal"] is True
        assert d["target"] == 1
        conn.close()

    def test_zero_made_but_pending_publish_not_abnormal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 생성 0이어도 발행대기(approved_n>0)가 있으면 그날 발행은 됨 — 오경보 방지
        conn = self._conn(tmp_path, monkeypatch)
        d = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"approved": [], "held": []}, approved_n=2, target=1
        )
        assert d["abnormal"] is False
        conn.close()

    def test_target_zero_keeps_legacy_behavior(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # target 미지정(0·기존 호출) — made=0만으로는 abnormal 아님(하위호환·의도적 일시정지 무경보)
        conn = self._conn(tmp_path, monkeypatch)
        d = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"approved": [], "held": []}, approved_n=0
        )
        assert d["abnormal"] is False
        conn.close()
