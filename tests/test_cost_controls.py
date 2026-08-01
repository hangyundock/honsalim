"""세션 #48 — 비용 낭비 방지 3종 회귀: 실험 하네스·LLM 사용량 추적·캐시 관찰성.

배경(실측): 07-31~08-01 밀도 문제를 라이브 사이클 6회(LLM 15콜·3시간)로 쫓았다. 확률적 출력을
n=1로 판단한 것이 원인이고, 그때 쓴 비용은 **원화로 환산조차 불가능**했다 — LLM 사용량이 어디에도
기록되지 않았기 때문이다(api_usage는 Imagen 전용, 콘솔 로그는 마지막 시도 1회분).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import cli
from common import db, settings
from writer import api_usage

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def usage_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sqlite3.Connection:
    p = tmp_path / "usage.db"
    monkeypatch.setattr(db, "DB_PATH", p)
    db.migrate(db_path=p)
    return db.connect(p)


class TestLlmUsageTracking:
    """★기록이 없으면 낭비를 관리할 수 없다 — 재시도分까지 전량 기록되어야 한다."""

    def test_migration_010_adds_token_columns(self, usage_db: sqlite3.Connection) -> None:
        cols = {r[1] for r in usage_db.execute("PRAGMA table_info(api_usage)")}
        assert {"tokens_in", "tokens_out"} <= cols

    def test_record_llm_stores_tokens(self, usage_db: sqlite3.Connection) -> None:
        assert api_usage.record_llm(
            usage_db, model="deepseek/x", tokens_in=9000, tokens_out=4800, purpose="article"
        )
        row = usage_db.execute(
            "SELECT provider, kind, tokens_in, tokens_out, detail FROM api_usage"
        ).fetchone()
        assert row == ("llm", "article", 9000, 4800, "deepseek/x")

    def test_cost_is_zero_until_prices_are_configured(
        self, usage_db: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★모르는 단가를 지어내지 않는다 — 미설정이면 비용 0, 토큰은 그대로 기록(§0)."""
        monkeypatch.setattr(settings, "get_float", lambda *a, **k: 0.0)
        assert api_usage.llm_cost_usd(1_000_000, 1_000_000) == 0.0

    def test_cost_uses_configured_prices(self, monkeypatch: pytest.MonkeyPatch) -> None:
        prices = {"llm_price_in_per_1m": 0.5, "llm_price_out_per_1m": 2.0}
        monkeypatch.setattr(settings, "get_float", lambda k, *a, **kw: prices.get(k, 0.0))
        assert api_usage.llm_cost_usd(2_000_000, 1_000_000) == pytest.approx(1.0 + 2.0)

    def test_summary_counts_every_call_including_retries(
        self, usage_db: sqlite3.Connection
    ) -> None:
        """★핵심 — 실패한 재시도도 과금된다. 마지막 1회만 세면 실제 비용을 과소평가한다."""
        for _ in range(3):  # 1편 생성에 재시도 3회
            api_usage.record_llm(
                usage_db, model="m", tokens_in=9000, tokens_out=4800, purpose="article"
            )
        s = api_usage.llm_summary(usage_db, days=1)
        assert s["calls"] == 3
        assert s["tokens_in"] == 27000 and s["tokens_out"] == 14400

    def test_summary_is_safe_without_table(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "empty.db"))
        assert api_usage.llm_summary(conn)["calls"] == 0
        conn.close()

    def test_recorder_never_breaks_generation(self, usage_db: sqlite3.Connection) -> None:
        """추적 실패가 본기능(생성)을 막으면 안 된다(§0)."""

        class Broken:
            model = "m"

        cli._record_llm_usage(usage_db, Broken(), None, "article")  # usage 없음 → 무시
        cli._record_llm_usage(
            usage_db, Broken(), {"input_tokens": 1, "output_tokens": 2}, "article"
        )
        assert api_usage.llm_summary(usage_db)["calls"] == 1


class TestCacheObservability:
    """캐시가 걸렸는지 **관측조차 못 하던** 갭 — 응답의 cached_tokens를 읽어 온다."""

    def test_openrouter_response_exposes_cached_tokens(self) -> None:
        from enricher.claude_client import _LLMResponse

        r = _LLMResponse("본문", 100, 50, "end_turn", 80)
        assert r.cached_tokens == 80
        assert r.usage.input_tokens == 100 and r.usage.output_tokens == 50

    def test_defaults_to_zero_when_provider_omits_it(self) -> None:
        from enricher.claude_client import _LLMResponse

        assert _LLMResponse("본문", 100, 50).cached_tokens == 0


