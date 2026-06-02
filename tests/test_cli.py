"""cli 명령 회귀 테스트 — argparse subcommand 인식·매개변수.

출처: BACKEND §9 [확정].

doctor 자체 실행은 환경 의존이 커서 (jinja2 설치 여부·secrets 폴더·git repo 등)
유닛 테스트로는 parser·subcommand 구조만 검증. doctor 자체 검증은 수동 실행으로.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
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


import cli


class TestParser:
    def test_build_parser_returns_argparse(self) -> None:
        parser = cli.build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "honsalim"

    def test_doctor_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["doctor"])
        assert args.command == "doctor"
        assert args.func == cli.cmd_doctor

    def test_db_migrate_subcommand(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["db", "migrate"])
        assert args.command == "db"
        assert args.db_command == "migrate"
        assert args.dry_run is False
        assert args.func == cli.cmd_db_migrate

    def test_db_migrate_dry_run_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["db", "migrate", "--dry-run"])
        assert args.dry_run is True

    def test_db_seed_subcommand(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["db", "seed"])
        assert args.command == "db"
        assert args.db_command == "seed"
        assert args.func == cli.cmd_db_seed

    def test_db_seed_dry_run_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["db", "seed", "--dry-run"])
        assert args.dry_run is True

    def test_verbose_quiet_flags(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["--verbose", "doctor"])
        assert args.verbose is True
        args = parser.parse_args(["--quiet", "doctor"])
        assert args.quiet is True

    def test_unknown_command_errors(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["unknown-command"])

    def test_db_without_subcommand_errors(self) -> None:
        """db 단독은 db_command 필수 — SystemExit (argparse 표준)."""
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["db"])

    def test_no_command_errors(self) -> None:
        """command 필수 — argparse가 SystemExit."""
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args([])


class TestConstants:
    def test_required_deps_includes_core(self) -> None:
        """BACKEND §10-1 핵심 의존성이 doctor 체크 대상에 포함."""
        for dep in ("anthropic", "jinja2", "requests", "dotenv"):
            assert dep in cli.REQUIRED_DEPS

    def test_project_root_resolves(self) -> None:
        """PROJECT_ROOT는 D:\\affiliate_hub 또는 worktree root."""
        # 존재 확인만 — 정확한 경로는 환경 의존
        assert cli.PROJECT_ROOT.exists()
        assert (cli.PROJECT_ROOT / "src").exists()


class TestPhase2HealthChecks:
    """세션 #4 추가 — doctor §9~§12 헬스 체크 (BACKEND §3-3·§2 + DB §12-2 정합)."""

    def test_prompt_templates_check_passes(self) -> None:
        """BACKEND §3-3 명시 6종 prompt_templates 실제 존재."""
        assert cli._check_prompt_templates() is True

    def test_phase2_modules_check_passes(self) -> None:
        """Phase 2 핵심 모듈 진입점 모두 import + callable."""
        assert cli._check_phase2_modules() is True

    def test_state_machine_matrix_check_passes(self) -> None:
        """DB §12-2 전이 매트릭스 정합 (6 상태)."""
        assert cli._check_state_machine_matrix() is True

    def test_tests_loadable_check_passes(self) -> None:
        """tests/ 모듈 모두 import 가능."""
        assert cli._check_tests_loadable() is True


class TestPhase2Commands:
    """세션 #4 추가 — BACKEND §9 명시 enrich·validate·approve 명령 (3개)."""

    # enrich
    def test_enrich_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["enrich", "--draft", "1"])
        assert args.command == "enrich"
        assert args.draft == 1
        assert args.dry_run is True  # 기본 dry_run
        assert args.func == cli.cmd_enrich

    def test_enrich_no_dry_run_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["enrich", "--draft", "5", "--no-dry-run"])
        assert args.dry_run is False

    def test_enrich_requires_draft_id(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["enrich"])

    def test_enrich_draft_must_be_int(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["enrich", "--draft", "not-a-number"])

    # validate
    def test_validate_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["validate", "--draft", "1"])
        assert args.command == "validate"
        assert args.draft == 1
        assert args.func == cli.cmd_validate

    def test_validate_requires_draft_id(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["validate"])

    # approve
    def test_approve_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["approve", "--draft", "1"])
        assert args.command == "approve"
        assert args.draft == 1
        assert args.note is None
        assert args.func == cli.cmd_approve

    def test_approve_note_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["approve", "--draft", "1", "--note", "검토 완료"])
        assert args.note == "검토 완료"

    def test_approve_requires_draft_id(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["approve"])

    # approve-category / unapprove-category (세션 #18 — 카테고리 공개 승인 게이트)
    def test_approve_category_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["approve-category", "office-chair"])
        assert args.command == "approve-category"
        assert args.slug == "office-chair"
        assert args.func == cli.cmd_approve_category

    def test_approve_category_requires_slug(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["approve-category"])

    def test_unapprove_category_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["unapprove-category", "desk"])
        assert args.command == "unapprove-category"
        assert args.slug == "desk"
        assert args.func == cli.cmd_unapprove_category

    # collect (positional arg)
    def test_collect_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["collect", "wonroom-30man"])
        assert args.command == "collect"
        assert args.scenario_slug == "wonroom-30man"
        assert args.func == cli.cmd_collect

    def test_collect_requires_scenario_slug(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["collect"])

    # unapprove
    def test_unapprove_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["unapprove", "--draft", "1"])
        assert args.command == "unapprove"
        assert args.draft == 1
        assert args.func == cli.cmd_unapprove

    def test_unapprove_requires_draft_id(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["unapprove"])

    # promote
    def test_promote_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["promote", "--draft", "6"])
        assert args.command == "promote"
        assert args.draft == 6
        assert args.note is None
        assert args.func == cli.cmd_promote

    def test_promote_note_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["promote", "--draft", "6", "--note", "게시 승인"])
        assert args.note == "게시 승인"

    def test_promote_requires_draft_id(self) -> None:
        parser = cli.build_parser()
        with raises(SystemExit):
            parser.parse_args(["promote"])


