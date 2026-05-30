"""혼살림 검증 게이트 4모듈 통합.

출처: BACKEND §2-3 + POLICY §3·§4·§5·§6 + VALIDATOR_PATTERNS [확정].

5 게이트:
- truth      : 가격·재고·1인칭·AI 흔적·단정형 (POLICY §3·VALIDATOR §4·§5·§6·§7)
- schema     : Schema.org JSON-LD 필수 필드 (POLICY §4·VALIDATOR §8)
- disclosure : 공정위 첫머리·푸터 문구 (POLICY §2·VALIDATOR §3)
- links      : 단축 URL 차단·rel 검증 (POLICY §6·VALIDATOR §1·§2·§9)
- seo        : 키워드 밀도·배치 (AutoBlog SEO_MASTER·seo_gate 포팅, 세션 #15) — opt-in

Phase 2 stub — 핵심 패턴만 구현. 전체 30+ 회귀 케이스는 후속.
"""

from __future__ import annotations

from typing import Any

from .disclosure import check_disclosure
from .links import check_links
from .schema import check_schema
from .seo import check_seo
from .truth import check_truth

__all__ = (
    "check_disclosure",
    "check_links",
    "check_schema",
    "check_seo",
    "check_truth",
    "serialize_report",
    "validate_all",
)


def validate_all(payload: dict[str, Any]) -> dict[str, tuple[bool, dict[str, Any]]]:
    """게이트 일괄 실행 — VALIDATOR_PATTERNS §11 흐름.

    payload 기대 키:
    - body_md       : 본문 Markdown
    - schema_jsonld : Schema.org JSON-LD 문자열
    - products      : [{id, price_krw, ...}, ...] 가격 검증용
    - photos        : list — 1인칭 게이트용 (POLICY §3-1-3)
    - seo           : (선택) {primary, secondary, ...} — SEO 키워드 게이트용.
                      없으면 seo 게이트는 skip(pass) → 기존 세팅 글 무영향 (세션 #15)

    반환: { gate_name: (pass, report) }
    """
    return {
        "truth": check_truth(payload),
        "schema": check_schema(payload.get("schema_jsonld")),
        "disclosure": check_disclosure(payload.get("body_md")),
        "links": check_links(payload.get("body_md")),
        "seo": check_seo(payload),
    }


def serialize_report(
    results: dict[str, tuple[bool, dict[str, Any]]],
) -> dict[str, Any]:
    """validate_all 결과를 JSON 직렬화 가능한 dict로 정돈.

    구조:
    {
      "overall_pass": bool,
      "gates": {
        "truth":      {"pass": bool, "issues": [...]},
        "schema":     {"pass": bool, "issues": [...]},
        "disclosure": {"pass": bool, "issues": [...]},
        "links":      {"pass": bool, "issues": [...]},
      }
    }

    drafts.validation_report 컬럼 저장용 (DB §5).
    """
    gates: dict[str, dict[str, Any]] = {}
    overall = True
    for name, (ok, rpt) in results.items():
        entry: dict[str, Any] = {"pass": ok, "issues": list(rpt.get("issues", []))}
        # warnings·metrics는 제공하는 게이트(예: seo)만 — 자문 정보(대시보드 표시·인간 편집 게이트용),
        # overall_pass에는 영향 없음 (세션 #15).
        if "warnings" in rpt:
            entry["warnings"] = list(rpt.get("warnings", []))
        if "metrics" in rpt:
            entry["metrics"] = rpt["metrics"]
        gates[name] = entry
        if not ok:
            overall = False
    return {"overall_pass": overall, "gates": gates}
