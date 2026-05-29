# ruff: noqa: S607
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
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined,union-attr]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined,union-attr]
    except (AttributeError, OSError):
        pass

# src/를 직접 실행 시에도 동작하도록 부모 경로 보정
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from common import config, db, size_caps  # noqa: E402

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
        ("writer.article_writer", "compute_content_hash"),
        ("writer.article_writer", "extract_disclosure_first"),
        ("writer.state_machine", "transition"),
        ("writer.state_machine", "VALID_TRANSITIONS"),
        ("enricher.claude_client", "ClaudeClient"),
        ("enricher.meta_extractor", "MetaExtractor"),
        ("enricher.retry", "retry_with_backoff"),
        ("enricher.retry", "RetryConfig"),
        ("collector.scenario_loader", "list_active_scenarios"),
        ("collector.scenario_loader", "next_scenarios_for_collection"),
        ("builder", "build_article_jsonld"),
        ("builder", "build_itemlist_jsonld"),
        ("builder", "build_product_jsonld"),
        ("builder.manifest", "new_manifest"),
        ("builder.manifest", "load"),
        ("builder.manifest", "save"),
        ("builder.manifest", "needs_rebuild"),
        ("deployer", "git_push"),
        ("deployer", "wrangler_deploy"),
        ("deployer", "verify_deploy"),
        ("tracker", "aggregate"),
        ("tracker", "export_to_sqlite"),
        ("tracker", "aggregate_weekly"),
        ("tracker", "aggregate_monthly"),
        ("tracker", "top_articles_by_clicks"),
        ("tracker", "weekly"),
        ("tracker", "monthly"),
        ("dashboard.render", "render_dashboard"),
        ("dashboard.render", "render_html"),
        ("dashboard.render", "fetch_drafts_by_status"),
        ("dashboard.approve", "approve"),
    ]
    all_ok = True
    found = 0
    for mod_name, attr in checks:
        try:
            mod = importlib.import_module(mod_name)
            target = getattr(mod, attr)
            if target is None:
                print(f"{FAIL} {mod_name}.{attr} (None)")
                all_ok = False
            else:
                print(f"{OK} {mod_name}.{attr}")
                found += 1
        except ImportError as e:
            print(f"{FAIL} {mod_name} import 실패: {e}")
            all_ok = False
        except AttributeError:
            print(f"{FAIL} {mod_name}.{attr} 누락")
            all_ok = False
    print(f"  → 진입점 {found}/{len(checks)} OK")
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


def _check_workers_files() -> bool:
    """Workers JS 파일 존재 확인 (BACKEND §5 [확정]).

    JS라 Python import 불가 — 파일 존재·기본 export 패턴만 점검.
    """
    workers_dir = PROJECT_ROOT / "src" / "workers"
    if not workers_dir.exists():
        print(f"{WARN} src/workers/ 폴더 없음 (BACKEND §5 미구현)")
        return False
    expected = ("go_gateway.js",)
    all_ok = True
    for name in expected:
        p = workers_dir / name
        if not p.exists():
            print(f"{FAIL} src/workers/{name} 없음")
            all_ok = False
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        if "export default" not in content:
            print(f"{WARN} src/workers/{name} — `export default` 패턴 누락 [관찰]")
            all_ok = False
        else:
            print(f"{OK} src/workers/{name} (export default 확인)")
    return all_ok


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


def _check_size_caps() -> bool:
    """docs/ 동적 파일 size cap 점검 (CLAUDE.md §3).

    cap 초과는 회전·정돈 신호 — 운영 알림용 (WARN). 게이트 X.
    파일 누락은 5파일 시스템 손상 — FAIL.
    """
    code, results = size_caps.check(PROJECT_ROOT)
    for r in results:
        path = r["path"]
        if not r["exists"]:
            print(f"{FAIL} {path} 없음 (5파일 시스템 손상)")
            continue
        size_kb = r["size"] / 1024
        cap_kb = r["cap"] / 1024
        pct = r["ratio"] * 100
        if r.get("over"):
            print(
                f"{WARN} {path:<18} {size_kb:6.2f} / {cap_kb:5.1f} KB ({pct:5.1f}%) — 회전·정돈 필요"
            )
        else:
            print(f"{OK} {path:<18} {size_kb:6.2f} / {cap_kb:5.1f} KB ({pct:5.1f}%)")
    return code != 2  # 파일 누락만 게이트, cap 초과는 WARN


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

    _print_section("13. Workers JS 파일 (BACKEND §5)")
    workers_ok = _check_workers_files()

    _print_section("14. docs/ size cap (CLAUDE.md §3)")
    caps_ok = _check_size_caps()

    _print_section("종합")
    phase2_ok = tmpl_ok and mod_ok and sm_ok and tests_ok and workers_ok and caps_ok
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


