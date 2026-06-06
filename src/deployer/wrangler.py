"""deployer.wrangler — Cloudflare wrangler CLI wrapper.

출처: BACKEND §4-1·§4-2 + ARCH §8 [확정].

기본 명령: `wrangler pages deploy build/`
dry_run=True 기본 — 실제 배포는 사용자 명시 승인 후만.
"""

# 사유: subprocess wrangler 호출 — 인자 list로만 사용.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.proc import resolve_argv, run_text


@dataclass
class WranglerResult:
    """wrangler 명령 결과."""

    dry_run: bool
    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    cwd: str


def wrangler_deploy(
    *,
    build_dir: str | Path = "build",
    project_name: str = "honsalim",
    cwd: str | Path = ".",
    dry_run: bool = True,
    timeout: int = 120,
) -> WranglerResult:
    """wrangler pages deploy 실행.

    Phase 2: dry_run=True 기본. 실제 배포는 사용자 명시 승인 후만.

    인자:
        build_dir: 배포할 정적 사이트 디렉토리
        project_name: Cloudflare Pages 프로젝트 이름
        cwd: 작업 디렉토리 (wrangler.toml 위치)
        dry_run: True면 명령 빌드만, False면 실행
        timeout: subprocess 타임아웃 (초)

    반환: WranglerResult.

    Raises:
        ValueError: build_dir 또는 project_name 빈 값
    """
    if not build_dir or not project_name:
        raise ValueError("build_dir 또는 project_name 빈 값")

    cmd = [
        "wrangler",
        "pages",
        "deploy",
        str(build_dir),
        "--project-name",
        project_name,
    ]
    cwd_str = str(Path(cwd).resolve())

    if dry_run:
        return WranglerResult(
            dry_run=True,
            returncode=0,
            stdout=f"[DRY] would run: {' '.join(cmd)} (cwd={cwd_str})",
            stderr="",
            command=cmd,
            cwd=cwd_str,
        )

    proc = run_text(
        resolve_argv(cmd),
        cwd=cwd_str,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return WranglerResult(
        dry_run=False,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=cmd,
        cwd=cwd_str,
    )
