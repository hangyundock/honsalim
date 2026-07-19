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


class TestSession45Seeds:
    """세션 #45 씨앗 확장 — 도마·미니밥솥 엔트리와 require_terms 파이프라인."""

    def test_cutting_board_seed_loaded(self) -> None:
        entry = sk.get("cutting-board")
        assert entry is not None
        assert entry["primary"] == "도마"
        assert "나무도마" in entry["secondary"]
        # 씨앗 exclude가 category_sources 제외 정책을 미러(자기해제 우회 차단)
        assert "캠핑" in entry["exclude_terms"] and "업소" in entry["exclude_terms"]

    def test_mini_rice_cooker_seed_niche_only(self) -> None:
        entry = sk.get("mini-rice-cooker")
        assert entry is not None
        assert entry["primary"] == "미니밥솥"
        assert entry["require_terms"] == ["미니", "1인", "2인", "소형", "자취"]
        # ★핵심: 세그먼트 이탈 헤드(압력밥솥·전기밥솥·6인용)와 브랜드(쿠쿠 등)가 secondary에 없어야
        niche = ("미니", "1인", "2인", "소형", "자취")
        for kw2 in entry["secondary"]:
            assert any(n in kw2 for n in niche), f"니치 한정어 없는 secondary: {kw2}"
            assert "쿠쿠" not in kw2 and "쿠첸" not in kw2

    def test_require_terms_filter_in_research(self) -> None:
        rows = [
            {"keyword": "압력밥솥", "volume": 40870, "competition": "중간"},  # 헤드 — 차단
            {"keyword": "미니압력밥솥", "volume": 4190, "competition": "높음"},  # 니치 — 채택
            {"keyword": "전기밥솥6인용", "volume": 3010, "competition": "높음"},  # 세그 이탈 — 차단
        ]
        out = kr.research_keywords(
            "미니밥솥",
            core="밥솥",
            require_terms=("미니", "1인"),
            fetch=lambda *_a, **_k: [dict(r) for r in rows],
        )
        assert out["secondary"] == ["미니압력밥솥"]
        reasons = {x["keyword"]: x["reason"] for x in out["excluded"]}
        assert reasons["압력밥솥"] == "no_require"
        assert reasons["전기밥솥6인용"] == "no_require"

    def test_recommender_passes_require_terms(self) -> None:
        # default_seeds가 yml require_terms를 추천 리서치로 전달하는지(엔드투엔드 배선)
        from writer import keyword_recommender as krec

        seeds = krec.default_seeds()
        rice = next(s for s in seeds if s["category"] == "mini-rice-cooker")
        assert rice["require_terms"] == ("미니", "1인", "2인", "소형", "자취")
        board = next(s for s in seeds if s["category"] == "cutting-board")
        assert board["require_terms"] == ()  # 미지정 카테고리는 미적용(기존 동작 불변)


class TestLintAlignment:
    """세션 #45 재발방지 가드 — 드리프트·교차 중복·공개 카테고리 씨앗 누락."""

    def test_repo_files_clean(self) -> None:
        """저장소에 커밋된 실제 yml 2종은 드리프트 0·교차 중복 0이어야 한다(회귀 고정).

        위반 실증(#45에서 정리): monitor-stand secondary의 '모니터암'이 monitor-arm primary를
        first-match로 가려 오매핑됐다. 이 테스트가 있는 한 같은 실수는 커밋 단계에서 잡힌다.
        """
        assert sk.lint_alignment() == []

    def test_drift_detected(self, tmp_path: Path) -> None:
        seo = tmp_path / "seo.yml"
        seo.write_text(
            "categories:\n  no-such-slug:\n    primary: 가상\n    secondary: [가상추천]\n",
            encoding="utf-8",
        )
        issues = sk.lint_alignment(path=seo)
        assert [c for c, _ in issues] == ["drift"]

    def test_cross_duplicate_detected(self, tmp_path: Path) -> None:
        seo = tmp_path / "seo.yml"
        seo.write_text(
            "categories:\n"
            "  cat-a:\n    primary: 도마\n    secondary: [겹침키워드]\n"
            "  cat-b:\n    primary: 밥솥\n    secondary: ['겹침 키워드']\n",  # 공백 달라도 norm 동일
            encoding="utf-8",
        )
        sources = tmp_path / "sources.yml"
        sources.write_text(
            "categories:\n" "  cat-a: {require_any: [도마]}\n" "  cat-b: {require_any: [밥솥]}\n",
            encoding="utf-8",
        )
        issues = sk.lint_alignment(path=seo, sources_path=sources)
        assert [c for c, _ in issues] == ["dup"]
        assert "cat-a" in issues[0][1] and "cat-b" in issues[0][1]

    def test_published_category_without_seed_flagged(self, tmp_path: Path) -> None:
        import sqlite3 as sql

        conn = sql.connect(":memory:")
        conn.execute(
            "CREATE TABLE categories (id INTEGER PRIMARY KEY, slug TEXT, name_ko TEXT, "
            "status TEXT DEFAULT 'draft')"
        )
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) VALUES "
            "('office-chair','의자','published'), ('drying-rack','빨래건조대','draft'), "
            "('mystery-cat','미지','published')"
        )
        issues = sk.lint_alignment(conn)
        codes = [c for c, _ in issues]
        # 공개+씨앗 없음(mystery-cat)만 경고 — draft(drying-rack)는 공개 전이라 미대상
        assert codes == ["published_no_seed"]
        assert "mystery-cat" in issues[0][1]
        conn.close()

    def test_no_categories_table_skips_db_check(self) -> None:
        import sqlite3 as sql

        conn = sql.connect(":memory:")  # categories 없음(구 스키마) — 예외 없이 파일 점검만
        assert sk.lint_alignment(conn) == []
        conn.close()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