def cmd_enrich(args: argparse.Namespace) -> int:
    """Claude API로 본문 생성 (BACKEND §3).

    Phase 2 stub: 기본 dry_run=True — prompt 빌드만 검증 + 상태 전이 (enriched).
    실제 API 호출 (--no-dry-run)은 비용 발생 — 사용자 명시 승인 후.
    """
    from enricher.claude_client import ClaudeClient, GenerateRequest

    conn = db.connect(db.DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT s.slug, s.title_ko, s.season_peak, s.keywords,
                   p.slug, p.title_ko, p.description, p.age_range
            FROM drafts d
            JOIN scenarios s ON d.scenario_id = s.id
            JOIN personas p ON s.persona_id = p.id
            WHERE d.id = ?
            """,
            (args.draft,),
        ).fetchone()
        if row is None:
            print(f"{FAIL} draft {args.draft} 또는 연결된 scenario·persona 없음")
            return 2

        scenario_dict = {
            "slug": row[0],
            "title_ko": row[1],
            "season_peak": row[2],
            "keywords": row[3],
        }
        persona_dict = {
            "slug": row[4],
            "title_ko": row[5],
            "description": row[6],
            "age_range": row[7],
        }
        req = GenerateRequest(scenario=scenario_dict, persona=persona_dict)

        import os

        api_key = None
        if not args.dry_run:
            config.load_secrets()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        client = ClaudeClient(api_key=api_key)
        result = client.generate_article(req, dry_run=args.dry_run)

        from writer import article_writer, state_machine

        state_machine.transition(
            conn,
            args.draft,
            "enriched",
            reason=f"cli enrich ({'dry_run' if args.dry_run else 'live'})",
        )
        article_writer.save_enriched(
            conn,
            args.draft,
            {
                "dry_run": result.dry_run,
                "user_prompt_preview": result.user_prompt[:500],
                "system_blocks_count": len(result.system_blocks),
                "usage": result.usage,
            },
        )
        mode = "dry_run" if args.dry_run else "live"
        print(f"{OK} draft {args.draft} → enriched ({mode})")
        print(f"     user_prompt 길이: {len(result.user_prompt)}자")
        print(f"     system_blocks: {len(result.system_blocks)}개 (cache_control)")
        if not args.dry_run and result.usage:
            print(
                f"     usage: input={result.usage.get('input_tokens')} output={result.usage.get('output_tokens')}"
            )
        return 0
    finally:
        conn.close()


def cmd_validate(args: argparse.Namespace) -> int:
    """validator 4 게이트 검사 (POLICY §3·§4·§2·§6) + 상태 전이.

    drafts.enriched_payload를 payload로 사용. 모든 게이트 PASS → validated,
    하나라도 fail → rejected (BACKEND §2-3 흐름).
    """
    from writer import article_writer

    conn = db.connect(db.DB_PATH)
    try:
        row = conn.execute(
            "SELECT enriched_payload FROM drafts WHERE id = ?", (args.draft,)
        ).fetchone()
        if row is None:
            print(f"{FAIL} draft {args.draft} 없음")
            return 2
        if not row[0]:
            print(f"{FAIL} draft {args.draft} enriched_payload 비어있음 (enrich 먼저 실행)")
            return 2

        import json as _json

        payload = _json.loads(row[0])
        ok, report = article_writer.validate_and_save(conn, args.draft, payload)
        if ok:
            print(f"{OK} draft {args.draft} → validated (4 게이트 모두 PASS)")
            for gate in ("truth", "schema", "disclosure", "links"):
                print(f"     {gate}: pass")
            return 0
        print(f"{WARN} draft {args.draft} → rejected")
        for gate, info in report["gates"].items():
            mark = OK if info["pass"] else FAIL
            print(f"     {mark} {gate}: {info['issues'] if info['issues'] else 'pass'}")
        return 1
    finally:
        conn.close()


def cmd_approve(args: argparse.Namespace) -> int:
    """validated draft → approved (사용자 1클릭 승인). BACKEND §9 [확정]."""
    from writer import state_machine

    conn = db.connect(db.DB_PATH)
    try:
        reason = "cli approve" + (f" — {args.note}" if args.note else "")
        state_machine.transition(conn, args.draft, "approved", reason=reason)
        # drafts.user_approved_at·user_approved_note 갱신은 promote 시점에 자동
        print(f"{OK} draft {args.draft} → approved")
        if args.note:
            print(f"     note: {args.note}")
        return 0
    finally:
        conn.close()


def cmd_collect(args: argparse.Namespace) -> int:
    """scenario slug → drafts INSERT (status='collected'). BACKEND §9 [확정]."""
    from writer import article_writer

    conn = db.connect(db.DB_PATH)
    try:
        row = conn.execute(
            "SELECT id, title_ko FROM scenarios WHERE slug = ?", (args.scenario_slug,)
        ).fetchone()
        if row is None:
            print(f"{FAIL} scenario slug={args.scenario_slug!r} 없음")
            return 2
        scenario_id, title_ko = row[0], row[1]
        draft_id = article_writer.create_draft(
            conn,
            scenario_id=scenario_id,
            raw_payload={"source": "cli collect", "scenario_slug": args.scenario_slug},
            working_title=title_ko,
        )
        print(f"{OK} draft {draft_id} 생성 (scenario={args.scenario_slug!r}, status=collected)")
        return 0
    finally:
        conn.close()


def cmd_unapprove(args: argparse.Namespace) -> int:
    """approved draft → validated 회귀. BACKEND §9 [확정]."""
    from writer import state_machine

    conn = db.connect(db.DB_PATH)
    try:
        state_machine.transition(conn, args.draft, "validated", reason="cli unapprove")
        print(f"{OK} draft {args.draft} → validated (승인 취소)")
        return 0
    finally:
        conn.close()


def cmd_deploy(args: argparse.Namespace) -> int:
    """deployer 3 단계: git_push → wrangler_deploy → verify_deploy.

    출처: BACKEND §9 + DECISIONS H4 [확정] — dry_run=True 기본.
    """
    from deployer import git_push, verify_deploy, wrangler_deploy

    dry_run: bool = args.dry_run
    mode = "[DRY]" if dry_run else "[LIVE]"
    print(f"{mode} deploy 시작 (project={args.project!r}, build_dir={args.build_dir!r})")

    if not args.skip_push:
        push_res = git_push(
            cwd=str(PROJECT_ROOT),
            remote=args.remote,
            branch=args.branch,
            dry_run=dry_run,
        )
        if push_res.returncode != 0:
            print(f"{FAIL} git push 실패 rc={push_res.returncode}: {push_res.stderr.strip()}")
            return 2
        print(f"{OK} git push {' '.join(push_res.command)} → rc={push_res.returncode}")
    else:
        print("[SKIP] git push (--skip-push)")

    if not args.skip_wrangler:
        wrangler_res = wrangler_deploy(
            build_dir=args.build_dir,
            project_name=args.project,
            cwd=str(PROJECT_ROOT),
            dry_run=dry_run,
        )
        if wrangler_res.returncode != 0:
            print(
                f"{FAIL} wrangler deploy 실패 rc={wrangler_res.returncode}: "
                f"{wrangler_res.stderr.strip()}"
            )
            return 3
        print(f"{OK} wrangler deploy → rc={wrangler_res.returncode}")
    else:
        print("[SKIP] wrangler deploy (--skip-wrangler)")

    if args.verify_url:
        verify_res = verify_deploy(args.verify_url, dry_run=dry_run)
        if not verify_res.ok:
            print(
                f"{FAIL} verify {args.verify_url} → status={verify_res.status_code} "
                f"err={verify_res.error}"
            )
            return 4
        suffix = f"status={verify_res.status_code}" if verify_res.status_code is not None else "DRY"
        print(f"{OK} verify {args.verify_url} → {suffix}")

    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """drafts 단일 HTML 미리보기 생성 (BACKEND §2-6 + DECISIONS G3 [확정 #9]).

    --open 옵션 시 브라우저 자동 열기 (webbrowser.open).
    """
    from dashboard import render as dash_render

    output_path = Path(args.output) if args.output else dash_render.DEFAULT_OUTPUT
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    out = dash_render.render_dashboard(output_path=output_path)
    print(f"{OK} dashboard 생성 → {out}")

    if args.open:
        import webbrowser

        webbrowser.open(out.as_uri())
        print(f"{OK} 브라우저 열기")
    else:
        print(f"     수동 열기: file:///{out.as_posix()}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """builder.manifest 인터페이스 호출 — Phase 2 stub.

    출처: BACKEND §9 + DB §10 [추정]. renderer/pages/sitemap 미작성 — manifest 로드·요약만.
    """
    from builder import manifest as manifest_mod

    manifest_path = Path(args.manifest) if args.manifest else manifest_mod.DEFAULT_MANIFEST_PATH
    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path

    manifest = manifest_mod.load(manifest_path)
    print(
        f"{OK} manifest 로드 path={manifest_path} "
        f"schema_v={manifest.get('schema_version')} "
        f"articles={len(manifest.get('articles', {}))} "
        f"assets={len(manifest.get('assets', {}))} "
        f"templates={len(manifest.get('templates', {}))}"
    )

    if args.full:
        print("[NOTE] --full: renderer/pages/sitemap 미작성 — 본 명령은 manifest 로드만 수행")

    if args.save_empty and not manifest_path.exists():
        manifest_mod.save(manifest_path, manifest)
        print(f"{OK} 빈 manifest 저장 → {manifest_path}")

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

    # BACKEND §9 [확정] — Phase 2 진입점 명령 3개
    p_enrich = sub.add_parser("enrich", help="Claude API 본문 생성 (BACKEND §3) — 기본 dry_run")
    p_enrich.add_argument("--draft", type=int, required=True, help="draft id")
    p_enrich.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 Claude API 호출 (비용 발생 — 명시 승인 후)",
    )
    p_enrich.set_defaults(func=cmd_enrich, dry_run=True)

    p_validate = sub.add_parser("validate", help="validator 4 게이트 검사 (POLICY §3·§4·§2·§6)")
    p_validate.add_argument("--draft", type=int, required=True, help="draft id")
    p_validate.set_defaults(func=cmd_validate)

    p_approve = sub.add_parser("approve", help="validated draft 사용자 1클릭 승인")
    p_approve.add_argument("--draft", type=int, required=True, help="draft id")
    p_approve.add_argument("--note", type=str, default=None, help="승인 메모")
    p_approve.set_defaults(func=cmd_approve)

    p_collect = sub.add_parser("collect", help="scenario slug → drafts 생성 (status=collected)")
    p_collect.add_argument("scenario_slug", type=str, help="scenarios.slug")
    p_collect.set_defaults(func=cmd_collect)

    p_unapprove = sub.add_parser("unapprove", help="approved draft → validated 회귀")
    p_unapprove.add_argument("--draft", type=int, required=True, help="draft id")
    p_unapprove.set_defaults(func=cmd_unapprove)

    # BACKEND §9 [확정] — deploy: git_push + wrangler + verify (dry_run 기본)
    p_deploy = sub.add_parser(
        "deploy",
        help="git push + wrangler pages deploy + verify (DECISIONS H4 — 기본 dry_run)",
    )
    p_deploy.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 push·배포 호출 (외부 영향 — 명시 승인 후)",
    )
    p_deploy.add_argument("--skip-push", action="store_true", help="git push 단계 건너뛰기")
    p_deploy.add_argument(
        "--skip-wrangler", action="store_true", help="wrangler deploy 단계 건너뛰기"
    )
    p_deploy.add_argument(
        "--verify-url",
        type=str,
        default=None,
        help="배포 후 HEAD 검증 URL (지정 시 verify_deploy 호출)",
    )
    p_deploy.add_argument("--remote", type=str, default="origin", help="git push remote")
    p_deploy.add_argument("--branch", type=str, default="main", help="git push branch")
    p_deploy.add_argument("--build-dir", type=str, default="build", help="wrangler 배포 디렉토리")
    p_deploy.add_argument(
        "--project", type=str, default="honsalim", help="Cloudflare Pages 프로젝트 이름"
    )
    p_deploy.set_defaults(func=cmd_deploy, dry_run=True)

    # BACKEND §9 [확정] — build: manifest 로드 (Phase 2 stub, renderer 미작성)
    p_build = sub.add_parser(
        "build",
        help="builder.manifest 로드·요약 (renderer 미작성 — Phase 3 디자인 후 본격)",
    )
    p_build.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="manifest 파일 경로 (기본 data/manifest.json)",
    )
    p_build.add_argument(
        "--full",
        action="store_true",
        help="전체 빌드 (현재 stub — renderer/pages/sitemap 미작성)",
    )
    p_build.add_argument(
        "--save-empty",
        action="store_true",
        help="manifest 없으면 빈 manifest 파일 생성·저장",
    )
    p_build.set_defaults(func=cmd_build)

    # BACKEND §2-6 + DECISIONS G3 [확정 #9] — dashboard: drafts 단일 HTML 미리보기
    p_dashboard = sub.add_parser(
        "dashboard",
        help="drafts 단일 HTML 미리보기 생성 (data/dashboard/index.html)",
    )
    p_dashboard.add_argument(
        "--output",
        type=str,
        default=None,
        help="출력 HTML 경로 (기본 data/dashboard/index.html)",
    )
    p_dashboard.add_argument(
        "--open",
        action="store_true",
        help="생성 후 브라우저 자동 열기",
    )
    p_dashboard.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
