# 사유: urllib 표준 라이브러리만 사용(의존성 0) — POST 대상은 코드 상수(api.indexnow.org)뿐.
"""deployer.indexnow — 배포 성공 후 IndexNow 통지 (세션 #45. DECISIONS F4·FRONTEND §7-3).

발행·배포가 끝난 뒤 새/갱신 URL을 IndexNow(Bing·Yandex 등 참여 엔진)에 통지해 색인을
가속한다. ★Google은 IndexNow 미참여 + Indexing API는 정책상 사용 금지(F6 [확정]) — 이 모듈은
Google과 무관하다.

계약(§0 — common.notify와 동일): **절대 예외를 전파하지 않는다.** 키 미설정·네트워크 실패·
사이트맵 파싱 실패 전부 False/빈 목록 반환 + 로그만. 핑 실패는 발행·배포 결과에 어떤 영향도
없다. 키는 프로토콜상 공개값(사이트 루트 <key>.txt로 공개 서빙 — STATE [확정])이지만 출력에는
키 문자열을 직접 찍지 않는다(logging 마스킹 관례).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
_TIMEOUT_S = 10
_MAX_URLS = 10000  # IndexNow 배치 상한 — 사이트는 수십 URL이라 여유
_KEY_RE = re.compile(r"[A-Za-z0-9-]{8,128}")  # 프로토콜 키 형식(방어적 검증)
_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _key() -> str:
    """env INDEXNOW_KEY(형식 검증 통과 시). 미설정·형식 불일치는 빈 문자열."""
    k = (os.environ.get("INDEXNOW_KEY") or "").strip()
    return k if _KEY_RE.fullmatch(k) else ""


def indexnow_ready() -> bool:
    """키 사용 가능 여부 — secrets 자체 로드 후 판단 (notify.telegram_ready 패턴).

    무인 발행 경로(publish-queue)는 config.load_secrets를 호출하지 않을 수 있어(§0 방어)
    여기서 직접 로드한다. 로드 실패도 조용히 무시(미설정=무동작).
    """
    try:
        from common import config

        config.load_secrets()
    except Exception:  # noqa: S110 — secrets 없음·dotenv 미설치 등은 '미설정'과 동일(무동작 설계)
        pass
    return bool(_key())


def sitemap_urls(site_dir: Path) -> list[str]:
    """빌드 산출물 sitemap.xml의 <loc> 전체 — 핑 대상 URL 목록.

    사이트가 소규모(수십 URL)라 '이번에 바뀐 것'을 따로 계산하지 않고 사이트맵 전체를
    통지한다(새 글·갱신된 카테고리·허브가 전부 포함 — 단순·race-free). 실패는 빈 목록(§0).
    """
    try:
        # 파싱 대상 = 우리 빌더(render_site)가 방금 만든 자체 산출물 — 외부 입력 아님(S314 예외 사유)
        tree = ElementTree.parse(site_dir / "sitemap.xml")  # noqa: S314
        return [
            el.text.strip()
            for el in tree.findall(".//sm:loc", _SITEMAP_NS)
            if el.text and el.text.strip()
        ]
    except Exception:
        return []


def ping(urls: list[str]) -> bool:
    """URL 목록을 IndexNow로 통지. 반환: 발송 성공 여부(2xx). 예외는 절대 전파하지 않음(§0).

    host·keyLocation은 첫 URL에서 유도(도메인 하드코딩 드리프트 방지 — honsalim/honsallim 혼동
    이력). 키 미설정·URL 없음은 False(무동작).
    """
    key = _key()
    if not key or not urls:
        return False
    host = urlparse(urls[0]).hostname or ""
    if not host:
        return False
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": list(urls)[:_MAX_URLS],
    }
    req = urllib.request.Request(  # noqa: S310 — URL은 코드 고정 https 상수(INDEXNOW_ENDPOINT)
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:  # noqa: S310 — https 고정
            ok = 200 <= int(getattr(resp, "status", 0) or 0) < 300
        if not ok:
            print("[indexnow] 응답 비정상(무시) — 다음 배포에서 재시도됨")
        return ok
    except (urllib.error.URLError, OSError, ValueError) as e:  # 네트워크·응답 오류 — 전파 금지
        print(f"[indexnow] 발송 실패(무시): {type(e).__name__}")
        return False
