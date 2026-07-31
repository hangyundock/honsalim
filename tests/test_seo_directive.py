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
        # ★세션 #48: 밀도 목표를 '1.7%'라는 백분율이 아니라 **'1,000자당 N회'**로 준다.
        #   첫 생성 시점엔 산문 길이를 몰라 백분율을 횟수로 못 옮기고, 그 간극이 도배를 불렀다.
        assert "1,000자당" in out
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
        # 세션 #33: 게이트 정합 — 정확형 밀도 하한 확보 + 도배 상한 금지 + 단정/과장 금지.
        # ★세션 #48: 하한 확보 표현("충분히 쓸 것")이 오히려 도배를 유발해, 하한·상한을 모두
        #   '1,000자당 N~M회'라는 길이 비례 밴드로 바꿨다(라이브 07-30·07-31 이틀 발행 0편).
        out = build_seo_directive("노트북 거치대", [])
        assert "1,000자당" in out  # 하한·상한을 함께 담은 길이 비례 밴드
        # ★#48 라이브 2차: 상한에만 '탈락'을 달자 반대편(미달)로 넘어갔다 — 양쪽 다 명시해야 한다.
        assert "'도배'로 탈락" in out and "'미달'로 탈락" in out
        assert "거치대" in out  # 대체 표현 안내
        assert "무조건" in out and "절대" in out  # 단정·과장 금지 어휘

    def test_keyword_substitute_is_not_a_noop(self) -> None:
        """★세션 #48 — 옛 `_short_form`은 단일어에서 **자기 자신**을 반환해 대체 지시가 무의미했다.

        '과하면 <줄임말>로 대체하라'가 실패한 키워드('책상추천'·'스텐도마'·'모니터암')에서
        전부 `X를 X로 대체하라`가 되어, 상한 초과를 막을 탈출구가 애초에 없었다.
        """
        from enricher.keyword_density import keyword_substitute

        assert keyword_substitute("노트북 거치대") == "거치대"
        assert keyword_substitute("컴퓨터 책상") == "책상"
        assert keyword_substitute("모니터암") is None  # 자기 자신을 돌려주지 않는다


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
