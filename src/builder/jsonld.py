"""Schema.org JSON-LD 빌더 — Article · ItemList · Product 타입.

출처: POLICY §4 + VALIDATOR §8 + FRONTEND §5 [확정].

용도:
- enricher.meta_extractor 결과 + 시나리오 정보 → Schema.org Article JSON-LD 문자열
- 시나리오 페이지 상품 추천 목록 → ItemList JSON-LD
- 개별 상품 → Product JSON-LD (가격·통화)
- validator.check_schema의 타입별 필수 필드 모두 충족
- 페이지 <head>에 <script type="application/ld+json"> 삽입용

키워드는 Schema.org 권장에 따라 쉼표 구분 문자열로 출력 (list 입력도 허용).
"""

from __future__ import annotations

import json
from typing import Any

# POLICY §4 + VALIDATOR §8 ARTICLE_REQUIRED와 동일
REQUIRED_META_FIELDS: tuple[str, ...] = ("title", "meta_description")

DEFAULT_AUTHOR_NAME = "혼살림 운영자"
DEFAULT_PUBLISHER_NAME = "혼살림"
SCHEMA_CONTEXT = "https://schema.org"


def _normalize_keywords(value: Any) -> str | None:
    """meta_keywords를 Schema.org 권장 쉼표 구분 문자열로.

    str 입력은 그대로, list 입력은 쉼표로 join. 빈/None은 None 반환.
    """
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, list):
        joined = ", ".join(str(k).strip() for k in value if str(k).strip())
        return joined or None
    return str(value).strip() or None


def _validate_inputs(meta: dict[str, Any], scenario: dict[str, Any]) -> None:
    """필수 입력 검증 — 빌드 전 사전 차단."""
    missing_meta = [f for f in REQUIRED_META_FIELDS if not meta.get(f)]
    if missing_meta:
        raise ValueError(f"meta 필수 필드 누락: {missing_meta}")
    if not scenario.get("slug"):
        raise ValueError("scenario.slug 누락 — mainEntityOfPage URL 생성 불가")


def build_article_jsonld(
    meta: dict[str, Any],
    scenario: dict[str, Any],
    site_base_url: str,
    image_url: str,
    published_at: str,
    modified_at: str | None = None,
    author_name: str = DEFAULT_AUTHOR_NAME,
    publisher_name: str = DEFAULT_PUBLISHER_NAME,
) -> str:
    """Article JSON-LD 문자열 생성.

    인자:
        meta: meta_extractor 결과 (필수: title, meta_description / 선택: meta_keywords)
        scenario: {slug, ...} — slug로 mainEntityOfPage 생성
        site_base_url: "https://honsalim.com" (끝 슬래시 자동 처리)
        image_url: 대표 이미지 절대 URL
        published_at: ISO 8601 (예: "2026-05-28" 또는 "2026-05-28T11:00:00+09:00")
        modified_at: ISO 8601. None이면 published_at과 동일
        author_name: 기본 "혼살림 운영자" (Person)
        publisher_name: 기본 "혼살림" (Organization)

    반환: JSON 문자열 (한국어 보존, ensure_ascii=False).

    Raises:
        ValueError: 필수 입력 누락.
    """
    _validate_inputs(meta, scenario)

    base = site_base_url.rstrip("/")
    main_entity_url = f"{base}/articles/{scenario['slug']}"

    doc: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Article",
        "headline": str(meta["title"]),
        "description": str(meta["meta_description"]),
        "image": image_url,
        "datePublished": published_at,
        "dateModified": modified_at or published_at,
        "author": {"@type": "Person", "name": author_name},
        "publisher": {"@type": "Organization", "name": publisher_name},
        "mainEntityOfPage": main_entity_url,
    }

    keywords = _normalize_keywords(meta.get("meta_keywords"))
    if keywords:
        doc["keywords"] = keywords

    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


# ─── ItemList 빌더 (시나리오 페이지 상품 추천 목록) ───────────────────


# VALIDATOR §8 — ITEMLIST_REQUIRED와 동일
PRODUCT_DEFAULT_CURRENCY = "KRW"  # DB §6 / SCENARIOS 한국 기본


