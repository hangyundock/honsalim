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


def keyword_gate_config(
    keyword: str, category_key: str, path: Path = SEO_KEYWORDS_FILE
) -> dict[str, Any] | None:
    """키워드 파생 글용 seo 설정 — **그 키워드 자신을 대표키워드(primary)**, 카테고리 대표어는 보조로.

    카테고리 페이지는 ``gate_config``(카테고리 대표어=primary)를 쓰지만, 키워드로 만든 글은 그
    키워드(winnable 롱테일)를 타겟해야 한다(세션 #39 근본수정). 광의·고경쟁 카테고리어를 primary로
    쓰면 ① seo 게이트가 그 광의어를 소제목·제목·도입부에 강요해 키워드 중심 글이 자가복원으로도
    못 맞춰 영구 rejected 되고(라이브 적발), ② 신생 사이트가 못 이길 광의어를 타겟하는 SEO 비효율이
    생긴다. 카테고리 대표어는 보조키워드(존재는 warning·하드 fail 아님)로 강등해 맥락은 유지한다.

    category_key 미매핑이면 None(상위에서 fail-open). density 오버라이드는 gate_config에서 승계.
    """
    cfg = gate_config(category_key, path)
    if cfg is None:
        return None
    kw = (keyword or "").strip()
    if not kw:
        return cfg
    cat_primary = str(cfg.get("primary") or "").strip()
    cfg = dict(cfg)
    cfg["primary"] = kw
    cfg["secondary"] = [cat_primary] if cat_primary and cat_primary != kw else []
    return cfg


def all_category_keys(path: Path = SEO_KEYWORDS_FILE) -> list[str]:
    """정의된 카테고리 key 정렬 목록."""
    return sorted(load_all(path).keys())
