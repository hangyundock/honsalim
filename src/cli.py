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
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

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

from common import config, db, settings, size_caps  # noqa: E402
from common.proc import run_text  # noqa: E402

PROJECT_ROOT = _THIS_DIR.parent

# BACKEND §10-1 1차 의존성 (Phase 1·2 운영 필수)
REQUIRED_DEPS = ("anthropic", "jinja2", "requests", "dotenv", "yaml", "markdown", "PIL")

# 시각적 출력
OK = "[OK]"
WARN = "[WARN]"
FAIL = "[FAIL]"

# 사이트 origin (builder.renderer.SITE_ORIGIN과 일치 — JSON-LD URL 생성용)
SITE_ORIGIN = "https://honsallim.com"


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

    # LLM(본문 생성) 키 — 활성 모델 기준 점검 (세션 #19: DeepSeek=OpenRouter, claude=Anthropic).
    import os

    from enricher.claude_client import DEFAULT_MODEL, is_anthropic_model, load_openrouter_key

    if is_anthropic_model(DEFAULT_MODEL):
        llm_present, llm_label = bool(os.environ.get("ANTHROPIC_API_KEY")), "ANTHROPIC_API_KEY"
    else:
        llm_present, llm_label = bool(load_openrouter_key()), "OPENROUTER_API_KEY (DeepSeek)"
    marker = OK if llm_present else FAIL
    print(f"{marker} LLM 키 {llm_label} {'도달 가능' if llm_present else '없음'} [{DEFAULT_MODEL}]")
    if not llm_present:
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
        out = run_text(
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
        ("validator", "check_seo"),
        ("writer.article_writer", "create_draft"),
        ("writer.article_writer", "save_enriched"),
        ("writer.article_writer", "validate_and_save"),
        ("writer.article_writer", "promote_to_article"),
        ("writer.article_writer", "link_article_products"),
        ("writer.article_writer", "unique_article_slug"),
        ("writer.article_writer", "compute_content_hash"),
        ("writer.article_writer", "extract_disclosure_first"),
        ("writer.state_machine", "transition"),
        ("writer.state_machine", "VALID_TRANSITIONS"),
        ("writer.category_state", "approve"),
        ("writer.category_state", "unapprove"),
        ("writer.category_state", "pending_approval"),
        ("writer.article_state", "unpublish"),
        ("writer.article_state", "republish"),
        ("writer.article_guardrail", "check"),
        ("writer.article_guardrail", "monitor"),
        ("writer.auto_approve", "auto_approve"),
        ("enricher.claude_client", "ClaudeClient"),
        ("enricher.meta_extractor", "MetaExtractor"),
        ("enricher.retry", "retry_with_backoff"),
        ("enricher.retry", "RetryConfig"),
        ("enricher.seo_directive", "build_seo_directive"),
        ("enricher.seo_regenerate", "regenerate_until_seo_pass"),
        ("enricher.category_writer", "generate_category_guide"),
        ("enricher.category_page_builder", "build_and_save"),
        ("enricher.concept_image", "generate_concept_image"),
        ("collector.scenario_loader", "list_active_scenarios"),
        ("collector.scenario_loader", "next_scenarios_for_collection"),
        ("collector.products_store", "upsert_products"),
        ("collector.keyword_map", "keywords_for_scenario"),
        ("collector.aliexpress", "query_products"),
        ("collector.aliexpress", "map_product"),
        ("collector.naver_searchad", "fetch_related_keywords"),
        ("collector.product_filter", "is_relevant"),
        ("collector.keyword_relevance", "filter_products"),
        ("collector.category_collect", "collect_category"),
        ("collector.keyword_research", "research_keywords"),
        ("collector.keyword_research", "build_entry"),
        ("collector.seo_keywords", "gate_config"),
        ("writer.keyword_recommender", "recommend"),
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
        ("tracker", "sync_slug_map"),
        ("tracker", "collect_slug_map_entries"),
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


def _load_module_from_path(name: str, path: Path) -> None:
    """경로의 .py를 단독 실행해 로드(회귀 인프라 헬스 점검용).

    ★세션 #30 근본수정: ``module_from_spec`` 후 ``exec_module`` **전에** 반드시 ``sys.modules``에
    등록한다(importlib 표준 패턴). 안 그러면 **모듈 레벨 @dataclass**가 생성하는 ``__init__``의
    globals를 ``sys.modules[__name__].__dict__``에서 못 찾아 ``'NoneType' object has no attribute
    '__dict__'``로 로드 실패한다. (실제 적발: ``test_refresh_cycle.py`` — pytest는 모든 test 모듈을
    미리 sys.modules에 올려둬 가려졌고, doctor 단독 실행에서만 드러났다.) 실행 후 원복해 pytest 등
    외부의 sys.modules를 오염시키지 않는다(@dataclass는 클래스 생성 시점=exec 중에만 참조하므로 안전).
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"spec 생성 실패: {path}")
    mod = importlib.util.module_from_spec(spec)
    prev = sys.modules.get(name)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        if prev is not None:
            sys.modules[name] = prev
        else:
            sys.modules.pop(name, None)


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
    # tests/conftest.py가 src/를 sys.path에 추가하므로 사전 로드(sys.path side effect는 원복돼도 유지)
    conftest = tests_dir / "conftest.py"
    if conftest.exists():
        try:
            _load_module_from_path("conftest", conftest)
        except Exception as e:
            print(f"{WARN} conftest.py 로드 실패: {e}")
    all_ok = True
    for tf in test_files:
        try:
            _load_module_from_path(tf.stem, tf)
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
            SELECT s.slug, s.title_ko, s.season_peak, s.description,
                   p.slug, p.title_ko, p.description, p.age_range, d.raw_payload, d.keyword_id
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
            "description": row[3],
            # scenarios 스키마에 keywords 컬럼 없음 (DB §7-1) — 검색 키워드 힌트는 비우고
            # 본문 생성 후 meta_extractor가 meta_keywords를 추출한다 (BACKEND §3).
            "keywords": "",
        }
        persona_dict = {
            "slug": row[4],
            "title_ko": row[5],
            "description": row[6],
            "age_range": row[7],
        }
        # 수집 후보(C-1, raw_payload.candidates)를 본문 프롬프트의 {{products}}로 주입
        products: list[dict] = []
        if row[8]:
            try:
                rp = json.loads(row[8])
                if isinstance(rp, dict) and isinstance(rp.get("candidates"), list):
                    products = rp["candidates"]
            except (json.JSONDecodeError, TypeError):
                products = []
        # ★세션 #33 — SEO 키워드 세트 주입: 키워드 경로 글도 카테고리 SEO 최적화·검증을 받게 한다.
        # 미주입 시 validator seo 게이트가 skip돼 무인 글이 SEO 미검증으로 양산되던 갭(실증 발견).
        # 키워드 → 카테고리(resolve_category) → seo_keywords.gate_config → 프롬프트 지시 + seo 게이트 활성.
        seo_cfg: dict[str, Any] = {}
        concept_image = ""
        concept_image_alt = ""
        keyword_id = row[9]
        if keyword_id:
            kwrow = conn.execute(
                "SELECT keyword FROM keyword_queue WHERE id = ?", (keyword_id,)
            ).fetchone()
            if kwrow and kwrow[0]:
                from collector import keyword_relevance, seo_keywords

                cat_slug = keyword_relevance.resolve_category(str(kwrow[0]))
                if cat_slug:
                    seo_cfg = seo_keywords.gate_config(cat_slug) or {}
                    # 시각 보강(세션 #34): 매핑 카테고리 개념 이미지를 글 히어로 배너로 재사용(생성 0)
                    crow = conn.execute(
                        "SELECT concept_image, concept_image_alt FROM categories WHERE slug = ?",
                        (cat_slug,),
                    ).fetchone()
                    if crow:
                        concept_image = crow[0] or ""
                        concept_image_alt = crow[1] or ""
                    if seo_cfg:
                        print(
                            f"     SEO 주입: 카테고리 {cat_slug} (primary={seo_cfg.get('primary')!r})"
                        )
        import os

        api_key = None
        if not args.dry_run:
            config.load_secrets()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        client = ClaudeClient(api_key=api_key)

        from writer import article_writer, state_machine

        def _build_enriched_payload(
            meta: dict[str, Any], body_md: str, usage: dict[str, int]
        ) -> dict[str, Any]:
            """META-JSON + 본문 → featured 선별·disclosure·schema_jsonld 포함 enriched_payload 조립."""
            # 모델이 선언한 featured 상품(deeplink_slug)만 검증·게시 대상. 쿠팡(수동)은 항상 featured
            # (수익원·세션 #28). 알리는 LLM 선언분(featured_products)만.
            declared = meta.get("featured_products")
            slug_set = {str(s).strip() for s in declared} if isinstance(declared, list) else set()
            featured = [
                {**c, "id": c.get("source_product_id")}
                for c in products
                if c.get("deeplink_slug") in slug_set
                or str(c.get("source") or "").lower() == "coupang"
            ]
            if products and not featured:
                print(f"{WARN} featured_products 미선언/미매칭 — truth 가격 검증 대상 0개")

            # disclosure는 featured 상품의 실제 제휴처 반영(공정위 정확성). source 없으면 ali- 접두어 추정.
            def _affiliate_of(c: dict[str, Any]) -> str | None:
                if c.get("source"):
                    return str(c["source"]).lower()
                sl = str(c.get("deeplink_slug") or "")
                return "aliexpress" if sl.startswith("ali-") else None

            affiliates = {a for c in (featured or products) if (a := _affiliate_of(c))}
            # POLICY §2-2/§2-3 disclosure 자동 삽입(모델 미작성 — 시스템 책임). 멱등 + 제휴처 인지형.
            disclosed = article_writer.apply_disclosure(body_md, sources=affiliates)
            payload: dict[str, Any] = {
                "body_md": disclosed,
                "title": meta.get("title"),
                "summary": meta.get("summary"),
                "meta_description": meta.get("meta_description"),
                "meta_keywords": meta.get("meta_keywords"),
                "faqs": meta.get("faqs", []),
                "products": featured,
                "candidate_count": len(products),
                "usage": usage,
                "model": client.model,
                "seo": seo_cfg,
            }
            # Tier 2 구조화(세션 #34) — 추천별 장단점·추천대상·빠른결론·체크포인트(LLM 있으면).
            # featured와 slug로 매칭돼 렌더러가 픽 카드/요약 박스를 채운다. 없으면 그 영역만 생략(graceful).
            notes: dict[str, Any] = {}
            picks = meta.get("picks")
            if isinstance(picks, list):
                for pk in picks:
                    if isinstance(pk, dict) and pk.get("slug"):
                        notes[str(pk["slug"])] = {
                            "pros": [str(x) for x in (pk.get("pros") or [])][:3],
                            "cons": [str(x) for x in (pk.get("cons") or [])][:2],
                            "for_who": str(pk.get("for") or pk.get("for_who") or ""),
                        }
            payload["product_notes"] = notes
            payload["quick_verdict"] = str(meta.get("quick_verdict") or "")
            cps = meta.get("checkpoints")
            payload["checkpoints"] = [
                {"title": str(c.get("title") or ""), "why": str(c.get("why") or "")}
                for c in (cps if isinstance(cps, list) else [])
                if isinstance(c, dict) and (c.get("title") or c.get("why"))
            ][:6]
            payload["concept_image"] = (
                concept_image  # 매핑 카테고리 개념 이미지(글 히어로·세션 #34)
            )
            payload["concept_image_alt"] = concept_image_alt
            # schema 게이트용 Article JSON-LD. image_url·published_at은 임시값(발행 시 확정).
            from datetime import date

            from builder import build_article_jsonld

            try:
                payload["schema_jsonld"] = build_article_jsonld(
                    meta=meta,
                    scenario={"slug": scenario_dict["slug"]},
                    site_base_url=SITE_ORIGIN,
                    image_url=f"{SITE_ORIGIN}/static/img/og-default.png",
                    published_at=date.today().isoformat(),
                )
            except ValueError as e:
                print(f"{WARN} schema_jsonld 생성 실패(메타 필드 부족): {e}")
            return payload

        enriched_payload: dict[str, Any]
        if args.dry_run:
            req = GenerateRequest(
                scenario=scenario_dict, persona=persona_dict, products=products, seo=seo_cfg
            )
            result = client.generate_article(req, dry_run=True)
            enriched_payload = {
                "dry_run": True,
                "user_prompt_preview": result.user_prompt[:500],
                "system_blocks_count": len(result.system_blocks),
                "products_count": len(products),
            }
        else:
            # ★세션 #33 — 무인 자가복원 재생성 루프: 5게이트 미달이면 issues를 피드백으로 최대 N회
            # 재생성(category_page_builder 패턴 미러). 게이트 기준은 절대 안 낮추고 생성 품질을 끌어올린다.
            # 비용 상한(enrich_max_attempts) — tistory 과금 사고 교훈(seo_regenerate 정신).
            from enricher.claude_client import (
                ArticleResponseError,
                is_truncated,
                split_article_response,
            )
            from validator import serialize_report, validate_all

            max_attempts = int(settings.get("enrich_max_attempts", 2) or 2)
            feedback: list[str] | None = None
            enriched_payload = {}
            passed = False
            for attempt in range(1, max_attempts + 1):
                req = GenerateRequest(
                    scenario=scenario_dict,
                    persona=persona_dict,
                    products=products,
                    seo=seo_cfg,
                    feedback=feedback,
                )
                result = client.generate_article(req, dry_run=False)
                if not result.response_text:
                    feedback = [
                        "직전 응답 본문이 비었습니다. META-JSON과 BODY-MARKDOWN을 정확히 출력하세요."
                    ]
                    print(f"     [시도 {attempt}] 빈 응답 — 재생성")
                    continue
                if is_truncated(result):
                    feedback = [
                        "직전 응답이 잘렸습니다(max_tokens). 본문을 약 2,000~2,500자로 더 간결히 쓰세요."
                    ]
                    print(f"     [시도 {attempt}] 응답 잘림 — 재생성")
                    continue
                try:
                    meta, body_md = split_article_response(result.response_text)
                except ArticleResponseError as e:
                    feedback = [
                        f"응답 형식 오류({e}). META-JSON + BODY-MARKDOWN 두 블록으로 분리 출력하세요."
                    ]
                    print(f"     [시도 {attempt}] 형식 오류 — 재생성")
                    continue
                enriched_payload = _build_enriched_payload(meta, body_md, result.usage)
                report = serialize_report(validate_all(enriched_payload))
                if report["overall_pass"]:
                    passed = True
                    print(f"     게이트 통과 (시도 {attempt}/{max_attempts})")
                    break
                feedback = [i for g in report["gates"].values() for i in g.get("issues", [])]
                print(
                    f"     게이트 미달 (시도 {attempt}/{max_attempts}) — 재생성: "
                    f"{'; '.join(feedback)[:140]}"
                )
            if not enriched_payload:
                print(f"{FAIL} {max_attempts}회 생성 모두 응답/형식 실패 — 저장 안 함")
                return 3
            if not passed:
                print(
                    f"{WARN} 게이트 미통과 — 마지막 시도 저장(검토 대기), cmd_validate가 최종 판정"
                )

        state_machine.transition(
            conn,
            args.draft,
            "enriched",
            reason=f"cli enrich ({'dry_run' if args.dry_run else 'live'})",
        )
        article_writer.save_enriched(conn, args.draft, enriched_payload)

        mode = "dry_run" if args.dry_run else "live"
        print(f"{OK} draft {args.draft} → enriched ({mode})")
        print(f"     상품 후보 {len(products)}개 주입 · user_prompt {len(result.user_prompt)}자")
        if args.dry_run:
            print(f"     system_blocks: {len(result.system_blocks)}개 (cache_control)")
        else:
            print(
                f"     제목: {enriched_payload['title']!r} · 본문 {len(enriched_payload['body_md'])}자"
                f" · featured {len(enriched_payload['products'])}/{len(products)}"
            )
            if result.usage:
                print(
                    f"     usage: input={result.usage.get('input_tokens')} "
                    f"output={result.usage.get('output_tokens')}"
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
            gates = report["gates"]
            print(f"{OK} draft {args.draft} → validated (게이트 {len(gates)}개 모두 PASS)")
            for gate, info in gates.items():
                skipped = isinstance(info.get("metrics"), dict) and info["metrics"].get("skipped")
                print(f"     {gate}: {'skip' if skipped else 'pass'}")
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


def _article_structured_json(ep: dict[str, Any]) -> str | None:
    """draft ep의 Tier 2 구조화(product_notes·quick_verdict·checkpoints)를 발행 저장용 JSON으로 (세션 #34).

    셋 다 비면 None(구조화 없는 글·옛 글 안전). 발행 글이 미리보기와 동일 레이아웃이 되도록 보존.
    """
    struct = {
        "product_notes": ep.get("product_notes") or {},
        "quick_verdict": ep.get("quick_verdict") or "",
        "checkpoints": ep.get("checkpoints") or [],
        "concept_image": ep.get("concept_image") or "",
        "concept_image_alt": ep.get("concept_image_alt") or "",
    }
    if not any(struct.values()):
        return None
    return json.dumps(struct, ensure_ascii=False)


def cmd_promote(args: argparse.Namespace) -> int:
    """approved draft → articles + article_products → published (게시 경로 배선).

    검증·승인된 enriched_payload(본문·메타)로 article_fields를 조립한다:
    - body_html : markdown → HTML 변환 (검증된 body_md 그대로 — content_hash 무결)
    - slug      : scenario.slug (충돌 시 -2 …)
    - content_hash · disclosure_first · truth/approved 타임스탬프
    그 후 promote_to_article + link_article_products(featured → /go/ 제휴 링크 소스).
    """
    from datetime import datetime, timezone

    from writer import article_writer

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conn = db.connect(db.DB_PATH)
    try:
        row = conn.execute(
            "SELECT scenario_id, status, enriched_payload FROM drafts WHERE id = ?",
            (args.draft,),
        ).fetchone()
        if row is None:
            print(f"{FAIL} draft {args.draft} 없음")
            return 2
        scenario_id, status, ep_json = row[0], row[1], row[2]
        if status != "approved":
            print(f"{FAIL} draft {args.draft} 상태={status!r} — approve(승인) 후에만 게시 가능")
            return 2
        if not ep_json:
            print(f"{FAIL} draft {args.draft} enriched_payload 비어있음")
            return 2

        ep = json.loads(ep_json)
        body_md = ep.get("body_md")
        if not body_md:
            print(f"{FAIL} draft {args.draft} body_md 없음 — 라이브 enrich 후 게시 가능")
            return 2
        missing_meta = [
            k for k in ("title", "summary", "meta_description", "schema_jsonld") if not ep.get(k)
        ]
        if missing_meta:
            print(f"{FAIL} enriched_payload 메타 누락: {missing_meta}")
            return 2

        srow = conn.execute("SELECT slug FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        if srow is None:
            print(f"{FAIL} scenario id={scenario_id} 없음")
            return 2
        slug = article_writer.unique_article_slug(conn, srow[0])

        disclosure_first = article_writer.extract_disclosure_first(body_md)
        if not disclosure_first:
            print(f"{FAIL} 첫머리 disclosure 추출 실패 — POLICY §2-2 표준 문구 누락 (게시 중단)")
            return 2

        # 검증된 body_md → HTML (제품 참조 코드 제거·본문 무결성 — validated 본문 = published 본문)
        body_html = article_writer.render_body_html(body_md)

        article_fields: dict[str, Any] = {
            "slug": slug,
            "scenario_id": scenario_id,
            "title": ep["title"],
            "summary": ep["summary"],
            "body_md": body_md,
            "body_html": body_html,
            "meta_description": ep["meta_description"],
            "meta_keywords": ep.get("meta_keywords"),
            "schema_jsonld": ep["schema_jsonld"],
            "disclosure_first": disclosure_first,
            "content_hash": article_writer.compute_content_hash(body_md),
            "truth_check_passed_at": now,
            "user_approved_at": now,
            "user_approved_note": args.note,
            # Tier 2 구조화(세션 #34) — 발행 글이 미리보기와 동일 레이아웃이 되도록 보존(없으면 None)
            "structured_json": _article_structured_json(ep),
        }
        article_id = article_writer.promote_to_article(conn, args.draft, article_fields)

        featured = ep.get("products") or []
        linked, skipped = article_writer.link_article_products(conn, article_id, featured)

        print(f"{OK} draft {args.draft} → published (article {article_id}, slug={slug!r})")
        msg = f"     제휴 상품 연결 {linked}개"
        if skipped:
            msg += f" · 매칭 실패 {skipped}개 (products 미존재)"
        print(msg)
        if featured and linked == 0:
            print(
                f"{WARN} 연결된 제휴 상품 0개 — /go/ 링크 없는 글. "
                "featured 상품이 products 테이블에 없습니다 (collect-products 먼저)"
            )
        print(f"     URL: /articles/{slug}/  (build 후 정적 렌더)")
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


def cmd_collect_products(args: argparse.Namespace) -> int:
    """AliExpress product.query → products 테이블 적재 (DECISIONS D9).

    검색어 소스 (둘 중 하나 필수):
    - ``--keywords <검색어>``  : 단일 영어 검색어
    - ``--scenario <slug>``   : 시나리오 매핑(search_keywords.yml)의 영어 검색어 목록 전체

    기본 dry_run: 검색어·요청만 빌드 — 실제 호출·DB 쓰기 없음.
    --no-dry-run: ali.env 로드 → 검색어별 실제 호출(쿼터 소모) → products upsert.
    외부 API 쿼터를 소모하므로 라이브는 사용자 명시 승인 후 (CLAUDE.md §2-라).
    """
    import time

    from collector import aliexpress as ali
    from collector import keyword_map, products_store
    from collector.keyword_map import SearchTerm

    # 1) 검색어(SearchTerm) 목록 결정 — --scenario 우선, 없으면 --keywords
    if args.scenario:
        terms = keyword_map.terms_for_scenario(args.scenario)
        if not terms:
            print(
                f"{FAIL} 시나리오 {args.scenario!r}에 매핑된 검색어 없음 "
                f"(search_keywords.yml 확인). 매핑된 slug: {keyword_map.all_mapped_slugs()}"
            )
            return 2
        source = f"scenario={args.scenario!r} ({len(terms)} 검색어)"
    elif args.keywords:
        terms = [SearchTerm(q=args.keywords, min_price=args.min_price, max_price=args.max_price)]
        source = f"keywords={args.keywords!r}"
    else:
        print(f"{FAIL} --keywords 또는 --scenario 중 하나가 필요합니다")
        return 2

    def _band(t: SearchTerm) -> str:
        if t.min_price is None and t.max_price is None:
            return ""
        lo = f"{t.min_price:,}" if t.min_price is not None else "0"
        hi = f"{t.max_price:,}" if t.max_price is not None else "∞"
        return f"  [{lo}~{hi} KRW]"

    mode = "dry_run" if args.dry_run else "live"
    print(f"{OK} collect-products {source}, page_size={args.page_size}, {mode}")

    # 2) dry_run: 검색어·밴드만 나열, 호출·DB 없음
    if args.dry_run:
        for t in terms:
            print(f"     - {t.q}{_band(t)}")
        print("     [DRY] 실제 호출·DB 쓰기 없음 — 라이브 수집은 --no-dry-run (쿼터·1클릭 승인)")
        return 0

    # 3) live: ali.env 로드 → 검색어별 호출(가격 밴드 적용) → 누적
    config.load_secrets()  # ali.env → ALI_APP_KEY/SECRET/TRACKING_ID
    all_products: list[dict] = []
    candidates: list[dict] = []  # 시나리오 draft.raw_payload용 (검색어 출처 포함)
    for i, t in enumerate(terms):
        if i:
            time.sleep(0.2)  # BACKEND §2-1 호출 간 간격 (rate limit 보호)
        # 라이브 검증 결과 게이트웨이 timestamp는 밀리초 (EVENTS #11 [확정])
        try:
            res = ali.query_products(
                t.q,
                timestamp=int(time.time() * 1000),
                dry_run=False,
                page_no=args.page_no,
                page_size=args.page_size,
                min_sale_price=t.min_price,
                max_sale_price=t.max_price,
            )
        except RuntimeError as e:  # 키 미설정
            print(f"{FAIL} {e}")
            return 2
        except Exception as e:  # 네트워크·응답 파싱 등 외부 요인
            print(f"{FAIL} {t.q!r} 호출 실패: {e}")
            return 3
        n = len(res.products)
        status = f" (API: {res.resp_msg})" if res.resp_msg else ""
        note = "  [NOTE] 0건 — 영어 검색어 권장" if n == 0 and not args.scenario else ""
        print(f"     {t.q:<22}{_band(t):<24} → {n}개{status}{note}")
        all_products.extend(res.products)
        for p in res.products:
            candidates.append(
                {
                    "source": p.get("source"),  # 제휴처 (aliexpress/coupang) — disclosure 정확성용
                    "source_product_id": p.get("source_product_id"),
                    "deeplink_slug": p.get("deeplink_slug"),
                    "name": p.get("name"),
                    "price_krw": p.get("price_krw"),
                    "keyword": t.q,  # 검색어 출처 (어느 카테고리로 수집됐는지)
                }
            )

    if not all_products:
        print(f"{WARN} 수신 상품 0개 — 적재할 데이터 없음")
        return 0

    # 4) 누적 상품 일괄 upsert + (시나리오 모드) 후보를 시나리오 draft.raw_payload에 기록
    from writer import article_writer

    conn = db.connect(db.DB_PATH)
    draft_id: int | None = None
    scenario_missing = False
    try:
        upsert = products_store.upsert_products(conn, all_products)
        if args.scenario:
            srow = conn.execute(
                "SELECT id FROM scenarios WHERE slug = ?", (args.scenario,)
            ).fetchone()
            if srow is not None:
                draft_id = article_writer.record_scenario_candidates(conn, int(srow[0]), candidates)
            else:
                scenario_missing = True
    finally:
        conn.close()
    print(
        f"{OK} products 적재 (수신 {len(all_products)}) — 신규 {upsert.inserted} · "
        f"갱신 {upsert.updated} · 스킵 {upsert.skipped} (필수 필드 누락)"
    )
    if draft_id is not None:
        print(f"{OK} 시나리오 draft {draft_id}에 후보 {len(candidates)}개 기록 — enrich 대상")
    elif scenario_missing:
        print(f"{WARN} 시나리오 {args.scenario!r}가 scenarios에 없어 draft 미기록 (db seed 필요)")
    return 0


def cmd_collect_category(args: argparse.Namespace) -> int:
    """카테고리 단위 제품 수집·정제·2티어 분류·연결 (세션 #17). 기본 dry_run.

    category_sources.yml의 카테고리 정의(검색어·밴드·필터)로 AliExpress 수집 →
    product_filter 정제 → category_products 연결. --no-dry-run은 쿼터 소모(§2-라 승인 후).
    """
    import sqlite3

    from collector import category_collect

    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        res = category_collect.collect_category(
            conn, args.slug, dry_run=args.dry_run, page_size=args.page_size
        )
    except (KeyError, ValueError) as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()

    mode = "dry_run" if args.dry_run else "live"
    print(f"{OK} collect-category {args.slug!r} ({mode})")
    for tname, term in res.terms:
        print(f"     [{tname}] q={term.q!r} band={term.min_price}~{term.max_price} KRW")
    if args.dry_run:
        print("     [DRY] 실제 호출·DB 쓰기 없음 — 라이브 수집은 --no-dry-run")
    else:
        print(f"{OK} 수신 {res.received} · 정제 {res.relevant} · 연결 {res.linked}")
        for tn, st in res.per_tier.items():
            print(f"     [{tn}] received={st['received']} relevant={st['relevant']}")
        if res.removed_stale:
            print(f"     [정합화] 옛 카탈로그 연결 {res.removed_stale}개 제거 (재수집 idempotent)")
    return 0


def cmd_suggest_categories(args: argparse.Namespace) -> int:
    """신규 카테고리 후보 제안 (세션 #35 ①) — 기존 카테고리 제외, LLM 브레인스토밍. 기본 dry_run."""
    import sqlite3

    from collector import category_config_gen

    if not args.dry_run:
        config.load_secrets()
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        existing = [r[0] for r in conn.execute("SELECT name_ko FROM categories").fetchall()]
    finally:
        conn.close()
    out = category_config_gen.suggest_categories(existing, n=args.count, dry_run=args.dry_run)
    if not out:
        print(f"{WARN} 후보 없음 (dry_run이거나 생성 실패 — 라이브는 --no-dry-run)")
        return 0
    print(f"{OK} 신규 카테고리 후보 {len(out)}개 (기존 {len(existing)}개 제외):")
    for c in out:
        print(f"     · {c['label']} — {c['reason']}")
    print("     마음에 드는 것을 'provision-category <이름> --no-dry-run'으로 생성")
    return 0


def cmd_provision_category(args: argparse.Namespace) -> int:
    """신규 카테고리 자동 프로비저닝 (세션 #35 ③): 설정생성→수집(vision 게이트)→빌드(draft).

    기본 dry_run. --no-dry-run은 LLM(설정·빌드)+알리 수집+Imagen 비용·DB 쓰기. status='draft'로만
    만들고 자동 공개 안 함 — 사람이 대시보드에서 검토·승인 후 배포(§2-마). vision_gate 강제로 사람
    단어튜닝 없이 오염 상품을 거른다(ANTHROPIC_API_KEY 필요 — 없으면 fail_closed로 전량 드롭).
    """
    import sqlite3

    from collector import category_autopilot

    if not args.dry_run:
        config.load_secrets()
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        res = category_autopilot.provision_category(
            conn, args.label, dry_run=args.dry_run, build=not args.no_build
        )
    finally:
        conn.close()
    if not res.get("ok"):
        print(f"{WARN} {res.get('reason', '프로비저닝 미완')}")
        print("     [DRY] 실제 실행은 --no-dry-run (LLM+알리+Imagen 비용·DB 쓰기)")
        return 0 if args.dry_run else 1
    built = "빌드함" if res.get("build") else "빌드 안 함"
    print(
        f"{OK} provision-category {res['label']!r} → slug={res['slug']} "
        f"(수집 {res['relevant']}편·비전드롭 {res['vision_dropped']}·연결 {res['linked']}, {built})"
    )
    print(
        f"     status=draft(미공개) — 검토 후 'approve-category {res['slug']}'로 공개 "
        "(AI 자동승인 금지·§2-마)"
    )
    return 0


def cmd_build_category(args: argparse.Namespace) -> int:
    """카테고리 콘텐츠(가이드·추천6선·FAQ·비교표·개념이미지) 생성·게이트·저장 (세션 #17).

    기본 dry_run. --no-dry-run은 Claude(글)+Imagen(이미지) 비용. SEO+진실성 게이트
    통과까지 재생성(상한 --max-attempts) 후 저장. 게이트 미통과 시 저장 안 함(가시화).
    """
    import os
    import sqlite3

    from enricher.category_page_builder import build_and_save
    from enricher.claude_client import ClaudeClient

    if not args.dry_run:
        config.load_secrets()
    client = ClaudeClient(api_key=os.environ.get("ANTHROPIC_API_KEY", "") or "dry-run")
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        res = build_and_save(
            conn,
            args.slug,
            client,
            dry_run=args.dry_run,
            generate_image=not args.no_image,
            max_attempts=args.max_attempts,
        )
    except (KeyError, ValueError) as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()

    if args.dry_run:
        print(
            f"{OK} build-category {args.slug!r} (dry_run) — "
            f"제품 {res['products']} · 프롬프트 {res['prompt_len']}자"
        )
        print("     [DRY] 실제 생성·DB 쓰기 없음 — 라이브는 --no-dry-run (Claude+Imagen 비용)")
        return 0

    print(f"{OK} build-category {args.slug!r}: {res['title']}")
    print(
        f"     추천 {res['picks']} · 타입표 {res['type_table']} · 체크 {res['checkpoints']} · "
        f"비교 {res['compare_rows']}항목 · FAQ {res['faq']}"
    )
    print(
        f"     게이트(truth·disclosure·links)={res['overall_pass']} · "
        f"SEO={res['seo_passed']}(밀도 {res['seo_density']}%) · 저장={res.get('saved')}"
    )
    if res.get("concept_image"):
        _tag = "재사용" if res.get("concept_image_reused") else "신규 생성"
        print(f"     개념 이미지({_tag}): {res['concept_image']}")
    if res.get("concept_image_error"):
        print(f"     {WARN} 이미지 실패: {res['concept_image_error']}")
    if not res.get("saved"):
        print(f"     {WARN} 게이트 미통과 — 저장 안 됨(인간 검토 필요): {res['gates']}")
    if res.get("saved"):
        print(
            f"     {WARN} status=draft(미공개) — 검토 후 'approve-category {args.slug}'로 공개 "
            "(AI 자동승인 금지·§2-마)"
        )
    return 0


def cmd_register_categories(args: argparse.Namespace) -> int:
    """수익 카테고리 리스트를 순차로 자동 등록(collect→build). 세션 #21.

    category_sources.yml의 카테고리(또는 지정 slug)를 차례로 수집·생성한다. 한 카테고리가
    실패해도 다음으로 계속(무인 안전·실패 격리) 후 마지막에 요약. 저장은 build_and_save가
    draft 고정 → 자동 공개 없음(E7·§2-마). 공개는 사용자가 approve-category로.
    기본 dry_run. --no-dry-run은 알리 수집 쿼터 + DeepSeek/Imagen 비용(§2-라 승인 후).
    """
    import os
    import sqlite3

    from collector import category_collect
    from enricher.category_page_builder import build_and_save
    from enricher.claude_client import ClaudeClient

    sources = category_collect.load_sources()
    slugs = sorted(sources) if args.all else list(args.slugs)
    if not slugs:
        print(f"{FAIL} 등록할 카테고리 없음 — slug를 지정하거나 --all 사용")
        return 2
    unknown = [s for s in slugs if s not in sources]
    if unknown:
        print(f"{FAIL} category_sources.yml에 정의 없는 slug: {unknown}")
        return 2

    if not args.dry_run:
        config.load_secrets()
    client = ClaudeClient(api_key=os.environ.get("ANTHROPIC_API_KEY", "") or "dry-run")
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row

    summary: list[tuple[str, str]] = []
    try:
        for i, slug in enumerate(slugs, 1):
            print(f"\n=== [{i}/{len(slugs)}] {slug} 등록 ===")
            try:
                if not args.skip_collect:
                    cres = category_collect.collect_category(
                        conn, slug, dry_run=args.dry_run, page_size=args.page_size
                    )
                    if not args.dry_run:
                        print(f"     수집: 수신 {cres.received} · 연결 {cres.linked}")
                bres = build_and_save(
                    conn,
                    slug,
                    client,
                    dry_run=args.dry_run,
                    generate_image=not args.no_image,
                    max_attempts=args.max_attempts,
                )
                if args.dry_run:
                    summary.append((slug, "DRY"))
                    print("     [DRY] 실제 수집·생성 없음")
                elif bres.get("saved"):
                    summary.append((slug, "OK(draft)"))
                    print(
                        f"     {OK} 저장(draft) 게이트={bres.get('overall_pass')} "
                        f"SEO={bres.get('seo_passed')} 이미지={bres.get('concept_image') or '—'}"
                    )
                    if args.auto_publish and not args.dry_run:
                        from writer import auto_publish as _ap

                        ar = _ap.auto_publish_one(conn, slug, client, use_llm=True)
                        if ar["published"]:
                            summary[-1] = (slug, "OK(published)")
                            print(f"     {OK} 가드레일 통과 → 자동 공개(published)")
                        else:
                            summary[-1] = (slug, "보류(draft)")
                            print(
                                f"     {WARN} 가드레일 보류 — draft 유지: "
                                f"{'; '.join(ar['reasons'][:2])}"
                            )
                else:
                    summary.append((slug, "게이트미통과"))
                    print(f"     {WARN} 게이트 미통과 — 저장 안 됨: {bres.get('gates')}")
            except Exception as e:  # 한 카테고리 실패 격리(무인 안전·다음 진행)
                summary.append((slug, f"실패:{type(e).__name__}"))
                print(f"     {FAIL} {slug}: {e}")
    finally:
        conn.close()

    print("\n=== 등록 요약 ===")
    for slug, status in summary:
        print(f"  {slug}: {status}")
    done = sum(1 for _, s in summary if s.startswith("OK") or s == "DRY")
    tag = OK if done == len(slugs) else WARN
    print(f"{tag} {done}/{len(slugs)} 완료 — 전부 draft (approve-category로 공개·E7)")
    return 0 if done == len(slugs) else 1


def cmd_approve_category(args: argparse.Namespace) -> int:
    """draft 카테고리 → published (사용자 1클릭 승인·공개). AI 자동승인 금지(§2-마·E7)."""
    from writer import category_state

    conn = db.connect(db.DB_PATH)
    try:
        res = category_state.approve(conn, args.slug)
        print(f"{OK} 카테고리 {res['slug']!r}({res['name']}) → published (공개)")
        if res["warned"]:
            print(
                f"     {WARN} 가이드 글이 아직 없음 — 빈약한 페이지일 수 있음(build-category 권장)"
            )
        print("     ※ 실제 공개 반영은 build(렌더) + deploy 후 (현재는 DB 상태만 전이)")
        return 0
    except category_state.CategoryStateError as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()


def cmd_unapprove_category(args: argparse.Namespace) -> int:
    """published 카테고리 → draft (공개 취소·비공개)."""
    from writer import category_state

    conn = db.connect(db.DB_PATH)
    try:
        res = category_state.unapprove(conn, args.slug)
        print(f"{OK} 카테고리 {res['slug']!r}({res['name']}) → draft (비공개)")
        return 0
    except category_state.CategoryStateError as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()


def cmd_unpublish_article(args: argparse.Namespace) -> int:
    """published 글 → unpublished (라이브 비공개·발행후 안전망·세션 #29). 재빌드·배포는 별도."""
    from writer import article_state

    conn = db.connect(db.DB_PATH)
    try:
        res = article_state.unpublish(conn, args.slug, reason=args.note or "")
        print(f"{OK} 글 {res['slug']!r}({res['title']}) → unpublished (비공개)")
        print("     ※ 라이브 반영은 build --full + deploy 필요")
        return 0
    except article_state.ArticleStateError as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()


def cmd_republish_article(args: argparse.Namespace) -> int:
    """unpublished/archived 글 → published (재공개·세션 #29). 재빌드·배포는 별도."""
    from writer import article_state

    conn = db.connect(db.DB_PATH)
    try:
        res = article_state.republish(conn, args.slug)
        print(f"{OK} 글 {res['slug']!r}({res['title']}) → published (재공개)")
        print("     ※ 라이브 반영은 build --full + deploy 필요")
        return 0
    except article_state.ArticleStateError as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()


def cmd_monitor_articles(args: argparse.Namespace) -> int:
    """published 글 사후 점검(무결성·적합성·세션 #29). --auto-unpublish면 미달 글 자동 비공개.

    기본 보고만(fail-closed 자동 비공개는 플래그). 자동 비공개 후 라이브 반영은 build+deploy 별도.
    """
    from writer import article_guardrail

    conn = db.connect(db.DB_PATH)
    try:
        res = article_guardrail.monitor(conn, auto_unpublish=args.auto_unpublish)
    finally:
        conn.close()
    print(f"{OK} 글 사후 점검 — 검사 {res['checked']}편 · 미달 {len(res['failed'])}편")
    for f in res["failed"]:
        print(f"     {WARN} {f['slug']}: {'; '.join(f['reasons'])}")
    if res["unpublished"]:
        print(f"{OK} 자동 비공개 {len(res['unpublished'])}편: {', '.join(res['unpublished'])}")
        print("     ※ 라이브 반영은 build --full + deploy 필요")
    return 0


def cmd_auto_publish(args: argparse.Namespace) -> int:
    """가드레일 통과 카테고리 자동 공개 (E7→가드레일·세션 #22). 보류는 draft 유지·사유 보고.

    기본 dry_run(판정만). --no-dry-run으로 실제 공개 + 추천6선 LLM 의미 검수(비용 소액).
    fail-closed: 조금이라도 애매하면 공개하지 않고 draft로 둔다(미탐<오탐).
    """
    import os
    import sqlite3

    from enricher.claude_client import ClaudeClient
    from writer import auto_publish, category_state

    apply = not args.dry_run
    use_llm = not args.no_llm
    if apply or use_llm:
        config.load_secrets()  # OpenRouter(LLM 검수)·ali 키
    client = ClaudeClient(api_key=os.environ.get("ANTHROPIC_API_KEY", "") or "dry-run")
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if args.all:
            slugs = [r["slug"] for r in category_state.pending_approval(conn)]
        else:
            slugs = list(args.slugs)
        if not slugs:
            print(f"{WARN} 대상 없음 — slug 지정 또는 --all(글 있는 draft 전체)")
            return 0
        results = auto_publish.auto_publish(conn, slugs, client, use_llm=use_llm, apply=apply)
    finally:
        conn.close()

    print("\n=== 자동 게시 판정 ===")
    pub = held = 0
    for r in results:
        if r["passed"]:
            pub += 1
            print(f"  {OK} {r['slug']}: {'공개' if r['published'] else '통과(판정만)'}")
        else:
            held += 1
            print(f"  {WARN} {r['slug']}: 보류 — {'; '.join(r['reasons'])}")
    mode = "공개" if apply else "DRY(판정만·공개 안 함)"
    print(
        f"\n[{mode}] 통과 {pub} · 보류 {held} / {len(results)} — 보류는 draft 유지(킬스위치 불필요)"
    )
    return 0 if held == 0 else 1


def cmd_category_status(args: argparse.Namespace) -> int:
    """카테고리 게시 현황 다이제스트 (무인 사후 감시·세션 #22) — 폰으로 10초 훑기용.

    각 카테고리 status·추천수·전체수·글 유무. --monitor면 published를 휴리스틱 재검수해
    '지금 가드레일 미달'(킬스위치 후보)을 표시한다(자동 비공개 안 함·보고만).
    """
    import sqlite3

    from writer import auto_publish

    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT c.slug, c.name_ko, c.status, c.guide_generated_at, "
            "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id) AS total, "
            "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id AND is_featured=1) "
            "AS feat FROM categories c ORDER BY c.display_order, c.id"
        ).fetchall()
        print("=== 카테고리 현황 ===")
        for r in rows:
            g = "글O" if r["guide_generated_at"] else "글X"
            print(
                f"  {r['status']:<9} {r['slug']:<18} 추천{r['feat']} 전체{r['total']:>3} {g}  "
                f"{r['name_ko']}"
            )
        pub = sum(1 for r in rows if r["status"] == "published")
        print(f"  → published {pub} / {len(rows)}")
        if args.monitor:
            flags = auto_publish.monitor(conn, use_llm=False)
            print("\n=== 사후 감시(published 재검수·휴리스틱) ===")
            if not flags:
                print(f"  {OK} 미달 없음 — 전부 가드레일 통과 상태")
            else:
                for f in flags:
                    print(
                        f"  {WARN} {f['slug']}: {'; '.join(f['reasons'])} "
                        f"→ 킬스위치: unapprove-category {f['slug']}"
                    )
    finally:
        conn.close()
    return 0


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


def cmd_sync_slugmap(args: argparse.Namespace) -> int:
    """published 상품 → D1 slug_map UPSERT (DB §11-2). 기본 dry_run.

    /go/<slug> 게이트웨이(go_gateway.js)가 조회하는 D1 라우팅 테이블 갱신.
    게시된 글에 연결된 상품의 deeplink_slug → deeplink_url만 노출(미게시 비노출).
    dry_run=True 기본 — 라이브는 wrangler d1 execute(외부 D1 쓰기·명시 승인, §2-라).
    """
    from tracker import slug_map as sm

    conn = db.connect(db.DB_PATH)
    try:
        result = sm.sync_slug_map(
            conn,
            database_name=args.database,
            cwd=str(PROJECT_ROOT),
            dry_run=args.dry_run,
        )
    finally:
        conn.close()

    mode = "dry_run" if result.dry_run else "live"
    print(f"{OK} sync-slugmap ({mode}) — slug {len(result.entries)}개")
    for e in result.entries[:20]:
        print(f"     /go/{e['slug']} → {e['source']} (product {e['product_id_local']})")
    if len(result.entries) > 20:
        print(f"     … 외 {len(result.entries) - 20}개")
    if not result.entries:
        print("     [NOTE] 게시 글 연결 상품 0개 — 동기화 대상 없음 (promote 먼저)")
        return 0
    if result.dry_run:
        print("     [DRY] 실제 D1 쓰기 없음 — 라이브는 --no-dry-run (wrangler·명시 승인)")
        return 0
    if result.error:
        print(f"{FAIL} D1 실행 실패: {result.error}")
        if result.stderr:
            print(f"     stderr: {result.stderr.strip()[:300]}")
        return 3
    print(f"{OK} D1 slug_map UPSERT 완료 ({len(result.entries)}개)")
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

    if args.full or args.preview:
        from builder import renderer

        out_dir = (PROJECT_ROOT / "build" / "preview") if args.preview else renderer.DEFAULT_OUT
        summary = renderer.render_site(out_dir=out_dir, include_drafts=args.preview)
        mode = "미리보기(draft 포함·검토용)" if args.preview else "공개(published만)"
        print(
            f"{OK} 사이트 렌더 [{mode}] → {summary['out_dir']} "
            f"(페이지 {summary['pages']} · 시나리오 {summary['scenarios']} · "
            f"카테고리 {summary['categories']} · 게시글 {summary['articles_published']})"
        )
        if summary["articles_published"] == 0:
            print(
                "[NOTE] 게시 article 0편 — 상세글 미렌더. "
                "시나리오 카드 링크(/articles/<slug>/)는 콘텐츠 게시(Phase 3~4) 후 활성"
            )

        # 공개 빌드는 /go/ 리다이렉트 Pages Function도 재생성(published 상품 맵). 미리보기는 생략.
        if args.full:
            import sqlite3 as _sqlite3

            from builder import go_function

            _conn = db.connect(db.DB_PATH)
            _conn.row_factory = _sqlite3.Row
            try:
                gres = go_function.generate_go_function(_conn, PROJECT_ROOT)
            finally:
                _conn.close()
            print(f"{OK} /go/ Pages Function 생성 → {gres['count']}개 제품 리다이렉트")

    if args.save_empty and not manifest_path.exists():
        manifest_mod.save(manifest_path, manifest)
        print(f"{OK} 빈 manifest 저장 → {manifest_path}")

    return 0


def cmd_refresh_cycle(args: argparse.Namespace) -> int:
    """무인 일일 새로고침·자가복원·빌드·배포 사이클 (A안·세션 #23). 기본 dry_run.

    published 카테고리 가격·판매량 새로고침 → 가드레일 자가복원(미달 자동 비공개) →
    빌드 → 변경분만 배포. dry_run은 현황·판정만(외부 영향 없음). --no-dry-run이 실제 사이클.
    LLM 미사용(수집·휴리스틱·렌더) → 일일 비용 ~$0.
    """
    import sqlite3

    from deployer import refresh_cycle as rc

    if not args.dry_run and not args.no_refresh:
        config.load_secrets()  # 알리 키(수집) — 라이브 새로고침 시
    conn = db.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        res = rc.run_refresh_cycle(
            conn,
            project_root=PROJECT_ROOT,
            page_size=args.page_size,
            refresh=not args.no_refresh,
            auto_killswitch=not args.no_killswitch,
            do_build=not args.no_build,
            do_deploy=not args.no_deploy,
            dry_run=args.dry_run,
            verify_url=args.verify_url,
        )
    finally:
        conn.close()

    mode = "DRY(판정만·외부영향 없음)" if res.dry_run else "LIVE"
    print(f"\n=== refresh-cycle [{mode}] ===")
    print(f"공개 카테고리 {len(res.published)}개: {', '.join(res.published) or '(없음)'}")
    if not args.no_refresh:
        ok = sum(1 for r in res.refreshed if r.ok)
        print(f"새로고침: 성공 {ok} / {len(res.refreshed)}")
        for r in res.refreshed:
            if r.ok:
                print(
                    f"     {OK} {r.slug}: 수신 {r.received} · 연결 {r.linked} · prune {r.removed_stale}"
                )
            else:
                print(f"     {FAIL} {r.slug}: {r.error}")
    print(f"가드레일 미달(사후감시): {len(res.flagged)}")
    for f in res.flagged:
        print(f"     {WARN} {f['slug']}: {'; '.join(f['reasons'])}")
    if res.killswitched:
        print(f"{WARN} 자가복원(자동 비공개): {', '.join(res.killswitched)}")
    if res.built:
        print(f"{OK} 빌드 완료 · /go/ 리다이렉트 {res.go_count}개")
    print(f"산출물 변경: {'있음' if res.changed else '없음'}")
    if res.deployed:
        print(f"{OK} 배포 push 완료 (rc={res.push_rc}) — CI가 honsallim.com 반영")
        if res.verify_status is not None:
            print(f"     verify status={res.verify_status}")
    for n in res.notes:
        print(f"     · {n}")

    # 무인 모니터링 — 사이클 다이제스트 저장 + 대시보드 갱신 (dry_run 포함 항상)
    from datetime import datetime

    from dashboard import render as dash_render

    ran_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report_path = db.DB_PATH.parent / "refresh_cycle_last.json"
    rc.write_cycle_report(res, report_path, ran_at)
    dash_out = dash_render.render_dashboard(
        output_path=db.DB_PATH.parent / "dashboard" / "index.html"
    )
    print(f"{OK} 모니터링 갱신 → 기록 {report_path.name} · 대시보드 {dash_out}")

    rc_fail = any(not r.ok for r in res.refreshed)
    deploy_fail = (not res.dry_run) and (not args.no_deploy) and res.changed and not res.deployed
    return 1 if (rc_fail or deploy_fail) else 0


# ─── 키워드 발행 큐 명령 (세션 #25) — 운영 대시보드 ──────────────────────


def _set_keyword_status(keyword_id: int, status: str, reason: str | None = None) -> None:
    """별도 연결로 키워드 상태 설정 (메인 conn이 닫힌 뒤 호출해도 안전)."""
    from writer import keyword_queue as kq

    conn = db.connect(db.DB_PATH)
    try:
        kq.set_status(conn, keyword_id, status, reason)
    finally:
        conn.close()


def cmd_keyword_add(args: argparse.Namespace) -> int:
    """키워드를 발행 큐에 추가 (status=pending). 운영 대시보드 '대기 키워드'."""
    from writer import keyword_queue as kq

    conn = db.connect(db.DB_PATH)
    try:
        kid = kq.add_keyword(
            conn,
            args.keyword,
            slug=args.slug,
            channel=args.channel,
            budget_min_krw=args.budget_min,
            budget_max_krw=args.budget_max,
            notes=args.note,
            score=args.score,
        )
    except ValueError as e:
        print(f"{FAIL} {e}")
        return 2
    finally:
        conn.close()
    print(f"{OK} 키워드 #{kid} 추가: {args.keyword!r} (채널={args.channel}, status=pending)")
    return 0


def cmd_keyword_recommend(args: argparse.Namespace) -> int:
    """추천 키워드 생성(검색량순) — 정의된 선정 방식(keyword_research)을 SEO 씨앗에 적용.

    네이버 실 월검색량(읽기 전용·무료). 씨앗별 실패 시 캐시 보조키워드로 자가복원.
    --add-top로 1순위를 큐에 추가(status=pending) — '선택 없으면 자동 세팅' 헤드리스 대응.
    """
    from writer import keyword_queue as kq
    from writer import keyword_recommender as kr

    config.load_secrets()  # 네이버 검색광고 키 (live 조회)
    conn = db.connect(db.DB_PATH)
    try:
        recs = kr.recommend(
            conn,
            custom_seed=args.seed,
            limit=args.limit,
            channel=args.channel,
            live=not args.no_live,
        )
        if not recs:
            print(f"{WARN} 추천 키워드 없음 — 씨앗(seo_keywords.yml)·네이버 키·네트워크 확인")
            return 0
        print(f"{OK} 추천 키워드 {len(recs)}건 (검색량순):")
        for i, r in enumerate(recs, 1):
            vol = f"{r['volume']:,}" if r["volume"] is not None else "—"
            src = "네이버" if r["source"] == "naver" else "캐시"
            print(
                f"  {i:>2}. {r['keyword']}  (월검색 {vol} · {r['competition']} · {src} · 씨앗 {r['seed']})"
            )
        if args.add_top:
            top = recs[0]
            kid = kq.add_keyword(
                conn, top["keyword"], channel=top["channel"], score=float(top["volume"] or 0)
            )
            print(
                f"{OK} 1순위 {top['keyword']!r} → 키워드 #{kid} 추가 "
                f"(채널 {top['channel']}, status=pending)"
            )
        return 0
    finally:
        conn.close()


def _gather_keyword_candidates(
    conn: sqlite3.Connection, kw: dict[str, Any], page_size: int
) -> tuple[list[dict[str, Any]], str]:
    """키워드 상품 후보 확보 — **수동 미리선택(쿠팡 등) + 알리 자동수집을 결합**(하이브리드).

    쿠팡(수동·이미지·수익) + 알리(판매량·가격 데이터=구글 Information Gain)를 한 글에 함께 담아
    구글 어필리에이트 페널티를 피하면서 쿠팡 수익도 확보(DECISIONS S1 멀티채널·세션 #28 PartA).

    ★세션 #30 근본수정: 알리 검색은 **카테고리 영어 티어 검색어**로 한다. 한글 키워드를 알리에
    직접 넣으면 영어 인덱스에 매칭 실패해 폰케이스·티셔츠 등 무관 상품만 와서(세션 #29 라이브
    적발) 적합성 가드가 전량 제외 → 글이 thin(쿠팡만)이 됐다. 키워드를 카테고리에 매핑하고
    그 카테고리의 검증된 영어 검색어(라이브 5카테고리 정상)로 검색한다. 미매핑 키워드는 영어
    검색어가 없어 알리를 건너뛴다(쿠팡 단독 또는 보류 — fail-closed 자동승인이 별도 처리).
    반환: (candidates, note). 후보는 enrich 프롬프트의 {{products}} + promote 연결 소스.
    """
    from collector import products_store

    def _cands(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "source": p.get("source"),
                "source_product_id": p.get("source_product_id"),
                "deeplink_slug": p.get("deeplink_slug"),
                "name": p.get("name"),
                "price_krw": p.get("price_krw"),
            }
            for p in items
        ]

    candidates: list[dict[str, Any]] = []
    notes: list[str] = []

    # (1) 수동 미리선택(쿠팡 등) — 운영자가 고른 것, 항상 포함
    tp = kw.get("target_products")
    if tp:
        try:
            items = json.loads(tp)
        except (json.JSONDecodeError, TypeError):
            items = []
        if isinstance(items, list) and items:
            up = products_store.upsert_products(conn, items)
            candidates.extend(_cands(items))
            notes.append(
                f"수동 미리선택 {len(items)}개(신규 {up.inserted}·갱신 {up.updated}·스킵 {up.skipped})"
            )

    # (2) 알리 자동수집(판매량·가격 데이터=Information Gain) — 채널 ali/both.
    #     ★세션 #30: 키워드→카테고리 매핑 → 카테고리 영어 티어 검색어로 검색(한글 직접검색 금지).
    if kw["channel"] in ("ali", "both"):
        from collector import category_collect, keyword_relevance

        slug = keyword_relevance.resolve_category(kw["keyword"])
        spec = category_collect.load_sources().get(slug) if slug else None
        if spec is None or not spec.tiers:
            # 미매핑/티어 없음 — 알리 영어 검색어가 없다. 한글 직접검색은 off-target만 와서 건너뛴다
            # (쿠팡 수동분만 또는 보류 — fail-closed 자동승인이 미매핑을 별도 처리).
            if slug is None:
                notes.append(
                    "ali 건너뜀(카테고리 미매핑 — 영어 검색어 없음·한글 직접검색은 off-target)"
                )
            else:
                notes.append(f"ali 건너뜀(카테고리 {slug} 티어 미정의)")
        else:
            config.load_secrets()
            # 카테고리 영어 티어 검색(검증된 라이브 경로) → 키워드-적합성 필터(키워드-인지 유효 제외어).
            # 쿠팡 수동 배너는 사람이 골라 필터하지 않는다.
            raw, received = category_collect.search_tiers(spec, page_size=page_size)
            kept, dropped = keyword_relevance.filter_products(kw["keyword"], raw)
            if kept:
                products_store.upsert_products(conn, kept)
            candidates.extend(_cands(kept))
            note = f"ali 카테고리({slug}) 영어검색 {received}개 → 적합 {len(kept)}개"
            if dropped:
                note += f"(off-target {len(dropped)}개 제외)"
            notes.append(note)

    if not candidates:
        return [], "상품 없음 — 쿠팡 단독 채널은 수동 미리선택(target_products)이 필요합니다"
    return candidates, " · ".join(notes)


def cmd_keyword_generate(args: argparse.Namespace) -> int:
    """키워드 → 시나리오 파생 → 상품 확보 → draft → enrich → validate. 기본 dry_run.

    라이브(--no-dry-run)는 본문 생성 LLM 비용 발생. 결과는 '검토 대기(drafted)'까지만 —
    E7 인간 승인 게이트 유지(자동 발행 안 함). 승인·발행은 대시보드/별도 명령.
    """
    from writer import article_writer
    from writer import keyword_queue as kq

    conn = db.connect(db.DB_PATH)
    draft_id: int
    try:
        kw = kq.get_keyword(conn, args.id)
        if kw is None:
            print(f"{FAIL} keyword id={args.id} 없음")
            return 2
        mode = "dry_run" if args.dry_run else "live"
        print(f"{OK} 키워드 #{args.id} {kw['keyword']!r} 채널={kw['channel']} ({mode})")

        if args.dry_run:
            tp_n = 0
            if kw.get("target_products"):
                try:
                    parsed = json.loads(kw["target_products"])
                    tp_n = len(parsed) if isinstance(parsed, list) else 0
                except (json.JSONDecodeError, TypeError):
                    tp_n = 0
            print(
                "     [DRY] 시나리오 파생→상품 확보→draft→enrich→validate (실제 쓰기·API·비용 없음)"
            )
            # ali 수집 여부는 채널뿐 아니라 카테고리 매핑에도 달림(미매핑이면 영어 검색어가 없어 건너뜀)
            ali_preview = "아니오(채널=쿠팡 단독)"
            if kw["channel"] in ("ali", "both"):
                from collector import keyword_relevance

                slug = keyword_relevance.resolve_category(kw["keyword"])
                ali_preview = (
                    f"예(카테고리 {slug} 영어검색)"
                    if slug
                    else "아니오(카테고리 미매핑 — 알리 영어 검색어 없음·건너뜀)"
                )
            print(f"     수동 미리선택 {tp_n}개 · ali 수집 {ali_preview}")
            return 0

        persona_slug = settings.get("default_keyword_persona")
        scenario_id = kq.ensure_scenario_for_keyword(
            conn, args.id, default_persona_slug=persona_slug
        )
        srow = conn.execute("SELECT slug FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        print(f"     시나리오 #{scenario_id} ({srow[0]})")
        kq.set_status(conn, args.id, "generating", "generate 시작")
        try:
            candidates, note = _gather_keyword_candidates(conn, kw, args.page_size)
        except Exception as e:  # 상품 확보 실패는 키워드 상태에 기록하고 종료
            kq.set_status(conn, args.id, "failed", f"상품 확보 실패: {e}")
            print(f"{FAIL} 상품 확보 실패: {e}")
            return 3
        print(f"     {note}")
        draft_id = article_writer.record_scenario_candidates(
            conn, scenario_id, candidates, working_title=kw["keyword"]
        )
        kq.link_draft(conn, args.id, draft_id)
        print(f"{OK} draft #{draft_id} 생성 · 후보 {len(candidates)}개")
    finally:
        conn.close()

    # enrich + validate (각 명령이 자체 연결) — 기존 발행 기계 재사용
    rc = cmd_enrich(argparse.Namespace(draft=draft_id, dry_run=False))
    if rc != 0:
        _set_keyword_status(args.id, "failed", f"enrich rc={rc}")
        print(f"{FAIL} enrich 실패 (rc={rc})")
        return rc
    rc = cmd_validate(argparse.Namespace(draft=draft_id))
    if rc == 0:
        _set_keyword_status(args.id, "drafted", "검토 대기")
        print(f"{OK} 키워드 #{args.id} → drafted. 대시보드에서 미리보기→1클릭 승인→발행 (E7)")
        return 0
    if rc == 1:
        _set_keyword_status(args.id, "drafted", "검증 rejected — 검토 필요")
        print(f"{WARN} 검증 실패(rejected) — 대시보드에서 검토 필요")
        return 0
    _set_keyword_status(args.id, "failed", f"validate rc={rc}")
    return rc


def cmd_keyword_list(args: argparse.Namespace) -> int:
    """키워드 큐 목록 출력 (status 필터 선택)."""
    from dashboard import queries

    conn = db.connect(db.DB_PATH)
    try:
        rows = queries.list_keywords(conn, status=args.status)
    finally:
        conn.close()
    if not rows:
        print(f"{WARN} 키워드 없음" + (f" (status={args.status})" if args.status else ""))
        return 0
    print(f"{OK} 키워드 {len(rows)}건:")
    for r in rows:
        print(
            f"  #{r['id']:>3} [{r['status']:<10}] {r['channel']:<7} "
            f"{r['keyword']}  (slug={r['slug']})"
        )
    return 0


def cmd_keyword_delete(args: argparse.Namespace) -> int:
    """키워드 큐에서 키워드 삭제 — 연결된 미발행 draft 동반 삭제.

    발행된 글이 연결돼 있으면 차단(라이브 글 보호·§0). foreign_keys=ON이라 draft를 먼저 지운다.
    """
    conn = db.connect(db.DB_PATH)
    try:
        kid = int(args.id)
        kw = conn.execute("SELECT keyword FROM keyword_queue WHERE id = ?", (kid,)).fetchone()
        if kw is None:
            print(f"{FAIL} 키워드 #{kid} 없음")
            return 2
        pub = conn.execute(
            "SELECT id FROM drafts WHERE keyword_id = ? AND status = 'published'", (kid,)
        ).fetchall()
        if pub:
            ids = ", ".join(f"#{r[0]}" for r in pub)
            print(
                f"{FAIL} 발행된 글({ids})이 연결돼 삭제 불가 — "
                "먼저 글을 비공개(unpublish-article)하세요."
            )
            return 2
        srow = conn.execute("SELECT scenario_id FROM keyword_queue WHERE id = ?", (kid,)).fetchone()
        sid = srow[0] if srow else None
        n = conn.execute("DELETE FROM drafts WHERE keyword_id = ?", (kid,)).rowcount
        conn.execute("DELETE FROM keyword_queue WHERE id = ?", (kid,))
        # 키워드 파생 가짜 시나리오도 함께 정리 — 단 글(article)이 안 걸린 경우만(라이브/잔존 글
        # 보호·FK 안전). 세션 #35: 키워드만 지우고 시나리오가 남아 세팅에 쓰레기 카드로 남던 버그 수정.
        scen_removed = False
        if sid is not None:
            has_art = conn.execute(
                "SELECT 1 FROM articles WHERE scenario_id = ? LIMIT 1", (sid,)
            ).fetchone()
            if has_art is None:
                conn.execute("DELETE FROM scenarios WHERE id = ?", (sid,))
                scen_removed = True
        conn.commit()
        extra = " + 연결 시나리오" if scen_removed else ""
        print(f"{OK} 키워드 #{kid} {kw[0]!r} 삭제 (연결 draft {n}건{extra} 동반 삭제)")
        return 0
    finally:
        conn.close()


def cmd_reject(args: argparse.Namespace) -> int:
    """draft → rejected (대시보드 반려). approved면 먼저 승인취소 후 반려."""
    from writer import state_machine

    conn = db.connect(db.DB_PATH)
    try:
        try:
            cur = state_machine.current_status(conn, args.draft)
        except ValueError as e:
            print(f"{FAIL} {e}")
            return 2
        reason = "cli reject" + (f" — {args.note}" if args.note else "")
        try:
            if cur == "approved":
                state_machine.transition(conn, args.draft, "validated", reason="reject: 승인취소")
            state_machine.transition(conn, args.draft, "rejected", reason=reason)
        except state_machine.IllegalStateError as e:
            print(f"{FAIL} 반려 불가 (현재 {cur}): {e}")
            return 2
        print(f"{OK} draft {args.draft} → rejected")
        return 0
    finally:
        conn.close()


def cmd_coupang_add(args: argparse.Namespace) -> int:
    """쿠팡 수동 상품을 키워드 미리선택(target_products)에 추가 (공식 딥링크·텍스트, 세션 #25).

    쿠팡 15만원 전 수동 단계 — CDN 이미지 미사용(함정 #3). 추가된 상품은 글 생성 후보로 쓰인다.
    """
    from collector import coupang_manual

    conn = db.connect(db.DB_PATH)
    try:
        try:
            product = coupang_manual.build_manual_product(
                args.name,
                args.url,
                price_krw=args.price,
                widget_html=getattr(args, "widget", None),
                banner_html=getattr(args, "banner", None),
                affiliate_tag=settings.get("coupang_tag"),
            )
            n = coupang_manual.add_to_keyword(conn, args.keyword_id, product)
        except ValueError as e:
            print(f"{FAIL} {e}")
            return 2
    finally:
        conn.close()
    print(f"{OK} 쿠팡 상품 {product['name']!r} → 키워드 #{args.keyword_id} 미리선택 (총 {n}개)")
    return 0


def cmd_category_coupang_add(args: argparse.Namespace) -> int:
    """카테고리 쿠팡 운영자추천 zone에 쿠팡 배너 상품 추가 (세션 #32).

    공식 배너(<a><img></a>) 여러 개 한 번에 가능 — 파싱 → products 업서트 → category_products 링크.
    """
    from collector import category_coupang

    conn = db.connect(db.DB_PATH)
    try:
        try:
            res = category_coupang.add_banners(
                conn,
                args.slug,
                getattr(args, "banner", None),
                affiliate_tag=settings.get("coupang_tag"),
            )
        except ValueError as e:
            print(f"{FAIL} {e}")
            return 2
    finally:
        conn.close()
    if res["added"] == 0:
        print(f"{WARN} 추가된 쿠팡 상품 없음 — 배너(<a><img></a>) 확인 (카테고리 {args.slug})")
        return 1
    print(f"{OK} 카테고리 {args.slug!r} 쿠팡 {res['added']}개 추가: " + ", ".join(res["names"]))
    return 0


def cmd_category_coupang_list(args: argparse.Namespace) -> int:
    """카테고리 쿠팡존 상품 목록."""
    from collector import category_coupang

    conn = db.connect(db.DB_PATH)
    try:
        rows = category_coupang.list_coupang(conn, args.slug)
    finally:
        conn.close()
    if not rows:
        print(f"{WARN} 카테고리 {args.slug!r} 쿠팡 상품 없음")
        return 0
    print(f"{OK} 카테고리 {args.slug!r} 쿠팡 {len(rows)}개:")
    for r in rows:
        print(f"  #{r['id']:>4} {r['name']}")
    return 0


def cmd_category_coupang_remove(args: argparse.Namespace) -> int:
    """카테고리 쿠팡존에서 상품 링크 해제 (products 행은 보존)."""
    from collector import category_coupang

    conn = db.connect(db.DB_PATH)
    try:
        try:
            n = category_coupang.remove(conn, args.slug, args.product_id)
        except ValueError as e:
            print(f"{FAIL} {e}")
            return 2
    finally:
        conn.close()
    if n == 0:
        print(f"{WARN} 해제할 쿠팡 링크 없음 (카테고리 {args.slug}, product #{args.product_id})")
        return 1
    print(f"{OK} 카테고리 {args.slug!r}에서 쿠팡 product #{args.product_id} 링크 해제")
    return 0


def cmd_build_deploy(args: argparse.Namespace) -> int:
    """현재 운영 DB로 빌드 → build/site·functions/go 커밋 → main push (CI가 honsallim.com 반영).

    카테고리·쿠팡 등 DB 변경의 라이브 반영용 원스톱 (세션 #32). refresh_cycle의 검증된
    빌드+커밋+푸시 로직 재사용(refresh·killswitch 끔). 외부 게시(§2-라) — 호출 자체가 승인.
    ★git_push stub의 'build/site 미커밋' 버그(EVENTS #30) 우회: refresh_cycle은 DEPLOY_PATHS를 commit.
    """
    import datetime

    from deployer import refresh_cycle

    if getattr(args, "dry_run", False):
        changed, txt = refresh_cycle.detect_changes(PROJECT_ROOT)
        print(f"[DRY] 배포 산출물 변경: {'있음' if changed else '없음'}")
        if txt:
            print(txt)
        return 0

    msg = getattr(args, "message", None) or (
        f"[운영 배포 {datetime.date.today().isoformat()}] 카테고리·쿠팡 등 변경 라이브 반영"
    )
    conn = db.connect(db.DB_PATH)
    try:
        res = refresh_cycle.run_refresh_cycle(
            conn,
            project_root=PROJECT_ROOT,
            refresh=False,
            auto_killswitch=False,
            do_build=True,
            do_deploy=True,
            dry_run=False,
            commit_message=msg,
            db_path=db.DB_PATH,
        )
    finally:
        conn.close()
    if res.deployed:
        print(f"{OK} 빌드·배포 완료 (go {res.go_count}개) — CI가 1~2분 후 honsallim.com 반영")
        return 0
    if not res.changed:
        print(f"{WARN} 산출물 변경 없음 — 이미 최신이거나 빌드 결과가 동일")
        return 0
    print(f"{FAIL} 배포 실패: {'; '.join(res.notes) or '알 수 없음'}")
    return 2


# ─── 예약 발행 (세션 #25) — 승인된 큐 자동/수동 발행 + 스케줄러 ──────────


def cmd_publish_queue(args: argparse.Namespace) -> int:
    """승인된 큐에서 N편 발행 (promote → build --full → deploy). 예약 스케줄러 + 수동 발행 공용.

    E7 준수: status='approved'(사람이 1클릭 승인한) draft만 발행 — 자동 '승인'은 하지 않는다.
    기본 dry_run. 라이브(--no-dry-run)는 실제 게시·git push(외부 영향). 메인 체크아웃에서 실행.
    """
    count = args.count if args.count is not None else int(settings.get("publish_per_day", 1) or 1)
    conn = db.connect(db.DB_PATH)
    try:
        rows = conn.execute(
            "SELECT id, working_title FROM drafts WHERE status='approved' "
            "ORDER BY updated_at, id LIMIT ?",
            (count,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        print(f"{WARN} 승인된(발행 대기) 글이 없습니다 — 발행할 항목 없음")
        return 0
    mode = "dry_run" if args.dry_run else "live"
    print(f"{OK} 발행 대상 {len(rows)}편 (상한 {count}, {mode}):")
    for r in rows:
        print(f"     #{r[0]} {r[1] or ''}")
    if args.dry_run:
        print("     [DRY] 실제 promote·build·deploy 없음 — 라이브는 --no-dry-run")
        return 0

    promoted = 0
    for r in rows:
        rc = cmd_promote(argparse.Namespace(draft=r[0], note="예약/수동 발행"))
        if rc == 0:
            promoted += 1
        else:
            print(f"{WARN} draft #{r[0]} promote 실패 (rc={rc}) — 건너뜀")
    if promoted == 0:
        print(f"{FAIL} promote된 글 없음 — 빌드·배포 생략")
        return 1

    # 빌드+배포는 refresh_cycle 재사용 — build/site·functions/go를 add+commit+push 한다.
    # ★EVENTS #30 버그 근본수정: 옛 경로(cmd_build + cmd_deploy)는 git_push가 commit 없이
    #   push만 하는 stub이라 새 글이 CI에 안 가 라이브 미반영(404). refresh_cycle은 DEPLOY_PATHS를
    #   커밋·푸시하므로 스케줄러 무인 발행도 라이브에 안전 반영(§0). cmd_build_deploy와 동일 로직.
    import datetime

    from deployer import refresh_cycle

    msg = f"[publish-queue {datetime.date.today().isoformat()}] 승인 글 {promoted}편 발행·배포"
    conn = db.connect(db.DB_PATH)
    try:
        res = refresh_cycle.run_refresh_cycle(
            conn,
            project_root=PROJECT_ROOT,
            refresh=False,
            auto_killswitch=False,
            do_build=True,
            do_deploy=not args.no_deploy,
            dry_run=False,
            verify_url=settings.get("verify_url"),
            commit_message=msg,
            db_path=db.DB_PATH,
        )
    finally:
        conn.close()

    if not res.built:
        print(f"{FAIL} 빌드 실패: {'; '.join(res.notes) or '알 수 없음'}")
        return 1
    if args.no_deploy:
        print(f"{OK} {promoted}편 게시·빌드 완료 (배포 생략 — --no-deploy)")
        return 0
    if res.deployed:
        print(f"{OK} {promoted}편 발행·배포 완료 (go {res.go_count}개) — CI가 honsallim.com 반영")
        return 0
    if not res.changed:
        print(f"{WARN} {promoted}편 게시했으나 배포 산출물 변경 없음 — 이미 반영됐을 수 있음")
        return 0
    print(f"{FAIL} 배포 실패: {'; '.join(res.notes) or '알 수 없음'}")
    return 2


def _deploy_ns() -> argparse.Namespace:
    """publish/auto-cycle 공용 배포 인자 (git push main → CI가 Cloudflare Pages 반영)."""
    return argparse.Namespace(
        dry_run=False,
        skip_push=False,
        skip_wrangler=True,
        verify_url=settings.get("verify_url"),
        remote="origin",
        branch="main",
        build_dir="build/site",
        project="honsalim",
    )


def cmd_auto_cycle(args: argparse.Namespace) -> int:
    """★무인 자동 사이클 (B-i·세션 #29): auto_mode ON일 때만 — 사후모니터→생성→자동승인→발행.

    auto_mode OFF(기본)면 즉시 중단 — 사람 게이트(E7) 유지. 자동 승인은 fail-closed(적합성 검증
    가능 + featured 적합만). 기본 dry_run. 라이브(--no-dry-run)는 LLM 비용·게시·배포. 메인 체크아웃.
    """
    from writer import article_guardrail
    from writer import auto_approve as aa

    if not settings.get("auto_mode", False):
        print(f"{WARN} auto_mode OFF — 자동 사이클 중단 (설정에서 켜야 동작·사람 게이트 E7 유지)")
        return 0
    count = args.count if args.count is not None else int(settings.get("publish_per_day", 1) or 1)
    live = not args.dry_run
    print(f"{OK} 자동 사이클 ({'live' if live else 'dry_run'}, 상한 {count})")

    # 1. 사후 모니터 — 기존 published 중 문제글 자동 비공개(fail-closed)
    conn = db.connect(db.DB_PATH)
    try:
        mr = article_guardrail.monitor(conn, auto_unpublish=live)
    finally:
        conn.close()
    if mr["failed"]:
        print(
            f"     사후 모니터 — 미달 {len(mr['failed'])}편 · 자동 비공개 {len(mr['unpublished'])}편"
        )

    # 2. 글 생성 N편 — 대기 키워드 우선, 부족하면 winnable 추천에서 자동 보충(★완전 무인·세션 #34).
    #    auto_pick_keyword: pending 있으면 그것(쿠팡 첨부 우선) 재사용, 없으면 seo 씨앗→winnable 추천을
    #    큐에 추가해 반환. 각 생성이 키워드를 generating→drafted/failed로 옮기므로 다음 회차가 다음
    #    키워드를 집는다(중복·무한루프 없음). ★큐가 비어도 멈추지 않는 게 완전 무인의 핵심 —
    #    옛 코드는 pending만 소비해 대기 키워드 0이면 0편 생성(EVENTS #33 갭). DeepSeek 비용은 count 상한.
    if live:
        from writer import keyword_recommender as kr_mod

        channel = str(settings.get("default_channel", "ali") or "ali")
        made = 0
        for _ in range(count):
            conn = db.connect(db.DB_PATH)
            try:
                pick = kr_mod.auto_pick_keyword(conn, channel=channel, live=True)
            finally:
                conn.close()
            if pick is None:
                print("     보충할 키워드 없음(대기·추천 모두 고갈) — 생성 중단")
                break
            print(
                f"     글 생성 — 키워드 #{pick['keyword_id']} {pick['keyword']!r} ({pick['source']})"
            )
            cmd_keyword_generate(
                argparse.Namespace(id=int(pick["keyword_id"]), page_size=20, dry_run=False)
            )
            made += 1
        print(f"     글 생성 {made}편 완료")
    else:
        conn = db.connect(db.DB_PATH)
        try:
            n_pending = int(
                conn.execute(
                    "SELECT COUNT(*) FROM keyword_queue WHERE status='pending'"
                ).fetchone()[0]
            )
        finally:
            conn.close()
        print(f"     [DRY] 대기 키워드 {n_pending}개(+추천 자동 보충) — 생성 생략")

    # 3. 자동 승인 (fail-closed — 적합성 검증 가능 + featured 적합만, 나머지 보류)
    conn = db.connect(db.DB_PATH)
    try:
        ar = aa.auto_approve(
            conn, apply=live, min_published=int(settings.get("auto_approve_min_published", 5) or 5)
        )
    finally:
        conn.close()
    print(f"     자동 승인 {len(ar['approved'])}편 · 보류 {len(ar['held'])}편")
    for h in ar["held"][:5]:
        print(f"       보류 #{h['draft']}: {h['reason']}")

    if not live:
        print("     [DRY] 발행·배포 생략 — 라이브는 --no-dry-run")
        return 0

    # 4. 발행 — 승인된(이번 자동승인 + 기존 대기) 글이 있으면 publish-queue(promote+build+deploy).
    #    발행 대상 없고 비공개만 있으면 재빌드로 반영. ※이번 회차 ar뿐 아니라 DB 전체 approved 기준.
    conn = db.connect(db.DB_PATH)
    try:
        approved_n = int(
            conn.execute("SELECT COUNT(*) FROM drafts WHERE status='approved'").fetchone()[0]
        )
    finally:
        conn.close()
    if approved_n:
        return cmd_publish_queue(
            argparse.Namespace(count=count, dry_run=False, no_deploy=args.no_deploy)
        )
    if mr["unpublished"] and not args.no_deploy:
        print("     발행 대상 없음 — 비공개 반영 위해 재빌드·배포")
        rc = cmd_build(
            argparse.Namespace(manifest=None, full=True, preview=False, save_empty=False)
        )
        return rc if rc != 0 else cmd_deploy(_deploy_ns())
    print("     발행/비공개 변경 없음 — 빌드 생략")
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    """예약 발행 작업 관리 (Windows schtasks): show | set [--time HH:MM] | off.

    기본 OFF(#24 수동전환 취지) — 주인이 명시적으로 set 할 때만 등록.
    """
    from deployer import scheduler

    if args.schedule_action == "show":
        t = scheduler.query_scheduled_time()
        if t:
            mode = (
                "완전 무인(생성·승인·발행)"
                if settings.get("auto_mode", False)
                else "발행(승인 글만)"
            )
            print(f"{OK} 예약 {mode} 등록됨 — 매일 {t[0]:02d}:{t[1]:02d}")
        else:
            print(f"{WARN} 예약 미등록 (수동 발행만)")
        return 0
    if args.schedule_action == "off":
        ok, msg = scheduler.delete_task()
        print(f"{OK if ok else FAIL} {msg}")
        return 0 if ok else 1
    # set — auto_mode ON이면 완전 무인(auto-cycle), OFF면 발행 전용(publish-queue) 래퍼 등록(세션 #34)
    time_hhmm = args.time or str(settings.get("schedule_time", "11:00"))
    full_auto = bool(settings.get("auto_mode", False))
    ok, msg = scheduler.create_or_update(time_hhmm, full_auto=full_auto)
    print(f"{OK if ok else FAIL} {msg}")
    if ok:
        cfg = settings.load()
        cfg["schedule_time"] = time_hhmm
        settings.save(cfg)
    return 0 if ok else 1


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

    # BACKEND §9 [확정] — promote: approved draft → articles + article_products → published
    p_promote = sub.add_parser(
        "promote",
        help="approved draft 게시 (articles + article_products INSERT, status=published)",
    )
    p_promote.add_argument("--draft", type=int, required=True, help="draft id")
    p_promote.add_argument(
        "--note", type=str, default=None, help="게시 메모 (articles.user_approved_note)"
    )
    p_promote.set_defaults(func=cmd_promote)

    p_collect = sub.add_parser("collect", help="scenario slug → drafts 생성 (status=collected)")
    p_collect.add_argument("scenario_slug", type=str, help="scenarios.slug")
    p_collect.set_defaults(func=cmd_collect)

    # DECISIONS D9 [확정] — collect-products: AliExpress product.query → products 적재
    p_collect_products = sub.add_parser(
        "collect-products",
        help="AliExpress product.query → products 테이블 적재 (기본 dry_run)",
    )
    p_cp_src = p_collect_products.add_mutually_exclusive_group(required=True)
    p_cp_src.add_argument(
        "--keywords", type=str, default=None, help="단일 영어 검색어 (예: 'desk lamp')"
    )
    p_cp_src.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="시나리오 slug — search_keywords.yml의 영어 검색어 목록 전체 수집",
    )
    p_collect_products.add_argument("--page-no", type=int, default=1, help="페이지 번호 (기본 1)")
    p_collect_products.add_argument(
        "--page-size", type=int, default=20, help="페이지당 상품 수 (기본 20, 최대 50 — FAQ 4.2)"
    )
    p_collect_products.add_argument(
        "--min-price",
        type=int,
        default=None,
        help="가격 하한 (KRW) — --keywords 단일 검색 시 (--scenario는 YAML 밴드 사용)",
    )
    p_collect_products.add_argument(
        "--max-price", type=int, default=None, help="가격 상한 (KRW) — --keywords 단일 검색 시"
    )
    p_collect_products.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 API 호출 + DB 적재 (쿼터 소모·외부 영향 — 명시 승인 후)",
    )
    p_collect_products.set_defaults(func=cmd_collect_products, dry_run=True)

    # 카테고리 단위 수집 (세션 #17)
    p_collect_cat = sub.add_parser(
        "collect-category", help="카테고리 제품 수집·정제·2티어 연결 (기본 dry_run)"
    )
    p_collect_cat.add_argument("slug", type=str, help="categories.slug (예: office-chair, desk)")
    p_collect_cat.add_argument("--page-size", type=int, default=30, help="티어당 조회 수 (기본 30)")
    p_collect_cat.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 API 호출 + DB 연결 (쿼터 소모 — 명시 승인 후)",
    )
    p_collect_cat.set_defaults(func=cmd_collect_category, dry_run=True)

    # 카테고리 콘텐츠·이미지 생성 (세션 #17)
    # 세션 #35 ①③ — 신규 카테고리 자동 프로비저닝
    p_suggest = sub.add_parser(
        "suggest-categories", help="신규 카테고리 후보 제안 (LLM·기존 제외) (기본 dry_run)"
    )
    p_suggest.add_argument("--count", type=int, default=5, help="후보 수 (기본 5)")
    p_suggest.add_argument(
        "--no-dry-run", dest="dry_run", action="store_false", help="실제 LLM 호출 (비용)"
    )
    p_suggest.set_defaults(func=cmd_suggest_categories, dry_run=True)

    p_prov = sub.add_parser(
        "provision-category",
        help="신규 카테고리 자동 프로비저닝 — 설정생성→수집(vision)→빌드(draft) (기본 dry_run)",
    )
    p_prov.add_argument("label", type=str, help="한글 카테고리명 (예: 가습기)")
    p_prov.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 실행 (LLM+알리+Imagen 비용·DB 쓰기 — 명시 승인 후)",
    )
    p_prov.add_argument("--no-build", action="store_true", help="수집까지만 (페이지 빌드 생략)")
    p_prov.set_defaults(func=cmd_provision_category, dry_run=True)

    p_build_cat = sub.add_parser(
        "build-category", help="카테고리 가이드·추천6선·FAQ·비교표·개념이미지 생성 (기본 dry_run)"
    )
    p_build_cat.add_argument("slug", type=str, help="categories.slug")
    p_build_cat.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 생성 (Claude 글 + Imagen 이미지 비용 — 명시 승인 후)",
    )
    p_build_cat.add_argument("--no-image", action="store_true", help="개념 이미지 생성 생략 (글만)")
    p_build_cat.add_argument(
        "--max-attempts", type=int, default=2, help="SEO+게이트 통과 재생성 상한 (기본 2)"
    )
    p_build_cat.set_defaults(func=cmd_build_category, dry_run=True)

    # 수익 카테고리 순차 자동 등록 (세션 #21) — 리스트(또는 --all)를 collect→build 반복, draft 저장(E7)
    p_register = sub.add_parser(
        "register-categories",
        help="수익 카테고리 리스트 순차 자동 등록(collect→build, draft 저장·E7)",
    )
    p_register.add_argument("slugs", nargs="*", help="categories.slug 목록 (없으면 --all)")
    p_register.add_argument("--all", action="store_true", help="category_sources.yml 전체 등록")
    p_register.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 수집(쿼터)+생성(비용) — 명시 승인 후",
    )
    p_register.add_argument("--skip-collect", action="store_true", help="수집 생략, 생성만")
    p_register.add_argument("--no-image", action="store_true", help="개념 이미지 생성 생략")
    p_register.add_argument("--page-size", type=int, default=30, help="티어당 조회 수 (기본 30)")
    p_register.add_argument(
        "--max-attempts", type=int, default=2, help="게이트 재생성 상한 (기본 2)"
    )
    p_register.add_argument(
        "--auto-publish",
        action="store_true",
        help="생성 후 가드레일 통과 시 자동 공개(E7→가드레일·세션 #22). 보류는 draft 유지",
    )
    p_register.set_defaults(func=cmd_register_categories, dry_run=True)

    # 카테고리 공개 승인 게이트 (세션 #18) — AI 자동승인 금지(§2-마·E7), 사용자 1클릭만 공개
    p_approve_cat = sub.add_parser(
        "approve-category", help="draft 카테고리 → published (사용자 1클릭 승인·공개)"
    )
    p_approve_cat.add_argument("slug", type=str, help="categories.slug")
    p_approve_cat.set_defaults(func=cmd_approve_category)

    p_unapprove_cat = sub.add_parser(
        "unapprove-category", help="published 카테고리 → draft (공개 취소·비공개·킬스위치)"
    )
    p_unapprove_cat.add_argument("slug", type=str, help="categories.slug")
    p_unapprove_cat.set_defaults(func=cmd_unapprove_category)

    # 발행후 안전망 (세션 #29) — 발행된 글을 라이브에서 내리기/되돌리기 (B 자동발행 대비)
    p_unpub_art = sub.add_parser(
        "unpublish-article", help="published 글 → unpublished (라이브 비공개·발행후 안전망)"
    )
    p_unpub_art.add_argument("slug", type=str, help="articles.slug")
    p_unpub_art.add_argument("--note", type=str, default=None, help="비공개 사유")
    p_unpub_art.set_defaults(func=cmd_unpublish_article)

    p_repub_art = sub.add_parser(
        "republish-article", help="unpublished/archived 글 → published (재공개)"
    )
    p_repub_art.add_argument("slug", type=str, help="articles.slug")
    p_repub_art.set_defaults(func=cmd_republish_article)

    p_mon_art = sub.add_parser(
        "monitor-articles",
        help="published 글 사후 점검(무결성·적합성). --auto-unpublish로 미달 글 자동 비공개",
    )
    p_mon_art.add_argument(
        "--auto-unpublish", action="store_true", help="미달 글 자동 비공개(fail-closed)"
    )
    p_mon_art.set_defaults(func=cmd_monitor_articles)

    # 자동 게시 가드레일 (세션 #22) — E7(사람 승인)을 fail-closed 가드레일로 대체
    p_auto_pub = sub.add_parser(
        "auto-publish",
        help="가드레일 통과 카테고리 자동 공개(보류는 draft 유지·세션 #22). 기본 dry_run",
    )
    p_auto_pub.add_argument("slugs", nargs="*", help="categories.slug 목록 (없으면 --all)")
    p_auto_pub.add_argument("--all", action="store_true", help="글 있는 draft 전체 대상")
    p_auto_pub.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 공개 + LLM 의미 검수(비용 소액) — 명시 승인 후",
    )
    p_auto_pub.add_argument(
        "--no-llm", action="store_true", help="LLM 의미검수 생략(휴리스틱만 — 오프라인·테스트)"
    )
    p_auto_pub.set_defaults(func=cmd_auto_publish, dry_run=True)

    # 카테고리 현황 다이제스트 + 사후 감시 (세션 #22) — 무인 오버사이트
    p_cat_status = sub.add_parser(
        "category-status",
        help="카테고리 게시 현황 + (--monitor) published 재검수 킬스위치 후보 표시",
    )
    p_cat_status.add_argument(
        "--monitor",
        action="store_true",
        help="published 카테고리 휴리스틱 재검수 — 지금 가드레일 미달 건 표시",
    )
    p_cat_status.set_defaults(func=cmd_category_status)

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
    p_deploy.add_argument(
        "--build-dir",
        type=str,
        default="build/site",
        help="wrangler 배포 디렉토리 (renderer 산출물 = build/site)",
    )
    p_deploy.add_argument(
        "--project", type=str, default="honsalim", help="Cloudflare Pages 프로젝트 이름"
    )
    p_deploy.set_defaults(func=cmd_deploy, dry_run=True)

    # DB §11-2 [확정] — sync-slugmap: published 상품 → D1 slug_map UPSERT (/go/ 라우팅)
    p_sync = sub.add_parser(
        "sync-slugmap",
        help="published 상품 → D1 slug_map UPSERT (/go/ 게이트웨이 라우팅, 기본 dry_run)",
    )
    p_sync.add_argument(
        "--database", type=str, default="honsalim-clicks", help="D1 database 이름/ID"
    )
    p_sync.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 wrangler d1 execute (외부 D1 쓰기 — 명시 승인 후)",
    )
    p_sync.set_defaults(func=cmd_sync_slugmap, dry_run=True)

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
        help="공개 빌드 → build/site (published만 — 배포 대상)",
    )
    p_build.add_argument(
        "--preview",
        action="store_true",
        help="미리보기 빌드 → build/preview (draft 포함·검토용, §2-마)",
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

    # 무인 일일 새로고침·자가복원·빌드·변경분 배포 사이클 (A안·세션 #23, 윈도우 스케줄러용)
    p_refresh = sub.add_parser(
        "refresh-cycle",
        help="무인 일일 새로고침·자가복원·빌드·변경분 배포 (A안·세션 #23, 기본 dry_run)",
    )
    p_refresh.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 사이클 (알리 수집·DB 쓰기·빌드·git push — 명시 승인/스케줄러)",
    )
    p_refresh.add_argument("--no-refresh", action="store_true", help="새로고침(재수집) 생략")
    p_refresh.add_argument(
        "--no-killswitch", action="store_true", help="가드레일 미달 자동 비공개 생략(보고만)"
    )
    p_refresh.add_argument("--no-build", action="store_true", help="빌드 생략")
    p_refresh.add_argument("--no-deploy", action="store_true", help="배포 생략(빌드까지만)")
    p_refresh.add_argument(
        "--page-size", type=int, default=30, help="새로고침 티어당 조회 수 (기본 30)"
    )
    p_refresh.add_argument(
        "--verify-url", type=str, default=None, help="배포 후 HEAD 검증 URL (선택)"
    )
    p_refresh.set_defaults(func=cmd_refresh_cycle, dry_run=True)

    # ─── 키워드 발행 큐 (세션 #25) — 운영 대시보드 ───
    p_kw_add = sub.add_parser("keyword-add", help="키워드를 발행 큐에 추가 (status=pending)")
    p_kw_add.add_argument("keyword", type=str, help="키워드/주제 (예: '자취생 전자레인지 추천')")
    p_kw_add.add_argument(
        "--channel", choices=["ali", "coupang", "both"], default="ali", help="제휴 채널"
    )
    p_kw_add.add_argument("--slug", type=str, default=None, help="식별 slug (기본 자동 생성)")
    p_kw_add.add_argument("--budget-min", type=int, default=None, help="예산 하한 KRW")
    p_kw_add.add_argument("--budget-max", type=int, default=None, help="예산 상한 KRW")
    p_kw_add.add_argument("--note", type=str, default=None, help="운영자 메모")
    p_kw_add.add_argument("--score", type=float, default=0.0, help="정렬 우선순위 점수")
    p_kw_add.set_defaults(func=cmd_keyword_add)

    p_kw_gen = sub.add_parser(
        "keyword-generate",
        help="키워드 → 글 생성(시나리오 파생·상품·enrich·validate). 기본 dry_run",
    )
    p_kw_gen.add_argument("--id", type=int, required=True, help="keyword_queue id")
    p_kw_gen.add_argument("--page-size", type=int, default=20, help="ali 수집 페이지 크기")
    p_kw_gen.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 수집·LLM 본문 생성(비용·쿼터) — 명시 승인 후",
    )
    p_kw_gen.set_defaults(func=cmd_keyword_generate, dry_run=True)

    p_kw_list = sub.add_parser("keyword-list", help="키워드 큐 목록 (status 필터 선택)")
    p_kw_list.add_argument("--status", type=str, default=None, help="status 필터 (예: pending)")
    p_kw_list.set_defaults(func=cmd_keyword_list)

    p_kw_del = sub.add_parser(
        "keyword-delete", help="키워드 삭제 (연결 미발행 draft 동반·발행글 차단)"
    )
    p_kw_del.add_argument("id", type=int, help="삭제할 키워드 id")
    p_kw_del.set_defaults(func=cmd_keyword_delete)

    p_kw_rec = sub.add_parser(
        "keyword-recommend",
        help="추천 키워드 생성 (네이버 연관검색어→필터→검색량순). --add-top로 1순위 큐 추가",
    )
    p_kw_rec.add_argument(
        "--seed", type=str, default=None, help="임의 주제 씨앗 (미지정 시 SEO 카테고리 씨앗 전부)"
    )
    p_kw_rec.add_argument("--limit", type=int, default=20, help="추천 개수 상한")
    p_kw_rec.add_argument(
        "--channel", choices=["ali", "coupang", "both"], default="ali", help="--add-top 시 채널"
    )
    p_kw_rec.add_argument(
        "--no-live", action="store_true", help="네이버 미조회 (캐시 보조키워드만·네트워크 0)"
    )
    p_kw_rec.add_argument(
        "--add-top", action="store_true", help="1순위를 큐에 추가 (status=pending)"
    )
    p_kw_rec.set_defaults(func=cmd_keyword_recommend)

    p_reject = sub.add_parser("reject", help="draft → rejected (반려)")
    p_reject.add_argument("--draft", type=int, required=True, help="draft id")
    p_reject.add_argument("--note", type=str, default=None, help="반려 사유")
    p_reject.set_defaults(func=cmd_reject)

    p_cp_add = sub.add_parser(
        "coupang-add",
        help="쿠팡 수동 상품을 키워드 미리선택에 추가 (공식 배너→이미지·링크·상품명 자동)",
    )
    p_cp_add.add_argument("--keyword-id", type=int, required=True, help="keyword_queue id")
    p_cp_add.add_argument(
        "--banner",
        type=str,
        default=None,
        help="쿠팡 공식 배너 HTML(<a><img>) — 이미지·링크·상품명 자동 추출",
    )
    p_cp_add.add_argument("--name", type=str, default="", help="상품명 (배너 alt 있으면 생략 가능)")
    p_cp_add.add_argument(
        "--url", type=str, default="", help="쿠팡 파트너스 딥링크 (배너 href 있으면 생략 가능)"
    )
    p_cp_add.add_argument("--price", type=int, default=None, help="가격 KRW (선택)")
    p_cp_add.add_argument("--widget", type=str, default=None, help="공식 위젯 HTML (선택·보관)")
    p_cp_add.set_defaults(func=cmd_coupang_add)

    p_ccp_add = sub.add_parser(
        "category-coupang-add",
        help="카테고리 쿠팡 운영자추천 zone에 쿠팡 배너 상품 추가 (여러 개 가능·세션 #32)",
    )
    p_ccp_add.add_argument("slug", type=str, help="카테고리 slug (예: office-chair)")
    p_ccp_add.add_argument(
        "--banner", type=str, default=None, help="쿠팡 공식 배너 HTML(<a><img>) — 여러 개 가능"
    )
    p_ccp_add.set_defaults(func=cmd_category_coupang_add)

    p_ccp_list = sub.add_parser("category-coupang-list", help="카테고리 쿠팡존 상품 목록")
    p_ccp_list.add_argument("slug", type=str, help="카테고리 slug")
    p_ccp_list.set_defaults(func=cmd_category_coupang_list)

    p_ccp_rm = sub.add_parser("category-coupang-remove", help="카테고리 쿠팡존에서 상품 링크 해제")
    p_ccp_rm.add_argument("slug", type=str, help="카테고리 slug")
    p_ccp_rm.add_argument("product_id", type=int, help="해제할 product id")
    p_ccp_rm.set_defaults(func=cmd_category_coupang_remove)

    p_bd = sub.add_parser(
        "build-deploy",
        help="현재 운영 DB로 빌드 → build/site·functions/go 커밋 → main push (CI 배포·세션 #32)",
    )
    p_bd.add_argument("--message", type=str, default=None, help="커밋 메시지 (기본 자동)")
    p_bd.add_argument("--dry-run", action="store_true", help="변경 감지만 (배포 안 함)")
    p_bd.set_defaults(func=cmd_build_deploy)

    # ─── 예약 발행 (세션 #25) ───
    p_pubq = sub.add_parser(
        "publish-queue",
        help="승인된 큐에서 N편 발행(promote→build→deploy). 예약/수동 공용. 기본 dry_run",
    )
    p_pubq.add_argument(
        "--count", type=int, default=None, help="발행 편수 (기본 config publish_per_day)"
    )
    p_pubq.add_argument("--no-deploy", action="store_true", help="배포(git push) 생략 — 빌드까지만")
    p_pubq.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 게시·빌드·배포(외부 영향) — 명시 승인/스케줄러",
    )
    p_pubq.set_defaults(func=cmd_publish_queue, dry_run=True)

    p_autocyc = sub.add_parser(
        "auto-cycle",
        help="★무인 자동 사이클(B-i): 사후모니터→생성→자동승인→발행. auto_mode ON일 때만. 기본 dry_run",
    )
    p_autocyc.add_argument(
        "--count", type=int, default=None, help="생성·발행 상한 (기본 config publish_per_day)"
    )
    p_autocyc.add_argument("--no-deploy", action="store_true", help="배포 생략 — 빌드까지만")
    p_autocyc.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="실제 LLM·게시·배포(외부 영향) — 스케줄러/명시 승인",
    )
    p_autocyc.set_defaults(func=cmd_auto_cycle, dry_run=True)

    p_sched = sub.add_parser("schedule", help="예약 발행 작업 관리 (Windows schtasks)")
    p_sched.add_argument(
        "schedule_action", choices=["show", "set", "off"], help="show: 현황 · set: 등록 · off: 해제"
    )
    p_sched.add_argument(
        "--time", type=str, default=None, help="set 시각 HH:MM (기본 config schedule_time)"
    )
    p_sched.set_defaults(func=cmd_schedule)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
