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

    def _run_cycle_with_gen_rc(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, gen_rc: int
    ) -> dict[str, Any]:
        """대기 키워드 1개짜리 사이클을 gen_rc로 돌리고 digest(auto_cycle_last.json)를 돌려준다."""
        import json

        from common import db
        from writer import keyword_queue as kq

        p = tmp_path / "t.db"
        db.migrate(db_path=p)
        db.seed(db_path=p)
        conn = db.connect(p)
        kq.get_or_create(conn, "컴퓨터의자", channel="ali")
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
        monkeypatch.setattr(cli, "cmd_keyword_generate", lambda ns: gen_rc)
        monkeypatch.setattr(cli, "cmd_publish_queue", lambda ns: 0)

        assert cli.cmd_auto_cycle(argparse.Namespace(count=1, dry_run=False, no_deploy=True)) == 0
        digest: dict[str, Any] = json.loads((p.parent / "auto_cycle_last.json").read_text("utf-8"))
        return digest

    def test_gate_reject_is_not_counted_as_made(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★세션 #47 재발 방지 — 게이트 반려를 '생성 성공'으로 세면 fail-loud가 뚫린다.

        라이브 적발: 07-21~23 '스텐도마'가 3일 연속 반려됐는데 cmd_keyword_generate가 0을
        돌려줘 made=1로 집계 → #45 가드 `target>0 and made==0`이 False → abnormal=False →
        발행 0편인 이틀(07-21·22)이 텔레그램 무경보로 조용히 지나갔다. 반려는 산출 0이다.
        """
        digest = self._run_cycle_with_gen_rc(tmp_path, monkeypatch, gen_rc=cli.RC_GATE_REJECTED)
        assert digest["made"] == 0  # 반려는 세지 않는다
        assert digest["target"] == 1
        assert digest["abnormal"] is True  # 발행 0편 위험이 경보로 노출된다(fail-loud)

    def test_successful_generate_is_counted_as_made(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """대조군 — 통과(rc=0)는 그대로 made로 집계된다(#47 수정이 성공 경로를 깨지 않음)."""
        digest = self._run_cycle_with_gen_rc(tmp_path, monkeypatch, gen_rc=0)
        assert digest["made"] == 1


class TestUnpublishOnlyDeploy:
    """★세션 #47 근본수정 — 비공개-only 날도 라이브에 반영돼야 한다(가드레일 무력화 방지).

    옛 코드는 발행 0 + 자동비공개만 있는 날 cmd_build + cmd_deploy(git_push stub·commit 없음)를
    타서 재빌드가 커밋되지 않아 CI가 안 돌고, 가드레일이 '미달'로 내린 글이 다음 발행일까지
    라이브에 계속 노출됐다(#30과 동일 결함의 잔존 분기). 발행 경로(#32)와 동일하게
    refresh_cycle(build + commit + push)을 거쳐야 한다.
    """

    def _run_unpublish_only_cycle(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        built: bool = True,
        deployed: bool = True,
        changed: bool = True,
    ) -> tuple[int, dict[str, Any], list[Any]]:
        """발행 0·자동비공개 1편인 라이브 사이클 실행 → (rc, refresh_cycle kwargs, notify 호출)."""
        from types import SimpleNamespace

        from common import db
        from writer import keyword_recommender as kr_mod

        p = tmp_path / "t.db"
        db.migrate(db_path=p)
        db.seed(db_path=p)  # 대기 키워드·approved draft 없음

        monkeypatch.setattr(cli.db, "DB_PATH", p)
        monkeypatch.setattr(
            cli.settings,
            "get",
            lambda k, d=None, **kw: (
                True if k == "auto_mode" else (1 if k == "publish_per_day" else d)
            ),
        )
        # 생성 없음(추천 고갈) — 이 테스트의 관심은 비공개-only 배포 분기뿐.
        monkeypatch.setattr(kr_mod, "auto_pick_keyword", lambda conn, **kw: None)
        # 사후 모니터가 1편 자동 비공개했다고 보고.
        monkeypatch.setattr(
            "writer.article_guardrail.monitor",
            lambda conn, auto_unpublish=False: {
                "checked": 1,
                "failed": [{"slug": "bad", "reasons": ["미달"], "flagged": []}],
                "unpublished": ["bad"],
            },
        )
        calls: dict[str, Any] = {}

        def fake_refresh(conn: Any, **kw: Any) -> Any:
            calls["kw"] = kw
            return SimpleNamespace(
                built=built, deployed=deployed, changed=changed, go_count=0, notes=[]
            )

        monkeypatch.setattr("deployer.refresh_cycle.run_refresh_cycle", fake_refresh)
        notify_calls: list[Any] = []
        monkeypatch.setattr(
            cli, "_auto_cycle_notify", lambda digest, rc, published=None: notify_calls.append(rc)
        )

        rc = cli.cmd_auto_cycle(argparse.Namespace(count=1, dry_run=False, no_deploy=False))
        return rc, calls.get("kw") or {}, notify_calls

    def test_unpublish_only_goes_through_refresh_cycle_commit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 죽은 경로(cmd_build/cmd_deploy)를 타면 즉시 실패하도록 지뢰 설치 — 재발 방지의 핵심.
        def boom(*a: Any, **k: Any) -> int:
            raise AssertionError("비공개-only 배포가 옛 stub 경로(cmd_build/cmd_deploy)를 탔음")

        monkeypatch.setattr(cli, "cmd_build", boom)
        monkeypatch.setattr(cli, "cmd_deploy", boom)

        rc, kw, notify_calls = self._run_unpublish_only_cycle(tmp_path, monkeypatch)
        assert rc == 0
        assert kw["do_build"] is True
        assert kw["do_deploy"] is True
        assert kw["refresh"] is False  # 수집 없음 — 비공개 반영 재빌드뿐
        assert kw["dry_run"] is False
        assert notify_calls == [None]  # 성공은 '발행 없음' 그대로(오경보 없음)

    def test_unpublish_only_deploy_failure_alerts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """배포 실패 rc가 notify로 전달돼 경보가 나간다(옛 코드는 None으로 삼켰다 — fail-loud)."""
        rc, _kw, notify_calls = self._run_unpublish_only_cycle(
            tmp_path, monkeypatch, built=True, deployed=False, changed=True
        )
        assert rc == 2
        assert notify_calls == [2]  # 실패 rc 전달 → '발행 단계 실패' 경보

    def test_unpublish_only_no_change_is_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """산출물 변경 없음(이미 반영됨)은 정상 종료 — 오경보를 만들지 않는다."""
        rc, _kw, notify_calls = self._run_unpublish_only_cycle(
            tmp_path, monkeypatch, built=True, deployed=False, changed=False
        )
        assert rc == 0
        assert notify_calls == [None]


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
