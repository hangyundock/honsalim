"""deployer.scheduler 회귀 테스트 (세션 #25) — schtasks 호출은 모킹(실제 작업 미등록)."""

from __future__ import annotations

import subprocess

import pytest

from deployer import scheduler

_XML = (
    "<Task><Triggers><CalendarTrigger>"
    "<StartBoundary>2026-06-14T11:30:00</StartBoundary>"
    "</CalendarTrigger></Triggers></Task>"
)


def _cp(
    returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["schtasks"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class TestQuery:
    def test_parses_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler, "_run", lambda argv, timeout=30.0: _cp(0, _XML))
        assert scheduler.query_scheduled_time() == (11, 30)

    def test_not_registered_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            scheduler, "_run", lambda argv, timeout=30.0: _cp(1, "", "ERROR: cannot find")
        )
        assert scheduler.query_scheduled_time() is None

    def test_is_registered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler, "_run", lambda argv, timeout=30.0: _cp(0, _XML))
        assert scheduler.is_registered() is True


class TestCreate:
    def test_bad_time_rejected(self) -> None:
        ok, msg = scheduler.create_or_update("25:99")
        assert ok is False
        assert "형식" in msg

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler, "_run", lambda argv, timeout=30.0: _cp(0, "SUCCESS"))
        ok, msg = scheduler.create_or_update("11:00")
        assert ok is True
        assert "11:00" in msg

    def test_failure_surfaces_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            scheduler, "_run", lambda argv, timeout=30.0: _cp(1, "", "Access denied")
        )
        ok, msg = scheduler.create_or_update("11:00")
        assert ok is False
        assert "denied" in msg.lower()

    def test_full_auto_registers_autocycle_wrapper(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ★완전 무인(세션 #34): full_auto=True → auto-cycle 래퍼(생성+발행) 등록
        cap: dict[str, list[str]] = {}

        def fake_run(argv: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
            cap["argv"] = argv
            return _cp(0, "SUCCESS")

        monkeypatch.setattr(scheduler, "_run", fake_run)
        ok, msg = scheduler.create_or_update("11:00", full_auto=True)
        assert ok is True
        assert any("run_auto_cycle.ps1" in a for a in cap["argv"])
        assert "무인" in msg

    def test_default_registers_publish_wrapper(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 기본(full_auto=False) → 발행 전용 래퍼(승인 글만) — 하위호환
        cap: dict[str, list[str]] = {}

        def fake_run(argv: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
            cap["argv"] = argv
            return _cp(0, "SUCCESS")

        monkeypatch.setattr(scheduler, "_run", fake_run)
        ok, _ = scheduler.create_or_update("11:00")
        assert ok is True
        assert any("run_publish_queue.ps1" in a for a in cap["argv"])


class TestReconcile:
    def test_reregisters_with_full_auto_when_registered(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 등록돼 있으면 시각 유지하고 auto_mode에 맞는 wrapper로 재등록(footgun 방지)
        monkeypatch.setattr(scheduler, "query_scheduled_time", lambda: (11, 0))
        cap: dict[str, list[str]] = {}

        def fake_run(argv: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
            cap["argv"] = argv
            return _cp(0, "SUCCESS")

        monkeypatch.setattr(scheduler, "_run", fake_run)
        res = scheduler.reconcile(full_auto=True)
        assert res is not None and res[0] is True
        assert any("run_auto_cycle.ps1" in a for a in cap["argv"])

    def test_noop_when_unregistered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler, "query_scheduled_time", lambda: None)
        assert scheduler.reconcile(full_auto=True) is None


class TestDelete:
    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler, "_run", lambda argv, timeout=30.0: _cp(0, "SUCCESS"))
        ok, _ = scheduler.delete_task()
        assert ok is True

    def test_already_deleted_is_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            scheduler,
            "_run",
            lambda argv, timeout=30.0: _cp(
                1, "", "ERROR: The system cannot find the specified task name."
            ),
        )
        ok, _ = scheduler.delete_task()
        assert ok is True
