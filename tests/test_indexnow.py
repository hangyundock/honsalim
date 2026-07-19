"""deployer.indexnow 회귀 테스트 (세션 #45) — 통지 페이로드·§0 실패 격리·키 검증.

외부 네트워크 0: urlopen은 전부 monkeypatch(test_notify.py 패턴). secrets 실로드 차단.
"""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from deployer import indexnow


class _FakeResp(io.BytesIO):
    status = 200

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """실 secrets 로드 차단 + 키 초기화 — 이 머신의 실키가 테스트에 새지 않게."""
    from common import config

    monkeypatch.setattr(config, "load_secrets", lambda *a, **k: {})
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)


class TestReadyAndKey:
    def test_not_ready_without_key(self) -> None:
        assert indexnow.indexnow_ready() is False

    def test_ready_with_valid_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", "abcd1234efgh5678")
        assert indexnow.indexnow_ready() is True

    def test_invalid_key_format_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 형식 밖 값(공백·특수문자·과단축)은 키로 쓰지 않음 — 경로 오염 방어
        for bad in ("short", "has space key", "weird/../key", "k" * 200):
            monkeypatch.setenv("INDEXNOW_KEY", bad)
            assert indexnow.indexnow_ready() is False


class TestPing:
    KEY = "abcd1234efgh5678"

    def test_payload_shape_and_host_derivation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)
        captured: dict[str, Any] = {}

        def fake_urlopen(req: Any, timeout: int = 0) -> _FakeResp:
            captured["url"] = req.full_url
            captured["payload"] = json.loads(req.data)
            return _FakeResp(b"")

        monkeypatch.setattr(indexnow.urllib.request, "urlopen", fake_urlopen)
        urls = ["https://honsallim.com/", "https://honsallim.com/articles/kw-x/"]
        assert indexnow.ping(urls) is True
        assert captured["url"] == indexnow.INDEXNOW_ENDPOINT
        p = captured["payload"]
        # host·keyLocation은 URL에서 유도(도메인 하드코딩 드리프트 방지 — honsalim/honsallim 이력)
        assert p["host"] == "honsallim.com"
        assert p["key"] == self.KEY
        assert p["keyLocation"] == f"https://honsallim.com/{self.KEY}.txt"
        assert p["urlList"] == urls

    def test_no_key_no_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            indexnow.urllib.request,
            "urlopen",
            lambda *a, **k: pytest.fail("키 미설정이면 네트워크 호출 금지"),
        )
        assert indexnow.ping(["https://honsallim.com/"]) is False

    def test_empty_urls_no_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)
        monkeypatch.setattr(
            indexnow.urllib.request,
            "urlopen",
            lambda *a, **k: pytest.fail("URL 없으면 네트워크 호출 금지"),
        )
        assert indexnow.ping([]) is False

    def test_urlerror_swallowed_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """§0: 네트워크 실패는 예외 전파 없이 False — 무인 발행을 절대 못 막는다."""
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)

        def boom(*a: Any, **k: Any) -> Any:
            raise urllib.error.URLError("down")

        monkeypatch.setattr(indexnow.urllib.request, "urlopen", boom)
        assert indexnow.ping(["https://honsallim.com/"]) is False  # 예외 없이 False


class TestSitemapUrls:
    def test_parses_locs(self, tmp_path: Path) -> None:
        (tmp_path / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "  <url><loc>https://honsallim.com/</loc></url>\n"
            "  <url><loc>https://honsallim.com/privacy/</loc><lastmod>2026-07-19</lastmod></url>\n"
            "</urlset>\n",
            encoding="utf-8",
        )
        assert indexnow.sitemap_urls(tmp_path) == [
            "https://honsallim.com/",
            "https://honsallim.com/privacy/",
        ]

    def test_missing_sitemap_returns_empty(self, tmp_path: Path) -> None:
        assert indexnow.sitemap_urls(tmp_path / "nope") == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
