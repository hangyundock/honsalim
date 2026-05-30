"""seo 게이트 회귀 테스트 (세션 #15 — AutoBlog seo_gate.py 포팅).

출처: BACKEND §8-1 회귀 테스트 최우선 + AUTOBLOG_SEO_MASTER §3 + WRITING_SPEC.md [확정].

규칙: seo 게이트 패턴 추가/수정 시 본 테스트 100% 통과 필수.
"""

from __future__ import annotations

import json
from typing import Any

from validator import check_seo, serialize_report, validate_all

PRIMARY = "사무용 의자"
SECONDARY = ["가성비 사무용 의자", "메쉬 의자", "게이밍 의자", "인체공학 의자"]

# 충분히 최적화된 본문 — 대표키워드 정확형 밀도 ~2%, 제목/도입부/소제목 2개 포함,
# 보조키워드 4종 모두 산문에 자연 등장. 소제목 4개.
WELL_OPTIMIZED = """# 사무용 의자 추천 가이드

재택근무로 하루 여덟 시간을 앉아 있다면 의자는 디자인이 아니라 얼마나 오래 편하게 앉을 수 있느냐로 골라야 합니다. 사무용 의자를 한 번 잘못 고르면 허리와 목, 어깨가 일 년 내내 고생하게 됩니다. 이 글은 1인 가구와 재택 환경을 기준으로 어떤 의자가 누구에게 맞는지 차근차근 비교합니다.

## 사무용 의자 타입부터 이해하기

오래 앉아 집중하는 사람과 자주 일어나 움직이는 사람은 맞는 타입이 서로 다릅니다. 메쉬 의자는 통기성이 좋아 여름에도 시원하게 앉을 수 있고, 게이밍 의자는 등받이가 높아 상반신을 전체적으로 받쳐 줍니다. 무릎꿇이 의자는 척추 정렬을 자연스럽게 유도해 자세 교정에 도움이 됩니다.

## 가성비 사무용 의자 고르는 기준

요추 지지와 팔걸이 조절, 좌판 높이, 가스실린더 등급을 차례대로 확인하세요. 아무리 인체공학 의자라도 좌판 높이가 책상과 맞지 않으면 어깨가 들려 통증이 생깁니다. 가격이 저렴한 제품은 가스실린더가 약해 몇 달 만에 주저앉는 경우가 흔하니 후기를 꼭 살펴봐야 합니다.

## 메쉬 의자와 게이밍 의자 비교

여름철 땀과 통기성이 걱정이라면 메쉬 의자가 유리하고, 오래 기대 쉬는 시간이 많다면 게이밍 의자가 편합니다. 둘 다 높이 조절과 회전을 지원하는 모델이 대부분이라 책상 환경에 맞춰 고르면 됩니다.

## 흔한 실수와 정리

디자인만 보고 고르면 여덟 시간 착좌에는 오히려 독이 됩니다. 허리 건강을 우선한다면 요추를 받쳐 주는 모델을 먼저 살펴보세요.
"""


def _seo(
    primary: str = PRIMARY, secondary: list[str] | None = None, **extra: Any
) -> dict[str, Any]:
    d: dict[str, Any] = {
        "primary": primary,
        "secondary": secondary if secondary is not None else SECONDARY,
    }
    d.update(extra)
    return d


# ─── opt-in skip ─────────────────────────────────────────────────────


class TestSkip:
    def test_skip_when_no_seo_config(self) -> None:
        ok, rpt = check_seo({"body_md": "아무 본문"})
        assert ok is True
        assert rpt["issues"] == []
        assert rpt["metrics"].get("skipped") is True

    def test_skip_when_primary_empty(self) -> None:
        ok, rpt = check_seo({"body_md": "본문", "seo": {"primary": "  "}})
        assert ok is True
        assert rpt["metrics"].get("skipped") is True


# ─── 정상 통과 ───────────────────────────────────────────────────────


class TestPass:
    def test_well_optimized_passes_clean(self) -> None:
        ok, rpt = check_seo({"body_md": WELL_OPTIMIZED, "seo": _seo()})
        assert ok is True, rpt
        assert rpt["issues"] == []
        assert rpt["warnings"] == []  # 소제목 4개·보조 4종 모두 충족 → 경고 없음

    def test_metrics_in_range(self) -> None:
        _ok, rpt = check_seo({"body_md": WELL_OPTIMIZED, "seo": _seo()})
        m = rpt["metrics"]
        assert 1.0 <= m["density_pct"] <= 3.5
        assert m["headings_with_keyword"] >= 2
        assert m["secondary_missing"] == []

    def test_explicit_title_used(self) -> None:
        # body에 H1이 없어도 payload title로 제목 검사
        body = WELL_OPTIMIZED.split("\n", 1)[1]  # 첫 H1 줄 제거
        ok, rpt = check_seo({"body_md": body, "title": "사무용 의자 추천", "seo": _seo()})
        assert ok is True, rpt


