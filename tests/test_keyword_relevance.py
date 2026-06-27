"""keyword_relevance — 키워드→글 경로 상품 적합성 가드 (세션 #29 B-2).

#28→#29 라이브 테스트가 적발한 결함: 키워드→글 생성 경로가 product_filter를 적용하지 않아
'컴퓨터의자' 글에 '화장/드레싱 의자'가 결합됐다(카테고리 경로엔 있던 안전망이 키워드 경로엔 없음).
근본 수정: 키워드를 카테고리에 매핑해 검증된 require/exclude를 자동수집 알리 상품에 적용.
"""

from __future__ import annotations

from collector import keyword_relevance as kr


class TestResolveCategory:
    def test_secondary_keyword_maps(self) -> None:
        assert kr.resolve_category("컴퓨터의자") == "office-chair"
        assert kr.resolve_category("게이밍의자") == "office-chair"

    def test_spacing_normalized(self) -> None:
        # '컴퓨터 의자'(공백)와 '컴퓨터의자'를 같게 매핑
        assert kr.resolve_category("컴퓨터 의자") == "office-chair"

    def test_primary_keyword_maps(self) -> None:
        assert kr.resolve_category("컴퓨터 책상") == "desk"

    def test_unknown_keyword_is_none(self) -> None:
        assert kr.resolve_category("강아지 사료") is None
        assert kr.resolve_category("") is None


class TestEffectiveExclude:
    """★ 자기차단 방지(§0 비판점검): 유효 제외어 = 카테고리 제외어 - 키워드에 든 단어."""

    def test_keyword_token_removed_from_exclude(self) -> None:
        # '안락의자'는 office-chair.secondary지만 exclude엔 '안락'이 있음 → 그대로면 자기 자신 전량 탈락
        terms = kr.relevance_terms("안락의자")
        assert terms is not None
        _require_any, _require_all, exclude, slug = terms
        assert slug == "office-chair"
        assert "안락" not in exclude  # 키워드에 든 제외어는 해제(자기차단 방지)
        assert "화장" in exclude  # 키워드에 없는 off-target 제외어는 유지

    def test_computer_chair_keeps_offtarget_excludes(self) -> None:
        terms = kr.relevance_terms("컴퓨터의자")
        assert terms is not None
        _require_any, _require_all, exclude, _slug = terms
        assert "화장" in exclude  # 드레싱/화장 의자 제외 유지(draft #2 케이스)

    def test_unknown_keyword_no_terms(self) -> None:
        assert kr.relevance_terms("강아지 사료") is None


class TestPublishability:
    """세션 #39: 키워드만으로 '생성 전' 판정 가능한 발행가능성(필요조건) — (ok, code).

    거부·skip이 아니라 후순위 강등·가시화의 단일 소스. eligible의 미매핑 보류와 정확히 일치
    (미매핑은 쿠팡 유무와 무관하게 보류되므로 여기서도 매핑 기준만 본다).
    """

    def test_mapped_keyword(self) -> None:
        ok, code = kr.publishability("컴퓨터의자")
        assert ok is True and code == "mapped"

    def test_unmapped_keyword(self) -> None:
        ok, code = kr.publishability("책상정리함")
        assert ok is False and code == "unmapped"

    def test_newly_mapped_keyword_publishable(self) -> None:
        # #39 매핑 보강된 키워드는 publishable
        ok, code = kr.publishability("메쉬의자")
        assert ok is True and code == "mapped"


class TestFilterProducts:
    def test_draft2_dressing_chair_dropped(self) -> None:
        # 세션 #29 draft #2 실제 적발: '컴퓨터의자' 글에 결합된 화장/드레싱 의자
        real_offtarget = "침실 의자, 등받이 화장 의자, 드레싱 의자, 패브릭, 대학 기숙사 컴퓨터 의자"
        products = [
            {"source_product_id": "ok", "name": "티야드 사무용 의자 허리받침 컴퓨터 메쉬 의자"},
            {"source_product_id": "bad", "name": real_offtarget},
        ]
        kept, dropped = kr.filter_products("컴퓨터의자", products)
        assert {p["source_product_id"] for p in kept} == {"ok"}
        assert {p["source_product_id"] for p in dropped} == {"bad"}  # 화장/드레싱 → 제외

    def test_anllak_chair_not_self_blocked(self) -> None:
        # '안락의자' 키워드는 안락 의자를 걸러내면 안 됨(자기차단 방지 실증)
        products = [{"source_product_id": "a", "name": "푹신한 1인용 안락 의자 패브릭형"}]
        kept, dropped = kr.filter_products("안락의자", products)
        assert len(kept) == 1 and not dropped

    def test_unknown_keyword_passes_all(self) -> None:
        # 매핑 없는 키워드는 gather 단계 fail-open(전량 통과) — 보류는 발행 배선(B)에서 처리
        products = [{"source_product_id": "x", "name": "아무 상품"}]
        kept, dropped = kr.filter_products("강아지 사료", products)
        assert len(kept) == 1 and not dropped

    def test_accessory_excluded_for_chair_keyword(self) -> None:
        # 의자 키워드에 섞인 액세서리(커버·방석)는 제외
        products = [
            {"source_product_id": "chair", "name": "인체공학 사무용 의자"},
            {"source_product_id": "cover", "name": "의자 커버 방석 세트"},
        ]
        kept, dropped = kr.filter_products("컴퓨터의자", products)
        assert {p["source_product_id"] for p in kept} == {"chair"}
        assert {p["source_product_id"] for p in dropped} == {"cover"}
