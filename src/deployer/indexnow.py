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
import time
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
    """빌드 산출물 sitemap.xml의 <loc> 전체. 실패는 빈 목록(§0)."""
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


def _parse_sitemap(xml_text: str) -> dict[str, str | None]:
    """sitemap XML 문자열 → {loc: lastmod|None}. 자체 산출물 파싱(S314 예외 사유 동일)."""
    root = ElementTree.fromstring(xml_text)  # noqa: S314
    out: dict[str, str | None] = {}
    for url in root.findall("sm:url", _SITEMAP_NS):
        loc_el = url.find("sm:loc", _SITEMAP_NS)
        if loc_el is None or not (loc_el.text or "").strip():
            continue
        lm_el = url.find("sm:lastmod", _SITEMAP_NS)
        out[(loc_el.text or "").strip()] = (lm_el.text or "").strip() if lm_el is not None else None
    return out


def changed_urls(prev_xml: str | None, curr_xml: str) -> list[str]:
    """직전 배포 사이트맵 대비 **변경분만** — 추가·lastmod 변경·삭제된 URL (세션 #45 적대검증).

    IndexNow 지침은 '추가·변경·삭제된 URL만 제출'을 요구한다 — 변경 없는 전체를 매일
    재제출하면 엔진이 호스트 제출 신뢰를 낮춰 정작 새 글 통지까지 무시될 수 있다.
    prev가 None(첫 배포·직전본 조회 실패)이거나 prev 파싱 실패면 전체 폴백(§0 — 과통지가
    무통지보다 낫다). curr 파싱 실패는 빈 목록.
    """
    try:
        curr = _parse_sitemap(curr_xml)
    except Exception:
        return []
    if prev_xml is None:
        return list(curr)
    try:
        prev = _parse_sitemap(prev_xml)
    except Exception:
        return list(curr)
    added_or_modified = [loc for loc, lm in curr.items() if loc not in prev or prev[loc] != lm]
    deleted = [loc for loc in prev if loc not in curr]  # 비공개·301 이전도 통지 대상(프로토콜)
    return added_or_modified + deleted


def deploy_urls(
    site_dir: Path, prev_sitemap_xml: str | None, refreshed_category_slugs: list[str]
) -> list[str]:
    """이번 배포의 IndexNow 통지 대상 = 사이트맵 변경분 + 이번 사이클에 갱신된 카테고리 페이지.

    카테고리 sitemap lastmod = MAX(last_seen_at)(#46)라 재수집일이 바뀌면 diff로 잡힌다. 다만
    lastmod는 날짜(YYYY-MM-DD) 단위라 같은 날 재수집은 diff에 안 보일 수 있어, 안전망으로 이번
    사이클에 새로고침(수집·가격 갱신)된 카테고리 slug도 직접 받아 합친다(중복은 아래 dedupe).
    실패는 빈 목록(§0).
    """
    try:
        curr_xml = (site_dir / "sitemap.xml").read_text(encoding="utf-8")
    except OSError:
        return []
    urls = changed_urls(prev_sitemap_xml, curr_xml)
    full = sitemap_urls(site_dir)
    host = urlparse(full[0]).hostname if full else None
    if host:
        for slug in refreshed_category_slugs:
            urls.append(f"https://{host}/categories/{slug}/")
    out: list[str] = []
    for u in urls:  # 순서 보존 dedupe
        if u not in out:
            out.append(u)
    return out


def key_file_live(host: str, *, attempts: int = 4, interval_s: float = 30.0) -> bool:
    """라이브 keyLocation(https://<host>/<key>.txt)이 실제 서빙 중인지 폴링 (세션 #45 적대검증).

    push 직후엔 CI 반영(1~2분) 전이라 키 파일이 404일 수 있고, 키 파일이 404인 채 핑하면
    엔진의 비동기 키 검증 실패로 그 배치가 통째로 폐기된다(202는 수신 확인일 뿐). 첫 배포·
    키 파일 유실 드리프트까지 상시 가드 — 미확인이면 핑을 생략한다(다음 배포에서 재시도).
    전 예외 무시·§0(폴링 실패가 배포 결과에 영향 없음).
    """
    key = _key()
    if not key or not host:
        return False
    url = f"https://{host}/{key}.txt"
    for i in range(max(1, attempts)):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:  # noqa: S310 — https 고정
                body = resp.read(4096).decode("utf-8", "replace").strip()
                if 200 <= int(getattr(resp, "status", 0) or 0) < 300 and body == key:
                    return True
        except (urllib.error.URLError, OSError, ValueError):
            pass
        if i < max(1, attempts) - 1:
            time.sleep(interval_s)
    return False


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
