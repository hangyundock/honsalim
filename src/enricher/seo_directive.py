"""seo_directive — 2층 키워드 배치 지시 빌더 (enrich 프롬프트 주입용). 세션 #15.

대표키워드(primary) + 보조키워드(secondary, 네이버 연관검색어) 세트를 받아,
콘텐츠 생성 프롬프트에 끼워 넣을 **키워드 배치 지시** 마크다운 블록을 만든다.

배치 전략(역제안 ①·②, 사용자 합의):
- 대표키워드 = 제목 앞·도입부·소제목 + ~2% 밀도 (validator/seo.py 게이트가 측정).
- 보조키워드 = 페이지 구조(타입·티어·FAQ·체크포인트)에 **각 1회씩 자연 분산** — 한 단어 도배 대신
  여러 수익 키워드를 잡되 과밀(스팸) 금지.

이 빌더는 텍스트만 생성한다. 실제 게이트 통과 여부는 validator/seo.py가 검증·재생성 유도한다.
"""

from __future__ import annotations

from collections.abc import Sequence


def build_seo_directive(primary: str | None, secondary: Sequence[str] | None = None) -> str:
    """키워드 배치 지시 마크다운 블록 반환. primary 없으면 빈 문자열(지시 생략)."""
    primary = (primary or "").strip()
    if not primary:
        return ""
    secondary_list = [s.strip() for s in (secondary or []) if s and s.strip()]

    lines = [
        "## SEO 키워드 배치 (검색 노출 최적화 — 자연스럽게, 도배 금지)",
        "",
        "아래 키워드는 실제 검색 수요가 있는 단어다. **자연스럽게** 본문에 녹여 검색 노출을 높여라.",
        "과밀(도배)은 오히려 스팸 패널티이니 금지한다.",
        "",
        f'**대표키워드: "{primary}"** (검색 노출의 핵심 — 이것만큼은 확실히)',
        f'- 제목 앞쪽 + 도입부 첫 문단에 반드시 "{primary}"를 포함.',
        f'- 소제목(##)에 "{primary}"(또는 자연스러운 변형)를 1~2개 포함.',
        f'- 본문 전체에서 정확히 "{primary}" 형태로 **약 1.7% 밀도(네이버 기준, 과하지 않게)**로 반복.',
    ]

    if secondary_list:
        lines += [
            "",
            "**보조키워드 (각각 최소 1회 자연 노출 — 관련 맥락에 녹일 것):**",
        ]
        lines += [f"- {kw}" for kw in secondary_list]
        lines += [
            "",
            "보조키워드 배치 원칙:",
            "- 타입 설명·티어(실속/고급)·비교·FAQ·추천 대상 등 **맥락이 맞는 자리**에 녹여라.",
            "- 의미가 안 맞는 키워드는 생략 가능(자연스러움 > 전부 욱여넣기). 단 과반 이상은 다뤄라.",
            "- 억지 나열·반복 금지. 1인칭·과장·단정 금지 규칙은 그대로 적용.",
        ]

    return "\n".join(lines)
