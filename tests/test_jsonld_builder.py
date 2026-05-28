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


from builder.jsonld import _normalize_keywords, build_article_jsonld
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
        site_base_url="https://honsalim.com",
        image_url="https://honsalim.com/static/img/wonroom-30man-cover.jpg",
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
        assert doc["mainEntityOfPage"] == "https://honsalim.com/articles/wonroom-30man"

    def test_base_url_trailing_slash_stripped(self) -> None:
        """site_base_url 끝 / 자동 제거."""
        jsonld = build_article_jsonld(
            meta=_minimal_meta(),
            scenario=_scenario(),
            site_base_url="https://honsalim.com/",
            image_url="https://x/i.jpg",
            published_at="2026-05-28",
        )
        doc = json.loads(jsonld)
        assert doc["mainEntityOfPage"] == "https://honsalim.com/articles/wonroom-30man"

    def test_modified_at_defaults_to_published_at(self) -> None:
        doc = json.loads(_build_default())
        assert doc["dateModified"] == doc["datePublished"] == "2026-05-28"

    def test_modified_at_explicit(self) -> None:
        jsonld = build_article_jsonld(
            meta=_minimal_meta(),
            scenario=_scenario(),
            site_base_url="https://honsalim.com",
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
            site_base_url="https://honsalim.com",
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
            site_base_url="https://honsalim.com",
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
            site_base_url="https://honsalim.com",
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
            site_base_url="https://honsalim.com",
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
                site_base_url="https://honsalim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_missing_meta_description_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta={"title": "x"},
                scenario=_scenario(),
                site_base_url="https://honsalim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_empty_title_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta={"title": "", "meta_description": "x"},
                scenario=_scenario(),
                site_base_url="https://honsalim.com",
                image_url="https://x/i.jpg",
                published_at="2026-05-28",
            )

    def test_missing_scenario_slug_raises(self) -> None:
        with raises(ValueError):
            build_article_jsonld(
                meta=_minimal_meta(),
                scenario={},
                site_base_url="https://honsalim.com",
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


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
