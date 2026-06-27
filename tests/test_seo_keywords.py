"""seo_keywords 로더 + build_entry 회귀 테스트 (세션 #15).

출처: BACKEND §8-1. yml 로딩은 임시 파일로, build_entry는 fetch 주입으로 검증.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from collector import keyword_research as kr
from collector import seo_keywords as sk

# ── build_entry 검증용 fake fetch ──
ROWS: list[dict[str, Any]] = [
    {"keyword": "컴퓨터의자", "volume": 32700, "competition": "높음"},
    {"keyword": "게이밍의자", "volume": 30100, "competition": "높음"},
    {"keyword": "서울대의자", "volume": 11430, "competition": "중간"},  # 브랜드 제외
    {"keyword": "메쉬의자", "volume": 3210, "competition": "중간"},
]


def _fetch(_seed: str, dry_run: bool = False) -> list[dict[str, Any]]:
    return [dict(r) for r in ROWS]


class TestRealYml:
    """저장소에 커밋된 실제 seo_keywords.yml (office-chair 엔트리) 로딩."""

    def test_office_chair_loaded(self) -> None:
        entry = sk.get("office-chair")
        assert entry is not None
        assert entry["primary"] == "사무용 의자"
        assert entry["core"] == "의자"
        assert "컴퓨터의자" in entry["secondary"]

    def test_gate_config_shape(self) -> None:
        cfg = sk.gate_config("office-chair")
        assert cfg is not None
        assert cfg["primary"] == "사무용 의자"
        assert isinstance(cfg["secondary"], list) and cfg["secondary"]

    def test_unknown_key_returns_none(self) -> None:
        assert sk.get("no-such-category") is None
        assert sk.gate_config("no-such-category") is None

    def test_all_category_keys_includes_office_chair(self) -> None:
        assert "office-chair" in sk.all_category_keys()

    def test_desk_loaded(self) -> None:
        # 세션 #15: 책상 카테고리(대표=컴퓨터 책상) 신규 검증 대상
        cfg = sk.gate_config("desk")
        assert cfg is not None
        assert cfg["primary"] == "컴퓨터 책상"
        assert "게이밍책상" in cfg["secondary"]


class TestLoaderEdge:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert sk.load_all(tmp_path / "nope.yml") == {}

    def test_density_overrides_in_gate_config(self, tmp_path: Path) -> None:
        p = tmp_path / "seo_keywords.yml"
        p.write_text(
            "categories:\n"
            "  test-cat:\n"
            "    primary: 테스트 키워드\n"
            "    secondary: [가나, 다라]\n"
            "    density_floor: 1.5\n"
            "    density_ceil: 3.0\n",
            encoding="utf-8",
        )
        cfg = sk.gate_config("test-cat", path=p)
        assert cfg is not None
        assert cfg["density_floor"] == 1.5
        assert cfg["density_ceil"] == 3.0

    def test_entry_without_primary_skipped(self, tmp_path: Path) -> None:
        p = tmp_path / "seo_keywords.yml"
        p.write_text(
            "categories:\n  broken:\n    secondary: [x]\n",
            encoding="utf-8",
        )
        assert sk.load_all(p) == {}


class TestKeywordGateConfig:
    """세션 #39: 키워드 글은 '그 키워드'를 대표키워드로, 카테고리 대표어는 보조로.

    카테고리어(광의·고경쟁)로 seo 검사하면 키워드 중심 글이 소제목 등에서 자가복원으로도 못 맞춰
    영구 rejected 되던 문제(라이브 적발) 근본수정.
    """

    def test_keyword_becomes_primary(self) -> None:
        cfg = sk.keyword_gate_config("등받이의자", "office-chair")
        assert cfg is not None
        assert cfg["primary"] == "등받이의자"

    def test_category_primary_demoted_to_secondary(self) -> None:
        cfg = sk.keyword_gate_config("무중력의자", "office-chair")
        assert cfg is not None
        assert cfg["primary"] == "무중력의자"
        assert cfg["secondary"] == ["사무용 의자"]  # 카테고리 대표어만 보조로(맥락 유지)

    def test_keyword_equal_to_category_primary_no_dup(self) -> None:
        # 키워드가 카테고리 대표어와 같으면 보조에 중복 안 넣음
        cfg = sk.keyword_gate_config("사무용 의자", "office-chair")
        assert cfg is not None
        assert cfg["primary"] == "사무용 의자"
        assert cfg["secondary"] == []

    def test_unmapped_returns_none(self) -> None:
        assert sk.keyword_gate_config("등받이의자", "no-such-category") is None

    def test_density_overrides_preserved(self, tmp_path: Path) -> None:
        p = tmp_path / "seo_keywords.yml"
        p.write_text(
            "categories:\n"
            "  test-cat:\n"
            "    primary: 테스트 대표어\n"
            "    secondary: [가나, 다라]\n"
            "    density_floor: 1.5\n"
            "    density_ceil: 3.0\n",
            encoding="utf-8",
        )
        cfg = sk.keyword_gate_config("롱테일 키워드", "test-cat", path=p)
        assert cfg is not None
        assert cfg["primary"] == "롱테일 키워드"
        assert cfg["secondary"] == ["테스트 대표어"]
        assert cfg["density_floor"] == 1.5  # gate_config 오버라이드 승계
        assert cfg["density_ceil"] == 3.0

    def test_keyword_primary_satisfies_headings_but_category_does_not(self) -> None:
        # 핵심 증명: '등받이의자' 글(소제목이 등받이의자 중심)을
        #   - 키워드 기준으로 보면 소제목 키워드 충족 → headings_keyword_low 없음
        #   - 카테고리 대표어('사무용 의자') 기준으로 보면 소제목에 그 광의어가 없어 rejected
        from validator.seo import check_seo

        body = (
            "# 등받이의자 추천\n\n"
            "등받이의자를 고를 때 허리 지지가 핵심이다.\n\n"
            "## 등받이의자 고르는 법\n등받이 각도와 재질을 본다.\n\n"
            "## 가격대별 비교\n실속형부터 고급형까지.\n"
        )
        kw_cfg = sk.keyword_gate_config("등받이의자", "office-chair")
        cat_cfg = sk.gate_config("office-chair")
        _, kw_rep = check_seo({"body_md": body, "title": "등받이의자 추천", "seo": kw_cfg})
        _, cat_rep = check_seo({"body_md": body, "title": "등받이의자 추천", "seo": cat_cfg})
        assert kw_rep["metrics"]["headings_with_keyword"] >= 1
        assert not any("headings_keyword_low" in i for i in kw_rep["issues"])
        assert cat_rep["metrics"]["headings_with_keyword"] == 0
        assert any("headings_keyword_low" in i for i in cat_rep["issues"])


class TestBuildEntry:
    def test_build_entry_shape(self) -> None:
        entry = kr.build_entry(
            "사무용 의자",
            core="의자",
            generated_at="2026-05-31",
            fetch=_fetch,
        )
        assert entry["primary"] == "사무용 의자"
        assert entry["core"] == "의자"
        assert entry["secondary"] == [
            "컴퓨터의자",
            "게이밍의자",
            "메쉬의자",
        ]  # 브랜드 제외·검색량순
        assert entry["generated_at"] == "2026-05-31"
        assert "source" in entry


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
