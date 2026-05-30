"""키워드 리서치 회귀 테스트 (세션 #15) — 필터·선별 로직.

라이브 네트워크 없이 fetch 의존성 주입으로 검증. 실데이터("사무용 의자" 665개) 모방 픽스처.
출처: BACKEND §8-1.
"""

from __future__ import annotations

from typing import Any

from collector import keyword_research as kr

# "사무용 의자" 라이브 데이터 모방 (세션 #15 실측 값 기반)
ROWS: list[dict[str, Any]] = [
    {"keyword": "의자", "volume": 58300, "competition": "중간"},  # 대표 부분문자열(redundant)
    {"keyword": "컴퓨터의자", "volume": 32700, "competition": "높음"},
    {"keyword": "게이밍의자", "volume": 30100, "competition": "높음"},
    {"keyword": "사무용 의자", "volume": 26100, "competition": "중간"},  # == seed
    {"keyword": "책상의자", "volume": 20620, "competition": "중간"},
    {"keyword": "서울대의자", "volume": 11430, "competition": "중간"},  # 브랜드(시디즈 별칭)
    {"keyword": "듀오백의자", "volume": 8590, "competition": "중간"},  # 브랜드
    {"keyword": "메쉬의자", "volume": 3210, "competition": "중간"},
    {"keyword": "접이식테이블", "volume": 41810, "competition": "중간"},  # 의자 아님(no_core)
    {"keyword": "중고의자", "volume": 5000, "competition": "중간"},  # 거래성
    {"keyword": "회의실의자", "volume": 1500, "competition": "중간"},  # 검색량 하한 미만
    {"keyword": "컴퓨터의자", "volume": 32700, "competition": "높음"},  # 중복
]


def _fetch(_seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
    return [dict(r) for r in ROWS]


class TestResearch:
    def test_primary_is_seed(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        assert out["primary"] == "사무용 의자"

    def test_secondary_sorted_by_volume_and_filtered(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        # 채택: 컴퓨터의자>게이밍의자>책상의자>메쉬의자 (검색량 내림차순)
        assert out["secondary"] == ["컴퓨터의자", "게이밍의자", "책상의자", "메쉬의자"]

    def test_seed_excluded_from_secondary(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        assert "사무용 의자" not in out["secondary"]

    def test_dedup(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        assert out["secondary"].count("컴퓨터의자") == 1

    def test_brand_excluded(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons["서울대의자"].startswith("brand")
        assert reasons["듀오백의자"].startswith("brand")
        assert "서울대의자" not in out["secondary"]

    def test_transactional_excluded(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons["중고의자"].startswith("transactional")

    def test_no_core_excluded(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons["접이식테이블"] == "no_core"

    def test_low_volume_excluded(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons["회의실의자"] == "low_volume"

    def test_redundant_in_primary_excluded(self) -> None:
        # 바로 그 "의자" 사례 — 대표 부분문자열이라 검색량 1위여도 보조에서 제외
        out = kr.research_keywords("사무용 의자", fetch=_fetch)
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons["의자"] == "redundant_in_primary"
        assert "의자" not in out["secondary"]

    def test_max_secondary_cap(self) -> None:
        out = kr.research_keywords("사무용 의자", fetch=_fetch, max_secondary=2)
        assert out["secondary"] == ["컴퓨터의자", "게이밍의자"]

    def test_custom_brand_block(self) -> None:
        # 게이밍을 브랜드처럼 차단(오버라이드) → 게이밍의자 제외
        out = kr.research_keywords("사무용 의자", fetch=_fetch, brand_block=("게이밍",))
        assert "게이밍의자" not in out["secondary"]

    def test_exclude_terms_off_target(self) -> None:
        # off-target 단어(예 책상 카테고리의 '학생') 제외 — 검색량 높아도 대상 부적합
        out = kr.research_keywords("사무용 의자", fetch=_fetch, exclude_terms=("게이밍",))
        reasons = {e["keyword"]: e["reason"] for e in out["excluded"]}
        assert reasons.get("게이밍의자") == "off_target:게이밍"
        assert "게이밍의자" not in out["secondary"]

    def test_dry_run_no_network(self) -> None:
        out = kr.research_keywords("사무용 의자", dry_run=True)
        assert out["dry_run"] is True
        assert out["secondary"] == []


class TestExclusionReason:
    def test_no_core(self) -> None:
        assert (
            kr.exclusion_reason(
                "접이식테이블",
                41810,
                core_ns="의자",
                volume_floor=2000,
                brands=(),
                transactional=(),
            )
            == "no_core"
        )

    def test_brand(self) -> None:
        r = kr.exclusion_reason(
            "듀오백의자",
            8590,
            core_ns="의자",
            volume_floor=2000,
            brands=("듀오백",),
            transactional=(),
        )
        assert r == "brand:듀오백"

    def test_transactional(self) -> None:
        r = kr.exclusion_reason(
            "중고의자",
            5000,
            core_ns="의자",
            volume_floor=2000,
            brands=(),
            transactional=("중고",),
        )
        assert r == "transactional:중고"

    def test_low_volume(self) -> None:
        r = kr.exclusion_reason(
            "회의실의자",
            1500,
            core_ns="의자",
            volume_floor=2000,
            brands=(),
            transactional=(),
        )
        assert r == "low_volume"

    def test_off_target(self) -> None:
        r = kr.exclusion_reason(
            "유아책상",
            5480,
            core_ns="책상",
            volume_floor=2000,
            brands=(),
            transactional=(),
            exclude_terms=("유아", "어린이"),
        )
        assert r == "off_target:유아"

    def test_clean_passes(self) -> None:
        r = kr.exclusion_reason(
            "메쉬의자",
            3210,
            core_ns="의자",
            volume_floor=2000,
            brands=("듀오백",),
            transactional=("중고",),
        )
        assert r is None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
