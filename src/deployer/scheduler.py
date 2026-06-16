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
WRAPPER_PUBLISH = PROJECT_ROOT / "scripts" / "run_publish_queue.ps1"  # 반자동: 승인 글만 발행
WRAPPER_AUTOCYCLE = PROJECT_ROOT / "scripts" / "run_auto_cycle.ps1"  # ★완전 무인: 생성+승인+발행
WRAPPER = WRAPPER_PUBLISH  # 하위호환(옛 참조 — 기본 발행 래퍼)

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


def create_or_update(time_hhmm: str, *, full_auto: bool = False) -> tuple[bool, str]:
    """매일 time_hhmm(HH:MM)에 예약 작업 등록(있으면 교체). 반환: (성공, 메시지).

    full_auto=True면 run_auto_cycle.ps1(★완전 무인: 생성→자동승인→발행)을, False면
    run_publish_queue.ps1(반자동: 사람이 승인한 글만 발행)을 등록한다. 단일 작업名(TASK_NAME)이라
    둘이 동시 등록돼 이중 발행되는 일은 없다(auto-cycle도 발행 포함). schtasks /create /f 로 멱등 등록.
    """
    if not _TIME_RE.match(time_hhmm):
        return False, f"시각 형식 오류: {time_hhmm!r} (HH:MM, 00:00~23:59)"
    wrapper = WRAPPER_AUTOCYCLE if full_auto else WRAPPER_PUBLISH
    tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{wrapper}"'
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
    kind = "완전 무인(생성·승인·발행)" if full_auto else "발행(승인 글만)"
    return True, f"예약 {kind} 등록 — 매일 {time_hhmm}"


def reconcile(full_auto: bool, time_hhmm: str | None = None) -> tuple[bool, str] | None:
    """등록된 예약이 있으면 config 상태(시각·wrapper)에 맞게 재등록. 미등록이면 None(무동작).

    두 footgun을 함께 막는다(§0 무인 안전 — 설정 저장 후 호출):
      ① auto_mode를 바꿔도 예약이 옛 wrapper(예: 발행만)로 굳어 무인 생성이 안 도는 문제.
      ② 설정창에서 '예약 시각'만 바꾸면 config만 갱신되고 실제 예약 작업은 옛 시각에 그대로 도는
         문제 — time_hhmm을 주면 그 시각으로 옮긴다(세션 #35 주인 테스트). 형식 오류·미지정이면
         기존 등록 시각을 유지(안전 폴백).
    베스트에포트: 실패해도 호출측 설정 저장은 유지.
    """
    t = query_scheduled_time()
    if t is None:
        return None
    when = time_hhmm if (time_hhmm and _TIME_RE.match(time_hhmm)) else f"{t[0]:02d}:{t[1]:02d}"
    return create_or_update(when, full_auto=full_auto)


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
