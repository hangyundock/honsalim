"""truth 게이트 — 가격·재고·1인칭·AI 흔적·단정형.

출처: POLICY §3 + VALIDATOR_PATTERNS §4·§5·§6·§7 [확정].
세션 #4: hard 패턴 + 가격 + 단정형 + 1인칭/사진 게이트 + AI soft 임계 구현.
"""

from __future__ import annotations

import re
from typing import Any

# VALIDATOR §4 — AI 흔적 hard 패턴 (정합 시 fail)
AI_TRACE_PATTERNS_HARD = (
    r"본 글은 AI(가|로) ",
    r"ChatGPT(로|가) (작성|생성)",
    r"As an AI",
    r"I cannot ",
    r"다음은 [가-힣\s]{1,20} 입니다[:.]",
    r"\*\*\*+",
    r"\$\$",
)

# VALIDATOR §4 — AI 흔적 soft 패턴 (임계 이상 등장 시 fail) [관찰]
AI_TRACE_PATTERNS_SOFT: tuple[tuple[str, int], ...] = (
    (r"~로 알려져 있습니다", 3),
    (r"(훌륭한|완벽한|최고의)", 5),
)

# VALIDATOR §5 — 1인칭 표현 (POLICY §3-1-3 [확정] — 직접 사진 없을 시 fail)
FIRST_PERSON_PATTERNS = (
    r"써본 (결과|이후|후)",
    r"사용해보(니|면서)",
    r"내 (원룸|책상|방|집|자취)",
    r"우리(집|원룸)",
    r"(지난|작년) (여름|겨울|봄|가을)에 (사용|샀|샀더니)",
    r"(\d+개월|\d+년) (사용|썼)",
)

# VALIDATOR §7 — 단정형·과장 (POLICY §3-1-5 그대로)
ABSOLUTE_FORBIDDEN = (
    r"100% 효과",
    r"절대 안전",
    r"무조건 (\w+)",
    r"반드시 (낫는|치료|효과)",
    r"병이 (낫는|치료)",
    r"건강에 (좋다|특효)",
)

PRICE_TOLERANCE = 0.05  # POLICY §3-1-1 — collector 가격 ±5%


def _check_ai_trace(body_md: str) -> list[str]:
    return [f"ai_trace_hard: {p}" for p in AI_TRACE_PATTERNS_HARD if re.search(p, body_md)]


def _check_ai_trace_soft(body_md: str) -> list[str]:
    """AI 흔적 soft 패턴 — 임계 이상 등장 시 fail (VALIDATOR §4 [관찰])."""
    issues: list[str] = []
    for pat, threshold in AI_TRACE_PATTERNS_SOFT:
        count = len(re.findall(pat, body_md))
        if count >= threshold:
            issues.append(f"ai_trace_soft: {pat} ({count}>={threshold})")
    return issues


def _check_absolute(body_md: str) -> list[str]:
    return [f"absolute_forbidden: {p}" for p in ABSOLUTE_FORBIDDEN if re.search(p, body_md)]


def _check_prices(body_md: str, products: list[dict[str, Any]]) -> list[str]:
    if not products:
        return []
    body_prices: list[int] = []
    for m in re.findall(r"([\d,]+)\s*원", body_md):
        try:
            body_prices.append(int(m.replace(",", "")))
        except ValueError:
            continue
    issues: list[str] = []
    for p in products:
        target = p.get("price_krw")
        if not target:
            continue
        if not any(abs(bp - target) / target <= PRICE_TOLERANCE for bp in body_prices):
            issues.append(f"price_mismatch: product_id={p.get('id')}")
    return issues


def _check_first_person(body_md: str) -> list[str]:
    """1인칭 표현 무조건 fail (DECISIONS L3·L5 [확정 세션 #6 2차 재변경]).

    사용자 직접 사진 없음 + AI 생성 이미지 결정 → AI 이미지로 1인칭 = 거짓 광고.
    위키바이형 정보 분석 톤 강제. owned_products 메타 우회 폐기.
    """
    for pat in FIRST_PERSON_PATTERNS:
        m = re.search(pat, body_md)
        if m:
            return [f"first_person_forbidden: {m.group()}"]
    return []


def check_truth(payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """truth 게이트 검사 (DECISIONS L1·L2·L3·L5 [확정 세션 #6 2차]).

    payload 기대 키:
    - body_md         : 본문 Markdown
    - products        : [{id, price_krw, ...}, ...] 가격 검증용

    반환: (pass, {"issues": [...], "gate": "truth"}).
    """
    body_md = payload.get("body_md") or ""
    products = payload.get("products") or []

    issues: list[str] = []
    issues.extend(_check_ai_trace(body_md))
    issues.extend(_check_ai_trace_soft(body_md))
    issues.extend(_check_absolute(body_md))
    issues.extend(_check_prices(body_md, products))
    issues.extend(_check_first_person(body_md))

    return len(issues) == 0, {"issues": issues, "gate": "truth"}
