"""Phase 2 통합 회귀 — 모듈 간 결합 검증.

출처: BACKEND §2 + DB §12 + ARCH §4 [확정].

목적: 단위 회귀 205개가 모두 PASS 상태에서 모듈 **결합** 시 어디서 깨지는지 검증.
흐름: scenario_loader → create_draft → transition → save_enriched → validate_and_save
     → (validated) → transition(approved) → promote_to_article → articles published

각 시나리오는 in-memory SQLite로 격리. 외부 API·파일 시스템 의존 없음.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from builder.jsonld import build_article_jsonld
from collector import scenario_loader
from validator import validate_all
from writer import IllegalStateError, article_writer
from writer.state_machine import transition

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"
MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"
SEED_001 = PROJECT_ROOT / "sql" / "seeds" / "001_personas_scenarios.sql"


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """전체 마이그레이션(001~)을 순서대로 적용 — 테스트 스키마=운영 스키마.

    001만 적용하면 이후 컬럼(예: 008 articles.structured_json)이 없어 실제 발행 경로와 어긋난다.
    """
    for sql_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(sql_path.read_text(encoding="utf-8"))


# ─── 공통 픽스처 ──────────────────────────────────────────────────────


def _full_db() -> sqlite3.Connection:
    """마이그레이션 + seed 적용 in-memory DB."""
    conn = sqlite3.connect(":memory:")
    _apply_migrations(conn)
    conn.executescript(SEED_001.read_text(encoding="utf-8"))
    conn.commit()
    return conn


# 정상 본문: disclosure 첫머리·푸터 + 가격 정합 + 1인칭 없음 + AI 흔적 없음
GOOD_BODY = (
    "이 글에는 쿠팡 파트너스 활동의 일환으로 일정 수수료를 제공받습니다.\n"
    "(구매자에게 추가 비용은 발생하지 않습니다.)\n\n"
    "# 원룸 자취 가이드\n"
    "30만원 예산으로 시작하는 원룸 자취 패키지를 정리했다.\n\n"
    "## 추천 상품\n"
    "책상 89,000원, 의자 65,000원, 수납 박스 32,000원으로 구성.\n\n"
    "## 마무리\n"
    "혼살림은 쿠팡 파트너스 및 AliExpress 활동의 일환으로 일정 수수료를 받습니다. "
    "본인 및 가족 구매는 금지하며 자동 실행 광고는 사용하지 않습니다."
)


def _good_meta() -> dict[str, Any]:
    return {
        "title": "원룸 30만원 자취 패키지 가이드",
        "summary": (
            "새내기 자취생을 위해 30만원 예산으로 꾸리는 원룸 패키지를 정리했다. "
            "수납·취사·청소 영역별 핵심 아이템과 우선순위를 시즌별로 함께 안내한다."
        ),
        "meta_description": (
            "30만원 예산으로 시작하는 원룸 자취 패키지 가이드 — 수납·취사·청소 영역별 "
            "핵심 아이템과 우선순위, 시즌별 구매 팁을 함께 한눈에 정리했다."
        ),
        "meta_keywords": "원룸자취,자취패키지,새내기,자취준비,30만원자취",
    }


def _good_payload(body_md: str = GOOD_BODY) -> dict[str, Any]:
    """validate_and_save 호환 payload."""
    meta = _good_meta()
    scenario = {"slug": "wonroom-30man"}
    jsonld = build_article_jsonld(
        meta=meta,
        scenario=scenario,
        site_base_url="https://honsallim.com",
        image_url="https://honsallim.com/static/img/wonroom.jpg",
        published_at="2026-05-28",
    )
    return {
        "body_md": body_md,
        "schema_jsonld": jsonld,
        "products": [],
        "photos": [],
    }


def _article_fields_from(scenario_id: int, body_md: str) -> dict[str, Any]:
    """promote_to_article용 12 필수 필드 — 보조 헬퍼 자동 생성 활용."""
    meta = _good_meta()
    content_hash = article_writer.compute_content_hash(body_md)
    disclosure_first = article_writer.extract_disclosure_first(body_md)
    assert disclosure_first is not None, "GOOD_BODY는 disclosure 자동 추출 가능해야 함"

    jsonld = build_article_jsonld(
        meta=meta,
        scenario={"slug": "wonroom-30man"},
        site_base_url="https://honsallim.com",
        image_url="https://honsallim.com/static/img/wonroom.jpg",
        published_at="2026-05-28",
    )
    return {
        "slug": "wonroom-30man",
        "scenario_id": scenario_id,
        "title": meta["title"],
        "summary": meta["summary"],
        "body_md": body_md,
        "body_html": f"<article>{body_md}</article>",
        "meta_description": meta["meta_description"],
        "meta_keywords": meta["meta_keywords"],
        "schema_jsonld": jsonld,
        "disclosure_first": disclosure_first,
        "content_hash": content_hash,
        "truth_check_passed_at": "2026-05-28T11:00:00Z",
        "user_approved_at": "2026-05-28T11:05:00Z",
        "user_approved_note": "통합 회귀 테스트",
    }


# ─── 시나리오 1: 정상 전체 흐름 — collected → published ───────────────


class TestHappyPathFullFlow:
    def test_scenario_to_published_article(self) -> None:
        """전체 흐름: seed scenarios → draft create → enriched → validated → approved → published."""
        conn = _full_db()

        # 1) scenario_loader로 활성 시나리오 1편 얻기
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        assert len(scenarios) >= 1, "seed scenarios 10편 적용됐어야 함"
        scenario = scenarios[0]

        # 2) drafts INSERT (collected)
        did = article_writer.create_draft(
            conn, scenario_id=scenario.id, raw_payload={"source": "integration_test"}
        )
        assert did > 0
        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "collected"

        # 3) state_machine collected → enriched (Claude 호출 simulation)
        transition(conn, did, "enriched", reason="enricher complete")
        article_writer.save_enriched(conn, did, {"meta": _good_meta(), "body_md": GOOD_BODY})

        # 4) validate_and_save: enriched → validated (모든 게이트 PASS)
        overall, report = article_writer.validate_and_save(conn, did, _good_payload())
        assert overall is True, f"validation fail: {report}"
        assert report["overall_pass"] is True
        for gate in ("truth", "schema", "disclosure", "links"):
            assert report["gates"][gate]["pass"] is True, f"{gate} fail: {report['gates'][gate]}"

        # 5) 사용자 1클릭 승인: validated → approved
        transition(conn, did, "approved", reason="user 1-click")

        # 6) promote_to_article: approved → published + articles INSERT
        article_id = article_writer.promote_to_article(
            conn, did, _article_fields_from(scenario.id, GOOD_BODY)
        )
        assert article_id > 0

        # 7) 최종 상태 검증
        art = conn.execute(
            "SELECT slug, status, scenario_id, content_hash FROM articles WHERE id = ?",
            (article_id,),
        ).fetchone()
        assert art[0] == "wonroom-30man"
        assert art[1] == "published"
        assert art[2] == scenario.id
        assert art[3].startswith("sha256:")

        draft = conn.execute(
            "SELECT status, promoted_article_id FROM drafts WHERE id = ?", (did,)
        ).fetchone()
        assert draft[0] == "published"
        assert draft[1] == article_id

        # 8) article_history 감사 로그 1건
        hist = conn.execute(
            "SELECT event_type, actor FROM article_history WHERE article_id = ?",
            (article_id,),
        ).fetchone()
        assert hist[0] == "created"
        assert hist[1] == "user"


# ─── 시나리오 2: truth fail → rejected ───────────────────────────────


class TestTruthFailRejection:
    def test_ai_trace_rejects_draft(self) -> None:
        """AI hard 패턴 본문 → validate_and_save 호출 시 rejected 전이."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")

        bad_body = "본 글은 AI로 작성되었습니다. " + GOOD_BODY
        payload = _good_payload(bad_body)
        overall, report = article_writer.validate_and_save(conn, did, payload)

        assert overall is False
        assert report["gates"]["truth"]["pass"] is False
        assert any("ai_trace_hard" in issue for issue in report["gates"]["truth"]["issues"])

        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "rejected"


