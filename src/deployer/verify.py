"""deployer.verify — 배포 후 URL HEAD 검증.

출처: BACKEND §2-7 [확정].

requests 라이브러리 의존 — 미설치 시 RuntimeError.
실제 HTTP 호출이지만 read-only HEAD라 dry_run 인자는 선택.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerifyResult:
    """배포 검증 결과."""

    ok: bool
    status_code: int | None
    url: str
    error: str | None = None


def verify_deploy(
    url: str,
    *,
    expected_status: int = 200,
    timeout: float = 5.0,
    dry_run: bool = False,
) -> VerifyResult:
    """URL에 HEAD 요청 → expected_status 일치 여부.

    인자:
        url: 검증할 절대 URL (https:// 또는 http://)
        expected_status: 기대 HTTP 상태 코드 (기본 200)
        timeout: HTTP 타임아웃 (초)
        dry_run: True면 실제 호출 없이 plan만 반환

    반환: VerifyResult.

    Raises:
        ValueError: url 빈 값 또는 형식 오류
        RuntimeError: requests SDK 미설치
    """
    if not url:
        raise ValueError("url 빈 값")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"url 형식 오류 (http:// 또는 https:// 필요): {url}")

    if dry_run:
        return VerifyResult(
            ok=True,
            status_code=None,
            url=url,
            error=f"[DRY] would HEAD {expected_status}",
        )

    try:
        import requests
    except ImportError as e:
        raise RuntimeError("requests SDK 미설치 — pip install requests") from e

    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
    except Exception as e:  # — requests 예외 다양, 모두 fail로 분류
        return VerifyResult(ok=False, status_code=None, url=url, error=f"{type(e).__name__}: {e}")

    return VerifyResult(
        ok=(resp.status_code == expected_status),
        status_code=resp.status_code,
        url=url,
    )
