"""deployer.git_push — git push wrapper (subprocess).

출처: BACKEND §2-7 + DECISIONS H4·H5 [확정].

dry_run=True 기본 — 실제 push는 사용자 명시 승인 후만.
commit 메시지 패턴 H5: `[YYYY-MM-DD #N] <한 줄>`
"""

# ruff: noqa: S603, S607
# 사유: subprocess git 호출 — 인자 list로만 사용, shell injection 위험 없음.

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PushResult:
    """git push 결과."""

    dry_run: bool
    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    cwd: str


def git_push(
    commit_message: str | None = None,
    *,
    cwd: str | Path = ".",
    remote: str = "origin",
    branch: str = "main",
    dry_run: bool = True,
    timeout: int = 30,
) -> PushResult:
    """git push 실행.

    Phase 2: dry_run=True 기본. 실제 push는 사용자 명시 승인 후 호출자가
    dry_run=False 명시 (DECISIONS H4 [확정]).

    인자:
        commit_message: 사전 commit 시 사용 (현재 stub은 commit 안 함, push만)
        cwd: git 저장소 경로
        remote: push 대상 remote (기본 'origin')
        branch: push 대상 branch (기본 'main')
        dry_run: True면 명령 빌드만, False면 실행
        timeout: subprocess 타임아웃 (초)

    반환: PushResult.

    Raises:
        ValueError: branch 또는 remote 빈 값
        subprocess.TimeoutExpired: dry_run=False + 타임아웃
    """
    if not remote or not branch:
        raise ValueError("remote 또는 branch 빈 값")

    cmd = ["git", "push", remote, branch]
    cwd_str = str(Path(cwd).resolve())

    if dry_run:
        return PushResult(
            dry_run=True,
            returncode=0,
            stdout=f"[DRY] would run: {' '.join(cmd)} (cwd={cwd_str})",
            stderr="",
            command=cmd,
            cwd=cwd_str,
        )

    proc = subprocess.run(
        cmd,
        cwd=cwd_str,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return PushResult(
        dry_run=False,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=cmd,
        cwd=cwd_str,
    )