# ─── 시나리오 3: disclosure fail → rejected ───────────────────────────


class TestDisclosureFailRejection:
    def test_missing_first_disclosure_rejects(self) -> None:
        """첫머리 disclosure 누락 → rejected."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")

        # 첫머리에 '쿠팡 파트너스'·'수수료' 없음
        bad_body = "# 일반 가이드\n원룸 자취 팁입니다. 가격 290,000원 모델 추천."
        payload = _good_payload(bad_body)
        overall, report = article_writer.validate_and_save(conn, did, payload)

        assert overall is False
        assert report["gates"]["disclosure"]["pass"] is False
        assert any("first_missing" in i for i in report["gates"]["disclosure"]["issues"])

        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "rejected"


# ─── 시나리오 4: rejected → 재수집(collected) 재시도 ──────────────────


class TestRejectedRetryFlow:
    def test_rejected_can_be_recollected_and_re_validated(self) -> None:
        """rejected 상태 draft를 collected로 되돌려 다시 흐름 진행 — DB §12-2 매트릭스."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")

        # 1차 실패: AI 흔적
        bad_body = "본 글은 AI로 작성. " + GOOD_BODY
        ok1, _ = article_writer.validate_and_save(conn, did, _good_payload(bad_body))
        assert ok1 is False
        assert (
            conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
            == "rejected"
        )

        # 재시도: rejected → collected → enriched → validated
        transition(conn, did, "collected", reason="재수집")
        transition(conn, did, "enriched", reason="재처리")
        ok2, report = article_writer.validate_and_save(conn, did, _good_payload(GOOD_BODY))
        assert ok2 is True, f"재시도 검증 fail: {report}"
        assert (
            conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
            == "validated"
        )


