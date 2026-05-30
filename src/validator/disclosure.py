"""disclosure 게이트 — 공정위 첫머리·푸터 문구.

출처: POLICY §2-2·§2-3 + VALIDATOR_PATTERNS §3 [확정].

첫머리 (200자 안) — 제휴처 인지형 [확정 2026-05-30, 알리 우선 전환 반영]:
- '수수료' 필수 + 제휴처명('쿠팡 파트너스' 또는 'AliExpress') **최소 1개** 포함.
  글이 실제 추천한 상품의 제휴처를 정확히 공시(공정위 정확성). 알리 글엔 알리 명시 가능.

푸터 (마지막 800자 안) — 사이트 전체 정책이라 둘 다 명시:
- '쿠팡 파트너스' + 'AliExpress' + '본인' 모두 포함 필수
"""

from __future__ import annotations

from typing import Any

# 첫머리: 수수료(대가성) 필수 + 제휴처명 최소 1개
FIRST_FEE_KEYWORD = "수수료"
FIRST_AFFILIATE_NAMES = ("쿠팡 파트너스", "AliExpress")
FOOTER_REQUIRED = ("쿠팡 파트너스", "AliExpress", "본인")

HEAD_LEN = 200
TAIL_LEN = 800


def check_disclosure(body_md: str | None) -> tuple[bool, dict[str, Any]]:
    """disclosure 게이트 검사.

    body_md: 본문 Markdown.
    반환: (pass, {"issues": [...], "gate": "disclosure"}).
    """
    if not body_md:
        return False, {"issues": ["body_missing"], "gate": "disclosure"}

    head = body_md[:HEAD_LEN]
    tail = body_md[-TAIL_LEN:]

    issues: list[str] = []
    # 첫머리: 대가성(수수료) + 제휴처명 최소 1개
    if FIRST_FEE_KEYWORD not in head:
        issues.append(f"first_missing: {FIRST_FEE_KEYWORD}")
    if not any(name in head for name in FIRST_AFFILIATE_NAMES):
        issues.append("first_missing: affiliate_name(쿠팡 파트너스 또는 AliExpress)")
    # 푸터: 사이트 전체 정책 — 둘 다 명시
    for keyword in FOOTER_REQUIRED:
        if keyword not in tail:
            issues.append(f"footer_missing: {keyword}")

    return len(issues) == 0, {"issues": issues, "gate": "disclosure"}
