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


_SM_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
)


def _sm(*entries: tuple[str, str | None]) -> str:
    body = "".join(
        f"  <url><loc>{loc}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>\n"
        for loc, lm in entries
    )
    return _SM_HEAD + body + "</urlset>\n"


class TestChangedUrls:
    """#45 적대검증 — IndexNow 지침(변경 URL만 제출) 준수: diff 산출."""

    def test_added_modified_deleted(self) -> None:
        prev = _sm(
            ("https://h.com/", None),
            ("https://h.com/a/", "2026-07-01"),
            ("https://h.com/gone/", None),
        )
        curr = _sm(
            ("https://h.com/", None),  # 불변 — 제출 안 함
            ("https://h.com/a/", "2026-07-19"),  # lastmod 변경
            ("https://h.com/new/", "2026-07-19"),  # 신규
        )
        out = indexnow.changed_urls(prev, curr)
        assert "https://h.com/" not in out  # 변경 없는 URL 재제출 금지
        assert set(out) == {"https://h.com/a/", "https://h.com/new/", "https://h.com/gone/"}

    def test_no_prev_falls_back_to_full(self) -> None:
        curr = _sm(("https://h.com/", None), ("https://h.com/a/", None))
        assert set(indexnow.changed_urls(None, curr)) == {"https://h.com/", "https://h.com/a/"}

    def test_broken_prev_falls_back_to_full(self) -> None:
        curr = _sm(("https://h.com/", None))
        assert indexnow.changed_urls("<broken", curr) == ["https://h.com/"]

    def test_broken_curr_returns_empty(self) -> None:
        assert indexnow.changed_urls(None, "<broken") == []


class TestDeployUrls:
    def test_merges_changed_and_refreshed_categories(self, tmp_path: Path) -> None:
        (tmp_path / "sitemap.xml").write_text(
            _sm(
                ("https://honsallim.com/", None),
                ("https://honsallim.com/articles/new/", "2026-07-19"),
            ),
            encoding="utf-8",
        )
        prev = _sm(("https://honsallim.com/", None))
        out = indexnow.deploy_urls(tmp_path, prev, refreshed_category_slugs=["office-chair"])
        assert out == [
            "https://honsallim.com/articles/new/",
            "https://honsallim.com/categories/office-chair/",
        ]

    def test_missing_sitemap_returns_empty(self, tmp_path: Path) -> None:
        assert indexnow.deploy_urls(tmp_path, None, refreshed_category_slugs=["x"]) == []


class TestKeyFileLive:
    KEY = "abcd1234efgh5678"

    def _resp(self, body: bytes, status: int = 200) -> _FakeResp:
        r = _FakeResp(body)
        r.status = status
        return r

    def test_live_when_body_matches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)
        seen: list[str] = []

        def fake_urlopen(url: str, timeout: int = 0) -> _FakeResp:
            seen.append(url)
            return self._resp(self.KEY.encode())

        monkeypatch.setattr(indexnow.urllib.request, "urlopen", fake_urlopen)
        assert indexnow.key_file_live("honsallim.com", attempts=1) is True
        assert seen == [f"https://honsallim.com/{self.KEY}.txt"]

    def test_retries_then_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)
        calls = {"n": 0}

        def fake_urlopen(url: str, timeout: int = 0) -> _FakeResp:
            calls["n"] += 1
            if calls["n"] < 3:
                raise urllib.error.URLError("404")  # CI 반영 전
            return self._resp(self.KEY.encode())

        monkeypatch.setattr(indexnow.urllib.request, "urlopen", fake_urlopen)
        assert indexnow.key_file_live("honsallim.com", attempts=4, interval_s=0) is True
        assert calls["n"] == 3

    def test_false_when_body_mismatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 200이어도 내용이 키와 다르면(예: SPA 폴백 페이지) 미라이브 판정
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)
        monkeypatch.setattr(
            indexnow.urllib.request,
            "urlopen",
            lambda url, timeout=0: self._resp(b"<html>not-key</html>"),
        )
        assert indexnow.key_file_live("honsallim.com", attempts=1) is False

    def test_false_after_attempts_exhausted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INDEXNOW_KEY", self.KEY)

        def boom(url: str, timeout: int = 0) -> _FakeResp:
            raise urllib.error.URLError("down")

        monkeypatch.setattr(indexnow.urllib.request, "urlopen", boom)
        assert indexnow.key_file_live("honsallim.com", attempts=2, interval_s=0) is False


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
