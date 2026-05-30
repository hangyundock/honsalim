"""category_writer — 카테고리 페이지 구매가이드 본문 생성 (세션 #15).

카테고리(예 "컴퓨터 책상")의 전문 8요소 가이드 산문을 운영자 "혼살다" 명의로 Sonnet 생성.
seo_keywords.gate_config({primary, secondary})를 받아 2층 키워드 배치 지시를 프롬프트에 주입하고,
enricher.seo_regenerate.regenerate_until_seo_pass로 SEO 게이트 통과까지 재생성(비용 상한 내).

상품 비교 카드·한눈비교표 등 12컴포넌트는 렌더러가 별도 결합 — 본 모듈은 **산문(8요소)** 담당.
출력은 "# 제목"으로 시작하는 마크다운(게이트의 _split_title_body가 제목/산문 분리).
"""

from __future__ import annotations

from typing import Any

from . import prompt_loader
from .seo_directive import build_seo_directive

# 정직한 큐레이터 페르소나 — AI 표기·1인칭 경험 금지(게이트와 정합).
CATEGORY_SYSTEM = (
    "당신은 1인 가구·홈오피스 살림 정보를 정직하게 큐레이션하는 한국어 에디터입니다. "
    "운영자 '혼살다' 명의로, 과장 없이 정확하고 실용적인 구매 가이드를 씁니다. "
    "직접 사용 경험을 지어내지 않고(1인칭 사용기 금지), 가짜 평점·후기·수치를 만들지 않습니다."
)


def build_category_prompt(
    category_name: str, seo: dict[str, Any], feedback: list[str] | None = None
) -> str:
    """카테고리 가이드 user 프롬프트 조립 (seo 2층 배치 지시 주입 + 재생성 피드백)."""
    directive = build_seo_directive(seo.get("primary"), seo.get("secondary"))
    prompt = prompt_loader.render(
        "category_guide",
        category_name=category_name,
        primary=seo.get("primary", ""),
        seo_directive=directive,
    )
    if feedback:
        prompt += "\n\n[지난 생성의 SEO 미달 — 반드시 보완]\n- " + "\n- ".join(feedback)
    return prompt


def generate_category_guide(
    client: Any,
    category_name: str,
    seo: dict[str, Any],
    *,
    feedback: list[str] | None = None,
    dry_run: bool = True,
) -> Any:
    """카테고리 가이드 1회 생성. client = ClaudeClient. 반환 = GenerateResult.

    응답 본문(response_text)이 "# 제목 + 마크다운". 호출 측이 regenerate 루프로 감쌀 수 있다.
    """
    user_prompt = build_category_prompt(category_name, seo, feedback)
    return client.generate_raw(CATEGORY_SYSTEM, user_prompt, dry_run=dry_run)
