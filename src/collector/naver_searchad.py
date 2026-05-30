"""네이버 검색광고 키워드도구 클라이언트 — 연관검색어 + 월 검색량 + 경쟁도.

출처: AutoBlog `tistory_revival/keyword_sources.py` (라이브 검증된 클라이언트, 세션 #15 미러).
엔드포인트: ``GET https://api.searchad.naver.com/keywordstool`` — HMAC-SHA256 서명.

용도(세션 #15 카테고리 페이지 SEO):
- 대표키워드(예: "사무용 의자")로 **연관검색어 + 실제 월 검색량 + 경쟁도**를 받아
  수익성 보조키워드를 데이터로 선별 → seo 게이트(`validator/seo.py`)에 주입.

자격증명 (``D:\\secrets\\affiliate_hub\\naver_searchad.env`` — common.config.load_secrets가 자동 로드):
- ``NAVER_SEARCHAD_API_KEY`` · ``NAVER_SEARCHAD_SECRET_KEY`` · ``NAVER_SEARCHAD_CUSTOMER_ID``

서명 (검증됨):
- ``msg = f"{timestamp}.{method}.{path}"`` → HMAC-SHA256(secret_key) → base64.
- 헤더: X-Timestamp · X-API-KEY · X-Customer · X-Signature.

모드:
- ``dry_run=True`` (기본): HTTP 없이 서명된 요청만 빌드 — 키 없이 구조/서명 검증, 비용 0.
- ``dry_run=False`` (live): 실제 호출(읽기 전용 키워드 조회 — 게시 아님).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SEARCHAD_BASE = "https://api.searchad.naver.com"
KEYWORDSTOOL_PATH = "/keywordstool"

ENV_API_KEY = "NAVER_SEARCHAD_API_KEY"
ENV_SECRET_KEY = "NAVER_SEARCHAD_SECRET_KEY"  # noqa: S105  (env var 이름, 시크릿 값 아님)
ENV_CUSTOMER_ID = "NAVER_SEARCHAD_CUSTOMER_ID"


class NaverSearchAdError(RuntimeError):
    """검색광고 API 호출 실패 (자격증명 누락·HTTP 오류 등)."""


def signature(timestamp: str, method: str, path: str, secret_key: str) -> str:
    """검색광고 HMAC-SHA256 서명 (base64). msg = '{ts}.{method}.{path}'."""
    msg = f"{timestamp}.{method}.{path}"
    digest = hmac.new(secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def build_keywordstool_request(
    keyword: str,
    *,
    api_key: str,
    customer_id: str,
    secret_key: str,
    timestamp: str,
) -> dict[str, Any]:
    """keywordstool GET 요청 구성요소를 dict로 반환 (dry_run 검증·테스트용).

    검색엔진 매칭과 동일하게 hintKeywords는 공백 제거. showDetail=1로 검색량/경쟁도 포함.
    """
    params = {"hintKeywords": keyword.replace(" ", ""), "showDetail": "1"}
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": str(customer_id),
        "X-Signature": signature(timestamp, "GET", KEYWORDSTOOL_PATH, secret_key),
    }
    return {
        "method": "GET",
        "url": SEARCHAD_BASE + KEYWORDSTOOL_PATH,
        "path": KEYWORDSTOOL_PATH,
        "headers": headers,
        "params": params,
    }


def to_int(value: Any) -> int:
    """검색량 파싱 — '< 10', '1,234' 등 비정수 표기를 안전하게 정수화 (실패 시 0)."""
    try:
        return int(str(value).replace("<", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    """keywordList 원소 → {keyword, volume(PC+모바일), competition} 정규화."""
    return {
        "keyword": (item.get("relKeyword") or "").strip(),
        "volume": to_int(item.get("monthlyPcQcCnt")) + to_int(item.get("monthlyMobileQcCnt")),
        "competition": item.get("compIdx", "unknown"),
    }


def _creds() -> tuple[str, str, str]:
    """os.environ에서 자격증명 로드 (common.config.load_secrets 선행 가정). 누락 시 에러."""
    api_key = os.environ.get(ENV_API_KEY, "")
    secret_key = os.environ.get(ENV_SECRET_KEY, "")
    customer_id = os.environ.get(ENV_CUSTOMER_ID, "")
    missing = [
        name
        for name, val in (
            (ENV_API_KEY, api_key),
            (ENV_SECRET_KEY, secret_key),
            (ENV_CUSTOMER_ID, customer_id),
        )
        if not val
    ]
    if missing:
        raise NaverSearchAdError(
            "네이버 검색광고 자격증명 누락: "
            + ", ".join(missing)
            + " (D:\\secrets\\affiliate_hub\\naver_searchad.env 확인)"
        )
    return api_key, secret_key, customer_id


def fetch_related_keywords(
    keyword: str,
    *,
    dry_run: bool = True,
    retries: int = 2,
    backoff: int = 30,
    timeout: int = 15,
) -> list[dict[str, Any]]:
    """연관검색어 + 검색량 정규화 리스트 반환.

    dry_run=True: HTTP 없이 빌드된 요청을 단일 원소로 반환 ``[{"dry_run": True, "request": {...}}]``.
        자격증명이 있으면 실제 서명을 쓰고, 없으면 더미 자격으로 구조만 빌드(테스트 가능).
    dry_run=False: 실제 호출 → normalize된 [{keyword, volume, competition}, ...].
        429(rate limit)는 backoff 후 재시도.
    """
    if dry_run:
        try:
            api_key, secret_key, customer_id = _creds()
        except NaverSearchAdError:
            api_key, secret_key, customer_id = "DRYRUN_KEY", "DRYRUN_SECRET", "0"
        req = build_keywordstool_request(
            keyword,
            api_key=api_key,
            customer_id=customer_id,
            secret_key=secret_key,
            timestamp=str(round(time.time() * 1000)),
        )
        return [{"dry_run": True, "request": req}]

    api_key, secret_key, customer_id = _creds()
    for attempt in range(retries + 1):
        ts = str(round(time.time() * 1000))
        req = build_keywordstool_request(
            keyword,
            api_key=api_key,
            customer_id=customer_id,
            secret_key=secret_key,
            timestamp=ts,
        )
        qs = urllib.parse.urlencode(req["params"])
        http_req = urllib.request.Request(  # noqa: S310 (https 고정 URL)
            f"{req['url']}?{qs}", headers=req["headers"], method="GET"
        )
        try:
            with urllib.request.urlopen(http_req, timeout=timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            return [normalize(it) for it in data.get("keywordList", [])]
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries:
                time.sleep(backoff)
                continue
            raise NaverSearchAdError(f"검색광고 HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise NaverSearchAdError(f"검색광고 연결 실패: {exc.reason}") from exc
    return []