# ─── 밀도 (하한·상한 둘 다) ──────────────────────────────────────────


class TestDensity:
    def test_fail_density_low(self) -> None:
        # 대표키워드는 제목·도입부·소제목 2개엔 있지만, 긴 filler로 밀도가 하한 미만
        filler = "좌석과 등받이가 안정적이고 프레임이 튼튼해 오래 쓰기 좋은 제품입니다. " * 40
        body = (
            f"# {PRIMARY} 가이드\n\n사무용 의자 도입부입니다. {filler}\n\n"
            f"## {PRIMARY} 기준\n{filler}\n\n## {PRIMARY} 비교\n{filler}\n"
        )
        ok, rpt = check_seo({"body_md": body, "seo": _seo(secondary=[])})
        assert ok is False
        assert any(i.startswith("density_low") for i in rpt["issues"]), rpt["issues"]

    def test_fail_density_high(self) -> None:
        # 짧은 본문에 대표키워드 도배 → 과밀
        body = (
            f"# {PRIMARY}\n\n사무용 의자 사무용 의자 사무용 의자 사무용 의자 사무용 의자.\n\n"
            f"## {PRIMARY}\n사무용 의자.\n\n## {PRIMARY} 비교\n사무용 의자 좋다.\n"
        )
        ok, rpt = check_seo({"body_md": body, "seo": _seo(secondary=[])})
        assert ok is False
        assert any(i.startswith("density_high") for i in rpt["issues"]), rpt["issues"]

    def test_density_floor_override(self) -> None:
        # 기본 하한(1.0)은 통과하나, 카테고리별 하한을 2.5%로 올리면 fail
        ok, rpt = check_seo({"body_md": WELL_OPTIMIZED, "seo": _seo(density_floor=2.5)})
        # WELL_OPTIMIZED 밀도가 2.5% 미만이면 fail (오버라이드 동작 확인)
        if rpt["metrics"]["density_pct"] < 2.5:
            assert ok is False
            assert any(i.startswith("density_low") for i in rpt["issues"])

    def test_floor_ceil_none_falls_back_to_default(self) -> None:
        # yml에서 None/누락으로 들어와도 float(None) 크래시 없이 기본값 복원 (§0 자가복원)
        ok, rpt = check_seo(
            {"body_md": WELL_OPTIMIZED, "seo": _seo(density_floor=None, density_ceil=None)}
        )
        assert ok is True, rpt
        assert 1.0 <= rpt["metrics"]["density_pct"] <= 3.5


# ─── 배치 (제목·도입부·소제목) ──────────────────────────────────────


class TestPlacement:
    def test_fail_title_no_keyword(self) -> None:
        body = WELL_OPTIMIZED
        ok, rpt = check_seo({"body_md": body, "title": "재택근무 추천 가이드", "seo": _seo()})
        # 명시 title에 대표키워드 없음 → title_no_keyword
        assert ok is False
        assert any(i.startswith("title_no_keyword") for i in rpt["issues"]), rpt["issues"]

    def test_fail_intro_no_keyword(self) -> None:
        # 도입부 앞 200자에 대표키워드 없음 (키워드를 본문 뒤로 밀어냄)
        lead = "재택근무 환경을 점검하는 일은 생각보다 중요합니다. " * 12
        body = (
            f"# {PRIMARY} 가이드\n\n{lead}\n\n"
            f"## {PRIMARY} 기준\n사무용 의자 본문. 인체공학 의자.\n\n"
            f"## {PRIMARY} 비교\n사무용 의자 비교.\n"
        )
        ok, rpt = check_seo({"body_md": body, "seo": _seo(secondary=[])})
        assert ok is False
        assert any(i.startswith("intro_no_keyword") for i in rpt["issues"]), rpt["issues"]

    def test_fail_headings_keyword_low(self) -> None:
        # 대표키워드가 소제목에 0개 → headings_keyword_low (네이버 경량: 하드 하한 ≥1)
        filler = "좌석과 등받이와 프레임 안정성을 두루 살펴야 오래 씁니다. "
        body = (
            f"# {PRIMARY} 가이드\n\n사무용 의자를 고르는 기준을 정리한 글입니다. {filler * 4}\n\n"
            f"## 고르는 기준\n요추 지지와 팔걸이 조절을 확인하세요. {filler * 3}\n\n"
            f"## 타입 비교\n메쉬와 게이밍을 비교합니다. {filler * 2}\n\n"
            f"## 흔한 실수\n디자인만 보면 안 됩니다.\n"
        )
        ok, rpt = check_seo({"body_md": body, "seo": _seo(secondary=[])})
        assert ok is False
        assert any(i.startswith("headings_keyword_low") for i in rpt["issues"]), rpt["issues"]


