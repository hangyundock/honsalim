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
