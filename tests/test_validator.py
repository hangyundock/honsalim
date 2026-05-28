"""validator 4 게이트 회귀 테스트.

출처: BACKEND §8-1 회귀 테스트 최우선 + POLICY §3·§4·§5·§6 + VALIDATOR_PATTERNS [확정].

규칙 (BACKEND §8-1):
- validator 변경 시 본 테스트 100% 통과 필수
- 패턴 추가 시 본 테스트도 추가 의무
"""

from __future__ import annotations

import json
from typing import Any

from validator import check_disclosure, check_links, check_schema, check_truth, validate_all

# ─── 공통 픽스처 ──────────────────────────────────────────────────────

GOOD_DISCLOSURE_BODY = (
    "이 글은 쿠팡 파트너스 활동의 일환으로 일정 수수료를 받을 수 있습니다.\n"
    "\n# 본문 시작\n"
    "원룸 첫 자취 가이드입니다. 가격 290,000원 모델 추천.\n"
    "\n## 푸터\n"
    "본인은 쿠팡 파트너스 및 AliExpress 활동으로 수수료를 받을 수 있습니다."
)


def _good_article_schema() -> str:
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "원룸 자취",
            "description": "30만원 가이드",
            "image": "https://honsalim.com/img.jpg",
            "datePublished": "2026-05-28",
            "dateModified": "2026-05-28",
            "author": {"@type": "Person", "name": "운영자"},
            "publisher": {"@type": "Organization", "name": "혼살림"},
            "mainEntityOfPage": "https://honsalim.com/articles/x",
        }
    )


# ─── truth 게이트 (POLICY §3 + VALIDATOR §4·§5·§6·§7) ───────────────


class TestTruth:
    def test_pass_basic(self) -> None:
        ok, rpt = check_truth({"body_md": "정상 본문입니다. 가격 290,000원.", "products": []})
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_ai_trace_hard(self) -> None:
        ok, rpt = check_truth({"body_md": "본 글은 AI로 작성된 글입니다.", "products": []})
        assert ok is False
        assert any("ai_trace_hard" in i for i in rpt["issues"])

    def test_fail_absolute_100_percent(self) -> None:
        ok, rpt = check_truth({"body_md": "이 제품은 100% 효과 보장.", "products": []})
        assert ok is False
        assert any("absolute_forbidden" in i for i in rpt["issues"])

    def test_fail_absolute_health(self) -> None:
        ok, rpt = check_truth({"body_md": "이 제품은 건강에 좋다.", "products": []})
        assert ok is False
        assert any("absolute_forbidden" in i for i in rpt["issues"])

    def test_fail_price_mismatch_over_5pct(self) -> None:
        ok, rpt = check_truth(
            {
                "body_md": "가격은 200,000원입니다.",
                "products": [{"id": 1, "price_krw": 300000}],
            }
        )
        assert ok is False
        assert any("price_mismatch" in i for i in rpt["issues"])

    def test_pass_price_within_5pct(self) -> None:
        # 300,000 ±5% = 285,000 ~ 315,000
        ok, rpt = check_truth(
            {
                "body_md": "가격은 295,000원입니다.",
                "products": [{"id": 1, "price_krw": 300000}],
            }
        )
        assert ok is True
        assert rpt["issues"] == []


# ─── schema 게이트 (POLICY §4 + VALIDATOR §8) ────────────────────────


class TestSchema:
    def test_pass_article_complete(self) -> None:
        ok, rpt = check_schema(_good_article_schema())
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_missing_jsonld(self) -> None:
        ok, rpt = check_schema(None)
        assert ok is False
        assert "schema_missing" in rpt["issues"]

    def test_fail_invalid_json(self) -> None:
        ok, rpt = check_schema("{ not json }")
        assert ok is False
        assert any("json_parse_error" in i for i in rpt["issues"])

    def test_fail_missing_field(self) -> None:
        data = json.loads(_good_article_schema())
        del data["headline"]
        ok, rpt = check_schema(json.dumps(data))
        assert ok is False
        assert "missing_field: headline" in rpt["issues"]

    def test_fail_review_organization_author(self) -> None:
        review = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Review",
                "author": {"@type": "Organization", "name": "혼살림"},
            }
        )
        ok, rpt = check_schema(review)
        assert ok is False
        assert "review_author_organization_forbidden" in rpt["issues"]