# ─── 보조키워드 (네이버 연관검색어) ─────────────────────────────────


class TestSecondary:
    def test_secondary_coverage_low_is_warning_not_fail(self) -> None:
        # 세션 #15: 보조키워드 미달은 warning(자문)일 뿐 하드 fail 아님 — "#1만 잡고" + 재생성 비용 방지
        ok, rpt = check_seo(
            {
                "body_md": WELL_OPTIMIZED,
                "seo": _seo(secondary=["접이식 의자", "원목 의자", "리클라이너", "좌식 의자"]),
            }
        )
        assert ok is True, rpt  # 대표키워드 요건 충족 → 통과
        assert rpt["issues"] == []
        assert any(w.startswith("secondary_coverage_low") for w in rpt["warnings"]), rpt["warnings"]

    def test_warning_secondary_partial_missing(self) -> None:
        # 과반 존재 + 일부 누락 → pass + warning (하드 fail 아님)
        ok, rpt = check_seo(
            {
                "body_md": WELL_OPTIMIZED,
                "seo": _seo(secondary=["메쉬 의자", "게이밍 의자", "인체공학 의자", "좌식 의자"]),
            }
        )
        assert ok is True, rpt
        assert any(w.startswith("secondary_missing") for w in rpt["warnings"]), rpt["warnings"]
        assert "좌식 의자" in rpt["metrics"]["secondary_missing"]


# ─── 제목 키워드 위치 (soft warning) ────────────────────────────────


class TestTitlePosition:
    def test_warning_title_keyword_late(self) -> None:
        # 대표키워드가 제목 뒤쪽(20자 초과)에 있으면 fail이 아니라 warning
        ok, rpt = check_seo(
            {
                "body_md": WELL_OPTIMIZED,
                "title": "하루 여덟 시간 넘게 앉아서 일하는 재택근무자에게 꼭 맞는 사무용 의자",
                "seo": _seo(),
            }
        )
        assert ok is True, rpt
        assert any(w.startswith("title_keyword_late") for w in rpt["warnings"]), rpt["warnings"]


# ─── validate_all / serialize_report 통합 ──────────────────────────


class TestIntegration:
    def test_validate_all_includes_seo(self) -> None:
        results = validate_all({"body_md": WELL_OPTIMIZED, "seo": _seo()})
        assert "seo" in results
        ok, rpt = results["seo"]
        assert isinstance(ok, bool)
        assert rpt["gate"] == "seo"

    def test_validate_all_seo_skips_when_absent(self) -> None:
        # seo 설정 없으면 seo 게이트는 pass(skip) → 기존 4게이트 흐름 무영향
        results = validate_all({"body_md": "정상 본문. 가격 290,000원.", "products": []})
        ok, rpt = results["seo"]
        assert ok is True
        assert rpt["metrics"].get("skipped") is True

    def test_serialize_report_carries_warnings_and_metrics(self) -> None:
        results = validate_all(
            {
                "body_md": WELL_OPTIMIZED,
                "title": "하루 여덟 시간 넘게 앉아서 일하는 재택근무자에게 꼭 맞는 사무용 의자",  # 키워드 늦음 → warning
                "seo": _seo(),
            }
        )
        report = serialize_report(results)
        seo_entry = report["gates"]["seo"]
        assert "warnings" in seo_entry
        assert "metrics" in seo_entry
        assert any(w.startswith("title_keyword_late") for w in seo_entry["warnings"])
        json.dumps(report)  # 직렬화 가능해야 함

    def test_serialize_report_no_extra_keys_for_other_gates(self) -> None:
        # warnings·metrics는 제공하는 게이트(seo)만 — truth 등엔 없음
        results = validate_all({"body_md": "정상 본문.", "products": []})
        report = serialize_report(results)
        assert "warnings" not in report["gates"]["truth"]
        assert "metrics" not in report["gates"]["truth"]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
