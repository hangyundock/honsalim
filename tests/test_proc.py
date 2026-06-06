"""common.proc 회귀 — resolve_argv(세션 #21) + run_text UTF-8 강제(세션 #24)."""

from __future__ import annotations

import shutil
import sys

from common.proc import resolve_argv, run_text


def test_resolves_when_found(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # PATH에서 찾으면 cmd[0]만 절대경로로 치환, 나머지 인자는 그대로
    monkeypatch.setattr(shutil, "which", lambda c: f"/usr/local/bin/{c}.cmd")
    assert resolve_argv(["wrangler", "d1", "execute"]) == [
        "/usr/local/bin/wrangler.cmd",
        "d1",
        "execute",
    ]


def test_keeps_original_when_not_found(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # 못 찾으면 원본 그대로(호출 측이 FileNotFoundError로 가시화)
    monkeypatch.setattr(shutil, "which", lambda c: None)
    assert resolve_argv(["wrangler", "deploy"]) == ["wrangler", "deploy"]


def test_empty_cmd() -> None:
    assert resolve_argv([]) == []


def test_run_text_defaults_to_utf8(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # 인코딩 미지정 시 utf-8/replace 강제 — 한글 Windows cp949 크래시 근본 차단
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return "sentinel"

    monkeypatch.setattr("common.proc.subprocess.run", fake_run)
    run_text(["echo", "hi"], capture_output=True, text=True)
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_run_text_respects_explicit_encoding(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # 호출자가 명시하면 존중(setdefault) — 기본값이 덮어쓰지 않음
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return "sentinel"

    monkeypatch.setattr("common.proc.subprocess.run", fake_run)
    run_text(["x"], encoding="latin-1", errors="strict")
    assert captured["encoding"] == "latin-1"
    assert captured["errors"] == "strict"


def test_run_text_reads_utf8_korean_without_crash() -> None:
    # 실제 UTF-8 한글 바이트를 내보내는 서브프로세스 캡처 — cp949 환경에서도 안 깨짐(리더 스레드)
    code = "import sys; sys.stdout.buffer.write('새로고침 완료'.encode('utf-8'))"
    proc = run_text(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0
    assert "새로고침" in proc.stdout
