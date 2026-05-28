"""schema 게이트 — Schema.org JSON-LD 필수 필드.

출처: POLICY §4 + VALIDATOR_PATTERNS §8 [확정].
"""

from __future__ import annotations

import json
from typing import Any

# VALIDATOR §8 — Article 필수 필드
ARTICLE_REQUIRED = (
    "@context",
    "@type",
    "headline",
    "description",
    "image",
    "datePublished",
    "dateModified",
    "author",
    "publisher",
    "mainEntityOfPage",
)

# VALIDATOR §8 — ItemList 필수 필드
ITEMLIST_REQUIRED = (
    "@context",
    "@type",
    "itemListElement",
)

# VALIDATOR §8 — Product 필수 필드 (offers.price·priceCurrency 포함)
PRODUCT_REQUIRED = (
    "@type",
    "name",
    "offers",
)
PRODUCT_OFFERS_REQUIRED = (
    "price",
    "priceCurrency",
)

# Review 조건 (POLICY §4 + tone_examples 1인칭 게이트)
REVIEW_FORBIDDEN_AUTHOR_TYPE = "Organization"  # Person만 허용


def _check_article(data: dict[str, Any]) -> list[str]:
    return [f"missing_field: {k}" for k in ARTICLE_REQUIRED if k not in data]


def _check_review(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    author = data.get("author")
    if isinstance(author, dict) and author.get("@type") == REVIEW_FORBIDDEN_AUTHOR_TYPE:
        issues.append("review_author_organization_forbidden")
    return issues


def _check_itemlist(data: dict[str, Any]) -> list[str]:
    issues = [f"missing_field: {k}" for k in ITEMLIST_REQUIRED if k not in data]
    elements = data.get("itemListElement")
    if isinstance(elements, list) and len(elements) == 0:
        issues.append("itemlist_empty")
    return issues


def _check_product(data: dict[str, Any]) -> list[str]:
    issues = [f"missing_field: {k}" for k in PRODUCT_REQUIRED if k not in data]
    offers = data.get("offers")
    if isinstance(offers, dict):
        for k in PRODUCT_OFFERS_REQUIRED:
            if k not in offers:
                issues.append(f"missing_offers_field: {k}")
    elif "offers" in data:
        issues.append("offers_not_object")
    return issues


def check_schema(jsonld: str | None) -> tuple[bool, dict[str, Any]]:
    """schema 게이트 검사.

    jsonld: Schema.org JSON-LD 문자열.
    지원 @type: Article · Review · ItemList · Product.
    반환: (pass, {"issues": [...], "gate": "schema"}).
    """
    if not jsonld:
        return False, {"issues": ["schema_missing"], "gate": "schema"}
    try:
        data: Any = json.loads(jsonld)
    except json.JSONDecodeError as e:
        return False, {"issues": [f"json_parse_error: {e}"], "gate": "schema"}

    if not isinstance(data, dict):
        return False, {"issues": ["schema_not_object"], "gate": "schema"}

    issues: list[str] = []
    schema_type = data.get("@type")
    if schema_type == "Article":
        issues.extend(_check_article(data))
    elif schema_type == "Review":
        issues.extend(_check_review(data))
    elif schema_type == "ItemList":
        issues.extend(_check_itemlist(data))
    elif schema_type == "Product":
        issues.extend(_check_product(data))
    # 알 수 없는 @type은 통과 (Phase 2 후반에 unknown_type 정책 결정)

    return len(issues) == 0, {"issues": issues, "gate": "schema"}
