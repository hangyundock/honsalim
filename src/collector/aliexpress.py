"""AliExpress Affiliate API 상품 수집기.

출처: AliExpress Open Platform "Affiliate API Guidance" (Portals Help Center, 2026-05-30 확인).

주요 메서드:
- ``aliexpress.affiliate.product.query`` — 키워드/카테고리로 제휴 상품 검색
  (페이지당 최대 50개, 단일 쿼리 최대 5000개 — FAQ 4.2)
- ``aliexpress.affiliate.productdetail.get`` — product_id 상세 (최대 50개)
- ``aliexpress.affiliate.category.get`` — 카테고리 ID/이름

서명 (FAQ 4.5):
- ``sign_method=sha256`` → 파라미터를 key 사전순으로 ``key+value`` 연결 후 HMAC-SHA256(app_secret)
  대문자 hex. 문서의 연결 예시(``app_key...end_time...method...sign_methodsha256...``)와 동일.
- ``app_signature`` 파라미터는 비필수 (FAQ 4.1).

자격 증명 (``D:\\secrets\\affiliate_hub\\ali.env``):
- ``ALI_TRACKING_ID`` — 발급 완료 ✅
- ``ALI_APP_KEY`` / ``ALI_APP_SECRET`` — **2026-05-30 미발급** (App 심사 대기). 없으면 dry_run만 가능.

모드:
- ``dry_run=True`` (기본): 실제 HTTP 호출 없이 서명된 요청만 빌드 — 키 없이 구조 검증, 비용 0.
- ``dry_run=False`` (live): App Key/Secret 필요 + 실제 호출(쿼터 소모). **키 발급 후 라이브 검증 필요**
  (게이트웨이 timestamp 형식·응답 JSON 경로는 실제 응답으로 최종 확인).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# IOP 게이트웨이 (싱가포르). 라이브 검증 시 timestamp 형식(초/밀리초) 최종 확인 필요.
API_GATEWAY = "https://api-sg.aliexpress.com/sync"
PRODUCT_QUERY = "aliexpress.affiliate.product.query"
PAGE_SIZE_MAX = 50  # FAQ 4.2

ENV_APP_KEY = "ALI_APP_KEY"
ENV_APP_SECRET = "ALI_APP_SECRET"  # noqa: S105  (env var 이름, 시크릿 값 아님)
ENV_TRACKING_ID = "ALI_TRACKING_ID"


def sign(params: dict[str, Any], app_secret: str, sign_method: str = "sha256") -> str:
    """TOP 스타일 서명 (FAQ 4.5).

    'sign'과 빈 값은 제외, key 사전순으로 ``key+value`` 연결 → 서명.
    sha256: HMAC-SHA256(연결문자열, app_secret). md5: ``MD5(secret+연결+secret)``. 모두 대문자 hex.
    """
    ordered = "".join(
        f"{k}{params[k]}" for k in sorted(params) if k != "sign" and params[k] not in (None, "")
    )
    if sign_method == "sha256":
        return (
            hmac.new(app_secret.encode("utf-8"), ordered.encode("utf-8"), hashlib.sha256)
            .hexdigest()
            .upper()
        )
    if sign_method == "md5":
        # md5는 AliExpress 지원 서명 방식 (FAQ 4.5, 비밀번호 해싱 아님)
        raw = f"{app_secret}{ordered}{app_secret}".encode()
        return hashlib.md5(raw).hexdigest().upper()  # noqa: S324
    raise ValueError(f"지원하지 않는 sign_method: {sign_method!r}")


def build_query_request(
    keywords: str,
    app_key: str,
    tracking_id: str,
    *,
    timestamp: int | str,
    page_no: int = 1,
    page_size: int = 20,
    target_currency: str = "KRW",
    target_language: str = "ko",
    ship_to_country: str = "KR",
    sort: str = "",
    min_sale_price: int | None = None,
    max_sale_price: int | None = None,
    app_secret: str = "",
    sign_method: str = "sha256",
    method: str = PRODUCT_QUERY,
) -> dict[str, str]:
    """product.query 요청 파라미터(서명 포함) 빌드. 순수 함수 — 테스트·dry_run 공용.

    sort: 결과 정렬. 빈 문자열이면 파라미터 생략(기본=관련도순). 예: ``LAST_VOLUME_DESC``
    (판매량 많은 순). 정렬 단독은 관련성에 불충분 — 가격 밴드와 병용 [관찰 2026-05-30].
    min_sale_price/max_sale_price: 가격 필터(None이면 생략). **단위는 라이브 검증 필요 [추정]**
    (target_currency 기준 정수인지, cents인지 확인 후 확정).
    app_secret이 비면 sign은 빈 문자열(dry_run에서 키 없이 구조만 확인).
    """
    if page_size > PAGE_SIZE_MAX:
        raise ValueError(f"page_size는 최대 {PAGE_SIZE_MAX} (FAQ 4.2): {page_size}")
    params: dict[str, str] = {
        # 시스템 파라미터
        "method": method,
        "app_key": str(app_key),
        "timestamp": str(timestamp),
        "sign_method": sign_method,
        "format": "json",
        "v": "2.0",
        # 비즈니스 파라미터
        "keywords": keywords,
        "tracking_id": str(tracking_id),
        "page_no": str(page_no),
        "page_size": str(page_size),
        "target_currency": target_currency,
        "target_language": target_language,
        "ship_to_country": ship_to_country,
    }
    # 선택 파라미터 — 값이 있을 때만 포함 (없으면 서명·기존 동작 불변)
    if sort:
        params["sort"] = sort
    if min_sale_price is not None:
        params["min_sale_price"] = str(min_sale_price)
    if max_sale_price is not None:
        params["max_sale_price"] = str(max_sale_price)
    params["sign"] = sign(params, app_secret, sign_method) if app_secret else ""
    return params


def map_product(item: dict[str, Any], tracking_id: str) -> dict[str, Any]:
    """API 상품 항목 → products 테이블 dict (DB §6).

    필드명은 API 버전별로 다를 수 있어 방어적으로 매핑 — 라이브 응답으로 최종 검증 필요.
    """

    def g(*keys: str, default: Any = None) -> Any:
        for k in keys:
            v = item.get(k)
            if v not in (None, ""):
                return v
        return default

    pid = str(g("product_id", "productId", default="") or "")
    price = g("target_sale_price", "targetSalePrice", "sale_price", default=None)
    return {
        "source": "aliexpress",
        "source_product_id": pid,
        "name": g("product_title", "productTitle", default=""),
        "category_path": g("second_level_category_name", "first_level_category_name", default=None),
        "price_krw": round(float(price)) if price not in (None, "") else None,
        "currency": g("target_sale_price_currency", default="KRW"),
        "image_url_external": g("product_main_image_url", "productMainImageUrl", default=None),
        "deeplink_url": g("promotion_link", "promotionLink", default=None),
        "deeplink_slug": f"ali-{pid}" if pid else None,
        "affiliate_tag": tracking_id,
        "availability": "unknown",
    }


def _response_root_key(method: str) -> str:
    """method → 응답 래퍼 키. 'aliexpress.affiliate.product.query'
    → 'aliexpress_affiliate_product_query_response' (라이브 응답으로 확인 [확정 2026-05-30])."""
    return method.replace(".", "_") + "_response"


def _resp_result(raw: Any, method: str = PRODUCT_QUERY) -> dict[str, Any]:
    """응답에서 resp_result dict까지 진입 (없으면 빈 dict)."""
    node: Any = raw
    for key in (_response_root_key(method), "resp_result"):
        if isinstance(node, dict) and key in node:
            node = node[key]
    return node if isinstance(node, dict) else {}


def _extract_status(raw: Any, method: str = PRODUCT_QUERY) -> tuple[str | None, str | None]:
    """API 응답 상태 (resp_code, resp_msg). 라이브 확인 [확정 2026-05-30]:
    성공 200 'Call succeeds' · 빈 결과 405 'The result is empty'.
    시스템 오류는 최상위 error_response(code·msg)로 옴."""
    if isinstance(raw, dict) and "error_response" in raw:
        err = raw.get("error_response") or {}
        code = err.get("code", "error")
        msg = err.get("msg") or err.get("sub_msg")
        return (str(code), str(msg) if msg is not None else None)
    rr = _resp_result(raw, method)
    code = rr.get("resp_code")
    msg = rr.get("resp_msg")
    return (str(code) if code is not None else None, str(msg) if msg is not None else None)


def _extract_items(raw: Any, method: str = PRODUCT_QUERY) -> list[dict[str, Any]]:
    """응답 JSON에서 상품 리스트 추출 (라이브 확인 [확정 2026-05-30]).

    경로: <root>_response → resp_result → result → products → product[]
    빈 결과(resp_code 405)는 result 키 자체가 없어 [] 반환.
    """
    node: Any = _resp_result(raw, method)
    for key in ("result", "products", "product"):
        if isinstance(node, dict) and key in node:
            node = node[key]
    return node if isinstance(node, list) else []


@dataclass
class QueryResult:
    dry_run: bool
    request: dict[str, str]
    products: list[dict[str, Any]] = field(default_factory=list)
    raw: Any = None
    resp_code: str | None = None
    resp_msg: str | None = None


def query_products(
    keywords: str,
    *,
    timestamp: int | str,
    dry_run: bool = True,
    page_no: int = 1,
    page_size: int = 20,
    sort: str = "",
    min_sale_price: int | None = None,
    max_sale_price: int | None = None,
    app_key: str | None = None,
    app_secret: str | None = None,
    tracking_id: str | None = None,
    timeout: int = 20,
) -> QueryResult:
    """키워드로 제휴 상품 검색.

    dry_run=True: HTTP 없이 서명된 요청만 반환 (키 없이 가능).
    dry_run=False: App Key/Secret 필요 + 실제 호출. 키 미설정 시 RuntimeError.
    sort: 결과 정렬값 (빈 문자열=기본 관련도순). 예: ``LAST_VOLUME_DESC`` (판매량순).
    min_sale_price/max_sale_price: 가격 필터(None이면 생략). 단위는 라이브 검증 필요 [추정].
    자격 증명은 인자 우선, 없으면 os.environ (config.load_secrets()로 ali.env 로드 후).
    """
    app_key = app_key if app_key is not None else os.environ.get(ENV_APP_KEY, "")
    app_secret = app_secret if app_secret is not None else os.environ.get(ENV_APP_SECRET, "")
    tracking_id = tracking_id if tracking_id is not None else os.environ.get(ENV_TRACKING_ID, "")

    req = build_query_request(
        keywords,
        app_key,
        tracking_id,
        timestamp=timestamp,
        page_no=page_no,
        page_size=page_size,
        sort=sort,
        min_sale_price=min_sale_price,
        max_sale_price=max_sale_price,
        app_secret=app_secret,
    )

    if dry_run:
        return QueryResult(dry_run=True, request=req)

    if not app_key or not app_secret:
        raise RuntimeError(
            "ALI_APP_KEY/ALI_APP_SECRET 미설정 — AliExpress App 발급 후 ali.env에 저장 필요"
        )
    data = urllib.parse.urlencode(req).encode("utf-8")
    with urllib.request.urlopen(API_GATEWAY, data=data, timeout=timeout) as resp:  # noqa: S310
        raw = json.loads(resp.read().decode("utf-8"))
    products = [map_product(it, tracking_id) for it in _extract_items(raw)]
    code, msg = _extract_status(raw)
    return QueryResult(
        dry_run=False, request=req, products=products, raw=raw, resp_code=code, resp_msg=msg
    )