# ─── disclosure 게이트 (POLICY §2 + VALIDATOR §3) ────────────────────


class TestDisclosure:
    def test_pass_complete(self) -> None:
        ok, rpt = check_disclosure(GOOD_DISCLOSURE_BODY)
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_body_missing(self) -> None:
        ok, rpt = check_disclosure(None)
        assert ok is False
        assert "body_missing" in rpt["issues"]

    def test_fail_first_missing(self) -> None:
        # 첫 200자에 '수수료' 없음
        body = "안녕하세요. 일반 가이드입니다." + " " * 200 + GOOD_DISCLOSURE_BODY
        ok, rpt = check_disclosure(body)
        assert ok is False
        assert any("first_missing" in i for i in rpt["issues"])

    def test_fail_footer_missing_aliexpress(self) -> None:
        # 푸터에서 'AliExpress' 누락
        body = (
            "이 글은 쿠팡 파트너스 활동으로 수수료를 받을 수 있습니다."
            + " " * 100
            + "본문 본문."
            + "본인의 글입니다. 쿠팡 파트너스 활동."
        )
        ok, rpt = check_disclosure(body)
        assert ok is False
        assert any("footer_missing: AliExpress" in i for i in rpt["issues"])


# ─── links 게이트 (POLICY §6 + VALIDATOR §1·§2·§9) ──────────────────


class TestLinks:
    def test_pass_empty(self) -> None:
        ok, rpt = check_links(None)
        assert ok is True

    def test_pass_no_links(self) -> None:
        ok, rpt = check_links("일반 본문 텍스트.")
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_short_url_bitly(self) -> None:
        ok, rpt = check_links("자세히는 https://bit.ly/abc 참고")
        assert ok is False
        assert any("short_url_blocked" in i for i in rpt["issues"])

    def test_fail_short_url_vivoldi(self) -> None:
        ok, rpt = check_links("링크: https://vivoldi.com/short")
        assert ok is False
        assert any("vivoldi" in i for i in rpt["issues"])

    def test_pass_internal_link(self) -> None:
        body = '<a href="https://honsalim.com/articles/abc">관련글</a>'
        ok, rpt = check_links(body)
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_external_rel_missing(self) -> None:
        body = '<a href="https://example.com/p">상품</a>'
        ok, rpt = check_links(body)
        assert ok is False
        assert any("rel_missing" in i for i in rpt["issues"])

    def test_pass_external_rel_correct(self) -> None:
        body = '<a href="https://link.coupang.com/x" rel="nofollow sponsored noopener">link</a>'
        ok, rpt = check_links(body)
        assert ok is True

    def test_fail_autoplay_ad(self) -> None:
        body = '<script src="//ad.example/popup-loader.js"></script>'
        ok, rpt = check_links(body)
        assert ok is False
        assert any("forbidden_ad" in i for i in rpt["issues"])


# ─── validate_all 통합 (VALIDATOR §11) ───────────────────────────────


class TestValidateAll:
    def test_all_pass(self) -> None:
        payload = {
            "body_md": GOOD_DISCLOSURE_BODY,
            "schema_jsonld": _good_article_schema(),
            "products": [],
        }
        results = validate_all(payload)
        assert all(ok for ok, _ in results.values())

    def test_each_gate_returns_tuple(self) -> None:
        payload: dict[str, Any] = {"body_md": "", "schema_jsonld": None, "products": []}
        results = validate_all(payload)
        for gate in ("truth", "schema", "disclosure", "links"):
            assert gate in results
            ok, rpt = results[gate]
            assert isinstance(ok, bool)
            assert "issues" in rpt
            assert rpt["gate"] == gate


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
