"""deployer.scheduler — Windows 작업 스케줄러(schtasks) 연동: 예약 발행 (세션 #25).

운영 대시보드가 '예약 발행'을 켜고/끄고/시간변경할 때 사용한다. schtasks 호출은 대시보드(주인
프로세스) 권한으로 실행되므로 Claude Code 안전가드와 무관(주인이 직접 통제 — #24 수동전환 취지와 정합:
기본 OFF, 주인이 명시적으로 켤 때만 등록). query는 읽기 전용.

작업은 매일 schedule_time에 scripts/run_publish_queue.ps1 실행 → 승인된 큐 N편 발행.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

TASK_NAME = "Honsalim_PublishQueue"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WRAPPER = PROJECT_ROOT / "scripts" / "run_publish_queue.ps1"

_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_START_RE = re.compile(r"<StartBoundary>\d{4}-\d{2}-\d{2}T(\d{2}):(\d{2}):")


def _run(argv: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    """schtasks 호출 (인자 list — shell 미사용, 주입 위험 없음)."""
    return subprocess.run(  # noqa: S603
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def query_scheduled_time() -> tuple[int, int] | None:
    """등록된 발행 작업의 시작 시각 (HH, MM). 미등록·오류 시 None."""
    try:
        r = _run(["schtasks", "/query", "/tn", TASK_NAME, "/xml"])
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = _START_RE.search(r.stdout or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def is_registered() -> bool:
    """발행 작업이 등록되어 있는가."""
    return query_scheduled_time() is not None


def create_or_update(time_hhmm: str) -> tuple[bool, str]:
    """매일 time_hhmm(HH:MM)에 발행 작업 등록(있으면 교체). 반환: (성공, 메시지).

    schtasks /create /f 로 멱등 등록. 작업은 run_publish_queue.ps1을 실행.
    """
    if not _TIME_RE.match(time_hhmm):
        return False, f"시각 형식 오류: {time_hhmm!r} (HH:MM, 00:00~23:59)"
    tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{WRAPPER}"'
    try:
        r = _run(
            [
                "schtasks",
                "/create",
                "/tn",
                TASK_NAME,
                "/tr",
                tr,
                "/sc",
                "daily",
                "/st",
                time_hhmm,
                "/f",
            ]
        )
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"schtasks 실행 실패: {e}"
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "schtasks 등록 실패").strip()
    return True, f"예약 발행 등록 — 매일 {time_hhmm}"


def delete_task() -> tuple[bool, str]:
    """발행 작업 해제. 반환: (성공, 메시지). 미등록도 성공으로 간주."""
    try:
        r = _run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"])
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"schtasks 실행 실패: {e}"
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip()
        if "ERROR: The system cannot find" in msg or "specified task name" in msg.lower():
            return True, "예약 발행 이미 해제됨"
        return False, msg or "삭제 실패"
    return True, "예약 발행 해제"
