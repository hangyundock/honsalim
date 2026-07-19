"""카테고리 SEO 키워드 리서치 — 네이버 연관검색어 → 수익성 보조키워드 자동 선별.

출처: AutoBlog `keyword_collector.expand_related` 발상 + 세션 #15 라이브 검증
      ("사무용 의자" 665개 연관검색어 실데이터로 필터 규칙 확정).

흐름:
  seed(한글 대표어, 예 "사무용 의자")
    → naver_searchad.fetch_related_keywords (월 검색량·경쟁도)
    → 필터 ① 카테고리 핵심어 포함(core, 예 "의자") ② 브랜드 제외 ③ 거래성 제외 ④ 검색량 하한
    → 검색량순 상위 N개 = 보조키워드
  결과 = {"primary": seed, "secondary": [...]} → validator/seo.py 게이트 + enrich 프롬프트에 주입.

가드레일(§0 진실성):
- **브랜드 제외** — 듀오백·시디즈 등 우리가 알리로 못 파는 브랜드 키워드는 헛 트래픽 +
  Google Helpful Content 저품질 위험이라 차단.
- **거래성 제외** — 중고·렌탈 등은 우리 페이지로 충족 불가.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from . import naver_searchad

# 사무용 의자/가구 카테고리 기본 브랜드 blocklist (우리가 알리로 못 파는 브랜드 — 오인·헛트래픽 차단).
# 카테고리별로 research_keywords(brand_block=...)로 확장/교체 가능 (세션 #15 라이브 관측 + 국내 주요 브랜드).
DEFAULT_BRAND_BLOCK: tuple[str, ...] = (
    "듀오백",
    "시디즈",
    "서울대의자",  # 시디즈 별칭
    "린백",
    "파트라",
    "일룸",
    "한샘",
    "데스커",
    "이케아",
    "퍼시스",
    "코아스",
)

# 거래성·비충족 키워드 (우리 어필리에이트 페이지로 충족 불가).
DEFAULT_TRANSACTIONAL_BLOCK: tuple[str, ...] = (
    "중고",
    "렌탈",
    "렌트",
    "대여",
    "리퍼",
    "직거래",
    "리스",
)

VOLUME_FLOOR = 2000  # 월 검색량 하한 (세션 #15 합의)
MAX_SECONDARY = 12  # 보조키워드 최대 개수


def _ns(text: str | None) -> str:
    return re.sub(r"\s", "", text or "")


def exclusion_reason(
    keyword_ns: str,
    volume: int,
    *,
    core_ns: str,
    volume_floor: int,
    brands: tuple[str, ...],
    transactional: tuple[str, ...],
    seed_ns: str = "",
    exclude_terms: tuple[str, ...] = (),
    require_terms: tuple[str, ...] = (),
) -> str | None:
    """제외 사유 반환 (없으면 None = 채택 후보).

    순서: 핵심어→세그먼트(require)→중복→off-target→브랜드→거래성→검색량.
    exclude_terms: 대상 부적합(off-target) 단어 — 예 책상 카테고리에서 학생·유아 책상 제외
    (검색량은 높아도 1인가구 홈오피스와 대상이 달라 헛 트래픽·Helpful Content 저품질 위험).
    require_terms: 니치 한정어 — 하나라도 포함해야 채택(예 미니밥솥 카테고리의 미니·1인·소형).
    core만으로 니치를 못 좁히는 카테고리(밥솥 전체 ≠ 미니밥솥)에서 이길 수 없는 헤드·
    세그먼트 이탈(6인용 등) 연관검색어가 씨앗·추천을 오염시키는 것을 구조로 차단(세션 #45).
    빈 튜플이면 미적용(기존 카테고리 동작 불변).
    """
    if core_ns and core_ns not in keyword_ns:
        return "no_core"
    if require_terms and not any(_ns(r) in keyword_ns for r in require_terms):
        return "no_require"
    # 대표키워드에 통째로 포함된 부분문자열(예 "의자" ⊂ "사무용의자")은 본문에 자동 포함 →
    # 타겟 가치 없는 중복이라 제외 (세션 #15: 바로 그 "의자" 사례).
    if seed_ns and keyword_ns in seed_ns:
        return "redundant_in_primary"
    for x in exclude_terms:
        if _ns(x) in keyword_ns:
            return f"off_target:{x}"
    for b in brands:
        if _ns(b) in keyword_ns:
            return f"brand:{b}"
    for t in transactional:
        if _ns(t) in keyword_ns:
            return f"transactional:{t}"
    if volume < volume_floor:
        return "low_volume"
    return None


def research_keywords(
    seed: str,
    *,
    core: str | None = "의자",
    volume_floor: int = VOLUME_FLOOR,
    max_secondary: int = MAX_SECONDARY,
    brand_block: tuple[str, ...] | None = None,
    transactional_block: tuple[str, ...] | None = None,
    exclude_terms: tuple[str, ...] = (),
    require_terms: tuple[str, ...] = (),
    fetch: Callable[..., list[dict[str, Any]]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """seed → 보조키워드 선별. validator/seo.py에 주입할 {primary, secondary} 포함 dict 반환.

    매개변수:
    - core: 카테고리 핵심어(예 "의자"). 포함 안 한 연관어는 타 카테고리로 보고 제외. None이면 미적용.
    - exclude_terms: 대상 부적합 단어(예 책상 카테고리의 학생·유아). 포함 시 off_target 제외.
    - require_terms: 니치 한정어(예 미니밥솥의 미니·1인·소형) — 하나라도 포함해야 채택. 빈 튜플=미적용.
    - fetch: 의존성 주입용(테스트). 기본 naver_searchad.fetch_related_keywords.
    - dry_run: True면 네트워크 없이 빈 결과 + dry_run 표식.

    반환: {primary, secondary, candidates, excluded, dry_run}.
    """
    seed = (seed or "").strip()
    if dry_run:
        return {
            "primary": seed,
            "secondary": [],
            "candidates": [],
            "excluded": [],
            "dry_run": True,
        }

    fetch_fn = fetch or naver_searchad.fetch_related_keywords
    brands = brand_block if brand_block is not None else DEFAULT_BRAND_BLOCK
    transactional = (
        transactional_block if transactional_block is not None else DEFAULT_TRANSACTIONAL_BLOCK
    )
    core_ns = _ns(core) if core else ""
    seed_ns = _ns(seed)

    rows = fetch_fn(seed, dry_run=False)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for row in rows:
        kw = (row.get("keyword") or "").strip()
        if not kw:
            continue
        kw_ns = _ns(kw)
        if kw_ns in seen:
            continue
        seen.add(kw_ns)
        if kw_ns == seed_ns:  # 대표키워드 자신은 보조에서 제외
            continue
        vol = int(row.get("volume", 0) or 0)
        comp = row.get("competition", "unknown")
        reason = exclusion_reason(
            kw_ns,
            vol,
            core_ns=core_ns,
            volume_floor=volume_floor,
            brands=brands,
            transactional=transactional,
            seed_ns=seed_ns,
            exclude_terms=exclude_terms,
            require_terms=require_terms,
        )
        if reason:
            excluded.append({"keyword": kw, "volume": vol, "reason": reason})
            continue
        candidates.append({"keyword": kw, "volume": vol, "competition": comp})

    candidates.sort(key=lambda c: c["volume"], reverse=True)
    secondary = [c["keyword"] for c in candidates[:max_secondary]]

    return {
        "primary": seed,
        "secondary": secondary,
        "candidates": candidates,
        "excluded": excluded,
        "dry_run": False,
    }


def build_entry(
    seed: str,
    *,
    core: str | None = "의자",
    generated_at: str = "",
    source: str = "네이버 검색광고 연관검색어 자동 선별",
    **research_kwargs: Any,
) -> dict[str, Any]:
    """research_keywords 결과 → seo_keywords.yml 엔트리 형태(primary·core·secondary·메타).

    seo_keywords.yml 생성·갱신용. research_kwargs는 research_keywords로 전달(단, core 중복 금지).
    """
    res = research_keywords(seed, core=core, **research_kwargs)
    entry: dict[str, Any] = {
        "primary": res["primary"],
        "core": core,
        "secondary": res["secondary"],
    }
    if generated_at:
        entry["generated_at"] = generated_at
    if source:
        entry["source"] = source
    return entry