# ─── 시나리오 5: state_machine 위반 — 매트릭스 보호 ───────────────────


class TestStateMachineViolation:
    def test_skip_state_blocks(self) -> None:
        """collected에서 바로 validated 전이 시도 → IllegalStateError (DB §12-2 매트릭스 보호)."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)  # collected

        with raises(IllegalStateError):
            transition(conn, did, "validated")  # collected → validated 불가

    def test_promote_blocked_from_collected(self) -> None:
        """promote_to_article은 approved 상태 필수."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)

        with raises(IllegalStateError):
            article_writer.promote_to_article(
                conn, did, _article_fields_from(scenarios[0].id, GOOD_BODY)
            )


# ─── 시나리오 6: validator 와 builder.jsonld 정합 ─────────────────────


class TestValidatorBuilderConsistency:
    def test_built_jsonld_passes_schema_gate_in_full_flow(self) -> None:
        """build_article_jsonld 산출물이 validator.check_schema를 통과 (단위 회귀에서도 확인했으나 통합으로 재검증)."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")

        # 모든 게이트 통과 — schema 게이트가 builder.jsonld의 출력을 거부하면 fail
        ok, report = article_writer.validate_and_save(conn, did, _good_payload())
        assert ok is True
        assert report["gates"]["schema"]["pass"] is True

    def test_validate_all_direct_with_built_jsonld(self) -> None:
        """validate_all 직접 호출도 동일 결과."""
        payload = _good_payload()
        results = validate_all(payload)
        for gate in ("truth", "schema", "disclosure", "links"):
            ok, rpt = results[gate]
            assert ok is True, f"{gate} fail: {rpt}"


# ─── 시나리오 7: content_hash + disclosure_first 자동 생성 정합 ───────


class TestAutoHelpersInPromote:
    def test_content_hash_matches_body_md(self) -> None:
        """promote_to_article에 자동 생성된 content_hash가 body_md와 일치."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")
        article_writer.validate_and_save(conn, did, _good_payload())
        transition(conn, did, "approved")

        fields = _article_fields_from(scenarios[0].id, GOOD_BODY)
        article_id = article_writer.promote_to_article(conn, did, fields)

        stored = conn.execute(
            "SELECT content_hash FROM articles WHERE id = ?", (article_id,)
        ).fetchone()[0]
        # 동일 본문 재계산 → 동일 hash (결정적)
        assert stored == article_writer.compute_content_hash(GOOD_BODY)

    def test_disclosure_first_extracted_into_article(self) -> None:
        """promote_to_article의 disclosure_first가 본문 첫머리에서 추출된 문구와 일치."""
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")
        article_writer.validate_and_save(conn, did, _good_payload())
        transition(conn, did, "approved")

        fields = _article_fields_from(scenarios[0].id, GOOD_BODY)
        article_id = article_writer.promote_to_article(conn, did, fields)

        stored = conn.execute(
            "SELECT disclosure_first FROM articles WHERE id = ?", (article_id,)
        ).fetchone()[0]
        assert "쿠팡 파트너스" in stored
        assert "수수료" in stored


# ─── 시나리오 8: validation_report 영속화 — drafts에 저장됨 ───────────


class TestValidationReportPersistence:
    def test_report_json_stored_in_drafts(self) -> None:
        conn = _full_db()
        scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
        did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
        transition(conn, did, "enriched")
        article_writer.validate_and_save(conn, did, _good_payload())

        raw = conn.execute("SELECT validation_report FROM drafts WHERE id = ?", (did,)).fetchone()[
            0
        ]
        rpt = json.loads(raw)
        assert rpt["overall_pass"] is True
        # 세션 #15: seo 게이트 추가 (seo 설정 없으면 skip-pass). 게이트 집합 5종.
        assert set(rpt["gates"]) == {"truth", "schema", "disclosure", "links", "seo"}


