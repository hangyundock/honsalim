"""collector — 어필리에이트 상품·시나리오 수집.

출처: ARCH §3 + BACKEND §2-1 + SCENARIOS [확정].

모듈:
- scenario_loader: DB scenarios → 수집 큐
- coupang        : 쿠팡 Open API (Phase 2 후반)
- aliexpress     : Phase 5 이후 stub
"""

from __future__ import annotations

from .scenario_loader import (
    ScenarioRow,
    list_active_scenarios,
    next_scenarios_for_collection,
)

__all__ = (
    "ScenarioRow",
    "list_active_scenarios",
    "next_scenarios_for_collection",
)