class TestExperimentHarness:
    """★n=1 라이브 판단을 대체하는 오프라인 분포 측정 — 기본은 비용 0."""

    def _seed(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            "INSERT INTO personas (slug, title_ko, description) VALUES ('p', '자취생', 'd');"
            "INSERT INTO scenarios (slug, title_ko, description, persona_id) "
            "VALUES ('s', 'S', 'd', 1);"
        )
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, raw_payload) VALUES (1, 'collected', ?)",
            (json.dumps({"candidates": [{"deeplink_slug": "ali-1", "name": "책상"}]}),),
        )
        conn.commit()

    def test_dry_run_makes_no_call_and_no_writes(
        self, usage_db: sqlite3.Connection, capsys: Any
    ) -> None:
        self._seed(usage_db)
        before = usage_db.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
        rc = cli.cmd_experiment(argparse.Namespace(draft=1, samples=5, dry_run=True))
        assert rc == 0
        out = capsys.readouterr().out
        assert "dry-run" in out and "비용 0" in out
        assert usage_db.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == before
        # ★LLM 호출이 없었어야 한다 — 사용량 기록이 0이면 호출도 0.
        assert api_usage.llm_summary(usage_db)["calls"] == 0

    def test_missing_draft_returns_2(self, usage_db: sqlite3.Connection) -> None:
        assert cli.cmd_experiment(argparse.Namespace(draft=999, samples=1, dry_run=True)) == 2

    def test_draft_without_candidates_is_refused(self, usage_db: sqlite3.Connection) -> None:
        """상품 후보가 없으면 실험 자체가 무의미하다 — 돈 쓰기 전에 막는다."""
        usage_db.executescript(
            "INSERT INTO personas (slug, title_ko, description) VALUES ('p', '자취생', 'd');"
            "INSERT INTO scenarios (slug, title_ko, description, persona_id) "
            "VALUES ('s', 'S', 'd', 1);"
            "INSERT INTO drafts (scenario_id, status, raw_payload) VALUES (1, 'collected', '{}');"
        )
        usage_db.commit()
        assert cli.cmd_experiment(argparse.Namespace(draft=1, samples=1, dry_run=True)) == 2

    def test_prompt_matches_production_exactly(self, usage_db: sqlite3.Connection) -> None:
        """★드리프트 가드 — 실험이 운영과 **다른 프롬프트**를 재면 결론도 틀린다.

        자체 재검수에서 실제로 적발: 실험용 SELECT를 따로 짜다 `season_peak`를 빠뜨려 프롬프트가
        갈라져 있었다. 두 경로가 같은 SQL·같은 조립을 쓰는지 프롬프트 문자열로 고정한다.
        """
        from enricher.claude_client import GenerateRequest, build_user_prompt

        usage_db.executescript(
            "INSERT INTO personas (slug, title_ko, description, age_range) "
            "VALUES ('p', '자취생', '설명', '20대');"
            "INSERT INTO scenarios (slug, title_ko, description, persona_id, season_peak) "
            "VALUES ('s', 'S', 'd', 1, '2026-03');"
        )
        usage_db.execute(
            "INSERT INTO drafts (scenario_id, status, raw_payload) VALUES (1, 'collected', ?)",
            (json.dumps({"candidates": [{"deeplink_slug": "ali-1", "name": "책상"}]}),),
        )
        usage_db.commit()

        row = usage_db.execute(cli._ENRICH_SOURCE_SQL, (1,)).fetchone()
        scenario, persona, products = cli._enrich_inputs(row)
        assert scenario["season_peak"] == "2026-03", "운영 프롬프트가 쓰는 필드가 빠지면 안 된다"
        prompt = build_user_prompt(
            GenerateRequest(scenario=scenario, persona=persona, products=products, seo={})
        )
        assert "2026-03" in prompt and "자취생" in prompt

    def test_registered_in_cli_parser_with_safe_default(self) -> None:
        """★드리프트 가드 — 기본이 dry_run이어야 실수로 돈이 나가지 않는다."""
        args = cli.build_parser().parse_args(["experiment", "--draft", "1"])
        assert args.func == cli.cmd_experiment
        assert args.dry_run is True and args.samples == 3
        live = cli.build_parser().parse_args(["experiment", "--draft", "1", "--no-dry-run"])
        assert live.dry_run is False


class TestBodyLengthBudget:
    """★#48 — 본문이 요청치의 1.5~2배로 나와 출력 토큰을 낭비했다(3,830~5,199자 vs 2,000~2,500).

    재검수에서 밝혀진 진짜 원인은 모델의 불복종이 아니라 **명세 모순**이었다: 총 2,000~2,500자를
    요구하면서 상품 6~12개를 각 200~300자로 쓰라고 해, 상품 섹션만으로 예산을 초과했다.
    """

    def _tpl(self, name: str) -> str:
        return (PROJECT_ROOT / "src" / "enricher" / "prompt_templates" / name).read_text(
            encoding="utf-8"
        )

    def test_per_product_budget_tightened(self) -> None:
        base = self._tpl("system_base.md")
        assert "120~180자" in base
        assert "200~300자" not in base  # 옛 예산 잔재 없음

    def test_total_budget_is_consistent_with_section_budgets(self) -> None:
        """총 예산이 섹션 합계보다 작으면 모델은 지킬 수 없다 — 모순이 재발하면 실패한다."""
        main = self._tpl("article_main.md")
        assert "2,600~3,200자" in main
        assert "2,000~2,500자" not in main
        # 상품 8개 최대(180자) + 나머지 섹션 최대치가 총 상한 안에 들어와야 한다.
        products_max = 8 * 180
        others_max = 350 + 350 + 250 + 5 * 120
        assert products_max + others_max <= 3200, (products_max, others_max)

    def test_warns_against_padding(self) -> None:
        """분량을 줄이라는 지시가 '내용을 부실하게'로 읽히면 안 된다."""
        main = self._tpl("article_main.md")
        assert "정보 밀도" in main and "반복" in main
