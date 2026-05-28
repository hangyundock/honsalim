"""disclosure 게이트 — 공정위 첫머리·푸터 문구.

출처: POLICY §2-2·§2-3 + VALIDATOR_PATTERNS §3 [확정].

첫머리 (200자 안):
- '쿠팡 파트너스' + '수수료' 모두 포함 필수

푸터 (마지막 800자 안):
- '쿠팡 파트너스' + 'AliExpress' + '본인' 모두 포함 필수
"""

from __future__ import annotations

from typing import Any

FIRST_REQUIRED = ("쿠팡 파트너스", "수수료")
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
    for keyword in FIRST_REQUIRED:
        if keyword not in head:
            issues.append(f"first_missing: {keyword}")
    for keyword in FOOTER_REQUIRED:
        if keyword not in tail:
            issues.append(f"footer_missing: {keyword}")

    return len(issues) == 0, {"issues": issues, "gate": "disclosure"}
