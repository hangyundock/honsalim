"""collector.vision_relevance 회귀 테스트 (세션 #35) — Haiku 비전 관련성 게이트.

실제 네트워크·Anthropic 호출 없이 _fetch_image·_call_vision을 monkeypatch. fail_closed/open
분기, JSON 파싱(코드펜스 포함), 페치/API 오류 처리, 배치 필터(cap·이미지없음·드롭사유)를 검증.
"""

from __future__ import annotations

import pytest

from collector import vision_relevance as vr


def _stub_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        vr, "_fetch_image", lambda url, timeout=15.0: (b"\xff\xd8\xff\x00", "image/jpeg")
    )


class TestCheckProductRelevance:
    def test_ok_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)
        monkeypatch.setattr(
            vr, "_call_vision", lambda *a, **k: '{"ok": true, "reason": "의자 맞음"}'
        )
        ok, reason = vr.check_product_relevance(
            "http://x/1.jpg", "의자", "메쉬 사무용 의자", api_key="k"
        )
        assert ok is True
        assert "의자" in reason

    def test_ok_false_drops(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)
        monkeypatch.setattr(
            vr, "_call_vision", lambda *a, **k: '{"ok": false, "reason": "폰케이스"}'
        )
        ok, reason = vr.check_product_relevance("http://x/1.jpg", "의자", api_key="k")
        assert ok is False
        assert "폰케이스" in reason

    def test_code_fence_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)
        monkeypatch.setattr(
            vr, "_call_vision", lambda *a, **k: '```json\n{"ok": true, "reason": "ok"}\n```'
        )
        ok, _ = vr.check_product_relevance("http://x/1.jpg", "책상", api_key="k")
        assert ok is True

    def test_no_key_fail_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vr, "_resolve_key", lambda k: None)
        ok, reason = vr.check_product_relevance("http://x/1.jpg", "의자", fail_closed=True)
        assert ok is False
        assert "ANTHROPIC" in reason

    def test_no_key_fail_open(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vr, "_resolve_key", lambda k: None)
        ok, _ = vr.check_product_relevance("http://x/1.jpg", "의자", fail_closed=False)
        assert ok is True

    def test_no_url_fail_closed(self) -> None:
        ok, reason = vr.check_product_relevance("", "의자", api_key="k", fail_closed=True)
        assert ok is False
        assert "URL" in reason

    def test_fetch_failure_fail_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(url: str, timeout: float = 15.0) -> tuple[bytes, str]:
            raise OSError("timeout")

        monkeypatch.setattr(vr, "_fetch_image", boom)
        ok, reason = vr.check_product_relevance(
            "http://x/1.jpg", "의자", api_key="k", fail_closed=True
        )
        assert ok is False
        assert "페치 실패" in reason

    def test_api_error_fail_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)

        def boom(*a: object, **k: object) -> str:
            raise RuntimeError("api down")

        monkeypatch.setattr(vr, "_call_vision", boom)
        ok, reason = vr.check_product_relevance(
            "http://x/1.jpg", "의자", api_key="k", fail_closed=True
        )
        assert ok is False
        assert "오류" in reason

    def test_api_error_fail_open_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)

        def boom(*a: object, **k: object) -> str:
            raise RuntimeError("x")

        monkeypatch.setattr(vr, "_call_vision", boom)
        ok, _ = vr.check_product_relevance("http://x/1.jpg", "의자", api_key="k", fail_closed=False)
        assert ok is True


class TestFilterRelevant:
    def test_separates_kept_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)

        def fake(api_key: str, model: str, media: str, data: str, prompt: str) -> str:
            # 프롬프트에 상품명이 들어간다. (템플릿에 '폰케이스'가 있어 '아이폰'으로 분기)
            return (
                '{"ok": false, "reason": "딴거"}'
                if "아이폰" in prompt
                else '{"ok": true, "reason": "ok"}'
            )

        monkeypatch.setattr(vr, "_call_vision", fake)
        products = [
            {"name": "메쉬 의자", "image_url_external": "http://x/1.jpg"},
            {"name": "아이폰 케이스", "image_url_external": "http://x/2.jpg"},
        ]
        res = vr.filter_relevant(products, "의자", api_key="k")
        assert [p["name"] for p in res["kept"]] == ["메쉬 의자"]
        assert [p["name"] for p in res["dropped"]] == ["아이폰 케이스"]
        assert res["dropped"][0]["_vision_reason"] == "딴거"
        assert res["checked"] == 2 and res["capped"] == 0

    def test_cap_limits_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _stub_fetch(monkeypatch)
        calls = {"n": 0}

        def fake(*a: object, **k: object) -> str:
            calls["n"] += 1
            return '{"ok": true, "reason": "ok"}'

        monkeypatch.setattr(vr, "_call_vision", fake)
        products = [{"name": f"p{i}", "image_url_external": f"http://x/{i}.jpg"} for i in range(5)]
        res = vr.filter_relevant(products, "의자", api_key="k", cap=2)
        assert res["checked"] == 2
        assert res["capped"] == 3
        assert calls["n"] == 2  # cap 초과분은 호출하지 않음(비용 보호)
        assert len(res["kept"]) == 5  # 검사된 2(ok) + 초과 3(통과)

    def test_no_image_fail_closed_drops(self) -> None:
        res = vr.filter_relevant(
            [{"name": "x", "image_url_external": ""}], "의자", api_key="k", fail_closed=True
        )
        assert len(res["dropped"]) == 1 and len(res["kept"]) == 0
