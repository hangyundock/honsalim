"""common.proc — subprocess 실행 보조 (세션 #21).

Windows는 subprocess.run(list)이 PATHEXT(.cmd/.exe/.bat)를 해석하지 못해 npm 래퍼인
wrangler.cmd를 'wrangler'로 찾지 못하고 FileNotFoundError를 낸다(무인 운영=Windows 스케줄러
에서 sync-slugmap·deploy가 깨지던 근본 원인). shutil.which로 실행 직전 cmd[0]만 절대경로로
해석한다. dry_run 명령 plan·결과의 command 필드는 원본('wrangler')을 유지 — 실행만 보정.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any


def run_text(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """subprocess.run 래퍼 — 출력 텍스트를 항상 UTF-8로 디코딩(errors='replace').

    한글 Windows의 기본 인코딩(cp949)이 git·wrangler의 UTF-8 출력을 디코딩하다
    UnicodeDecodeError(리더 스레드 크래시)를 내던 근본 원인(세션 #24)을 제거한다.
    출력을 텍스트로 캡처하는 서브프로세스 호출은 모두 이 함수를 거친다 — 호출자가
    encoding/errors를 명시하지 않는 한 utf-8/replace를 강제(재발 방지 가드).
    """
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    return subprocess.run(cmd, **kwargs)  # noqa: S603  # 인자 list — shell injection 없음


def resolve_argv(cmd: list[str]) -> list[str]:
    """cmd[0](실행 파일)을 PATH에서 절대경로로 해석해 반환.

    찾으면 [절대경로, *나머지], 못 찾으면 원본 그대로(호출 측이 FileNotFoundError를 잡아
    가시화 — 무인 진단). Linux/CI에서 'wrangler'가 PATH에 있으면 동일 경로로 해석된다.
    """
    if not cmd:
        return cmd
    exe = shutil.which(cmd[0])
    return [exe, *cmd[1:]] if exe else cmd
