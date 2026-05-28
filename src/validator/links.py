"""links 게이트 — 단축 URL 차단·rel 검증·자동 실행 광고 차단.

출처: POLICY §6·§12 + VALIDATOR_PATTERNS §1·§2·§9 [확정].
"""

from __future__ import annotations

import re
from typing import Any

# VALIDATOR §1 — 외부 단축 URL 차단 도메인
SHORT_URL_DOMAINS = (
    r"vivoldi\.com",
    r"bit\.ly",
    r"goo\.gl",
    r"tinyurl\.com",
    r"t\.co",
    r"bitly\.com",
    r"rebrand\.ly",
    r"ow\.ly",
    r"is\.gd",
    r"cutt\.ly",
    r"me2\.do",
    r"n\.kakao\.com",  # DECISIONS K3 — POLICY §6-1 누락분 (세션 #5)
    r"naver\.me",  # DECISIONS K3 — 국내 단축 빈번 [관찰] (세션 #5)
)

# VALIDATOR §2 — 허용 도메인 (Phase 5 알리 추가 시 확장)
ALLOWED_LINK_DOMAINS = (
    r"honsalim\.com",
    r"link\.coupang\.com",
    r"partners\.coupang\.com",
    r"ads-partners\.coupang\.com",
)

# VALIDATOR §9 — 광고·게재 정책 위반 (자동 실행 광고)
FORBIDDEN_AD_PATTERNS = (
    r"<script[^>]+(popup|autoplay|hijack)",
    r'<iframe[^>]+style="[^"]*(top:|left:)[^"]*0',
)


def _check_short_urls(body_md: str) -> list[str]:
    issues: list[str] = []
    for pat in SHORT_URL_DOMAINS:
        if re.search(rf"https?://[^/\s]*{pat}", body_md):
            issues.append(f"short_url_blocked: {pat}")
    return issues


def _check_forbidden_ads(body_md: str) -> list[str]:
    return [f"forbidden_ad: {p}" for p in FORBIDDEN_AD_PATTERNS if re.search(p, body_md)]


def _check_external_rel(body_md: str) -> list[str]:
    """외부 링크의 rel='nofollow sponsored' 필수 (POLICY §6-3)."""
    issues: list[str] = []
    # <a ...href="https://host/..." ...> 태그를 모두 찾고, 자체 도메인 외 외부면 rel 검증
    for m in re.finditer(r'<a\b[^>]*\bhref="https?://([^/"\s]+)[^"]*"[^>]*>', body_md):
        host = m.group(1)
        if any(re.match(d, host) for d in ALLOWED_LINK_DOMAINS):
            continue
        tag = m.group(0)
        if "nofollow" not in tag or "sponsored" not in tag:
            issues.append(f"rel_missing: {host}")
    return issues


def check_links(body_md: str | None) -> tuple[bool, dict[str, Any]]:
    """links 게이트 검사.

    body_md: 본문 Markdown (HTML 허용).
    반환: (pass, {"issues": [...], "gate": "links"}).
    """
    if not body_md:
        return True, {"issues": [], "gate": "links"}

    issues: list[str] = []
    issues.extend(_check_short_urls(body_md))
    issues.extend(_check_forbidden_ads(body_md))
    issues.extend(_check_external_rel(body_md))

    return len(issues) == 0, {"issues": issues, "gate": "links"}
