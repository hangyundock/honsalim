"""collector.coupang_manual — 쿠팡 수동 상품 등록 (세션 #25, 쿠팡 15만원 전 단계).

쿠팡 API 발급(누적 15만원) 전까지 운영자가 쿠팡 파트너스 딥링크/공식 위젯을 **수동 입력**한다.
저작권 안전(함정 #3): 쿠팡 상품 CDN 이미지는 다운로드하지 않는다 — 공식 위젯/텍스트 링크만.
입력한 상품은 키워드의 target_products(미리선택)에 추가되어, 글 생성 시 후보로 쓰이고
promote 시 /go/ 텍스트 링크로 연결된다(disclosure.py가 쿠팡 파트너스 대가성 문구 처리).

15만원 후: collector.coupang(API) 구현으로 자동 수집 전환(설정 coupang_mode=api).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any

DEFAULT_COUPANG_TAG = "coupang-partners"

# 쿠팡 공식 '블로그용 배너' HTML(<a href><img src alt></a>) 파싱 — 딥링크·이미지·상품명 추출
_A_HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)
_IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', re.I)
_IMG_ALT_RE = re.compile(r'<img\b[^>]*\balt=["\']([^"\']+)["\']', re.I)


def parse_banner(banner_html: str | None) -> dict[str, str | None]:
    """쿠팡 공식 배너 HTML에서 딥링크(href)·이미지URL(img src)·상품명(img alt) 추출.

    예: <a href="https://link.coupang.com/a/XXXX"><img src="https://image.coupangcdn.com/...jpg"
        alt="상품명"></a>
    각 값 없으면 None. 이미지는 **hotlink**(다운로드 아님·쿠팡 공식 임베드)이라 함정#3과 무관.
    """
    html = banner_html or ""
    href = _A_HREF_RE.search(html)
    src = _IMG_SRC_RE.search(html)
    alt = _IMG_ALT_RE.search(html)
    return {
        "deeplink_url": href.group(1).strip() if href else None,
        "image_url": src.group(1).strip() if src else None,
        "name": alt.group(1).strip() if alt else None,
    }


def build_manual_product(
    name: str,
    partners_url: str,
    *,
    price_krw: int | None = None,
    widget_html: str | None = None,
    banner_html: str | None = None,
    image_url: str | None = None,
    affiliate_tag: str | None = None,
    source_product_id: str | None = None,
) -> dict[str, Any]:
    """수동 입력 필드 → products 호환 dict (source='coupang').

    공식 배너 HTML(``banner_html``)을 주면 딥링크·이미지·상품명을 자동 추출해 명시 인자를 보충한다.
    ``image_url_external``은 쿠팡 공식 배너 이미지의 **hotlink**(다운로드 아님·함정#3 무관) — 채워지면
    알리 상품과 동일하게 글 카드에 이미지로 렌더된다. 배너/이미지 없으면 텍스트 링크로만 동작(하위호환).
    deeplink_slug는 coupang-<hash>로 결정적 생성(중복 안전).
    """
    parsed = parse_banner(banner_html) if banner_html else {}
    name = (name or parsed.get("name") or "").strip()
    partners_url = (partners_url or parsed.get("deeplink_url") or "").strip()
    image_url_external = (image_url or parsed.get("image_url") or "").strip() or None
    if not name:
        raise ValueError("상품명이 비어 있습니다 (배너 alt로도 못 채움)")
    if not partners_url:
        raise ValueError("쿠팡 파트너스 딥링크(URL)가 비어 있습니다 (배너 href로도 못 채움)")
    spid = (source_product_id or "").strip() or hashlib.sha1(  # noqa: S324 (식별용·비보안)
        partners_url.encode("utf-8")
    ).hexdigest()[:12]
    return {
        "source": "coupang",
        "source_product_id": spid,
        "name": name,
        "price_krw": price_krw,
        "image_url_external": image_url_external,
        "deeplink_url": partners_url,
        "deeplink_slug": f"coupang-{spid}",
        "affiliate_tag": (affiliate_tag or DEFAULT_COUPANG_TAG),
        "availability": "unknown",
        "widget_html": widget_html or banner_html or None,
    }


def add_to_keyword(conn: sqlite3.Connection, keyword_id: int, product: dict[str, Any]) -> int:
    """product를 keyword_queue.target_products(JSON 배열)에 추가. 반환: 추가 후 총 개수.

    같은 deeplink_slug가 이미 있으면 교체(중복 방지).
    """
    row = conn.execute(
        "SELECT target_products FROM keyword_queue WHERE id = ?", (keyword_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"keyword id={keyword_id} 없음")
    items: list[dict[str, Any]] = []
    if row[0]:
        try:
            parsed = json.loads(row[0])
            if isinstance(parsed, list):
                items = parsed
        except (json.JSONDecodeError, TypeError):
            items = []
    # 중복 deeplink_slug 제거 후 추가
    slug = product.get("deeplink_slug")
    items = [it for it in items if it.get("deeplink_slug") != slug]
    items.append(product)
    conn.execute(
        "UPDATE keyword_queue SET target_products = ? WHERE id = ?",
        (json.dumps(items, ensure_ascii=False), keyword_id),
    )
    conn.commit()
    return len(items)
