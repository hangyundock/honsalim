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


def _check_first_person(body_md: str, owned_products: list[str]) -> list[str]:
    """1인칭 검출 시 owned_products 메타 없으면 fail (DECISIONS L3 [확정 세션 #6]).

    위키바이형 정보 분석 톤 기본. owned_products 비어 있으면 1인칭 자동 차단.
    owned_products 명시되면 1인칭 액센트 허용 (본인 실보유 5~10개 제품).
    """
    if owned_products:
        return []
    for pat in FIRST_PERSON_PATTERNS:
        m = re.search(pat, body_md)
        if m:
            return [f"first_person_without_owned_products: {m.group()}"]
    return []


def _has_user_photo(payload: dict[str, Any]) -> bool:
    """payload에서 페르소나 사진 보유 여부 추출 (L2 [확정 세션 #6]).

    photos 리스트 또는 has_user_photo 플래그 모두 지원.
    페르소나 사진 6~9장 사이트 풀에서 1+ 참조 시 True.
    """
    photos = payload.get("photos")
    if isinstance(photos, list) and len(photos) > 0:
        return True
    return bool(payload.get("has_user_photo"))


def _owned_products(payload: dict[str, Any]) -> list[str]:
    """payload에서 owned_products SKU 리스트 추출 (L3 [확정 세션 #6])."""
    owned = payload.get("owned_products")
    if isinstance(owned, list):
        return [str(s) for s in owned if s]
    return []


def check_truth(payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """truth 게이트 검사 (DECISIONS L1·L2·L3 [확정 세션 #6 재설계]).

    payload 기대 키:
    - body_md         : 본문 Markdown
    - products        : [{id, price_krw, ...}, ...] 가격 검증용
    - photos          : list — 페르소나 사진 풀 참조 (L2)
    - has_user_photo  : bool — photos 대신 boolean (POLICY 코드 예시)
    - owned_products  : list[str] — 본인 실보유 제품 SKU (L3, 1인칭 액센트 허용 조건)

    반환: (pass, {"issues": [...], "gate": "truth"}).
    """
    body_md = payload.get("body_md") or ""
    products = payload.get("products") or []
    owned = _owned_products(payload)

    issues: list[str] = []
    issues.extend(_check_ai_trace(body_md))
    issues.extend(_check_ai_trace_soft(body_md))
    issues.extend(_check_absolute(body_md))
    issues.extend(_check_prices(body_md, products))
    issues.extend(_check_first_person(body_md, owned))

    return len(issues) == 0, {"issues": issues, "gate": "truth"}