def build_itemlist_jsonld(
    items: list[dict[str, Any]],
    list_name: str | None = None,
) -> str:
    """ItemList JSON-LD 문자열 생성.

    인자:
        items: 각 item dict 키 — name (필수), url (선택), position (선택, 1부터 자동)
        list_name: 선택. 목록 제목 ("원룸 30만원 추천 상품" 등)

    반환: JSON 문자열.

    Raises:
        ValueError: items 비어있거나 item.name 누락.
    """
    if not items:
        raise ValueError("items 비어있음 — ItemList는 최소 1개 요소 필요")

    elements: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        name = item.get("name")
        if not name:
            raise ValueError(f"items[{idx - 1}].name 누락")
        element: dict[str, Any] = {
            "@type": "ListItem",
            "position": int(item.get("position", idx)),
            "name": str(name),
        }
        url = item.get("url")
        if url:
            element["url"] = str(url)
        elements.append(element)

    doc: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "ItemList",
        "itemListElement": elements,
    }
    if list_name:
        doc["name"] = list_name

    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


# ─── Product 빌더 (개별 상품 카드) ────────────────────────────────────


def build_product_jsonld(
    product: dict[str, Any],
    image_url: str | None = None,
    description: str | None = None,
    brand_name: str | None = None,
    currency: str = PRODUCT_DEFAULT_CURRENCY,
) -> str:
    """Product JSON-LD 문자열 생성.

    인자:
        product: 필수 키 — name, price_krw (또는 price). 선택 — url, sku, category.
        image_url: 상품 이미지 절대 URL (선택)
        description: 상품 설명 (선택)
        brand_name: 브랜드 이름 — 있으면 brand 필드 추가 (선택)
        currency: ISO 4217 (기본 'KRW')

    반환: JSON 문자열.

    Raises:
        ValueError: name 또는 price 누락.
    """
    name = product.get("name")
    if not name:
        raise ValueError("product.name 누락")

    price = (
        product.get("price_krw") if product.get("price_krw") is not None else product.get("price")
    )
    if price is None:
        raise ValueError("product.price (또는 price_krw) 누락")

    doc: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Product",
        "name": str(name),
        "offers": {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": currency,
        },
    }

    url = product.get("url")
    if url:
        doc["offers"]["url"] = str(url)

    if image_url:
        doc["image"] = image_url
    if description:
        doc["description"] = description
    if brand_name:
        doc["brand"] = {"@type": "Brand", "name": brand_name}

    sku = product.get("sku")
    if sku:
        doc["sku"] = str(sku)

    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


# ─── 구조화 스키마 (FRONTEND §6-1) — 콘텐츠 무관 ──────────────────────


def build_breadcrumb_jsonld(crumbs: list[dict[str, Any]], site_base_url: str) -> str:
    """BreadcrumbList JSON-LD.

    crumbs: [{name, url}] — url은 상대("/scenarios/") 또는 절대. 마지막(현재)은 url 생략 가능.
    """
    if not crumbs:
        raise ValueError("crumbs 비어있음 — BreadcrumbList 생성 불가")
    base = site_base_url.rstrip("/")
    elements: list[dict[str, Any]] = []
    for idx, c in enumerate(crumbs, start=1):
        name = c.get("name")
        if not name:
            raise ValueError(f"crumbs[{idx - 1}].name 누락")
        el: dict[str, Any] = {"@type": "ListItem", "position": idx, "name": str(name)}
        url = c.get("url")
        if url:
            el["item"] = str(url) if str(url).startswith("http") else f"{base}{url}"
        elements.append(el)
    doc = {"@context": SCHEMA_CONTEXT, "@type": "BreadcrumbList", "itemListElement": elements}
    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


def build_website_jsonld(site_base_url: str, site_name: str = DEFAULT_PUBLISHER_NAME) -> str:
    """WebSite JSON-LD (홈)."""
    base = site_base_url.rstrip("/")
    doc = {"@context": SCHEMA_CONTEXT, "@type": "WebSite", "name": site_name, "url": f"{base}/"}
    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


def build_organization_jsonld(
    site_base_url: str, name: str = DEFAULT_PUBLISHER_NAME, email: str | None = None
) -> str:
    """Organization JSON-LD (발행처)."""
    base = site_base_url.rstrip("/")
    doc: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Organization",
        "name": name,
        "url": f"{base}/",
    }
    if email:
        doc["email"] = email
    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))


def as_script_tags(jsonld_strings: list[str]) -> str:
    """JSON-LD 문자열들을 <script type="application/ld+json"> 블록으로 래핑.

    빈/None 항목은 건너뜀. 페이지 <head>의 schema 블록에 그대로 주입 (|safe).
    """
    return "\n".join(
        f'<script type="application/ld+json">{s}</script>' for s in jsonld_strings if s
    )
