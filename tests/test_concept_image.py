"""concept_image 회귀 — 프롬프트 구성 + (requests 모킹) 생성·webp 저장. 라이브 호출 없음."""

from __future__ import annotations

import base64
import io
from typing import Any

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

from enricher import concept_image as ci


def _tiny_png_b64() -> str:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (20, 12), (120, 130, 140)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class _FakeResp:
    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self.status_code = status
        self._payload = payload
        self.text = ""

    def json(self) -> dict[str, Any]:
        return self._payload


class TestPrompt:
    def test_no_text_guard_in_prompt(self) -> None:
        p = ci.build_concept_prompt("monitor stand riser on a desk")
        assert "no text" in p
        assert "monitor stand riser on a desk" in p


class TestGenerate:
    def test_saves_webp(self, tmp_path: Any, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        payload = {"predictions": [{"bytesBase64Encoded": _tiny_png_b64()}]}
        monkeypatch.setattr(ci.requests, "post", lambda *a, **k: _FakeResp(payload))
        out = tmp_path / "concept.webp"
        ok = ci.generate_concept_image("computer desk", out, api_key="dummy")
        assert ok is True
        assert out.exists() and out.stat().st_size > 0
        # webp = RIFF 컨테이너
        head = out.read_bytes()[:12]
        assert head[:4] == b"RIFF" and head[8:12] == b"WEBP"

    def test_empty_predictions_returns_false(self, tmp_path: Any, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        monkeypatch.setattr(ci.requests, "post", lambda *a, **k: _FakeResp({"predictions": []}))
        assert ci.generate_concept_image("x", tmp_path / "y.webp", api_key="dummy") is False

    def test_missing_key_raises(self, tmp_path: Any, monkeypatch: Any) -> None:
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        try:
            ci.generate_concept_image("x", tmp_path / "z.webp", api_key="")
            raise AssertionError("RuntimeError 기대")
        except RuntimeError:
            pass

    def test_http_error_raises(self, tmp_path: Any, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return

        class _Err(_FakeResp):
            pass

        monkeypatch.setattr(ci.requests, "post", lambda *a, **k: _Err({}, status=429))
        try:
            ci.generate_concept_image("x", tmp_path / "e.webp", api_key="dummy")
            raise AssertionError("RuntimeError 기대(HTTP 429)")
        except RuntimeError:
            pass


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
