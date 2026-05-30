"""enricher 회귀 테스트 — prompt_loader + claude_client stub.

출처: BACKEND §3 [확정].
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
    CACHED_SYSTEM_TEMPLATES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    KNOWN_TEMPLATES,
    ArticleResponseError,
    ClaudeClient,
    GenerateRequest,
    build_system_blocks,
    build_user_prompt,
    list_templates,
    load,
    split_article_response,
    verify_known_templates_present,
)


class TestPromptLoader:
    def test_known_templates_all_present(self) -> None:
        """BACKEND §3-3 명시 6종 prompt_templates가 실제 존재."""
        present = verify_known_templates_present()
        for name in KNOWN_TEMPLATES:
            assert present[name] is True, f"missing: {name}"

    def test_list_templates_includes_all_known(self) -> None:
        files = set(list_templates())
        for name in KNOWN_TEMPLATES:
            assert name in files

    def test_load_returns_content(self) -> None:
        content = load("system_base")
        assert "혼살림" in content  # 한국어 본문 일부
        assert len(content) > 100

    def test_load_unknown_raises(self) -> None:
        with raises(FileNotFoundError):
            load("nonexistent_template")

    def test_render_simple_var(self) -> None:
        """Jinja2 없어도 단순 {{var}} 치환 동작."""
        # 직접 단순 치환 함수 검증 — article_main.md를 render 시 변수 치환
        from enricher.prompt_loader import render_simple

        out = render_simple("hello {{name}}!", name="혼살림")
        assert out == "hello 혼살림!"

    def test_render_simple_dotted_path(self) -> None:
        from enricher.prompt_loader import render_simple

        out = render_simple("title: {{scenario.title_ko}}", scenario={"title_ko": "원룸 자취"})
        assert out == "title: 원룸 자취"

    def test_render_missing_var_empty(self) -> None:
        from enricher.prompt_loader import render_simple

        out = render_simple("a={{a}}, b={{b}}", a="x")
        assert out == "a=x, b="


class TestClaudeClient:
    def test_defaults_match_backend_spec(self) -> None:
        """BACKEND §3-1 매개변수 일치."""
        assert DEFAULT_MODEL == "claude-haiku-4-5-20251001"
        assert DEFAULT_MAX_TOKENS == 4096
        assert DEFAULT_TEMPERATURE == 0.4

    def test_cached_system_templates_pair(self) -> None:
        """BACKEND §3-2·§3-4 — system 캐시 대상은 system_base + tone_examples."""
        assert CACHED_SYSTEM_TEMPLATES == ("system_base", "tone_examples")

    def test_build_system_blocks_has_cache_control(self) -> None:
        blocks = build_system_blocks()
        assert len(blocks) == 2
        for b in blocks:
            assert b["type"] == "text"
            assert b["cache_control"] == {"type": "ephemeral"}
            assert "text" in b and len(b["text"]) > 0

    def test_build_user_prompt_includes_scenario_title(self) -> None:
        req = GenerateRequest(
            scenario={"slug": "test", "title_ko": "원룸 30만원 패키지", "season_peak": "2-3월"},
            persona={"slug": "cheot-jachi", "title_ko": "새내기 자취생"},
            products=[],
            photos=[],
            related_scenarios=[],
        )
        prompt = build_user_prompt(req)
        # 변수 치환 결과에 시나리오 제목 포함
        assert "원룸 30만원 패키지" in prompt

    def test_generate_dry_run_returns_prompts_no_call(self) -> None:
        """dry_run=True (기본): API 호출 없이 프롬프트만 반환."""
        client = ClaudeClient(api_key=None)  # API 키 없어도 dry_run은 OK
        req = GenerateRequest(
            scenario={"slug": "test", "title_ko": "원룸 30만원", "season_peak": "2-3월"},
            persona={"slug": "cheot-jachi", "title_ko": "새내기 자취생"},
        )
        result = client.generate_article(req, dry_run=True)
        assert result.dry_run is True
        assert result.response_text is None
        assert len(result.system_blocks) == 2
        assert "원룸 30만원" in result.user_prompt

    def test_generate_real_call_requires_api_key(self) -> None:
        """dry_run=False + 키 없음 → RuntimeError."""
        client = ClaudeClient(api_key=None)
        req = GenerateRequest(
            scenario={"slug": "test", "title_ko": "x"},
            persona={"slug": "cheot-jachi"},
        )
        with raises(RuntimeError):
            client.generate_article(req, dry_run=False)


class TestSplitArticleResponse:
    """article_main 응답(META-JSON + BODY-MARKDOWN) 분리 — system §2 형식."""

    _GOOD = (
        "서두 잡담\n"
        "---META-JSON-START---\n"
        '{"title": "T", "summary": "S", "meta_keywords": "a,b,c"}\n'
        "---META-JSON-END---\n"
        "---BODY-MARKDOWN-START---\n"
        "## 1. 섹션\n본문 내용입니다.\n"
        "---BODY-MARKDOWN-END---\n"
        "꼬리 잡담"
    )

    def test_splits_meta_and_body(self) -> None:
        meta, body = split_article_response(self._GOOD)
        assert meta["title"] == "T"
        assert meta["meta_keywords"] == "a,b,c"
        assert body.startswith("## 1. 섹션")
        assert "본문 내용입니다." in body
        assert "META-JSON" not in body  # 구분자·메타 누출 없음

    def test_missing_meta_block_raises(self) -> None:
        text = "---BODY-MARKDOWN-START---\n본문\n---BODY-MARKDOWN-END---"
        with raises(ArticleResponseError):
            split_article_response(text)

    def test_missing_body_block_raises(self) -> None:
        text = "---META-JSON-START---\n{}\n---META-JSON-END---"
        with raises(ArticleResponseError):
            split_article_response(text)

    def test_invalid_meta_json_raises(self) -> None:
        text = (
            "---META-JSON-START---\n{not json}\n---META-JSON-END---\n"
            "---BODY-MARKDOWN-START---\n본문\n---BODY-MARKDOWN-END---"
        )
        with raises(ArticleResponseError):
            split_article_response(text)


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
