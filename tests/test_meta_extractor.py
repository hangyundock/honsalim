"""meta_extractor 회귀 테스트.

출처: BACKEND §3-3 + §49 + FRONTEND §5·§6 + ARCH §296 [확정].
"""

from __future__ import annotations

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


from enricher import (
    KEYWORDS_MAX,
    META_DESCRIPTION_MAX,
    SUMMARY_MAX,
    TITLE_MAX,
    ExtractRequest,
    MetaExtractionError,
    MetaExtractor,
    extract,
    normalize_meta,
    parse_meta_json,
    validate_meta,
)


# 검증 통과 minimal 메타 — 길이 경계 안쪽
def _valid_meta() -> dict[str, Any]:
    title = "원룸 30만원 자취 패키지 추천 — 새내기를 위한 5가지"
    summary = (
        "새내기 자취생을 위해 30만원 예산으로 꾸리는 원룸 패키지를 정리했다. "
        "수납·취사·청소 영역별 핵심 아이템과 우선순위를 시즌별로 함께 안내한다."
    )
    desc = (
        "30만원 예산으로 시작하는 원룸 자취 패키지 가이드 — 수납·취사·청소 영역별 "
        "핵심 아이템과 우선순위, 시즌별 구매 팁을 함께 한눈에 정리했다."
    )
    return {
        "title": title,
        "summary": summary,
        "meta_description": desc,
        "meta_keywords": "원룸자취,자취패키지,새내기,자취준비,30만원자취",
        "faqs": [{"q": "예산이 부족하면?", "a": "수납·청소부터 먼저 갖추세요."}],
        "schema_recommended_review_eligible": ["item-a"],
    }


class TestExtractRequest:
    def test_build_user_prompt_includes_body_md(self) -> None:
        from enricher.meta_extractor import build_user_prompt

        req = ExtractRequest(
            body_md="본문 마크다운 샘플입니다.",
            persona={"slug": "cheot-jachi"},
            scenario={"slug": "test-scenario"},
        )
        prompt = build_user_prompt(req)
        assert "본문 마크다운 샘플입니다." in prompt

    def test_build_user_prompt_includes_persona_slug(self) -> None:
        from enricher.meta_extractor import build_user_prompt

        req = ExtractRequest(
            body_md="x",
            persona={"slug": "homeoffice-1"},
            scenario={"slug": "y"},
        )
        prompt = build_user_prompt(req)
        assert "homeoffice-1" in prompt

    def test_build_user_prompt_includes_scenario_slug(self) -> None:
        from enricher.meta_extractor import build_user_prompt

        req = ExtractRequest(
            body_md="x",
            persona={"slug": "p"},
            scenario={"slug": "wonroom-30"},
        )
        prompt = build_user_prompt(req)
        assert "wonroom-30" in prompt

    def test_build_user_prompt_rejects_empty_body(self) -> None:
        from enricher.meta_extractor import build_user_prompt

        req = ExtractRequest(body_md="   ", persona={}, scenario={})
        with raises(MetaExtractionError):
            build_user_prompt(req)


class TestParseMetaJson:
    def test_parse_clean_json(self) -> None:
        text = '{"title": "x", "summary": "y"}'
        out = parse_meta_json(text)
        assert out == {"title": "x", "summary": "y"}

    def test_parse_json_with_code_fence(self) -> None:
        text = '```json\n{"title": "x"}\n```'
        out = parse_meta_json(text)
        assert out == {"title": "x"}

    def test_parse_json_with_surrounding_text(self) -> None:
        text = '다음은 추출 결과입니다:\n{"title": "x"}\n끝.'
        out = parse_meta_json(text)
        assert out == {"title": "x"}

    def test_parse_empty_raises(self) -> None:
        with raises(MetaExtractionError):
            parse_meta_json("")

    def test_parse_no_json_block_raises(self) -> None:
        with raises(MetaExtractionError):
            parse_meta_json("아무 JSON도 없는 텍스트")

    def test_parse_invalid_json_raises(self) -> None:
        with raises(MetaExtractionError):
            parse_meta_json('{"title": "broken)')

    def test_parse_non_object_raises(self) -> None:
        with raises(MetaExtractionError):
            parse_meta_json("[1, 2, 3]")


