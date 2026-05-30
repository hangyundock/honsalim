"""keyword_map — 시나리오 slug → AliExpress 영어 검색어(+가격 밴드) 매핑.

출처: SCENARIOS.md §8-2 + 라이브 발견 [확정 2026-05-30].

AliExpress product.query는 영어 검색어 기반(한글은 resp_code 405 빈 결과)이고,
결과 상품명은 target_language=ko로 한글 반환된다. 또한 가격 밴드(min/max_sale_price,
단위 KRW [확정 라이브])가 관련성의 핵심 레버다 — 번들 시나리오는 품목별 가격대가
천차만별이라 **검색어(카테고리)별 가격 밴드**로 좁힌다.

데이터: ``src/collector/search_keywords.yml`` (사용자 검토·편집 대상).
YAML 항목 형식 (두 가지 모두 허용):
- 평문 문자열: ``- office chair``               (가격 밴드 없음)
- 매핑:        ``- {q: office chair, min: 40000, max: 250000}``
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # 의존성 미설치 환경 대비 (BACKEND §10-1엔 포함)
    yaml = None  # type: ignore[assignment]

KEYWORDS_FILE = Path(__file__).resolve().parent / "search_keywords.yml"


@dataclass(frozen=True)
class SearchTerm:
    """검색어 1건 — 질의어 + 선택적 가격 밴드(KRW)."""

    q: str
    min_price: int | None = None
    max_price: int | None = None


def _to_term(raw: Any) -> SearchTerm | None:
    """YAML 항목(문자열 또는 {q,min,max} dict) → SearchTerm. 무효면 None."""
    if isinstance(raw, str):
        q = raw.strip()
        return SearchTerm(q=q) if q else None
    if isinstance(raw, dict):
        q = str(raw.get("q", "")).strip()
        if not q:
            return None

        def _int(v: Any) -> int | None:
            return int(v) if isinstance(v, (int, float)) else None

        return SearchTerm(q=q, min_price=_int(raw.get("min")), max_price=_int(raw.get("max")))
    return None


def load_map(path: Path = KEYWORDS_FILE) -> dict[str, list[SearchTerm]]:
    """YAML → {scenario_slug: [SearchTerm, ...]}.

    파일·yaml 모듈 없으면 빈 dict. 무효 항목은 방어적으로 제외.
    """
    if yaml is None or not path.exists():
        return {}
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    scenarios = data.get("scenarios") if isinstance(data, dict) else None
    if not isinstance(scenarios, dict):
        return {}
    out: dict[str, list[SearchTerm]] = {}
    for slug, items in scenarios.items():
        if isinstance(items, list):
            terms = [t for t in (_to_term(it) for it in items) if t is not None]
            if terms:
                out[str(slug)] = terms
    return out


def terms_for_scenario(slug: str, path: Path = KEYWORDS_FILE) -> list[SearchTerm]:
    """시나리오 slug의 SearchTerm 목록 (가격 밴드 포함). 매핑 없으면 빈 리스트."""
    return list(load_map(path).get(slug, []))


def keywords_for_scenario(slug: str, path: Path = KEYWORDS_FILE) -> list[str]:
    """시나리오 slug의 영어 검색어(질의어) 목록 — 가격 밴드 제외, 하위호환용."""
    return [t.q for t in terms_for_scenario(slug, path)]


def all_mapped_slugs(path: Path = KEYWORDS_FILE) -> list[str]:
    """매핑이 정의된 시나리오 slug 정렬 목록."""
    return sorted(load_map(path).keys())


def coupang_deferred_slugs(path: Path = KEYWORDS_FILE) -> list[str]:
    """전 품목 가전/대형이라 AliExpress 부적합 → 쿠팡 전담 시나리오 slug 목록.

    라이브 검증으로 AliExpress가 가전(220V·KC 정품)·가구·대형 생활용품을 공급하지
    못함이 확인됨 [확정 2026-05-30]. 이 시나리오들은 Phase 4 collector.coupang가 담당.
    """
    if yaml is None or not path.exists():
        return []
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    deferred = data.get("coupang_deferred") if isinstance(data, dict) else None
    if not isinstance(deferred, list):
        return []
    return sorted(str(s).strip() for s in deferred if str(s).strip())
