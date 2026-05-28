"""혼살림 검증 게이트 4모듈 통합.

출처: BACKEND §2-3 + POLICY §3·§4·§5·§6 + VALIDATOR_PATTERNS [확정].

4 게이트:
- truth      : 가격·재고·1인칭·AI 흔적·단정형 (POLICY §3·VALIDATOR §4·§5·§6·§7)
- schema     : Schema.org JSON-LD 필수 필드 (POLICY §4·VALIDATOR §8)
- disclosure : 공정위 첫머리·푸터 문구 (POLICY §2·VALIDATOR §3)
- links      : 단축 URL 차단·rel 검증 (POLICY §6·VALIDATOR §1·§2·§9)

Phase 2 stub — 핵심 패턴만 구현. 전체 30+ 회귀 케이스는 후속.
"""

from __future__ import annotations

from typing import Any

from .disclosure import check_disclosure
from .links import check_links
from .schema import check_schema
from .truth import check_truth

__all__ = (
    "check_truth",
    "check_schema",
    "check_disclosure",
    "check_links",
    "validate_all",
)


def validate_all(payload: dict[str, Any]) -> dict[str, tuple[bool, dict[str, Any]]]:
    """4 게이트 일괄 실행 — VALIDATOR_PATTERNS §11 흐름.

    payload 기대 키:
    - body_md       : 본문 Markdown
    - schema_jsonld : Schema.org JSON-LD 문자열
    - products      : [{id, price_krw, ...}, ...] 가격 검증용

    반환: { gate_name: (pass, report) }
    """
    return {
        "truth": check_truth(payload),
        "schema": check_schema(payload.get("schema_jsonld")),
        "disclosure": check_disclosure(payload.get("body_md")),
        "links": check_links(payload.get("body_md")),
    }