class TestValidateMeta:
    def test_valid_meta_passes(self) -> None:
        validate_meta(_valid_meta())

    def test_missing_title_raises(self) -> None:
        meta = _valid_meta()
        del meta["title"]
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_empty_summary_raises(self) -> None:
        meta = _valid_meta()
        meta["summary"] = ""
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_title_too_long_raises(self) -> None:
        meta = _valid_meta()
        meta["title"] = "가" * (TITLE_MAX + 1)
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_summary_too_short_raises(self) -> None:
        meta = _valid_meta()
        meta["summary"] = "짧음"
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_summary_too_long_raises(self) -> None:
        meta = _valid_meta()
        meta["summary"] = "가" * (SUMMARY_MAX + 1)
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_meta_description_too_short_raises(self) -> None:
        meta = _valid_meta()
        meta["meta_description"] = "짧음"
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_meta_description_too_long_raises(self) -> None:
        meta = _valid_meta()
        meta["meta_description"] = "가" * (META_DESCRIPTION_MAX + 1)
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_keywords_too_few_raises(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = "a,b"  # KEYWORDS_MIN=3 미만
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_keywords_too_many_raises(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = ",".join(f"k{i}" for i in range(KEYWORDS_MAX + 1))
        with raises(MetaExtractionError):
            validate_meta(meta)

    def test_keywords_as_list_format_accepted(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = ["원룸자취", "자취패키지", "새내기"]
        validate_meta(meta)

    def test_keywords_invalid_type_raises(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = 12345
        with raises(MetaExtractionError):
            validate_meta(meta)


class TestNormalizeMeta:
    def test_defaults_added(self) -> None:
        meta = _valid_meta()
        del meta["faqs"]
        del meta["schema_recommended_review_eligible"]
        out = normalize_meta(meta)
        assert out["faqs"] == []
        assert out["schema_recommended_review_eligible"] == []

    def test_keywords_string_to_list(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = "a, b, c, d"
        out = normalize_meta(meta)
        assert out["meta_keywords"] == ["a", "b", "c", "d"]

    def test_keywords_list_passthrough(self) -> None:
        meta = _valid_meta()
        meta["meta_keywords"] = ["x", "y", "z"]
        out = normalize_meta(meta)
        assert out["meta_keywords"] == ["x", "y", "z"]

    def test_original_dict_not_mutated(self) -> None:
        meta = _valid_meta()
        original_keywords = meta["meta_keywords"]
        normalize_meta(meta)
        assert meta["meta_keywords"] == original_keywords


class TestMetaExtractor:
    def test_extract_dry_run_returns_prompts_no_call(self) -> None:
        """dry_run=True (기본): API 호출 없이 프롬프트만 반환."""
        extractor = MetaExtractor(api_key=None)
        req = ExtractRequest(
            body_md="본문 내용",
            persona={"slug": "cheot-jachi"},
            scenario={"slug": "wonroom-30"},
        )
        result = extractor.extract(req, dry_run=True)
        assert result.dry_run is True
        assert result.extracted is None
        assert result.response_text is None
        assert len(result.system_blocks) == 2  # system_base + tone_examples
        assert "본문 내용" in result.user_prompt

    def test_extract_real_call_requires_api_key(self) -> None:
        """dry_run=False + 키 없음 → RuntimeError."""
        extractor = MetaExtractor(api_key=None)
        req = ExtractRequest(body_md="본문", persona={"slug": "p"}, scenario={"slug": "s"})
        with raises(RuntimeError):
            extractor.extract(req, dry_run=False)


class TestModuleHelper:
    def test_extract_helper_dry_run(self) -> None:
        """모듈 레벨 extract() 헬퍼 — BACKEND §49 시그니처."""
        result = extract(
            body_md="본문입니다.",
            persona={"slug": "cheot-jachi"},
            scenario={"slug": "wonroom-30"},
            dry_run=True,
        )
        assert result.dry_run is True
        assert "본문입니다." in result.user_prompt

    def test_extract_helper_minimal_args(self) -> None:
        """persona·scenario 생략 시 빈 dict default."""
        result = extract(body_md="x", dry_run=True)
        assert result.dry_run is True
        # persona·scenario 슬러그가 빈 값으로 치환되어 prompt 빌드 성공
        assert result.user_prompt  # 비어있지 않음


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
