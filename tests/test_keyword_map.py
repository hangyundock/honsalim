"""keyword_map 회귀 테스트 — YAML 로드·시나리오 매핑·시드 정합·영어 검증 + CLI --scenario dry_run.

핵심 불변식:
- 시드(sql/seeds/001)의 시나리오 10종이 모두 매핑되어 있을 것 (드리프트 방지).
- 검색어는 모두 ASCII(영어) — 한글은 AliExpress에서 빈 결과(resp_code 405).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from collector import keyword_map

# sql/seeds/001_personas_scenarios.sql 의 시나리오 10종 slug (드리프트 가드)
SEED_SCENARIO_SLUGS = (
    "wonroom-cheot-jachi-30",
    "cheot-jachi-50-complete",
    "cheot-jachi-gajeon-100",
    "gaeul-cheot-jachi-30",
    "homeoffice-chair-desk-50",
    "homeoffice-100-setup",
    "homeoffice-200-premium",
    "saehae-minimal-20",
    "jeongchak-gajeon-up-50",
    "isacheol-jeongni-30",
)


class TestLoad:
    def test_load_map_returns_nonempty_dict(self) -> None:
        m = keyword_map.load_map()
        # 시드 10 중 일부는 쿠팡 전담(coupang_deferred)이라 매핑에서 빠짐 — 합산은 별도 테스트가 보증
        assert isinstance(m, dict) and len(m) >= 8

    def test_all_seed_scenarios_mapped_or_deferred(self) -> None:
        """모든 시드 시나리오는 AliExpress 매핑되거나 쿠팡 전담으로 명시되어야 함 (드리프트 가드)."""
        covered = set(keyword_map.all_mapped_slugs()) | set(keyword_map.coupang_deferred_slugs())
        missing = set(SEED_SCENARIO_SLUGS) - covered
        assert not missing, f"매핑·쿠팡이관 모두 누락된 시나리오: {sorted(missing)}"

    def test_deferred_and_mapped_are_disjoint(self) -> None:
        """한 시나리오가 매핑과 쿠팡이관에 동시에 있으면 모순."""
        both = set(keyword_map.all_mapped_slugs()) & set(keyword_map.coupang_deferred_slugs())
        assert not both, f"매핑·쿠팡이관 중복: {sorted(both)}"

    def test_coupang_deferred_listed(self) -> None:
        deferred = keyword_map.coupang_deferred_slugs()
        assert "cheot-jachi-gajeon-100" in deferred
        assert "jeongchak-gajeon-up-50" in deferred

    def test_keywords_for_known_scenario(self) -> None:
        kws = keyword_map.keywords_for_scenario("homeoffice-chair-desk-50")
        assert "office chair" in kws
        assert len(kws) >= 6  # 번들형 — 카테고리 다수

    def test_unknown_scenario_returns_empty(self) -> None:
        assert keyword_map.keywords_for_scenario("does-not-exist") == []

    def test_all_mapped_slugs_sorted(self) -> None:
        slugs = keyword_map.all_mapped_slugs()
        assert slugs == sorted(slugs)


class TestPriceBands:
    """검색어별 가격 밴드 — dict 양식 {q, min, max} + 평문 하위호환 [확정 2026-05-30]."""

    def test_homeoffice_terms_have_bands(self) -> None:
        terms = keyword_map.terms_for_scenario("homeoffice-chair-desk-50")
        by_q = {t.q: t for t in terms}
        assert by_q["office chair"].min_price == 40000
        assert by_q["office chair"].max_price == 250000
        # 작은 품목은 낮은 상한
        assert by_q["cable management box"].max_price == 30000

    def test_plain_string_scenario_has_no_band(self, tmp_path: Any = None) -> None:
        """평문 문자열 항목은 밴드 None — 하위호환 (라이브 YAML 이관 상태와 무관하게 검증)."""
        target = (tmp_path / "kw.yml") if tmp_path else Path("_tmp_plain_test.yml")
        target.write_text("scenarios:\n  s1:\n    - lamp\n    - office chair\n", encoding="utf-8")
        try:
            terms = keyword_map.terms_for_scenario("s1", path=target)
            assert terms and all(t.min_price is None and t.max_price is None for t in terms)
        finally:
            if not tmp_path and target.exists():
                target.unlink()

    def test_keywords_for_scenario_returns_plain_q(self) -> None:
        """하위호환 — keywords_for_scenario는 질의어 문자열만."""
        kws = keyword_map.keywords_for_scenario("homeoffice-chair-desk-50")
        assert "office chair" in kws and all(isinstance(k, str) for k in kws)

    def test_to_term_forms(self) -> None:
        assert keyword_map._to_term("lamp") == keyword_map.SearchTerm(q="lamp")
        t = keyword_map._to_term({"q": "chair", "min": 1000, "max": 5000})
        assert t is not None
        assert (t.q, t.min_price, t.max_price) == ("chair", 1000, 5000)
        assert keyword_map._to_term({"q": ""}) is None
        assert keyword_map._to_term(123) is None


class TestEnglishOnly:
    def test_every_keyword_is_ascii(self) -> None:
        """검색어에 한글 등 비ASCII가 섞이면 AliExpress 매칭 실패 — 설계 불변식."""
        bad: list[tuple[str, str]] = []
        for slug, terms in keyword_map.load_map().items():
            for t in terms:
                if not t.q.isascii():
                    bad.append((slug, t.q))
        assert not bad, f"비ASCII 검색어: {bad}"

    def test_keywords_are_trimmed_nonempty(self) -> None:
        for terms in keyword_map.load_map().values():
            for t in terms:
                assert t.q == t.q.strip()
                assert t.q  # 빈 문자열 없음

    def test_price_bands_sane_when_present(self) -> None:
        """밴드가 있으면 min < max, 양수 — 데이터 정합 가드."""
        for slug, terms in keyword_map.load_map().items():
            for t in terms:
                if t.min_price is not None and t.max_price is not None:
                    assert 0 < t.min_price < t.max_price, f"{slug}/{t.q} 밴드 이상: {t}"


class TestCustomFile:
    def test_loads_from_given_path(self, tmp_path: Any = None) -> None:
        # pytest tmp_path 의존 없이 동작하도록 직접 파일 작성
        target = (tmp_path / "kw.yml") if tmp_path else Path("_tmp_kw_test.yml")
        target.write_text("scenarios:\n  foo:\n    - bar baz\n    - qux\n", encoding="utf-8")
        try:
            assert keyword_map.keywords_for_scenario("foo", path=target) == ["bar baz", "qux"]
            assert keyword_map.all_mapped_slugs(path=target) == ["foo"]
        finally:
            if not tmp_path and target.exists():
                target.unlink()

    def test_missing_file_returns_empty(self) -> None:
        assert keyword_map.load_map(Path("does/not/exist.yml")) == {}


class TestCliScenarioDryRun:
    def test_scenario_dry_run_lists_keywords(self) -> None:
        import cli

        rc = cli.main(["collect-products", "--scenario", "homeoffice-chair-desk-50"])
        assert rc == 0

    def test_unmapped_scenario_dry_run_errors(self) -> None:
        import cli

        rc = cli.main(["collect-products", "--scenario", "no-such-slug"])
        assert rc == 2

    def test_requires_keywords_or_scenario(self) -> None:
        import cli

        with raises(SystemExit):  # mutually exclusive required group
            cli.main(["collect-products"])
