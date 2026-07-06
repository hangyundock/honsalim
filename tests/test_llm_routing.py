"""LLM 백엔드 라우팅(세션 #19) — claude→Anthropic SDK, deepseek→OpenRouter(requests).

라이브 호출 없이 requests.post를 mock해 OpenRouter 경로의 응답 변환·재시도·키 누락·
system 블록 평탄화를 검증한다. 본문 생성 모델을 DeepSeek로 전환한 뒤의 무인 안전 가드.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import requests

from enricher import claude_client as cc
from enricher.claude_client import (
    ClaudeClient,
    _AnthropicBackend,
    _OpenRouterBackend,
    build_llm_client,
    is_anthropic_model,
)


class _FakeResp:
    """requests.Response 호환 — status_code·json()·text."""

    def __init__(self, status_code: int = 200, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> Any:
        return self._payload


def _ok_payload(content: str = "안녕", finish: str = "stop", pin: int = 11, pout: int = 22) -> dict:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": pin, "completion_tokens": pout},
    }


_MSG = [{"role": "user", "content": "hi"}]


class TestRouting:
    def test_is_anthropic_model(self) -> None:
        assert is_anthropic_model("claude-sonnet-4-6") is True
        assert is_anthropic_model("deepseek/deepseek-v4-pro") is False

    def test_default_model_is_deepseek(self) -> None:
        assert cc.DEFAULT_MODEL == "deepseek/deepseek-v4-pro"
        assert is_anthropic_model(cc.DEFAULT_MODEL) is False

    def test_build_llm_client_routes_by_model(self) -> None:
        claude = build_llm_client("claude-sonnet-4-6", "k")
        deepseek = build_llm_client("deepseek/deepseek-v4-pro")
        assert isinstance(claude.messages._backend, _AnthropicBackend)
        assert isinstance(deepseek.messages._backend, _OpenRouterBackend)


class TestOpenRouterBackend:
    def test_missing_key_raises_without_network(self, monkeypatch) -> None:
        def boom(*a: Any, **k: Any) -> None:
            raise AssertionError("키 없으면 네트워크 호출하면 안 됨")

        monkeypatch.setattr(requests, "post", boom)
        be = _OpenRouterBackend(key_loader=lambda: "")
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            be.create(
                model="deepseek/deepseek-v4-pro",
                max_tokens=10,
                temperature=0.4,
                system=None,
                messages=_MSG,
            )

    def test_maps_response_to_anthropic_shape(self, monkeypatch) -> None:
        monkeypatch.setattr(
            requests, "post", lambda *a, **k: _FakeResp(200, _ok_payload("본문", "stop", 5, 7))
        )
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        resp = be.create(
            model="deepseek/deepseek-v4-pro",
            max_tokens=10,
            temperature=0.4,
            system="sys",
            messages=_MSG,
        )
        assert resp.content[0].text == "본문"
        assert resp.usage.input_tokens == 5 and resp.usage.output_tokens == 7
        assert resp.stop_reason == "end_turn"

    def test_finish_length_maps_to_max_tokens(self, monkeypatch) -> None:
        monkeypatch.setattr(
            requests, "post", lambda *a, **k: _FakeResp(200, _ok_payload("잘림", "length"))
        )
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        resp = be.create(
            model="deepseek/deepseek-v4-pro",
            max_tokens=1,
            temperature=None,
            system=None,
            messages=_MSG,
        )
        assert resp.stop_reason == "max_tokens"  # is_truncated 호환 — 잘림 무인 진단 유지

    def test_system_blocks_flattened_to_system_message(self, monkeypatch) -> None:
        captured: dict[str, Any] = {}

        def fake_post(
            url: str, headers: Any = None, data: Any = None, timeout: Any = None
        ) -> _FakeResp:
            captured["payload"] = json.loads(data)
            return _FakeResp(200, _ok_payload())

        monkeypatch.setattr(requests, "post", fake_post)
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        blocks = [{"type": "text", "text": "규칙A"}, {"type": "text", "text": "규칙B"}]
        be.create(
            model="deepseek/deepseek-v4-pro",
            max_tokens=10,
            temperature=0.4,
            system=blocks,
            messages=[{"role": "user", "content": "질문"}],
        )
        msgs = captured["payload"]["messages"]
        assert msgs[0] == {"role": "system", "content": "규칙A\n규칙B"}
        assert msgs[1] == {"role": "user", "content": "질문"}

    def test_retries_on_429_then_succeeds(self, monkeypatch) -> None:
        seq = [_FakeResp(429, text="rate"), _FakeResp(200, _ok_payload("재시도성공"))]
        calls = {"n": 0}

        def fake_post(*a: Any, **k: Any) -> _FakeResp:
            r = seq[calls["n"]]
            calls["n"] += 1
            return r

        monkeypatch.setattr(requests, "post", fake_post)
        monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        resp = be.create(
            model="deepseek/deepseek-v4-pro",
            max_tokens=10,
            temperature=0.4,
            system=None,
            messages=_MSG,
        )
        assert resp.content[0].text == "재시도성공"
        assert calls["n"] == 2

    def test_retries_on_provider_403_then_succeeds(self, monkeypatch) -> None:
        """세션 #42: OpenRouter 제공자 풀 403('Provider returned error')은 일시 오류 — 재시도.

        라이브 적발: DigitalOcean 제공자 403으로 무인 사이클 0편·쿠팡 키워드 격리.
        재시도하면 다른 제공자로 라우팅돼 성공하는 게 보통이라 429와 동일 취급."""
        seq = [
            _FakeResp(
                403,
                text='{"error":{"message":"Provider returned error","code":403,'
                '"metadata":{"provider_name":"DigitalOcean"}}}',
            ),
            _FakeResp(200, _ok_payload("제공자재시도성공")),
        ]
        calls = {"n": 0}

        def fake_post(*a: Any, **k: Any) -> _FakeResp:
            r = seq[calls["n"]]
            calls["n"] += 1
            return r

        monkeypatch.setattr(requests, "post", fake_post)
        monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        resp = be.create(
            model="deepseek/deepseek-v4-pro",
            max_tokens=10,
            temperature=0.4,
            system=None,
            messages=_MSG,
        )
        assert resp.content[0].text == "제공자재시도성공"
        assert calls["n"] == 2

    def test_plain_403_auth_fails_fast(self, monkeypatch) -> None:
        """진짜 인증 403(키 폐기 등)은 재시도 없이 즉시 실패 — 비용·무한루프 안전 유지."""
        calls = {"n": 0}

        def fake_post(*a: Any, **k: Any) -> _FakeResp:
            calls["n"] += 1
            return _FakeResp(403, text='{"error":{"message":"Invalid API key"}}')

        monkeypatch.setattr(requests, "post", fake_post)
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        with pytest.raises(RuntimeError, match="OpenRouter 403"):
            be.create(
                model="deepseek/deepseek-v4-pro",
                max_tokens=10,
                temperature=0.4,
                system=None,
                messages=_MSG,
            )
        assert calls["n"] == 1  # 재시도 없음

    def test_http_4xx_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(
            requests,
            "post",
            lambda *a, **k: _FakeResp(400, {"error": "bad"}, text='{"error":"bad"}'),
        )
        be = _OpenRouterBackend(key_loader=lambda: "KEY")
        with pytest.raises(RuntimeError, match="OpenRouter 400"):
            be.create(
                model="deepseek/deepseek-v4-pro",
                max_tokens=10,
                temperature=0.4,
                system=None,
                messages=_MSG,
            )


class TestClaudeClientDeepSeekPath:
    def test_generate_raw_end_to_end_mocked(self, monkeypatch) -> None:
        monkeypatch.setattr(cc, "load_openrouter_key", lambda: "KEY")
        monkeypatch.setattr(
            requests, "post", lambda *a, **k: _FakeResp(200, _ok_payload("생성됨", "stop", 3, 9))
        )
        client = ClaudeClient(api_key=None)  # 기본 모델 = deepseek → OpenRouter 경로
        result = client.generate_raw("시스템", "유저", dry_run=False)
        assert result.dry_run is False
        assert result.response_text == "생성됨"
        assert result.usage == {"input_tokens": 3, "output_tokens": 9}
        assert result.stop_reason == "end_turn"