# ─── 시나리오 9: deployer 3단계 dry_run 결합 ──────────────────────────


class TestDeployerDryRunChain:
    """세션 #5 — deployer.git_push + wrangler_deploy + verify_deploy 결합.

    DECISIONS H4 [확정] — 모든 외부 영향 함수 dry_run=True 기본.
    """

    def test_three_stage_dry_run_chain(self) -> None:
        from deployer import git_push, verify_deploy, wrangler_deploy

        push_res = git_push(dry_run=True)
        assert push_res.dry_run is True
        assert push_res.returncode == 0
        assert push_res.command == ["git", "push", "origin", "main"]

        wrangler_res = wrangler_deploy(dry_run=True)
        assert wrangler_res.dry_run is True
        assert wrangler_res.returncode == 0
        assert "wrangler" in wrangler_res.command[0]
        assert "honsalim" in wrangler_res.command

        verify_res = verify_deploy("https://honsallim.com/", dry_run=True)
        assert verify_res.ok is True
        assert verify_res.status_code is None
        assert "[DRY]" in (verify_res.error or "")

    def test_verify_rejects_non_http_url(self) -> None:
        from deployer import verify_deploy

        with raises(ValueError):
            verify_deploy("ftp://example.com/", dry_run=True)


# ─── 시나리오 10: tracker.aggregate → export_to_sqlite 결합 ────────────


class TestTrackerAggregateExportChain:
    """세션 #5 — tracker.d1_aggregator.aggregate + export_to_sqlite.

    dry_run plan 검증 + export_to_sqlite 실 SQLite UPDATE 동작 검증.
    """

    def test_aggregate_dry_run_builds_wrangler_command(self) -> None:
        from tracker import d1_aggregator

        result = d1_aggregator.aggregate("2026-05-28", dry_run=True)
        assert result.dry_run is True
        assert result.date == "2026-05-28"
        assert result.command[:3] == ["wrangler", "d1", "execute"]
        assert "--remote" in result.command
        assert "honsalim-clicks" in result.command

    def test_aggregate_rejects_bad_date(self) -> None:
        from tracker import d1_aggregator

        with raises(ValueError):
            d1_aggregator.aggregate("2026/05/28", dry_run=True)

    def test_export_updates_view_count_cached(self) -> None:
        """실 SQLite — articles row UPDATE 동작 확인 (dry_run=False).

        published article 1편 만든 뒤 같은 DB 경로(임시 파일)로 export 호출 →
        view_count_cached UPDATE rowcount=1 확인.
        """
        import tempfile

        from tracker import d1_aggregator

        # 임시 파일 DB (export_to_sqlite가 별도 connect 하므로 :memory: 불가)
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            conn = sqlite3.connect(db_path)
            _apply_migrations(conn)
            conn.executescript(SEED_001.read_text(encoding="utf-8"))
            conn.commit()

            scenarios = scenario_loader.list_active_scenarios(conn, limit=1)
            did = article_writer.create_draft(conn, scenario_id=scenarios[0].id)
            transition(conn, did, "enriched")
            article_writer.validate_and_save(conn, did, _good_payload())
            transition(conn, did, "approved")
            fields = _article_fields_from(scenarios[0].id, GOOD_BODY)
            article_id = article_writer.promote_to_article(conn, did, fields)
            slug = conn.execute("SELECT slug FROM articles WHERE id = ?", (article_id,)).fetchone()[
                0
            ]
            conn.close()

            result = d1_aggregator.export_to_sqlite(
                [{"slug": slug, "clicks": 42}],
                db_path=db_path,
                dry_run=False,
            )
            assert result.dry_run is False
            assert result.error is None
            assert result.articles_updated == 1

            # UPDATE 적용 확인
            conn2 = sqlite3.connect(db_path)
            try:
                row = conn2.execute(
                    "SELECT view_count_cached FROM articles WHERE slug = ?", (slug,)
                ).fetchone()
                assert row[0] == 42
            finally:
                conn2.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_export_dry_run_returns_plan(self) -> None:
        from tracker import d1_aggregator

        result = d1_aggregator.export_to_sqlite([{"slug": "test", "clicks": 10}], dry_run=True)
        assert result.dry_run is True
        assert result.articles_updated == 1
        assert result.aggregates_loaded == [{"slug": "test", "clicks": 10}]

    def test_export_rejects_missing_keys(self) -> None:
        from tracker import d1_aggregator

        with raises(ValueError):
            d1_aggregator.export_to_sqlite([{"slug": "x"}], dry_run=True)


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
