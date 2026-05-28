"""truth 게이트 — 가격·재고·1인칭·AI 흔적·단정형.

출처: POLICY §3 + VALIDATOR_PATTERNS §4·§5·§6·§7 [확정].
Phase 2 stub: hard 패턴 + 가격·단정형 구현. soft 임계 튜닝은 후속.
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


def check_truth(payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """truth 게이트 검사.

    payload: body_md + products (가격 검증용).
    반환: (pass, {"issues": [...], "gate": "truth"}).
    """
    body_md = payload.get("body_md") or ""
    products = payload.get("products") or []

    issues: list[str] = []
    issues.extend(_check_ai_trace(body_md))
    issues.extend(_check_absolute(body_md))
    issues.extend(_check_prices(body_md, products))

    return len(issues) == 0, {"issues": issues, "gate": "truth"}
