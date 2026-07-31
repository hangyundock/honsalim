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
#
# ★세션 #48 — 'N년 사용' 패턴의 오탐 제거(기준 완화 아님, 주인 승인) **2차 근본수정**.
#   1차는 "경험 주장이 될 수 없는 꼬리(에/시/기간…)만 예외"라는 블랙리스트였는데, 라이브에서
#   곧바로 다른 형태("1~2년 사용 **후** 이동할 가능성이 높은 환경")가 새 오탐으로 재발했다 —
#   한국어의 비경험 꼬리는 열린 집합이라 나열로는 끝나지 않는다.
#   → 방향을 뒤집어 **경험을 주장하는 동사 활용형만** 잡는 화이트리스트로 고정한다.
#   'N년/N개월' 뒤에서 실제로 "내가 그 기간 써 봤다"를 뜻하려면 동사가 과거·시도·진행형이어야 한다:
#     막힘(경험 주장): "6개월 사용해보았습니다" · "3년 사용했습니다" · "2년 썼는데" ·
#                      "1년 사용해보니" · "3년 사용 중입니다"
#     통과(객관 서술): "1~2년 사용 후 이동" · "2~3년 사용에도 견고" · "3년 사용 시 마모" ·
#                      "2년 사용 기간" · "5년 사용할 수 있는" · "장기 사용하면 마모"
#   애매한 잔여 형태는 막히는 쪽으로 남는다(컴플라이언스는 fail-closed가 안전 방향).
#   '내/우리/써본/사용해보(니·면서)' 등 명시적 1인칭 표지는 아래 다른 패턴이 그대로 전부 잡는다.
FIRST_PERSON_PATTERNS = (
    r"써본 (결과|이후|후)",
    r"사용해보(니|면서)",
    r"내 (원룸|책상|방|집|자취)",
    r"우리(집|원룸)",
    r"(지난|작년) (여름|겨울|봄|가을)에 (사용|샀|샀더니)",
    r"(\d+개월|\d+년)\s*(?:썼|사용\s*(?:했|해\s*보|해\s*봤|중이|중입))",
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
