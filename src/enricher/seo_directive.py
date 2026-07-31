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

from validator.seo import DENSITY_CEIL, DENSITY_FLOOR, DENSITY_TARGET

from .keyword_density import join_josa, keyword_substitute, ns, per_1000_band


def build_seo_directive(
    primary: str | None,
    secondary: Sequence[str] | None = None,
    *,
    density_floor: float | None = None,
    density_ceil: float | None = None,
) -> str:
    """키워드 배치 지시 마크다운 블록 반환. primary 없으면 빈 문자열(지시 생략).

    세션 #19: 대표키워드 '통째 반복'을 줄이고 대체 표현을 쓰도록 구체화 — DeepSeek가
    키워드를 과다 반복(밀도 4~5%)해 SEO 게이트(상한 3.5%)에 걸리던 문제의 근본 지시(A).

    ★세션 #48: #19 지시가 라이브에서 반대로 작동한 두 지점을 근본수정한다.
    - "본문이 길수록 더 여러 번…충분히 쓸 것"이 **하한 미달을 막으려다 도배를 유발**했다.
      산문 길이를 모르는 첫 생성에 절대 횟수를 줄 수 없어 정성 표현을 쓴 것이 원인이므로,
      길이에 자동으로 비례하는 **'1,000자당 N~M회'** 밴드로 바꾼다(keyword_density).
    - "과해지면 <줄임말>로 대체하라"의 줄임말이 단일 토큰 키워드에서 **자기 자신**이라
      no-op였다(#48 적발). `keyword_substitute`로 실제 대체어를 주고, 없으면 그 줄을 뺀다.
    - 라이브에서 관찰된 도배 패턴(제품 문단·FAQ 답변마다 1~2회, 키워드를 제품 지칭 명사로
      사용)을 **금지 예시로 명시**한다 — 추상적 "도배 금지"로는 막히지 않았다.
    """
    primary = (primary or "").strip()
    if not primary:
        return ""
    secondary_list = [s.strip() for s in (secondary or []) if s and s.strip()]
    floor = float(density_floor or DENSITY_FLOOR)
    ceil = float(density_ceil or DENSITY_CEIL)
    kw_len = max(1, len(ns(primary)))
    low, high = per_1000_band(kw_len, floor, ceil, DENSITY_TARGET)
    substitute = keyword_substitute(primary)

    lines = [
        "## SEO 키워드 배치 (검색 노출 최적화 — 아래 필수 조건을 정확히 맞출 것)",
        "",
        "아래 키워드는 실제 검색 수요가 있는 단어다. **자연스럽게** 본문에 녹여 검색 노출을 높여라.",
        "★**너무 적어도(미달) 너무 많아도(도배) 똑같이 탈락한다.** 한쪽만 피하려다 반대쪽으로",
        "  넘어가는 것이 가장 흔한 실패다 — 아래 숫자 범위 **안**에 들어오게 맞춰라.",
        "",
        f'**대표키워드: "{primary}"** (정확형) — 아래 3개는 **전부 필수**, 하나라도 어기면 탈락한다.',
        f'- (필수) 제목 앞쪽 1회 + 도입부 첫 문단(앞 200자 이내) 1회 "{primary}"를 정확히 포함.',
        f'- (필수) 소제목(##) **최소 1개**에 "{primary}"를 글자 그대로 포함 — **0개면 탈락**.',
        "  다만 3개 이상은 도배이니 1~2개까지만.",
        f"- (필수) 분량: 본문 1,000자당 **최소 {low}회 이상 ~ 최대 {high}회 이하**. "
        f"**{low}회 미만이면 '미달'로 탈락**하고 **{high}회 초과면 '도배'로 탈락**한다. "
        "본문이 길어지면 이 비율만 유지하면 된다.",
        "",
        "★위 필수 조건은 지키되, 아래 방식으로 채우면 '도배'로 탈락한다:",
        f'- ❌ 상품 소개 문단마다 "{primary}"를 넣기 · ❌ FAQ 답변마다 "{primary}"를 넣기',
        f'- ❌ 소제목 3개 이상에 "{primary}"를 넣기(1~2개까지만 — 0개도 탈락이다).',
        f'- ❌ "{primary}"를 **상품을 가리키는 명사**로 쓰기 — 이것이 가장 흔한 도배 형태다.',
    ]
    if substitute:
        bad = join_josa(primary, "이다")
        good = join_josa(substitute, "이다")
        lines += [
            f'  ✗ "가성비 높은 {bad}" / "수납형 소형 {primary}" '
            f'→ ✅ "가성비 높은 {good}" / "수납형 소형 {substitute}"',
            # ★#48 라이브 적발: "두 번째 언급부터는 대체어로"라고 쓰자 모델이 **전부** 바꿔
            #   0.78%까지 떨어져 하한 미달로 탈락했다. 대체는 상한을 지킬 때만 쓰는 수단이다.
            f'- 위 최소 횟수를 채운 **뒤**, 그래도 반복이 과하면 그때만 "{substitute}"·"이 제품"·'
            f"대명사로 바꿔라. **전부 바꾸면 하한 미달로 탈락한다.**",
        ]
    else:
        lines += [
            '- 위 최소 횟수를 채운 **뒤**, 그래도 반복이 과하면 그때만 "이 제품"·"해당 상품"·'
            "대명사로 바꿔라. **전부 바꾸면 하한 미달로 탈락한다.**",
        ]
    lines += [
        '- "무조건·절대·100%·반드시·최고·완벽" 등 단정·과장 표현 금지(정직성 게이트 — 위반 시 탈락).',
        "- 1인칭·직접 사용경험('N년 사용'·'써보니') 금지 — 'N년 내구성'처럼 객관 서술로(위반 시 탈락).",
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
