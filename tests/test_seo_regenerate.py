"""seo_regenerate 재생성 루프 회귀 테스트 (세션 #15).

실제 LLM 없이 generate 콜백을 mock으로 주입해 루프 동작만 검증.
출처: BACKEND §8-1.
"""

from __future__ import annotations

from enricher import regenerate_until_seo_pass

TITLE = "사무용 의자 추천 가이드"

# validator/seo.py 게이트를 통과하는 본문 (대표키워드 ~2%·제목/도입부/소제목 2개·소제목 4개)
GOOD_BODY = """# 사무용 의자 추천 가이드

재택근무로 하루 여덟 시간을 앉아 있다면 의자는 디자인이 아니라 얼마나 오래 편하게 앉을 수 있느냐로 골라야 합니다. 사무용 의자를 한 번 잘못 고르면 허리와 목, 어깨가 일 년 내내 고생하게 됩니다. 이 글은 1인 가구와 재택 환경을 기준으로 어떤 의자가 누구에게 맞는지 차근차근 비교합니다.

## 사무용 의자 타입부터 이해하기

오래 앉아 집중하는 사람과 자주 일어나 움직이는 사람은 맞는 타입이 서로 다릅니다. 메쉬 의자는 통기성이 좋아 여름에도 시원하게 앉을 수 있고, 게이밍 의자는 등받이가 높아 상반신을 전체적으로 받쳐 줍니다. 무릎꿇이 의자는 척추 정렬을 자연스럽게 유도해 자세 교정에 도움이 됩니다.

## 가성비 사무용 의자 고르는 기준

요추 지지와 팔걸이 조절, 좌판 높이, 가스실린더 등급을 차례대로 확인하세요. 아무리 인체공학 의자라도 좌판 높이가 책상과 맞지 않으면 어깨가 들려 통증이 생깁니다. 가격이 저렴한 제품은 가스실린더가 약해 몇 달 만에 주저앉는 경우가 흔하니 후기를 꼭 살펴봐야 합니다.

## 메쉬 의자와 게이밍 의자 비교

여름철 땀과 통기성이 걱정이라면 메쉬 의자가 유리하고, 오래 기대 쉬는 시간이 많다면 게이밍 의자가 편합니다. 둘 다 높이 조절과 회전을 지원하는 모델이 대부분이라 책상 환경에 맞춰 고르면 됩니다.

## 흔한 실수와 정리

디자인만 보고 고르면 여덟 시간 착좌에는 오히려 독이 됩니다. 허리 건강을 우선한다면 요추를 받쳐 주는 모델을 먼저 살펴보세요.
"""

BAD_BODY = "# 가이드\n\n의자를 고르는 방법을 간단히 정리한 글입니다.\n\n## 정리\n끝.\n"

SEO = {"primary": "사무용 의자", "secondary": []}


class TestRegenerate:
    def test_passes_first_attempt(self) -> None:
        def generate(_feedback: list[str] | None) -> tuple[str, str]:
            return TITLE, GOOD_BODY

        out = regenerate_until_seo_pass(generate, SEO)
        assert out["passed"] is True
        assert out["attempts"] == 1
        assert out["body_md"] == GOOD_BODY

    def test_recovers_on_second_attempt(self) -> None:
        calls: list[list[str] | None] = []

        def generate(feedback: list[str] | None) -> tuple[str, str]:
            calls.append(feedback)
            # 첫 시도(피드백 없음) 실패본 → 둘째 시도(피드백 받음) 통과본
            return (TITLE, BAD_BODY) if feedback is None else (TITLE, GOOD_BODY)

        out = regenerate_until_seo_pass(generate, SEO, max_attempts=3)
        assert out["passed"] is True
        assert out["attempts"] == 2
        assert calls[0] is None  # 첫 호출 피드백 없음
        assert calls[1] and len(calls[1]) > 0  # 둘째 호출에 게이트 issues 전달
        assert len(out["history"][0]) > 0  # 첫 시도는 issues 존재

    def test_exhausts_when_always_bad(self) -> None:
        def generate(_feedback: list[str] | None) -> tuple[str, str]:
            return TITLE, BAD_BODY

        out = regenerate_until_seo_pass(generate, SEO, max_attempts=2)
        assert out["passed"] is False
        assert out["attempts"] == 2
        assert len(out["history"]) == 2
        assert len(out["report"]["issues"]) > 0

    def test_feedback_is_previous_issues(self) -> None:
        seen: list[list[str] | None] = []

        def generate(feedback: list[str] | None) -> tuple[str, str]:
            seen.append(feedback)
            return TITLE, BAD_BODY

        out = regenerate_until_seo_pass(generate, SEO, max_attempts=2)
        # 둘째 호출 피드백 = 첫 시도 issues
        assert seen[1] == out["history"][0]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
