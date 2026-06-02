"""배포 워크플로(build.yml) 가드 — 세션 #20 재발방지.

버그: wrangler `pages deploy`가 git 커밋 메시지를 Cloudflare 배포 메타데이터로 전송하는데,
  본 프로젝트 커밋 규칙(`[YYYY-MM-DD #N] …` 한국어+특수문자 ★ → 등)을 CF API가 거부함
  (code 8000111 "Invalid commit message, it must be a valid UTF-8 string") → 배포 실패.
대책: wrangler 명령에 안전한 ASCII `--commit-message`를 명시해 git 메시지 스크래핑을 우회.
무인 배포가 커밋 메시지 때문에 깨지지 않도록 워크플로를 구조로 고정한다.
"""

from __future__ import annotations

from pathlib import Path

_BUILD_YML = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "build.yml"


class TestDeployWorkflow:
    def _wrangler_command(self) -> str:
        text = _BUILD_YML.read_text(encoding="utf-8")
        # 'command: pages deploy ...' 한 줄 추출
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("command:") and "pages deploy" in s:
                return s
        raise AssertionError("build.yml에 wrangler 'command: pages deploy ...' 라인이 없음")

    def test_commit_message_is_overridden_ascii(self) -> None:
        cmd = self._wrangler_command()
        assert "--commit-message=" in cmd, (
            "wrangler 명령에 --commit-message 오버라이드 누락 — git 커밋 메시지(한국어·특수문자)가 "
            "CF에 전송되어 배포 실패(code 8000111) 재발"
        )
        # 오버라이드 값은 ASCII여야 안전 (CF가 비ASCII/특수문자 거부)
        idx = cmd.index("--commit-message=") + len("--commit-message=")
        value = cmd[idx:].split()[0]
        assert value.isascii() and value, f"--commit-message 값이 ASCII 아님/빈값: {value!r}"

    def test_production_branch_and_project(self) -> None:
        cmd = self._wrangler_command()
        assert "--project-name=honsalim" in cmd
        assert "--branch=main" in cmd  # 프로덕션 배포
