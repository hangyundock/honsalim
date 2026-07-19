"""seo_keywords — 카테고리별 SEO 키워드 세트 로더 (대표 + 보조). 세션 #15 신설.

데이터: ``src/collector/seo_keywords.yml`` (운영자 검토·편집 대상, §2-마 인간 편집 게이트).
생성: ``collector.keyword_research.build_entry`` (네이버 검색광고 실검색량 자동 선별).
소비: ``validator/seo.py`` 게이트(payload["seo"]) + enrich 프롬프트 2층 키워드 배치.

매 빌드마다 네이버를 재호출하지 않고 이 yml을 읽는다(rate limit·재현성). 검색량이 크게
변하면 build_entry로 재생성 후 yml을 갱신한다.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
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


def _norm_kw(text: Any) -> str:
    """교차 중복 비교용 정규화 — writer.keyword_recommender._norm과 동일 규칙(NFKC+공백 제거+소문자)."""
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", str(text or ""))).lower()


def lint_alignment(
    conn: sqlite3.Connection | None = None,
    *,
    path: Path = SEO_KEYWORDS_FILE,
    sources_path: Path | None = None,
) -> list[tuple[str, str]]:
    """씨앗 데이터 정합 lint — [(code, 문제설명)] 반환(빈 리스트=정상). 세션 #45 재발방지 가드.

    code:
    - 'drift'             씨앗 키 ∉ category_sources — 키 오타면 resolve_category까지만 되고 수집
                          정의가 없어 relevance_terms=None → 자동승인 'unmapped' 보류·ali 건너뜀의
                          침묵 실패 체인이 된다.
    - 'dup'               같은 정규화 키워드(primary/core/secondary)가 두 카테고리에 존재 —
                          resolve_category가 yml 순서 first-match라 뒤 카테고리 키워드를 앞
                          카테고리로 오매핑(#45 실증: 모니터암이 monitor-stand로 흡수).
    - 'published_no_seed' (conn 제공 시) published 카테고리에 씨앗 없음 — 그 클러스터는 추천·
                          키워드 글이 구조적으로 불가능(#45 도마·미니밥솥 갭의 재발 방지).
                          provision-category가 씨앗을 만들지 않으므로 공개 시 사람이 씨앗을
                          투입해야 하며, 누락 시 doctor가 경고로 가시화한다.
    """
    from collector import category_collect  # 지연 임포트(순환 회피)

    issues: list[tuple[str, str]] = []
    entries = load_all(path)
    if sources_path is not None:
        sources = category_collect.load_sources(sources_path)
    else:
        sources = category_collect.load_sources()

    for key in entries:  # yml 순서 유지 — 보고 순서도 사람이 파일에서 찾기 쉽게
        if key not in sources:
            issues.append(
                ("drift", f"씨앗 {key!r}가 category_sources.yml에 없음(키 오타·수집 정의 누락)")
            )

    owner: dict[str, str] = {}
    for key, entry in entries.items():  # yml 순서 = resolve_category first-match 순서
        for kw in [entry.get("primary"), entry.get("core"), *(entry.get("secondary") or [])]:
            norm = _norm_kw(kw)
            if not norm:
                continue
            prev = owner.get(norm)
            if prev is None:
                owner[norm] = key
            elif prev != key:
                issues.append(
                    ("dup", f"{kw!r}가 {prev}·{key} 양쪽에 있음 — first-match로 {prev}에 오매핑")
                )

    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT slug FROM categories WHERE status = 'published' ORDER BY slug"
            ).fetchall()
        except sqlite3.OperationalError:  # categories 없음(구 스키마·빈 DB) — 점검 생략
            rows = []
        for (slug,) in rows:
            if str(slug) not in entries:
                issues.append(
                    (
                        "published_no_seed",
                        f"공개 카테고리 {slug!r}에 씨앗 없음 — 추천·키워드 글 불가(공개 시 씨앗 투입 필요)",
                    )
                )
    return issues
