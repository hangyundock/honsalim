"""collector — 어필리에이트 상품·시나리오 수집.

출처: ARCH §3 + BACKEND §2-1 + SCENARIOS [확정].

모듈:
- scenario_loader: DB scenarios → 수집 큐
- aliexpress     : AliExpress Affiliate API product.query (DECISIONS D9, production-ready)
- keyword_map    : 시나리오 slug → 영어 검색어 매핑 (search_keywords.yml)
- products_store : 수집 상품 dict → products 테이블 upsert
- coupang        : 쿠팡 Open API (Phase 4)
"""

from __future__ import annotations

from .keyword_map import (
    SearchTerm,
    all_mapped_slugs,
    coupang_deferred_slugs,
    keywords_for_scenario,
    terms_for_scenario,
)
from .products_store import UpsertResult, upsert_products
from .scenario_loader import (
    ScenarioRow,
    list_active_scenarios,
    next_scenarios_for_collection,
)

__all__ = (
    "ScenarioRow",
    "SearchTerm",
    "UpsertResult",
    "all_mapped_slugs",
    "coupang_deferred_slugs",
    "keywords_for_scenario",
    "list_active_scenarios",
    "next_scenarios_for_collection",
    "terms_for_scenario",
    "upsert_products",
)
