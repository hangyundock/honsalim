"""네이버 검색광고 클라이언트 회귀 테스트 (세션 #15) — dry_run·서명·파싱.

라이브 HTTP는 본 회귀에서 호출하지 않는다(비용·네트워크 의존). 라이브 검증은 별도 스모크.
출처: AutoBlog keyword_sources.py 미러 + BACKEND §8-1.
"""

from __future__ import annotations

import base64

import pytest

from collector import naver_searchad as ns


class TestSignature:
    def test_deterministic(self) -> None:
        a = ns.signature("1700000000000", "GET", "/keywordstool", "secret")
        b = ns.signature("1700000000000", "GET", "/keywordstool", "secret")
        assert a == b

    def test_timestamp_changes_signature(self) -> None:
        a = ns.signature("1700000000000", "GET", "/keywordstool", "secret")
        b = ns.signature("1700000000001", "GET", "/keywordstool", "secret")
        assert a != b

    def test_is_base64(self) -> None:
        sig = ns.signature("1700000000000", "GET", "/keywordstool", "secret")
        # base64 디코딩 가능해야 함 (SHA-256 → 32바이트)
        assert len(base64.b64decode(sig)) == 32


class TestBuildRequest:
    def test_structure(self) -> None:
        req = ns.build_keywordstool_request(
            "사무용 의자",
            api_key="KEY",
            customer_id="123",
            secret_key="SECRET",
            timestamp="1700000000000",
        )
        assert req["method"] == "GET"
        assert req["url"].endswith("/keywordstool")
        assert req["params"]["hintKeywords"] == "사무용의자"  # 공백 제거
        assert req["params"]["showDetail"] == "1"
        for h in ("X-Timestamp", "X-API-KEY", "X-Customer", "X-Signature"):
            assert h in req["headers"]
        assert req["headers"]["X-API-KEY"] == "KEY"
        assert req["headers"]["X-Customer"] == "123"


class TestParsing:
    def test_to_int_variants(self) -> None:
        assert ns.to_int("< 10") == 10
        assert ns.to_int("1,234") == 1234
        assert ns.to_int(560) == 560
        assert ns.to_int(None) == 0
        assert ns.to_int("abc") == 0

    def test_normalize_sums_volume(self) -> None:
        out = ns.normalize(
            {
                "relKeyword": "사무용 의자",
                "monthlyPcQcCnt": "1,000",
                "monthlyMobileQcCnt": 500,
                "compIdx": "높음",
            }
        )
        assert out == {"keyword": "사무용 의자", "volume": 1500, "competition": "높음"}

    def test_normalize_handles_low_volume_marker(self) -> None:
        out = ns.normalize(
            {"relKeyword": "x", "monthlyPcQcCnt": "< 10", "monthlyMobileQcCnt": "< 10"}
        )
        assert out["volume"] == 20
        assert out["competition"] == "unknown"


class TestDryRun:
    def test_dry_run_without_creds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 자격증명 없이도 dry_run은 더미로 요청을 빌드 (구조 검증용)
        monkeypatch.delenv(ns.ENV_API_KEY, raising=False)
        monkeypatch.delenv(ns.ENV_SECRET_KEY, raising=False)
        monkeypatch.delenv(ns.ENV_CUSTOMER_ID, raising=False)
        out = ns.fetch_related_keywords("사무용 의자", dry_run=True)
        assert len(out) == 1
        assert out[0]["dry_run"] is True
        assert out[0]["request"]["params"]["hintKeywords"] == "사무용의자"

    def test_dry_run_uses_real_creds_when_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ns.ENV_API_KEY, "REALKEY")
        monkeypatch.setenv(ns.ENV_SECRET_KEY, "REALSECRET")
        monkeypatch.setenv(ns.ENV_CUSTOMER_ID, "999")
        out = ns.fetch_related_keywords("의자", dry_run=True)
        assert out[0]["request"]["headers"]["X-API-KEY"] == "REALKEY"
        assert out[0]["request"]["headers"]["X-Customer"] == "999"


class TestCredsGuard:
    def test_live_without_creds_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ns.ENV_API_KEY, raising=False)
        monkeypatch.delenv(ns.ENV_SECRET_KEY, raising=False)
        monkeypatch.delenv(ns.ENV_CUSTOMER_ID, raising=False)
        with pytest.raises(ns.NaverSearchAdError):
            ns.fetch_related_keywords("사무용 의자", dry_run=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
