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

    def test_density_range_and_bans_absolutes(self) -> None:
        # 세션 #33: 게이트 정합 — 정확형 밀도 하한(1.0%) 확보 + 상한(3%) 도배 금지 + 단정/과장 금지.
        # (세션 #19 '정확형 억제' 과교정으로 하한 미달하던 것을 게이트 범위와 정합하게 수정)
        out = build_seo_directive("노트북 거치대", [])
        assert "1.0~1.7%" in out  # 밀도 하한 확보 범위 명시(게이트 정합)
        assert "3% 초과" in out  # 도배 상한 금지
        assert "거치대" in out  # 대체 표현(short form) 안내
        assert "무조건" in out and "절대" in out  # 단정·과장 금지 어휘

    def test_short_form_substitution(self) -> None:
        from enricher.seo_directive import _short_form

        assert _short_form("노트북 거치대") == "거치대"
        assert _short_form("컴퓨터 책상") == "책상"
        assert _short_form("모니터암") == "모니터암"  # 단일어는 그대로


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
