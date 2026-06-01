"""product_filter — 수집 상품 관련성·할인 신뢰 필터 (세션 #16).

라이브 수집 실측에서 드러난 두 문제의 근본 대책(§0):
1. **카테고리 오염** — "computer desk" 검색에 스탠드·홀더·송풍기·진공·의자·차량용 테이블 등
   비대상이 섞임. → 카테고리 핵심어 포함 필수 + 액세서리/타카테고리 제외어.
2. **부풀린 정가/과장 할인** — 알리 정가 패딩으로 "90%↓"처럼 과장. → 할인율 상한 초과 시
   할인 신호를 신뢰하지 않음(가격만 표시). 공정위 가격표시 정확성 보호.

수집기·전체제품 카탈로그·추천 카드가 공통으로 쓰는 안전망. 검색어/밴드 튜닝(search_keywords.yml)은
관련성을 1차로 높이고, 본 필터가 잔여 오염을 거른다.
"""

from __future__ import annotations

# 책상 카테고리 기본 제외어(액세서리·타카테고리). 카테고리별로 override 가능.
DESK_EXCLUDE: tuple[str, ...] = (
    "스탠드",
    "홀더",
    "컵",
    "송풍기",
    "진공",
    "청소기",
    "클램프",
    "팬 ",
    "선풍기",
    "차량",
    "자동차",
    "테슬라",
    "트레이",
    "받침",
    "라이저",
    "의자",
    "매트",
    "마우스",
    "키보드",
    "정리함",
    "충전",
    "카메라",
    "거치대",
    "브래킷",
    "펌프",
    "먼지",
    "침대",
    "모니터암",
    "암 ",
    "후드",
    "조명",
    "스피커",
    "가방",
    "인형",
    "미니어처",
    "bjd",
    "지지대",
)

DISCOUNT_CAP = 70  # % — 초과 할인율은 알리 정가 패딩으로 보고 신뢰 안 함(가격만 표시)


def is_relevant(
    name: str,
    *,
    require_any: tuple[str, ...] = ("책상",),
    require_all: tuple[tuple[str, ...], ...] = (),
    exclude_terms: tuple[str, ...] = DESK_EXCLUDE,
) -> bool:
    """상품명이 카테고리에 관련 있는지. (require_all 그룹 모두) ∧ (require_any 중 하나) ∧ (exclude 미포함).

    require_all: '타입+대상' 동시 검증(세션 #19). 각 그룹은 OR-set이고, **모든 그룹**을 만족해야 함.
        예) [[노트북, 랩탑], [거치대, 스탠드]] → 노트북 계열 AND 거치대 계열을 둘 다 가진 상품만 통과.
        → "노트북"만 언급한 캠핑 테이블은 거치대 그룹 미충족으로 구조적 탈락(OR 필터의 한계 보완).
    require_any: 적어도 하나는 포함해야 하는 카테고리 핵심어(단일 그룹 호환 — 기존 카테고리용).
    exclude_terms: 하나라도 포함하면 제외(액세서리·타카테고리).
    """
    n = (name or "").lower()
    # require_all: 각 그룹(OR)을 전부(AND) 만족해야 함 — 품목 정체성('이게 그 물건인가') 강제
    for group in require_all:
        if group and not any(t.lower() in n for t in group):
            return False
    if require_any and not any(t.lower() in n for t in require_any):
        return False
    return not any(t.lower() in n for t in exclude_terms)


def trusted_discount(discount_pct: int | None, *, cap: int = DISCOUNT_CAP) -> int | None:
    """신뢰 가능한 할인율만 반환. None/0이하/cap 초과(정가 패딩 의심)는 None(=할인 신호 없음).

    cap 초과를 None으로 돌려 '90%↓' 같은 과장 표시를 차단(공정위 가격표시 정확성, §0).
    """
    if discount_pct is None or discount_pct <= 0 or discount_pct > cap:
        return None
    return discount_pct