class TestStateMachineMatrixUnapprove:
    """세션 #4 — BACKEND §9 unapprove 정합: approved → validated 허용."""

    def test_approved_to_validated_allowed(self) -> None:
        from writer.state_machine import VALID_TRANSITIONS

        assert "validated" in VALID_TRANSITIONS["approved"]

    def test_approved_to_published_still_allowed(self) -> None:
        """기존 정상 흐름 — promote_to_article."""
        from writer.state_machine import VALID_TRANSITIONS

        assert "published" in VALID_TRANSITIONS["approved"]


class TestDeployParser:
    """세션 #5 — BACKEND §9 deploy 명령. DECISIONS H4 dry_run 기본."""

    def test_deploy_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy"])
        assert args.command == "deploy"
        assert args.func == cli.cmd_deploy

    def test_deploy_dry_run_default_true(self) -> None:
        """DECISIONS H4 [확정] — 외부 영향 작업 기본 dry_run=True."""
        parser = cli.build_parser()
        args = parser.parse_args(["deploy"])
        assert args.dry_run is True

    def test_deploy_no_dry_run_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy", "--no-dry-run"])
        assert args.dry_run is False

    def test_deploy_skip_flags_default_false(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy"])
        assert args.skip_push is False
        assert args.skip_wrangler is False
        assert args.verify_url is None

    def test_deploy_skip_push_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy", "--skip-push"])
        assert args.skip_push is True

    def test_deploy_skip_wrangler_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy", "--skip-wrangler"])
        assert args.skip_wrangler is True

    def test_deploy_verify_url_arg(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy", "--verify-url", "https://honsallim.com/"])
        assert args.verify_url == "https://honsallim.com/"

    def test_deploy_remote_branch_defaults(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["deploy"])
        assert args.remote == "origin"
        assert args.branch == "main"
        assert args.build_dir == "build/site"  # renderer 산출물 경로
        assert args.project == "honsalim"

    def test_deploy_dry_run_executes_without_external_call(self) -> None:
        """dry_run=True 호출 시 외부 git·wrangler 실행 없이 rc=0 반환."""
        parser = cli.build_parser()
        args = parser.parse_args(["deploy"])
        rc = cli.cmd_deploy(args)
        assert rc == 0


class TestBuildParser:
    """세션 #5 — BACKEND §9 build 명령 (Phase 2 stub — manifest 로드만)."""

    def test_build_subcommand_recognized(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["build"])
        assert args.command == "build"
        assert args.func == cli.cmd_build

    def test_build_default_flags(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["build"])
        assert args.manifest is None
        assert args.full is False
        assert args.save_empty is False

    def test_build_full_flag(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["build", "--full"])
        assert args.full is True

    def test_build_manifest_arg(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["build", "--manifest", "data/test-manifest.json"])
        assert args.manifest == "data/test-manifest.json"

    def test_build_loads_manifest(self, tmp_path: Any) -> None:
        """빈 manifest 경로 → new_manifest 로드 (파일 없어도 OK)."""
        parser = cli.build_parser()
        manifest_path = tmp_path / "manifest.json"
        args = parser.parse_args(["build", "--manifest", str(manifest_path)])
        rc = cli.cmd_build(args)
        assert rc == 0

    def test_build_save_empty_creates_file(self, tmp_path: Any) -> None:
        """--save-empty + 파일 없음 → 빈 manifest 생성."""
        parser = cli.build_parser()
        manifest_path = tmp_path / "new-manifest.json"
        args = parser.parse_args(["build", "--manifest", str(manifest_path), "--save-empty"])
        rc = cli.cmd_build(args)
        assert rc == 0
        assert manifest_path.exists()


class TestEnrichCommandExecution:
    """enrich 명령 실제 실행 — `s.keywords`(스키마에 없는 컬럼) 회귀 방지 (2026-05-30 버그 수정).

    기존 CLI 테스트는 인자 파싱만 검증해 SQL 실행 경로가 빠져 있었다.
    """

    def test_collect_then_enrich_dry_run(self, tmp_path: Any, monkeypatch: Any) -> None:
        from common import db

        tmp_db = tmp_path / "cli_enrich.db"
        monkeypatch.setattr(db, "DB_PATH", tmp_db)
        db.migrate(db_path=tmp_db)
        db.seed(db_path=tmp_db)

        assert cli.cmd_collect(argparse.Namespace(scenario_slug="wonroom-cheot-jachi-30")) == 0
        # dry-run: API 호출 없음. s.keywords OperationalError 없이 enriched 전이해야 함.
        assert cli.cmd_enrich(argparse.Namespace(draft=1, dry_run=True)) == 0

        conn = db.connect(tmp_db)
        try:
            status = conn.execute("SELECT status FROM drafts WHERE id = 1").fetchone()[0]
        finally:
            conn.close()
        assert status == "enriched"


class TestPromoteCommandExecution:
    """promote 명령 실제 실행 — approved draft → articles + article_products → published."""

    def _insert_product(self, conn: Any, spid: str) -> None:
        conn.execute(
            "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
            "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
            "VALUES ('aliexpress', ?, '상품', 'KRW', 12000, ?, ?, 'honsalim', "
            "datetime('now'), datetime('now'), datetime('now'))",
            (spid, f"https://s.click.aliexpress.com/{spid}", f"ali-{spid}"),
        )
        conn.commit()

    def test_approved_draft_promotes_with_products(self, tmp_path: Any, monkeypatch: Any) -> None:
        from builder.jsonld import build_article_jsonld
        from common import db
        from writer import article_writer
        from writer.state_machine import transition

        tmp_db = tmp_path / "cli_promote.db"
        monkeypatch.setattr(db, "DB_PATH", tmp_db)
        db.migrate(db_path=tmp_db)
        db.seed(db_path=tmp_db)

        body = (
            "이 글에는 AliExpress 어필리에이트 활동의 일환으로 일정 수수료를 제공받습니다. "
            "(구매자에게 추가 비용은 발생하지 않습니다.)\n\n# 제목\n본문 12,000원.\n\n"
            "혼살림은 쿠팡 파트너스 및 AliExpress Portals 어필리에이트 활동의 일환으로 "
            "일정 수수료를 받습니다. 어필리에이트 정책을 준수합니다."
        )
        conn = db.connect(tmp_db)
        try:
            srow = conn.execute("SELECT id, slug FROM scenarios ORDER BY id LIMIT 1").fetchone()
            scenario_id, scenario_slug = srow[0], srow[1]
            self._insert_product(conn, "sp1")
            schema = build_article_jsonld(
                meta={"title": "제목", "meta_description": "메타 설명입니다"},
                scenario={"slug": scenario_slug},
                site_base_url="https://honsallim.com",
                image_url="https://honsallim.com/static/img/og-default.png",
                published_at="2026-05-30",
            )
            did = article_writer.create_draft(conn, scenario_id=scenario_id)
            transition(conn, did, "enriched")
            article_writer.save_enriched(
                conn,
                did,
                {
                    "body_md": body,
                    "title": "제목",
                    "summary": "요약",
                    "meta_description": "메타 설명입니다",
                    "schema_jsonld": schema,
                    "products": [{"source": "aliexpress", "source_product_id": "sp1"}],
                },
            )
            transition(conn, did, "validated")
            transition(conn, did, "approved")
        finally:
            conn.close()

        assert cli.cmd_promote(argparse.Namespace(draft=did, note=None)) == 0

        conn = db.connect(tmp_db)
        try:
            art = conn.execute(
                "SELECT id, status FROM articles WHERE scenario_id = ?", (scenario_id,)
            ).fetchone()
            assert art is not None
            assert art[1] == "published"
            cnt = conn.execute(
                "SELECT COUNT(*) FROM article_products WHERE article_id = ?", (art[0],)
            ).fetchone()[0]
            assert cnt == 1
            dstatus = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
            assert dstatus == "published"
        finally:
            conn.close()

    def test_promote_rejects_non_approved(self, tmp_path: Any, monkeypatch: Any) -> None:
        from common import db
        from writer import article_writer

        tmp_db = tmp_path / "cli_promote2.db"
        monkeypatch.setattr(db, "DB_PATH", tmp_db)
        db.migrate(db_path=tmp_db)
        db.seed(db_path=tmp_db)
        conn = db.connect(tmp_db)
        try:
            did = article_writer.create_draft(conn, scenario_id=1)  # collected 상태
        finally:
            conn.close()
        # 승인 안 된 draft 게시 시도 → 데이터 에러(rc=2), articles 미생성
        assert cli.cmd_promote(argparse.Namespace(draft=did, note=None)) == 2


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
