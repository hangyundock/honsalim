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


class TestAutoCycleNotifyPublishedUrls:
    """세션 #42 — 무인 사이클 텔레그램에 발행 글 제목+URL 포함(주인 지시). send_telegram만 몽키패치."""

    def _capture(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        import cli

        sent: list[str] = []
        monkeypatch.setattr(cli.settings, "get", lambda k, d=None: d)  # 기본값 사용
        monkeypatch.setattr(cli.settings, "get_int", lambda k: 2)
        from common import config as _cfg
        from common import notify as _nt

        monkeypatch.setattr(_cfg, "load_secrets", lambda: None)
        monkeypatch.setattr(_nt, "telegram_ready", lambda: True)

        def _fake_send(t: str) -> bool:
            sent.append(t)
            return True

        monkeypatch.setattr(_nt, "send_telegram", _fake_send)
        return sent

    def test_published_urls_in_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import cli

        sent = self._capture(monkeypatch)
        digest = {"queue_coupang_pending": 3, "queue_pending": 3, "made": 1, "approved_this_run": 1}
        published = [
            {"title": "허리편한의자 추천", "url": "https://honsallim.com/articles/kw-abc/"}
        ]
        cli._auto_cycle_notify(digest, 0, published)
        assert len(sent) == 1
        assert "허리편한의자 추천" in sent[0]
        assert "https://honsallim.com/articles/kw-abc/" in sent[0]
        assert "발행 완료" in sent[0]

    def test_publish_notifies_even_if_daily_report_off(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import cli

        sent = self._capture(monkeypatch)
        # telegram_daily_report=False여도 발행이 있으면 발송(주인이 원한 발행 결과 알림)
        monkeypatch.setattr(
            cli.settings, "get", lambda k, d=None: False if k == "telegram_daily_report" else d
        )
        digest = {"queue_coupang_pending": 3, "queue_pending": 3}
        published = [{"title": "글", "url": "https://honsallim.com/articles/kw-x/"}]
        cli._auto_cycle_notify(digest, 0, published)
        assert len(sent) == 1 and "kw-x" in sent[0]

    def test_no_publish_no_alert_report_off_is_silent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import cli

        sent = self._capture(monkeypatch)
        monkeypatch.setattr(
            cli.settings, "get", lambda k, d=None: False if k == "telegram_daily_report" else d
        )
        digest = {"queue_coupang_pending": 3, "queue_pending": 3}
        cli._auto_cycle_notify(digest, None, None)
        assert sent == []  # 발행·경보·리포트 모두 없음 = 무발송


class TestNotifyAlertCommand:
    """세션 #44 — 무인 래퍼 안전 정지 통지(cli notify-alert). fail-loud지만 래퍼는 절대 안 막음."""

    def _patch(self, monkeypatch: pytest.MonkeyPatch, ready: bool = True) -> list[str]:
        from common import config as _cfg
        from common import notify as _nt

        sent: list[str] = []
        monkeypatch.setattr(_cfg, "load_secrets", lambda: None)
        monkeypatch.setattr(_nt, "telegram_ready", lambda: ready)

        def _fake_send(t: str) -> bool:
            sent.append(t)
            return True

        monkeypatch.setattr(_nt, "send_telegram", _fake_send)
        return sent

    def _run(self, msg: str) -> int:
        import argparse

        import cli

        return cli.cmd_notify_alert(argparse.Namespace(message=msg))

    def test_sends_message_and_exit_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._patch(monkeypatch, ready=True)
        rc = self._run("브랜치 X — 안전 정지")
        assert rc == 0
        assert len(sent) == 1
        assert "브랜치 X — 안전 정지" in sent[0]

    def test_empty_message_no_send_exit_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._patch(monkeypatch, ready=True)
        assert self._run("   ") == 0
        assert sent == []

    def test_not_ready_no_send_exit_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._patch(monkeypatch, ready=False)
        assert self._run("정지 사유") == 0
        assert sent == []

    def test_send_failure_still_exit_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """발송 실패(False)여도 래퍼를 막지 않도록 반드시 exit 0."""
        import argparse

        import cli
        from common import config as _cfg
        from common import notify as _nt

        monkeypatch.setattr(_cfg, "load_secrets", lambda: None)
        monkeypatch.setattr(_nt, "telegram_ready", lambda: True)
        monkeypatch.setattr(_nt, "send_telegram", lambda t: False)
        assert cli.cmd_notify_alert(argparse.Namespace(message="x")) == 0

    def test_secrets_load_error_swallowed_exit_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """secrets 로드 예외도 삼키고 exit 0 (§0 — 래퍼 보호)."""
        import argparse

        import cli
        from common import config as _cfg

        def _boom() -> None:
            raise RuntimeError("secrets down")

        monkeypatch.setattr(_cfg, "load_secrets", _boom)
        assert cli.cmd_notify_alert(argparse.Namespace(message="x")) == 0
