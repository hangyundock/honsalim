"""tracker.gsc — Google Search Console 검색 성과 조회 (세션 #52 신설).

목적: 순위·노출·클릭 데이터를 사람 스크린샷 없이 코드로 읽는다 — 주간 무인 운영
세션(성장 분석)의 데이터 열쇠. GSC API는 무료(쿼터만 존재·본 규모 무관).

인증 = **서비스 계정** (무인 최적 — 브라우저 동의·토큰 갱신 없음):
1. Google Cloud 콘솔(기존 `review-helpfulknow` 프로젝트)에서 Search Console API 활성화
2. 서비스 계정 생성 → JSON 키 다운로드 → ``D:\\secrets\\affiliate_hub\\gsc_service_account.json``
3. 서치콘솔 속성 설정 → 사용자 추가에 서비스 계정 이메일(…@….iam.gserviceaccount.com) 등록
   (권한 '전체' 불요 — '제한된' 권한으로 충분, 읽기 전용 스코프만 쓴다)

의존성: google-auth (이미 설치 — Imagen 스택 동반. §12 환경 변경 없음). 새 패키지 0.

★ 데이터 지연: GSC 성과 데이터는 보통 2~3일 늦게 채워진다 — 조회 창의 끝을
오늘-2일로 잡지 않으면 최신 구간이 0으로 나와 "트래픽 급락"으로 오판한다.
"""

from __future__ import annotations

import datetime as dt
import os
import urllib.parse
from pathlib import Path
from typing import Any

from common import config

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
API_BASE = "https://searchconsole.googleapis.com/webmasters/v3"

ENV_KEY_PATH = "GSC_SERVICE_ACCOUNT_JSON"
ENV_SITE_URL = "GSC_SITE_URL"
DEFAULT_KEY_FILENAME = "gsc_service_account.json"
# 속성 유형이 다르면(URL 접두어) gsc.env의 GSC_SITE_URL로 오버라이드. --list-sites로 실값 확인.
DEFAULT_SITE_URL = "sc-domain:honsallim.com"

DATA_LAG_DAYS = 2  # 최신 2일은 GSC가 아직 집계 전 — 창 끝을 이만큼 당긴다
PAGE_ROW_LIMIT = 5000  # searchAnalytics.query 1회 최대 25,000 — 본 규모엔 5천이면 1페이지 종결


class GscError(RuntimeError):
    """GSC 호출 실패 (키 파일 누락·권한 미등록·속성 불일치 등) — 메시지에 조치 포함."""


def key_path() -> Path:
    """서비스 계정 JSON 경로 — env 오버라이드 없으면 secrets 폴더 기본 파일명."""
    override = os.environ.get(ENV_KEY_PATH, "").strip()
    if override:
        return Path(override)
    return config.SECRETS_DIR / DEFAULT_KEY_FILENAME


def site_url() -> str:
    """조회 대상 속성 — env(GSC_SITE_URL) 오버라이드 없으면 도메인 속성 기본값."""
    return os.environ.get(ENV_SITE_URL, "").strip() or DEFAULT_SITE_URL


def build_session(path: Path | None = None) -> Any:
    """서비스 계정 자격으로 AuthorizedSession 생성. 키 파일 없으면 조치 포함 GscError."""
    p = path or key_path()
    if not p.exists():
        raise GscError(
            f"서비스 계정 키 파일 없음: {p} — Google Cloud 콘솔에서 서비스 계정 JSON 키를 "
            "내려받아 이 경로에 두고, 서치콘솔 속성 '사용자 및 권한'에 서비스 계정 이메일을 "
            "추가하세요 (tracker/gsc.py 머리 주석의 3단계)."
        )
    # 지연 임포트 — google 스택은 이 함수를 실제 쓸 때만 필요(doctor 진입점 임포트 무부담).
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(str(p), scopes=SCOPES)
    return AuthorizedSession(creds)


def _check(resp: Any, *, context: str) -> dict[str, Any]:
    """HTTP 응답 → dict. 403/404는 원인별 조치 문구로 승격 (fail-loud)."""
    code = int(getattr(resp, "status_code", 0) or 0)
    if code == 403:
        raise GscError(
            f"{context}: 403 권한 거부 — ①서치콘솔 속성 '사용자 및 권한'에 서비스 계정 "
            "이메일을 추가했는지 ②Cloud 프로젝트에서 Search Console API를 활성화했는지 확인."
        )
    if code == 404:
        raise GscError(
            f"{context}: 404 속성 없음 — 속성 URL('{site_url()}')이 서치콘솔 실제 속성과 "
            "다름. `gsc-report --list-sites`로 실값을 확인해 gsc.env의 GSC_SITE_URL로 지정."
        )
    if code >= 400:
        raise GscError(f"{context}: HTTP {code} — {getattr(resp, 'text', '')[:200]}")
    data = resp.json()
    return data if isinstance(data, dict) else {}


