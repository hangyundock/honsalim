"""seo_keywords — 카테고리별 SEO 키워드 세트 로더 (대표 + 보조). 세션 #15 신설.

데이터: ``src/collector/seo_keywords.yml`` (운영자 검토·편집 대상, §2-마 인간 편집 게이트).
생성: ``collector.keyword_research.build_entry`` (네이버 검색광고 실검색량 자동 선별).
소비: ``validator/seo.py`` 게이트(payload["seo"]) + enrich 프롬프트 2층 키워드 배치.

매 빌드마다 네이버를 재호출하지 않고 이 yml을 읽는다(rate limit·재현성). 검색량이 크게
변하면 build_entry로 재생성 후 yml을 갱신한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # 의존성 미설치 환경 대비
    yaml = None  # type: ignore[assignment]

SEO_KEYWORDS_FILE = Path(__file__).resolve().parent / "seo_keywords.yml"


def load_all(path: Path = SEO_KEYWORDS_FILE) -> dict[str, dict[str, Any]]:
    """YAML → {category_key: entry}. 파일·yaml 모듈 없으면 빈 dict."""
    if yaml is None or not path.exists():
        return {}
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cats = data.get("categories") if isinstance(data, dict) else None
    if not isinstance(cats, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, entry in cats.items():
        if isinstance(entry, dict) and entry.get("primary"):
            out[str(key)] = entry
    return out


def get(category_key: str, path: Path = SEO_KEYWORDS_FILE) -> dict[str, Any] | None:
    """카테고리 전체 엔트리(primary·core·secondary·메타) 반환. 없으면 None."""
    return load_all(path).get(category_key)


def gate_config(category_key: str, path: Path = SEO_KEYWORDS_FILE) -> dict[str, Any] | None:
    """validator/seo.py payload["seo"]에 바로 넣을 형태로 반환.

    {primary, secondary, [density_floor], [density_ceil]}. 없으면 None.
    """
    entry = get(category_key, path)
    if not entry:
        return None
    cfg: dict[str, Any] = {
        "primary": entry.get("primary"),
        "secondary": list(entry.get("secondary") or []),
    }
    if entry.get("density_floor") is not None:
        cfg["density_floor"] = entry["density_floor"]
    if entry.get("density_ceil") is not None:
        cfg["density_ceil"] = entry["density_ceil"]
    return cfg


def all_category_keys(path: Path = SEO_KEYWORDS_FILE) -> list[str]:
    """정의된 카테고리 key 정렬 목록."""
    return sorted(load_all(path).keys())
