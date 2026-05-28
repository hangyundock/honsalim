# ruff: noqa: S603, S607
# 사유: subprocess 호출은 git 등 PATH 검색 도구 인자 list로만 사용.
# shell injection 위험 없음. 도구 가용성 확인이 본 파일 책임.
"""혼살림 CLI 진입점.

출처: BACKEND §9 CLI 명령 표 [확정] + ARCH §4-3 [확정].

사용 (Phase 2 — 패키지 설치 전):
    cd D:\\affiliate_hub
    python -m src.cli doctor

사용 (Phase 2 후 pip install -e . 적용 시):
    honsalim doctor      # pyproject.toml의 entry point

현재 구현: doctor 만 (Phase 1 게이트).
Phase 2에서 build·deploy·validate·dashboard 등 순차 추가 (BACKEND §9 표).
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# Windows 콘솔 cp949 기본 인코딩에서 한국어·유니코드 출력 보장
# (PYTHONIOENCODING 환경 변수가 없어도 동작하도록 코드에서 강제)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

# src/를 직접 실행 시에도 동작하도록 부모 경로 보정
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from common import config, db  # noqa: E402

PROJECT_ROOT = _THIS_DIR.parent

# BACKEND §10-1 1차 의존성 (Phase 1·2 운영 필수)
REQUIRED_DEPS = ("anthropic", "jinja2", "requests", "dotenv", "yaml", "markdown", "PIL")

# 시각적 출력
OK = "[OK]"
WARN = "[WARN]"
FAIL = "[FAIL]"


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _check_python() -> bool:
    v = sys.version_info
    if v.major == 3 and v.minor == 10:
        print(f"{OK} Python {v.major}.{v.minor}.{v.micro} (CLAUDE.md §12 정합)")
        return True
    print(f"{FAIL} Python {v.major}.{v.minor}.{v.micro} — 본 프로젝트는 3.10 기준 (CLAUDE.md §12)")
    return False


def _check_dependencies() -> tuple[int, int]:
    found = 0
    for mod in REQUIRED_DEPS:
        try:
            importlib.import_module(mod)
            print(f"{OK} import {mod}")
            found += 1
        except ImportError:
            print(f"{WARN} import {mod} 실패 — pyproject.toml dependencies 설치 필요")
    return found, len(REQUIRED_DEPS)


def _check_secrets() -> bool:
    loaded = config.load_secrets()
    if loaded.get(str(config.SECRETS_DIR)) == "MISSING_DIR":
        print(f"{FAIL} secrets 폴더 없음: {config.SECRETS_DIR}")
        return False
    for name, status in loaded.items():
        marker = OK if status == "loaded" else WARN
        print(f"{marker} secrets/{name} ({status})")

    required = config.check_required()
    all_ok = True
    for key, present in required.items():
        marker = OK if present else FAIL
        print(f"{marker} env {key} {'존재' if present else '누락'}")
        if not present:
            all_ok = False
    return all_ok


def _check_paths() -> bool:
    all_ok = True
    for sub in ("data", "logs"):
        p = PROJECT_ROOT / sub
        if p.exists():
            print(f"{OK} {sub}/ 존재")
        else:
            print(f"{WARN} {sub}/ 없음 (Phase 2 첫 실행 시 자동 생성 예정)")
    return all_ok


def _check_tools() -> bool:
    all_ok = True
    for tool in ("git",):
        path = shutil.which(tool)
        if path:
            print(f"{OK} {tool} 가용 ({path})")
        else:
            print(f"{FAIL} {tool} 미설치")
            all_ok = False
    for tool in ("wrangler", "sqlite3"):
        path = shutil.which(tool)
        if path:
            print(f"{OK} {tool} 가용 ({path})")
        else:
            print(f"{WARN} {tool} 미설치 (운영 시 필요할 수 있음)")
    return all_ok


def _check_sqlite_module() -> bool:
    try:
        ver = sqlite3.sqlite_version
        print(f"{OK} sqlite3 모듈 (lib {ver})")
        return True
    except Exception as exc:  # pragma: no cover
        print(f"{FAIL} sqlite3 모듈 로드 실패: {exc}")
        return False


def _check_db_state() -> bool:
    if not db.DB_PATH.exists():
        print(f"{WARN} DB 파일 없음: {db.DB_PATH} (db migrate 실행 필요)")
        return False
    conn = db.connect(db.DB_PATH)
    try:
        ver = db.current_version(conn)
        if ver == 0:
            print(f"{WARN} schema_version 미적용 (db migrate 필요)")
        else:
            print(f"{OK} schema_version v{ver}")
        stats = db.db_stats(db.DB_PATH)
        for table, count in stats.items():
            marker = OK if count >= 0 else WARN
            shown = "테이블 없음" if count < 0 else f"{count}행"
            print(f"{marker} {table}: {shown}")
        return bool(ver > 0)
    finally:
        conn.close()


def _check_git_repo() -> bool:
    # git을 PATH에서 찾아 인자는 list로 전달 — shell injection 위험 없음
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"{WARN} git repo 확인 실패")
        return False
    if out.returncode == 0:
        print(f"{OK} git 저장소 branch={out.stdout.strip()}")
        return True
    print(f"{WARN} git 저장소 아님")
    return False


def _check_prompt_templates() -> bool:
    """BACKEND §3-3 명시 6종 prompt_templates 존재 확인."""
    try:
        from enricher.prompt_loader import KNOWN_TEMPLATES, verify_known_templates_present
    except ImportError as e:
        print(f"{FAIL} enricher.prompt_loader 로드 실패: {e}")
        return False
    present = verify_known_templates_present()
    all_ok = True
    for name in KNOWN_TEMPLATES:
        if present.get(name):
            print(f"{OK} prompt_templates/{name}.md")
        else:
            print(f"{FAIL} prompt_templates/{name}.md 누락")
            all_ok = False
    return all_ok


def _check_phase2_modules() -> bool:
    """Phase 2 핵심 모듈 import + 진입점 callable 확인.

    BACKEND §2 모듈 인터페이스 명세 [확정] 기반.
    """
    checks: list[tuple[str, str]] = [
        ("validator", "validate_all"),
        ("validator", "serialize_report"),
        ("validator", "check_truth"),
        ("validator", "check_schema"),
        ("validator", "check_disclosure"),
        ("validator", "check_links"),
        ("writer.article_writer", "create_draft"),
        ("writer.article_writer", "save_enriched"),
        ("writer.article_writer", "validate_and_save"),
        ("writer.article_writer", "promote_to_article"),
        ("writer.state_machine", "transition"),
        ("writer.state_machine", "VALID_TRANSITIONS"),
        ("enricher.claude_client", "ClaudeClient"),
        ("enricher.meta_extractor", "MetaExtractor"),
        ("collector.scenario_loader", "list_active_scenarios"),
        ("collector.scenario_loader", "next_scenarios_for_collection"),
    ]
    all_ok = True
    for mod_name, attr in checks:
        try:
            mod = importlib.import_module(mod_name)
            target = getattr(mod, attr)
            if target is None:
                print(f"{FAIL} {mod_name}.{attr} (None)")
                all_ok = False
            else:
                print(f"{OK} {mod_name}.{attr}")
        except ImportError as e:
            print(f"{FAIL} {mod_name} import 실패: {e}")
            all_ok = False
        except AttributeError:
            print(f"{FAIL} {mod_name}.{attr} 누락")
            all_ok = False
    return all_ok


def _check_state_machine_matrix() -> bool:
    """DB §12-2 전이 매트릭스 정합성 (6 상태 + 정의된 전이만)."""
    try:
        from writer.state_machine import ALL_STATES, VALID_TRANSITIONS
    except ImportError as e:
        print(f"{FAIL} writer.state_machine 로드 실패: {e}")
        return False
    expected_states = {"collected", "enriched", "validated", "approved", "published", "rejected"}
    if set(ALL_STATES) != expected_states:
        print(f"{FAIL} ALL_STATES 불일치: {sorted(ALL_STATES)} vs {sorted(expected_states)}")
        return False
    # 매트릭스에서 도달 가능한 상태가 ALL_STATES에 모두 포함되는지
    for src, targets in VALID_TRANSITIONS.items():
        unknown = targets - ALL_STATES
        if unknown:
            print(f"{FAIL} 매트릭스 {src} → 알 수 없는 상태: {sorted(unknown)}")
            return False
    print(f"{OK} state_machine 6 상태 + 전이 매트릭스 정합 (DB §12-2)")
    return True


def _check_tests_loadable() -> bool:
    """tests/ 모듈 로드 가능 확인 (회귀 인프라 헬스)."""
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        print(f"{WARN} tests/ 폴더 없음")
        return False
    test_files = sorted(tests_dir.glob("test_*.py"))
    if not test_files:
        print(f"{WARN} test_*.py 파일 없음")
        return False
    # tests/conftest.py가 src/를 sys.path에 추가하므로 사전 로드
    conftest = tests_dir / "conftest.py"
    if conftest.exists():
        spec = importlib.util.spec_from_file_location("conftest", conftest)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    all_ok = True
    for tf in test_files:
        spec = importlib.util.spec_from_file_location(tf.stem, tf)
        if spec is None or spec.loader is None:
            print(f"{FAIL} {tf.name} spec 생성 실패")
            all_ok = False
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            print(f"{OK} {tf.name}")
        except Exception as e:
            print(f"{FAIL} {tf.name} 로드 실패: {e}")
            all_ok = False
    return all_ok


def cmd_doctor(args: argparse.Namespace) -> int:
    """secrets·DB·외부 API 헬스 체크 (BACKEND §9 [확정])."""
    print("혼살림 doctor — Phase 1 인프라 헬스 체크")
    print(f"프로젝트: {PROJECT_ROOT}")

    _print_section("1. Python 환경")
    py_ok = _check_python()

    _print_section("2. 1차 의존성 (BACKEND §10-1)")
    dep_found, dep_total = _check_dependencies()

    _print_section("3. secrets·환경 변수 (BACKEND §11)")
    sec_ok = _check_secrets()

    _print_section("4. 데이터·로그 경로 (ARCH §3)")
    _check_paths()

    _print_section("5. sqlite3 모듈")
    sql_ok = _check_sqlite_module()

    _print_section("6. 외부 도구 (git·wrangler·sqlite3)")
    tools_ok = _check_tools()

    _print_section("7. git 저장소 상태")
    _check_git_repo()

    _print_section("8. DB 상태 (data/honsalim.db)")
    _check_db_state()

    _print_section("9. prompt_templates (BACKEND §3-3)")
    tmpl_ok = _check_prompt_templates()

    _print_section("10. Phase 2 모듈 진입점 (BACKEND §2)")
    mod_ok = _check_phase2_modules()

    _print_section("11. state_machine 매트릭스 (DB §12-2)")
    sm_ok = _check_state_machine_matrix()

    _print_section("12. tests 로드 가능 (회귀 인프라)")
    tests_ok = _check_tests_loadable()

    _print_section("종합")
    phase2_ok = tmpl_ok and mod_ok and sm_ok and tests_ok
    if py_ok and sec_ok and sql_ok and tools_ok and dep_found == dep_total and phase2_ok:
        print(f"{OK} 모든 필수 체크 통과 — Phase 2 진입 가능")
        return 0
    if py_ok and sec_ok and sql_ok and tools_ok and phase2_ok:
        print(
            f"{WARN} 의존성 일부 누락 ({dep_found}/{dep_total}) — `pip install -e .` 후 재실행 권장"
        )
        return 0
    print(f"{FAIL} 필수 체크 실패 — 위 항목 점검 필요")
    return 2  # BACKEND §9-2 데이터 에러


def cmd_db_migrate(args: argparse.Namespace) -> int:
    """DB 마이그레이션 적용 (DB.md §14 [확정])."""
    pending = db.migrate(dry_run=args.dry_run)
    if args.dry_run:
        if pending:
            print(f"[DRY] 적용 예정 {len(pending)}건:")
            for m in pending:
                print(f"  - v{m.version}  {m.name}")
        else:
            print(f"{OK} 적용할 마이그레이션 없음 (이미 최신)")
        return 0
    if pending:
        print(f"{OK} {len(pending)}건 적용:")
        for m in pending:
            print(f"  - v{m.version}  {m.name}")
    else:
        print(f"{OK} 이미 최신 — 적용할 마이그레이션 없음")
    return 0


def cmd_db_seed(args: argparse.Namespace) -> int:
    """seed 적용 (INSERT OR IGNORE — idempotent)."""
    files = db.seed(dry_run=args.dry_run)
    if args.dry_run:
        if files:
            print(f"[DRY] seed 파일 {len(files)}건:")
            for f in files:
                print(f"  - {f.name}")
        else:
            print(f"{WARN} seed 파일 없음")
        return 0
    if files:
        print(f"{OK} seed {len(files)}건 적용:")
        for f in files:
            print(f"  - {f.name}")
        stats = db.db_stats()
        for table, count in stats.items():
            if count > 0:
                print(f"  → {table}: {count}행")
    else:
        print(f"{WARN} seed 파일 없음")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="honsalim",
        description="혼살림 CLI — BACKEND §9 [확정]",
    )
    parser.add_argument("--verbose", action="store_true", help="DEBUG 로그")
    parser.add_argument("--quiet", action="store_true", help="WARN 이상만")

    sub = parser.add_subparsers(dest="command", required=True)

    p_doctor = sub.add_parser("doctor", help="secrets·DB·외부 API 헬스 체크")
    p_doctor.set_defaults(func=cmd_doctor)

    p_db = sub.add_parser("db", help="DB 관리 (마이그레이션 등)")
    p_db_sub = p_db.add_subparsers(dest="db_command", required=True)
    p_db_migrate = p_db_sub.add_parser("migrate", help="마이그레이션 적용 (DB §14)")
    p_db_migrate.add_argument("--dry-run", action="store_true", help="실행 없이 목록만")
    p_db_migrate.set_defaults(func=cmd_db_migrate)

    p_db_seed = p_db_sub.add_parser("seed", help="seed 적용 (INSERT OR IGNORE)")
    p_db_seed.add_argument("--dry-run", action="store_true", help="실행 없이 파일 목록만")
    p_db_seed.set_defaults(func=cmd_db_seed)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
