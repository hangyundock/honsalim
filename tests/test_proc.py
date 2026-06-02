"""common.proc.resolve_argv 회귀 — Windows wrangler.cmd 해석 (세션 #21)."""

from __future__ import annotations

import shutil

from common.proc import resolve_argv


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
