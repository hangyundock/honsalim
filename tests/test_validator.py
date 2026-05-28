"""validator 4 게이트 회귀 테스트.

출처: BACKEND §8-1 회귀 테스트 최우선 + POLICY §3·§4·§5·§6 + VALIDATOR_PATTERNS [확정].

규칙 (BACKEND §8-1):
- validator 변경 시 본 테스트 100% 통과 필수
- 패턴 추가 시 본 테스트도 추가 의무
"""

from __future__ import annotations

import json
from typing import Any

from validator import (
    check_disclosure,
    check_links,
    check_schema,
    check_truth,
    serialize_report,
    validate_all,
)

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

    def test_fail_first_person_without_photo(self) -> None:
        """POLICY §3-1-3 — 1인칭 검출 시 직접 사진 없으면 fail."""
        ok, rpt = check_truth(
            {
                "body_md": "내 원룸에서 써본 결과 너무 편했습니다.",
                "products": [],
            }
        )
        assert ok is False
        assert any("first_person_without_photo" in i for i in rpt["issues"])

    def test_pass_first_person_with_photos_list(self) -> None:
        """photos 리스트 비어있지 않으면 1인칭 허용."""
        ok, rpt = check_truth(
            {
                "body_md": "내 원룸에서 사용해보니 편했습니다.",
                "products": [],
                "photos": [{"product_slug": "x"}],
            }
        )
        assert ok is True
        assert rpt["issues"] == []

    def test_pass_first_person_with_has_user_photo_flag(self) -> None:
        """has_user_photo boolean 플래그도 지원 (POLICY 코드 예시 호환)."""
        ok, rpt = check_truth(
            {
                "body_md": "우리집에서 3개월 사용했더니 만족합니다.",
                "products": [],
                "has_user_photo": True,
            }
        )
        assert ok is True

    def test_fail_first_person_n_months_used(self) -> None:
        """N개월 사용 패턴도 직접 사진 없으면 fail."""
        ok, rpt = check_truth(
            {
                "body_md": "이 제품을 6개월 사용해보았습니다.",
                "products": [],
            }
        )
        assert ok is False
        assert any("first_person_without_photo" in i for i in rpt["issues"])

    def test_fail_ai_trace_soft_threshold(self) -> None:
        """'훌륭한/완벽한/최고의' 패턴 5회 이상 → fail."""
        body = " ".join(["훌륭한"] * 5)
        ok, rpt = check_truth({"body_md": body, "products": []})
        assert ok is False
        assert any("ai_trace_soft" in i for i in rpt["issues"])

    def test_pass_ai_trace_soft_below_threshold(self) -> None:
        """4회는 임계 미만 → pass."""
        body = "이 제품은 훌륭한 디자인과 완벽한 마감, 그리고 최고의 가성비를 보였다."
        ok, rpt = check_truth({"body_md": body, "products": []})
        # 훌륭한·완벽한·최고의 각 1회 → 임계 5 미만, soft 패턴 모두 통과
        assert ok is True


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

    def test_pass_itemlist_complete(self) -> None:
        """VALIDATOR §8 — ItemList 필수 3필드 + 요소 1개 이상."""
        itemlist = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "itemListElement": [{"@type": "ListItem", "position": 1, "name": "x"}],
            }
        )
        ok, rpt = check_schema(itemlist)
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_itemlist_missing_element(self) -> None:
        itemlist = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
            }
        )
        ok, rpt = check_schema(itemlist)
        assert ok is False
        assert "missing_field: itemListElement" in rpt["issues"]

    def test_fail_itemlist_empty_elements(self) -> None:
        itemlist = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "itemListElement": [],
            }
        )
        ok, rpt = check_schema(itemlist)
        assert ok is False
        assert "itemlist_empty" in rpt["issues"]

    def test_pass_product_complete(self) -> None:
        """VALIDATOR §8 — Product + offers.price·priceCurrency."""
        product = json.dumps(
            {
                "@type": "Product",
                "name": "원룸 자취 패키지",
                "offers": {"price": "290000", "priceCurrency": "KRW"},
            }
        )
        ok, rpt = check_schema(product)
        assert ok is True
        assert rpt["issues"] == []

    def test_fail_product_missing_offers_price(self) -> None:
        product = json.dumps(
            {
                "@type": "Product",
                "name": "x",
                "offers": {"priceCurrency": "KRW"},
            }
        )
        ok, rpt = check_schema(product)
        assert ok is False
        assert "missing_offers_field: price" in rpt["issues"]


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

    def test_fail_short_url_n_kakao(self) -> None:
        """DECISIONS K3 [확정] — n.kakao.com 카카오 단축 차단."""
        ok, rpt = check_links("자세히는 https://n.kakao.com/abc123 참고")
        assert ok is False
        assert any("n" in i and "kakao" in i for i in rpt["issues"])

    def test_fail_short_url_naver_me(self) -> None:
        """DECISIONS K3 [확정] — naver.me 네이버 단축 차단."""
        ok, rpt = check_links("링크: https://naver.me/xyz")
        assert ok is False
        assert any("naver" in i and "me" in i for i in rpt["issues"])

    def test_fail_multiple_short_urls_in_body(self) -> None:
        """여러 단축 동시 등장 시 모두 차단."""
        body = "단축1 https://bit.ly/a 단축2 https://naver.me/b"
        ok, rpt = check_links(body)
        assert ok is False
        assert len([i for i in rpt["issues"] if "short_url_blocked" in i]) >= 2

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


# ─── serialize_report — JSON 직렬화 ──────────────────────────────────


class TestSerializeReport:
    def test_all_pass_overall_true(self) -> None:
        payload: dict[str, Any] = {
            "body_md": GOOD_DISCLOSURE_BODY,
            "schema_jsonld": _good_article_schema(),
            "products": [],
        }
        report = serialize_report(validate_all(payload))
        assert report["overall_pass"] is True
        for gate in ("truth", "schema", "disclosure", "links"):
            assert gate in report["gates"]
            assert report["gates"][gate]["pass"] is True
            assert report["gates"][gate]["issues"] == []

    def test_any_fail_overall_false(self) -> None:
        payload: dict[str, Any] = {
            "body_md": "본 글은 AI로 작성되었습니다.",  # truth fail (AI hard)
            "schema_jsonld": None,  # schema fail
            "products": [],
        }
        report = serialize_report(validate_all(payload))
        assert report["overall_pass"] is False
        assert report["gates"]["truth"]["pass"] is False
        assert report["gates"]["schema"]["pass"] is False
        assert len(report["gates"]["truth"]["issues"]) > 0

    def test_serialized_is_json_safe(self) -> None:
        """결과 dict가 json.dumps로 직렬화 가능해야 함."""
        payload: dict[str, Any] = {"body_md": "x", "schema_jsonld": None, "products": []}
        report = serialize_report(validate_all(payload))
        json.dumps(report)  # 예외 없으면 OK


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