def _site_path(site: str) -> str:
    return f"{API_BASE}/sites/{urllib.parse.quote(site, safe='')}"


def list_sites(session: Any = None) -> list[dict[str, Any]]:
    """서비스 계정이 접근 가능한 속성 목록 — 연동 검증용."""
    s = session or build_session()
    data = _check(s.get(f"{API_BASE}/sites"), context="sites.list")
    entries = data.get("siteEntry") or []
    return [e for e in entries if isinstance(e, dict)]


def list_sitemaps(site: str | None = None, session: Any = None) -> list[dict[str, Any]]:
    """제출된 sitemap 목록(제출/색인 수 포함) — 색인 커버리지 근사치."""
    s = session or build_session()
    target = site or site_url()
    data = _check(s.get(f"{_site_path(target)}/sitemaps"), context="sitemaps.list")
    return [e for e in (data.get("sitemap") or []) if isinstance(e, dict)]


def query(
    start_date: dt.date,
    end_date: dt.date,
    *,
    dimensions: tuple[str, ...] = ("query",),
    site: str | None = None,
    row_limit: int = PAGE_ROW_LIMIT,
    session: Any = None,
) -> list[dict[str, Any]]:
    """searchAnalytics.query — startRow 페이지네이션 포함, rows 정규화 반환."""
    s = session or build_session()
    target = site or site_url()
    url = f"{_site_path(target)}/searchAnalytics/query"
    out: list[dict[str, Any]] = []
    start_row = 0
    while True:
        payload = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": list(dimensions),
            "rowLimit": row_limit,
            "startRow": start_row,
        }
        data = _check(s.post(url, json=payload), context="searchAnalytics.query")
        rows = data.get("rows") or []
        for r in rows:
            out.append(
                {
                    "keys": list(r.get("keys") or []),
                    "clicks": int(r.get("clicks") or 0),
                    "impressions": int(r.get("impressions") or 0),
                    "ctr": float(r.get("ctr") or 0.0),
                    "position": float(r.get("position") or 0.0),
                }
            )
        if len(rows) < row_limit:
            return out
        start_row += len(rows)


def window(days: int, *, today: dt.date | None = None) -> tuple[dt.date, dt.date]:
    """조회 창 [start, end] — 끝은 오늘-DATA_LAG_DAYS (지연 데이터 0 오판 방지)."""
    base = today or dt.date.today()
    end = base - dt.timedelta(days=DATA_LAG_DAYS)
    return end - dt.timedelta(days=max(1, days) - 1), end


def _totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    """clicks/impressions 합 + 노출 가중 평균 순위 + ctr."""
    clicks = sum(r["clicks"] for r in rows)
    imps = sum(r["impressions"] for r in rows)
    pos = sum(r["position"] * r["impressions"] for r in rows) / imps if imps else 0.0
    return {
        "clicks": float(clicks),
        "impressions": float(imps),
        "ctr": (clicks / imps) if imps else 0.0,
        "position": pos,
    }


def summary(
    days: int = 28, *, site: str | None = None, session: Any = None, top: int = 25
) -> dict[str, Any]:
    """기간 총계 + 최근7일 vs 이전7일 추이 + 상위 쿼리/페이지 + sitemap 색인 근사.

    무인 세션이 그대로 소비할 수 있는 dict (CLI --json이 이 구조를 출력).
    """
    s = session or build_session()
    target = site or site_url()
    start, end = window(days)
    by_date = query(start, end, dimensions=("date",), site=target, session=s)
    by_date.sort(key=lambda r: r["keys"][0] if r["keys"] else "")

    result: dict[str, Any] = {
        "site": target,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": days,
        "totals": _totals(by_date),
        "by_date": by_date,
        "trend": None,
        "top_queries": query(start, end, dimensions=("query",), site=target, session=s)[:top],
        "top_pages": query(start, end, dimensions=("page",), site=target, session=s)[:top],
    }
    if days >= 14:
        cut = (end - dt.timedelta(days=6)).isoformat()
        prev_cut = (end - dt.timedelta(days=13)).isoformat()
        last7 = [r for r in by_date if r["keys"] and r["keys"][0] >= cut]
        prev7 = [r for r in by_date if r["keys"] and prev_cut <= r["keys"][0] < cut]
        result["trend"] = {"last7": _totals(last7), "prev7": _totals(prev7)}
    try:
        result["sitemaps"] = [
            {
                "path": sm.get("path"),
                "submitted": sum(int(c.get("submitted") or 0) for c in (sm.get("contents") or [])),
                "indexed": sum(int(c.get("indexed") or 0) for c in (sm.get("contents") or [])),
            }
            for sm in list_sitemaps(site=target, session=s)
        ]
    except GscError:
        # sitemap 조회 실패는 성과 요약을 죽일 사유가 아니다 — 표시만 생략(§0 실패 격리).
        result["sitemaps"] = []
    return result
