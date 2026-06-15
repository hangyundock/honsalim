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


def _short_form(primary: str) -> str:
    """대표키워드의 대체용 줄임말 — 다단어면 마지막 토큰(예 '노트북 거치대'→'거치대'). 단일어면 그대로."""
    parts = primary.split()
    return parts[-1] if len(parts) > 1 else primary


def build_seo_directive(primary: str | None, secondary: Sequence[str] | None = None) -> str:
    """키워드 배치 지시 마크다운 블록 반환. primary 없으면 빈 문자열(지시 생략).

    세션 #19: 대표키워드 '통째 반복'을 줄이고 대체 표현을 쓰도록 구체화 — DeepSeek가
    키워드를 과다 반복(밀도 4~5%)해 SEO 게이트(상한 3.5%)에 걸리던 문제의 근본 지시(A).
    """
    primary = (primary or "").strip()
    if not primary:
        return ""
    secondary_list = [s.strip() for s in (secondary or []) if s and s.strip()]
    short = _short_form(primary)

    lines = [
        "## SEO 키워드 배치 (검색 노출 최적화 — 자연스럽게, 도배 절대 금지)",
        "",
        "아래 키워드는 실제 검색 수요가 있는 단어다. **자연스럽게** 본문에 녹여 검색 노출을 높여라.",
        "★과밀(도배)은 스팸 패널티이며, 본 작업에서 가장 흔한 실패 원인이다. 반드시 절제하라.",
        "",
        f'**대표키워드: "{primary}"** (정확형으로, 아래 밀도 범위 안에서 충분히)',
        f'- 제목 앞쪽 1회 + 도입부 첫 문단(앞 200자 이내) 1회 "{primary}"를 정확히 포함(필수).',
        f'- 소제목(##) 중 1~2개에 "{primary}"(또는 자연 변형)를 포함.',
        f'- 본문 전체에 "{primary}"를 정확형으로 자연스럽게 분산해 **밀도 1.0~1.7%를 확보**하라.'
        f" 본문이 길수록 더 여러 번 써야 한다 — ★하한 1.0% 미달도 탈락이니 충분히 쓸 것.",
        f'- 다만 밀도 3% 초과(도배·스팸)는 절대 금지 — 과해지면 "{short}"·대명사로 대체해 상한을 지켜라.',
        '- "무조건·절대·100%·반드시·최고·완벽" 등 단정·과장 표현 금지(정직성 게이트 — 위반 시 탈락).',
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
