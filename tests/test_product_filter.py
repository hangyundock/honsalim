"""product_filter 회귀 테스트 (세션 #16) — 관련성·할인 신뢰 필터.

라이브 수집 실측 오염 사례(송풍기·스탠드·의자·90% 과장할인) 기반. 출처: BACKEND §8-1.
"""

from __future__ import annotations

from collector import product_filter as pf


class TestRelevant:
    def test_real_desk_passes(self) -> None:
        assert pf.is_relevant("현대적인 높이 조절 가능한 컴퓨터 책상, 가정 사무실용") is True
        assert pf.is_relevant("L자형 원목 책상 테이블 코너 책상") is True

    def test_accessory_dropped(self) -> None:
        # 실측 오염 사례 — 책상 검색에 섞여 들어온 비책상
        assert pf.is_relevant("접이식 높이 조절 컴퓨터 스탠드, 수납 서랍") is False  # 스탠드
        assert pf.is_relevant("모니터 스탠드 라이저, 수납 서랍 포함") is False  # 스탠드/라이저
        assert pf.is_relevant("스토리지 데스크 컵 홀더 컴퓨터 책상 고정 컵홀더") is False  # 홀더/컵
        assert pf.is_relevant("전기 공기 송풍기 먼지 떨이 컴퓨터 책상 청소") is False  # 송풍기/먼지
        assert pf.is_relevant("현대식 컴퓨터 의자 사무실 의자 가정용 책상") is False  # 의자
        assert pf.is_relevant("테슬라 모델 3Y 차량용 테이블 컴퓨터 책상") is False  # 차량/테슬라
        assert pf.is_relevant("1:6 BJD 인형 집 컴퓨터 책상 미니어처") is False  # 인형/미니어처/bjd
        assert pf.is_relevant("비천공 테이블 다리 지지대 책상 컴퓨터 책상") is False  # 지지대

    def test_require_any_missing(self) -> None:
        # '책상' 없는 일반 테이블/스탠드는 제외 (require_any 미충족)
        assert pf.is_relevant("Foldable Laptop Stand Tray") is False

    def test_custom_require_and_exclude(self) -> None:
        assert pf.is_relevant("게이밍 의자 메쉬", require_any=("의자",), exclude_terms=()) is True
        assert (
            pf.is_relevant("게이밍 의자 발받침", require_any=("의자",), exclude_terms=("발받침",))
            is False
        )


class TestRequireAll:
    """require_all('타입+대상' 동시 충족) — OR 필터가 놓치던 오염 차단 (세션 #19 laptop-stand).

    근본 원인: require_any(OR)는 '노트북'만 언급하면 통과 → 캠핑 테이블·휴대폰 스탠드가 섞임.
    대책: 그룹을 모두(AND) 만족(노트북 계열 ∧ 거치대 계열)해야 통과 → 품목 정체성 강제.
    """

    _LAPTOP = (
        ("노트북", "랩탑", "맥북", "laptop", "macbook"),
        ("거치대", "스탠드", "받침", "홀더", "마운트", "stand", "holder", "riser"),
    )

    def test_real_laptop_stand_passes(self) -> None:
        assert (
            pf.is_relevant(
                "UGREEN 맥북 에어 프로용 수직 노트북 스탠드 홀더 알루미늄 접이식",
                require_any=(),
                require_all=self._LAPTOP,
                exclude_terms=(),
            )
            is True
        )

    def test_camping_table_mentioning_laptop_rejected(self) -> None:
        # ★ 실측 버그: "노트북"만 언급한 캠핑 테이블이 OR 필터로 통과하던 사례
        name = "Sonuto 대나무 접이식 테이블 스테인리스 스틸 경량 미니 데스크 캠핑 서재 책상 노트북"
        assert (
            pf.is_relevant(name, require_any=("노트북",), exclude_terms=()) is True
        )  # OR=버그 재현
        assert (
            pf.is_relevant(name, require_any=(), require_all=self._LAPTOP, exclude_terms=())
            is False
        )  # require_all=거치대 그룹 미충족으로 구조적 탈락

    def test_phone_stand_rejected_by_exclude(self) -> None:
        name = "실리콘 접이식 휴대폰 스탠드 태블릿 노트북 디스플레이 스탠드"
        # require_all은 통과(노트북+스탠드)하지만 exclude(휴대폰/태블릿)로 차단 — 2중 방어
        assert (
            pf.is_relevant(name, require_any=(), require_all=self._LAPTOP, exclude_terms=()) is True
        )
        assert (
            pf.is_relevant(
                name, require_any=(), require_all=self._LAPTOP, exclude_terms=("휴대폰", "태블릿")
            )
            is False
        )

    def test_all_groups_must_match(self) -> None:
        groups = (("노트북",), ("거치대",))
        kw = {"require_any": (), "exclude_terms": ()}  # require_all 로직만 격리 검증
        assert pf.is_relevant("노트북 거치대", require_all=groups, **kw) is True
        assert (
            pf.is_relevant("노트북 가방", require_all=groups, **kw) is False
        )  # 거치대 그룹 미충족
        assert (
            pf.is_relevant("모니터 거치대", require_all=groups, **kw) is False
        )  # 노트북 그룹 미충족


class TestTrustedDiscount:
    def test_normal_discount_kept(self) -> None:
        assert pf.trusted_discount(52) == 52
        assert pf.trusted_discount(35) == 35

    def test_inflated_discount_dropped(self) -> None:
        # 90%·74% 등 정가 패딩 의심 → None (할인 신호 미표시)
        assert pf.trusted_discount(90) is None
        assert pf.trusted_discount(74) is None

    def test_none_and_zero(self) -> None:
        assert pf.trusted_discount(None) is None
        assert pf.trusted_discount(0) is None

    def test_custom_cap(self) -> None:
        assert pf.trusted_discount(60, cap=50) is None
        assert pf.trusted_discount(40, cap=50) == 40


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
