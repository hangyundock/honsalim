"""common.notify 회귀 테스트 (세션 #41) — 텔레그램 푸시 채널.

핵심(§0): 미설정=무동작, 어떤 실패도 예외를 전파하지 않음(무인 사이클 보호).
네트워크는 절대 호출하지 않음(urlopen 몽키패치).
"""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest

from common import notify


def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """가짜 토큰/챗ID 주입 — 실제 자격증명 아님(네트워크 미호출·urlopen 몽키패치)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "C")


class TestReady:
    def test_not_ready_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert notify.telegram_ready() is False

    def test_ready_with_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_env(monkeypatch)
        assert notify.telegram_ready() is True

    def test_not_ready_with_token_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert notify.telegram_ready() is False


class _FakeResp(io.BytesIO):
    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: Any) -> None:
        self.close()


class TestSend:
    def test_unconfigured_noop_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert notify.send_telegram("hi") is False

    def test_empty_text_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_env(monkeypatch)
        assert notify.send_telegram("  ") is False

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_env(monkeypatch)
        sent: dict[str, Any] = {}

        def fake_urlopen(req: Any, timeout: float = 0) -> _FakeResp:
            sent["url"] = req.full_url
            sent["payload"] = json.loads(req.data.decode("utf-8"))
            return _FakeResp(b'{"ok": true}')

        monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
        assert notify.send_telegram("혼살림 테스트") is True
        assert "botT/sendMessage" in sent["url"]
        assert sent["payload"]["chat_id"] == "C"
        assert sent["payload"]["text"] == "혼살림 테스트"

    def test_api_ok_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_env(monkeypatch)
        monkeypatch.setattr(
            notify.urllib.request,
            "urlopen",
            lambda *a, **k: _FakeResp(b'{"ok": false}'),
        )
        assert notify.send_telegram("x") is False

    def test_network_error_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """네트워크 오류가 예외로 전파되면 무인 사이클이 죽는다 — 반드시 False로 삼켜야(§0)."""
        _set_env(monkeypatch)

        def boom(*a: Any, **k: Any) -> None:
            raise urllib.error.URLError("down")

        monkeypatch.setattr(notify.urllib.request, "urlopen", boom)
        assert notify.send_telegram("x") is False  # 예외 없이 False

    def test_long_text_truncated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_env(monkeypatch)
        captured: dict[str, Any] = {}

        def fake_urlopen(req: Any, timeout: float = 0) -> _FakeResp:
            captured["text"] = json.loads(req.data.decode("utf-8"))["text"]
            return _FakeResp(b'{"ok": true}')

        monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
        assert notify.send_telegram("a" * 5000) is True
        assert len(captured["text"]) <= 4096  # 텔레그램 상한 이하
        assert captured["text"].endswith("…(잘림)")
