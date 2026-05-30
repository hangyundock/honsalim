"""seo_directive 빌더 + build_user_prompt 주입 회귀 테스트 (세션 #15).

출처: BACKEND §8-1.
"""

from __future__ import annotations

from enricher import build_seo_directive
from enricher.claude_client import GenerateRequest, build_user_prompt

PRIMARY = "사무용 의자"
SECONDARY = ["컴퓨터의자", "게이밍의자", "메쉬의자"]


class TestBuildDirective:
    def test_empty_when_no_primary(self) -> None:
        assert build_seo_directive(None) == ""
        assert build_seo_directive("  ") == ""

    def test_includes_primary_rules(self) -> None:
        out = build_seo_directive(PRIMARY, SECONDARY)
        assert PRIMARY in out
        assert "1.7%" in out  # 네이버 기준 밀도 목표
        assert "제목" in out and "도입부" in out and "소제목" in out

    def test_lists_each_secondary(self) -> None:
        out = build_seo_directive(PRIMARY, SECONDARY)
        for kw in SECONDARY:
            assert kw in out

    def test_no_secondary_section_when_empty(self) -> None:
        out = build_seo_directive(PRIMARY, [])
        assert PRIMARY in out
        assert "보조키워드" not in out

    def test_filters_blank_secondary(self) -> None:
        out = build_seo_directive(PRIMARY, ["컴퓨터의자", "  ", ""])
        assert "컴퓨터의자" in out


class TestPromptInjection:
    def test_directive_injected_when_seo_present(self) -> None:
        req = GenerateRequest(
            scenario={"slug": "office-chair", "title_ko": "사무용 의자 추천"},
            seo={"primary": PRIMARY, "secondary": SECONDARY},
        )
        prompt = build_user_prompt(req)
        assert "SEO 키워드 배치" in prompt
        assert PRIMARY in prompt
        assert "컴퓨터의자" in prompt

    def test_no_directive_when_seo_absent(self) -> None:
        # 기존 시나리오 흐름(seo 미지정) — 지시 미주입, 기존 동작 유지
        req = GenerateRequest(scenario={"slug": "test", "title_ko": "원룸 30만원"})
        prompt = build_user_prompt(req)
        assert "SEO 키워드 배치" not in prompt
        assert "원룸 30만원" in prompt


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
