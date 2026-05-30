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
