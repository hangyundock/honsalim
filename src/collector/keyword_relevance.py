"""keyword_relevance — 키워드→글 생성 경로의 상품 적합성 가드 (세션 #29, B-2).

키워드를 카테고리에 매핑(``seo_keywords.yml``)하고, 그 카테고리의 검증된 관련성 정의
(``category_sources.yml``: require/exclude)를 **자동수집 알리 상품**에 적용한다. 카테고리 경로엔
이미 있던 ``product_filter.is_relevant`` 안전망을 키워드 경로에도 연결하는 것(새 필터 발명 아님).
쿠팡 수동 배너는 사람이 고른 것이라 필터 대상이 아니다.

★ 핵심 보정(§0 비판점검): **유효 제외어 = 카테고리 제외어 - 키워드에 든 단어.**
  ``office-chair`` 제외어엔 '안락'이 있는데 secondary엔 '안락의자'도 있어, 그대로 적용하면
  '안락의자' 키워드가 자기 자신을 전량 탈락시킨다(0개→영구 미발행). 키워드에 포함된 제외어는
  그 생성 한정으로 해제해 자기차단을 막는다.

매핑 없는 키워드는 (보수적으로) gather 단계에서 전량 통과 — fail-open. 자동발행 보류(fail-closed)는
발행 배선 단계(B)에서 relevance 신호로 별도 처리한다. 비용 0(문자열 매칭)·무인 적합.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from collector import category_collect, product_filter, seo_keywords

# (require_any, require_all, effective_exclude, category_slug)
RelevanceTerms = tuple[tuple[str, ...], tuple[tuple[str, ...], ...], tuple[str, ...], str]


def _despace(s: str) -> str:
    """공백 제거 + 소문자 — '컴퓨터 의자'와 '컴퓨터의자'를 같게 본다."""
    return "".join((s or "").split()).lower()


def resolve_category(keyword: str, seo: dict[str, dict[str, Any]] | None = None) -> str | None:
    """키워드가 속한 카테고리 slug — seo_keywords.yml primary/core/secondary 정확 매칭(공백·대소문자 무시).

    부분일치는 쓰지 않는다(오매핑 방지) — '컴퓨터의자'는 office-chair, '강아지 사료'는 None.
    """
    kw = _despace(keyword)
    if not kw:
        return None
    data = seo if seo is not None else seo_keywords.load_all()
    for slug, entry in data.items():
        cands = [entry.get("primary"), entry.get("core"), *(entry.get("secondary") or [])]
        if any(c and _despace(str(c)) == kw for c in cands):
            return slug
    return None


def relevance_terms(keyword: str) -> RelevanceTerms | None:
    """키워드 → (require_any, require_all, effective_exclude, category_slug). 매핑 없으면 None.

    effective_exclude = 카테고리 exclude_terms - 키워드에 포함된 단어(자기차단 방지·위 docstring).
    """
    slug = resolve_category(keyword)
    if slug is None:
        return None
    spec = category_collect.load_sources().get(slug)
    if spec is None:
        return None
    kw = _despace(keyword)
    eff_exclude = tuple(t for t in spec.exclude_terms if _despace(t) not in kw)
    return spec.require_any, spec.require_all, eff_exclude, slug


def category_blocked(conn: sqlite3.Connection, slug: str) -> bool:
    """slug 카테고리가 '행이 있는데 비공개(draft)'면 True — 무인 자동 경로 차단용 (세션 #45).

    draft 카테고리에 매핑된 글은 공개 카테고리 페이지가 없어 빵부스러기·내부링크가 폴백으로
    강등된 고아 글이 된다(laptop-stand가 실제 이 상태). 행이 아예 없거나(미프로비저닝 DB·테스트)
    categories 테이블이 없으면(구 스키마) 막지 않는다(fail-open) — 운영 위험은 '행이 있는데
    draft'뿐이고, 과차단은 완전무인 자동보충·기존 승인 흐름을 죽인다(§0 멈추지 않음).
    소비처: keyword_recommender.auto_pick_keyword(추천 보충) · auto_approve.eligible(자동 승인).
    """
    try:
        row = conn.execute("SELECT status FROM categories WHERE slug = ?", (slug,)).fetchone()
    except sqlite3.OperationalError:  # categories 없음(구 스키마)
        return False
    return bool(row) and str(row[0]) != "published"


def publishability(keyword: str) -> tuple[bool, str]:
    """키워드만으로 '생성 전' 판정 가능한 발행가능성(필요조건) — (ok, code). 세션 #39.

    생성 전에 확실히 아는 건 '카테고리에 매핑되나'(resolve_category) 하나뿐이다. 매핑이 없으면
    auto_approve.eligible이 featured 검사 이전에 '적합성 검증 불가'로 보류하므로(코드 'unmapped')
    쿠팡 첨부 여부와 무관하게 자동 발행이 안 된다 — 그래서 여기서도 쿠팡으로 면제하지 않는다(eligible과
    정확히 일치). off-target·featured>0·seo 통과는 글·상품을 만든 뒤에만 알 수 있어 여기선 못 본다.

    ★따라서 ok=True는 '발행 보장'이 아니라 '생성 전엔 명백히 막히지 않음'(필요조건)이다 — 이 신호로
    키워드를 **거부/skip 하지 말 것**(추천 롱테일·완전무인 자동보충을 죽임). 후순위 강등 + 가시화
    (어떤 키워드가 왜 막히는지 보고)에만 쓴다. code: 'mapped' | 'unmapped'(드리프트 방지 단일 소스).
    """
    if resolve_category(keyword) is None:
        return False, "unmapped"
    return True, "mapped"


def filter_products(
    keyword: str, products: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """자동수집 상품을 키워드-카테고리 적합성으로 분리 → (kept, dropped).

    매핑 없는 키워드는 (전량, []) — gather 단계 fail-open(보수적). 적합 판정은 카테고리 경로와
    동일한 product_filter.is_relevant(검증된 안전망)을 그대로 쓴다.
    """
    terms = relevance_terms(keyword)
    if terms is None:
        return list(products), []
    require_any, require_all, exclude, _slug = terms
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for p in products:
        if product_filter.is_relevant(
            str(p.get("name", "")),
            require_any=require_any,
            require_all=require_all,
            exclude_terms=exclude,
        ):
            kept.append(p)
        else:
            dropped.append(p)
    return kept, dropped
