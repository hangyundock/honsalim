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


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
