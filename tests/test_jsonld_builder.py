"""builder.jsonld 회귀 테스트 — Article JSON-LD 빌드 + validator schema 게이트 정합.

출처: POLICY §4 + VALIDATOR §8 + FRONTEND §5 [확정].
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from builder.jsonld import (
    _normalize_keywords,
    as_script_tags,
    build_article_jsonld,
    build_breadcrumb_jsonld,
    build_itemlist_jsonld,
    build_organization_jsonld,
    build_product_jsonld,
    build_website_jsonld,
)
from validator import check_schema


def _minimal_meta() -> dict[str, Any]:
    return {
        "title": "원룸 30만원 자취 패키지 추천",
        "meta_description": (
            "30만원 예산으로 시작하는 원룸 자취 패키지 가이드 — 수납·취사·청소 영역별 핵심 아이템과 우선순위."
        ),
    }


def _scenario() -> dict[str, Any]:
    return {"slug": "wonroom-30man"}


def _build_default() -> str:
    out: str = build_article_jsonld(
        meta=_minimal_meta(),
        scenario=_scenario(),
        site_base_url="https://honsallim.com",
        image_url="https://honsallim.com/static/img/wonroom-30man-cover.jpg",
        published_at="2026-05-28",
    )
    return out


class TestRequiredFields:
    def test_all_10_required_fields_present(self) -> None:
        """VALIDATOR §8 ARTICLE_REQUIRED 10필드 모두 출력에 포함."""
        doc = json.loads(_build_default())
        for field in (
            "@context",
            "@type",
            "headline",
            "description",
            "image",
            "datePublished",
            "dateModified",
            "author",
            "publisher",
            "mainEntityOfPage",
        ):
            assert field in doc, f"missing: {field}"

    def test_context_and_type(self) -> None:
        doc = json.loads(_build_default())
        assert doc["@context"] == "https://schema.org"
        assert doc["@type"] == "Article"

    def test_passes_validator_schema_gate(self) -> None:
        """validator.check_schema → pass (전체 흐름 검증)."""
        jsonld = _build_default()
        ok, rpt = check_schema(jsonld)
        assert ok is True, f"schema 게이트 fail: {rpt}"
        assert rpt["issues"] == []


class TestFieldMapping:
    def test_headline_from_meta_title(self) -> None:
        doc = json.loads(_build_default())
        assert doc["headline"] == "원룸 30만원 자취 패키지 추천"

    def test_description_from_meta_description(self) -> None:
        doc = json.loads(_build_default())
        assert doc["description"].startswith("30만원 예산으로")

    def test_main_entity_url_from_slug(self) -> None:
        doc = json.loads(_build_default())
        assert doc["mainEntityOfPage"] == "https://honsallim.com/articles/wonroom-30man"

    def test_base_url_trailing_slash_stripped(self) -> None:
        """site_base_url 끝 / 자동 제거."""
        jsonld = build_article_jsonld(
            meta=_minimal_meta(),
            scenario=_scenario(),
            site_base_url="https://honsallim.com/",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
        )
        doc = json.loads(jsonld)
        assert doc["mainEntityOfPage"] == "https://honsallim.com/articles/wonroom-30man"

    def test_modified_at_defaults_to_published_at(self) -> None:
        doc = json.loads(_build_default())
        assert doc["dateModified"] == doc["datePublished"] == "2026-05-28"

    def test_modified_at_explicit(self) -> None:
        jsonld = build_article_jsonld(
            meta=_minimal_meta(),
            scenario=_scenario(),
            site_base_url="https://honsallim.com",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
            modified_at="2026-06-15",
        )
        doc = json.loads(jsonld)
        assert doc["datePublished"] == "2026-05-28"
        assert doc["dateModified"] == "2026-06-15"


class TestAuthorPublisher:
    def test_default_author_person_type(self) -> None:
        doc = json.loads(_build_default())
        assert doc["author"]["@type"] == "Person"
        assert doc["author"]["name"] == "혼살림 운영자"

    def test_default_publisher_organization_type(self) -> None:
        doc = json.loads(_build_default())
        assert doc["publisher"]["@type"] == "Organization"
        assert doc["publisher"]["name"] == "혼살림"

    def test_custom_author_publisher(self) -> None:
        jsonld = build_article_jsonld(
            meta=_minimal_meta(),
            scenario=_scenario(),
            site_base_url="https://honsallim.com",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
            author_name="홍길동",
            publisher_name="테스트사이트",
        )
        doc = json.loads(jsonld)
        assert doc["author"]["name"] == "홍길동"
        assert doc["publisher"]["name"] == "테스트사이트"


class TestKeywords:
    def test_string_keywords_pass_through(self) -> None:
        meta = _minimal_meta()
        meta["meta_keywords"] = "원룸자취, 자취패키지, 새내기"
        jsonld = build_article_jsonld(
            meta=meta,
            scenario=_scenario(),
            site_base_url="https://honsallim.com",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
        )
        doc = json.loads(jsonld)
        assert doc["keywords"] == "원룸자취, 자취패키지, 새내기"

    def test_list_keywords_joined(self) -> None:
        meta = _minimal_meta()
        meta["meta_keywords"] = ["원룸자취", "자취패키지", "새내기"]
        jsonld = build_article_jsonld(
            meta=meta,
            scenario=_scenario(),
            site_base_url="https://honsallim.com",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
        )
        doc = json.loads(jsonld)
        assert doc["keywords"] == "원룸자취, 자취패키지, 새내기"

    def test_empty_keywords_field_omitted(self) -> None:
        """meta_keywords 비어있으면 JSON-LD에서 keywords 필드 생략."""
        meta = _minimal_meta()
        meta["meta_keywords"] = ""
        jsonld = build_article_jsonld(
            meta=meta,
            scenario=_scenario(),
            site_base_url="https://honsallim.com",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
        )
        doc = json.loads(jsonld)
        assert "keywords" not in doc

    def test_missing_keywords_field_omitted(self) -> None:
        doc = json.loads(_build_default())  # meta_keywords 키 자체 없음
        assert "keywords" not in doc

    def test_normalize_keywords_helper(self) -> None:
        assert _normalize_keywords("a, b") == "a, b"
        assert _normalize_keywords(["a", "b", "c"]) == "a, b, c"
        assert _normalize_keywords(["", "a", " "]) == "a"
        assert _normalize_keywords(None) is None
        assert _normalize_keywords("") is None
        assert _normalize_keywords([]) is None


class TestValidation:
    def test_missing_title_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta={"meta_description": "x"},
                scenario=_scenario(),
                site_base_url="https://honsallim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_missing_meta_description_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta={"title": "x"},
                scenario=_scenario(),
                site_base_url="https://honsallim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_empty_title_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta={"title": "", "meta_description": "x"},
                scenario=_scenario(),
                site_base_url="https://honsallim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_missing_scenario_slug_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta=_minimal_meta(),
                scenario={},
                site_base_url="https://honsallim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )


class TestEncoding:
    def test_korean_preserved_not_escaped(self) -> None:
        """ensure_ascii=False — 한국어가 \\uXXXX로 escape되지 않음."""
        out = _build_default()
        assert "원룸" in out
        assert "\\u" not in out

    def test_output_is_valid_json(self) -> None:
        json.loads(_build_default())  # 예외 없으면 OK


# ─── ItemList 빌더 ────────────────────────────────────────────────────


class TestItemListBuilder:
    def test_required_fields_present(self) -> None:
        out = build_itemlist_jsonld([{"name": "상품 A"}, {"name": "상품 B"}])
        doc = json.loads(out)
        for field in ("@context", "@type", "itemListElement"):
            assert field in doc
        assert doc["@type"] == "ItemList"

    def test_passes_validator_schema_gate(self) -> None:
        out = build_itemlist_jsonld(
            [{"name": "상품 A", "url": "https://honsallim.com/p/a"}],
            list_name="원룸 추천",
        )
        ok, rpt = check_schema(out)
        assert ok is True, f"schema fail: {rpt}"

    def test_position_auto_assigned(self) -> None:
        out = build_itemlist_jsonld([{"name": "A"}, {"name": "B"}, {"name": "C"}])
        doc = json.loads(out)
        positions = [el["position"] for el in doc["itemListElement"]]
        assert positions == [1, 2, 3]

    def test_position_explicit_respected(self) -> None:
        out = build_itemlist_jsonld([{"name": "X", "position": 5}, {"name": "Y", "position": 2}])
        doc = json.loads(out)
        assert doc["itemListElement"][0]["position"] == 5
        assert doc["itemListElement"][1]["position"] == 2

    def test_url_optional(self) -> None:
        out = build_itemlist_jsonld([{"name": "A"}])
        doc = json.loads(out)
        assert "url" not in doc["itemListElement"][0]

    def test_url_included_when_present(self) -> None:
        out = build_itemlist_jsonld([{"name": "A", "url": "https://x/a"}])
        doc = json.loads(out)
        assert doc["itemListElement"][0]["url"] == "https://x/a"

    def test_list_name_optional(self) -> None:
        out = build_itemlist_jsonld([{"name": "A"}])
        doc = json.loads(out)
        assert "name" not in doc

    def test_list_name_included(self) -> None:
        out = build_itemlist_jsonld([{"name": "A"}], list_name="원룸 추천")
        doc = json.loads(out)
        assert doc["name"] == "원룸 추천"

    def test_empty_items_raises(self) -> None:
        with raises(ValueError):
            build_itemlist_jsonld([])

    def test_missing_item_name_raises(self) -> None:
        with raises(ValueError):
            build_itemlist_jsonld([{"name": "A"}, {"url": "x"}])  # 두 번째 name 없음


# ─── Product 빌더 ─────────────────────────────────────────────────────


class TestProductBuilder:
    def test_required_fields_present(self) -> None:
        out = build_product_jsonld({"name": "원룸 책상", "price_krw": 89000})
        doc = json.loads(out)
        for field in ("@type", "name", "offers"):
            assert field in doc
        assert doc["@type"] == "Product"
        for field in ("price", "priceCurrency"):
            assert field in doc["offers"]

    def test_passes_validator_schema_gate(self) -> None:
        out = build_product_jsonld({"name": "원룸 책상", "price_krw": 89000})
        ok, rpt = check_schema(out)
        assert ok is True, f"schema fail: {rpt}"

    def test_price_krw_accepted(self) -> None:
        out = build_product_jsonld({"name": "x", "price_krw": 50000})
        doc = json.loads(out)
        assert doc["offers"]["price"] == "50000"
        assert doc["offers"]["priceCurrency"] == "KRW"

    def test_price_field_also_accepted(self) -> None:
        """price_krw 대신 price 키도 허용."""
        out = build_product_jsonld({"name": "x", "price": 99999})
        doc = json.loads(out)
        assert doc["offers"]["price"] == "99999"

    def test_custom_currency(self) -> None:
        out = build_product_jsonld({"name": "x", "price": 19.99}, currency="USD")
        doc = json.loads(out)
        assert doc["offers"]["priceCurrency"] == "USD"

    def test_optional_image(self) -> None:
        out = build_product_jsonld({"name": "x", "price_krw": 1000}, image_url="https://x/i.jpg")
        doc = json.loads(out)
        assert doc["image"] == "https://x/i.jpg"

    def test_optional_description(self) -> None:
        out = build_product_jsonld(
            {"name": "x", "price_krw": 1000}, description="간결한 디자인의 책상"
        )
        doc = json.loads(out)
        assert doc["description"] == "간결한 디자인의 책상"

    def test_optional_brand(self) -> None:
        out = build_product_jsonld({"name": "x", "price_krw": 1000}, brand_name="이케아")
        doc = json.loads(out)
        assert doc["brand"]["@type"] == "Brand"
        assert doc["brand"]["name"] == "이케아"

    def test_sku_optional(self) -> None:
        out = build_product_jsonld({"name": "x", "price_krw": 1000, "sku": "SKU-001"})
        doc = json.loads(out)
        assert doc["sku"] == "SKU-001"

    def test_offers_url_when_product_url(self) -> None:
        out = build_product_jsonld(
            {"name": "x", "price_krw": 1000, "url": "https://link.coupang.com/x"}
        )
        doc = json.loads(out)
        assert doc["offers"]["url"] == "https://link.coupang.com/x"

    def test_missing_name_raises(self) -> None:
        with raises(ValueError):
            build_product_jsonld({"price_krw": 1000})

    def test_missing_price_raises(self) -> None:
        with raises(ValueError):
            build_product_jsonld({"name": "x"})


class TestStructuredSchemas:
    """FRONTEND §6-1 — Breadcrumb / WebSite / Organization (콘텐츠 무관)."""

    def test_breadcrumb_positions_and_absolute_urls(self) -> None:
        doc = json.loads(
            build_breadcrumb_jsonld(
                [{"name": "홈", "url": "/"}, {"name": "시나리오"}], "https://honsallim.com"
            )
        )
        assert doc["@type"] == "BreadcrumbList"
        els = doc["itemListElement"]
        assert els[0]["position"] == 1 and els[1]["position"] == 2
        assert els[0]["item"] == "https://honsallim.com/"  # 상대→절대 변환
        assert "item" not in els[1]  # 마지막(현재) url 생략

    def test_breadcrumb_empty_raises(self) -> None:
        with raises(ValueError):
            build_breadcrumb_jsonld([], "https://honsallim.com")

    def test_website_and_organization(self) -> None:
        web = json.loads(build_website_jsonld("https://honsallim.com", "혼살림"))
        assert web["@type"] == "WebSite" and web["url"] == "https://honsallim.com/"
        org = json.loads(
            build_organization_jsonld(
                "https://honsallim.com", "혼살림", "dugihappyending@gmail.com"
            )
        )
        assert org["@type"] == "Organization" and org["email"] == "dugihappyending@gmail.com"

    def test_as_script_tags_wraps_and_skips_empty(self) -> None:
        out = as_script_tags([build_website_jsonld("https://honsallim.com"), ""])
        assert out.count('<script type="application/ld+json">') == 1
        assert "WebSite" in out


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
