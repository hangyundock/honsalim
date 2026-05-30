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
