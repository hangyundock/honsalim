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

from common import config, db, size_caps  # noqa: E402

PROJECT_ROOT = _THIS_DIR.parent

# BACKEND §10-1 1차 의존성 (Phase 1·2 운영 필수)
REQUIRED_DEPS = ("anthropic", "jinja2", "requests", "dotenv", "yaml", "markdown", "PIL")

# 시각적 출력
OK = "[OK]"
WARN = "[WARN]"
FAIL = "[FAIL]"

# 사이트 origin (builder.renderer.SITE_ORIGIN과 일치 — JSON-LD URL 생성용)
SITE_ORIGIN = "https://honsalim.com"


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
        ("collector.category_collect", "collect_category"),
        ("collector.keyword_research", "research_keywords"),
        ("collector.keyword_research", "build_entry"),
        ("collector.seo_keywords", "gate_config"),
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
            SELECT s.slug, s.title_ko, s.season_peak, s.description,
                   p.slug, p.title_ko, p.description, p.age_range, d.raw_payload
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
        req = GenerateRequest(scenario=scenario_dict, persona=persona_dict, products=products)

        import os

        api_key = None
        if not args.dry_run:
            config.load_secrets()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        client = ClaudeClient(api_key=api_key)
        result = client.generate_article(req, dry_run=args.dry_run)

        from writer import article_writer, state_machine

        # 라이브: 응답을 META-JSON + BODY-MARKDOWN으로 분리해 본문을 영구 저장.
        # 분리 실패 시 본문 미저장·상태 전이 없음(돈만 쓰고 stub 저장 방지).
        if not args.dry_run:
            from enricher.claude_client import (
                ArticleResponseError,
                is_truncated,
                split_article_response,
            )

            if not result.response_text:
                print(f"{FAIL} 라이브 응답 본문 비어있음 — 저장 안 함")
                return 3
            if is_truncated(result):
                print(
                    f"{FAIL} 응답이 max_tokens({client.max_tokens})에서 잘림 — "
                    "본문 미완성. max_tokens 상향 또는 본문 축소 필요 (저장 안 함)"
                )
                return 3
            try:
                meta, body_md = split_article_response(result.response_text)
            except ArticleResponseError as e:
                print(f"{FAIL} 응답 형식 오류(META-JSON/BODY 분리 실패): {e}")
                return 3
            # 모델이 선언한 featured 상품(deeplink_slug)만 검증·게시 대상으로 — 후보 풀 전체가
            # 아니라 글이 실제 추천한 상품만 truth 가격 검증을 받아야 정확 (id는 식별용).
            declared = meta.get("featured_products")
            slug_set = {str(s).strip() for s in declared} if isinstance(declared, list) else set()
            featured = [
                {**c, "id": c.get("source_product_id")}
                for c in products
                if c.get("deeplink_slug") in slug_set
            ]
            if products and not featured:
                print(
                    f"{WARN} featured_products 미선언/미매칭 — truth 가격 검증 대상 0개 "
                    "(모델이 추천 상품 ID를 안 냈거나 ID 불일치)"
                )

            # disclosure는 featured 상품의 실제 제휴처를 반영 (공정위 정확성). source 없으면
            # deeplink_slug 접두어(ali-)로 추정. featured 비면 전체 후보로 fallback.
            def _affiliate_of(c: dict[str, Any]) -> str | None:
                if c.get("source"):
                    return str(c["source"]).lower()
                slug = str(c.get("deeplink_slug") or "")
                return "aliexpress" if slug.startswith("ali-") else None

            affiliates = {a for c in (featured or products) if (a := _affiliate_of(c))}
            # POLICY §2-2/§2-3 disclosure 자동 삽입 (모델 미작성 — 시스템 책임). 멱등 + 제휴처 인지형.
            body_md = article_writer.apply_disclosure(body_md, sources=affiliates)
            enriched_payload: dict[str, Any] = {
                "body_md": body_md,
                "title": meta.get("title"),
                "summary": meta.get("summary"),
                "meta_description": meta.get("meta_description"),
                "meta_keywords": meta.get("meta_keywords"),
                "faqs": meta.get("faqs", []),
                "products": featured,
                "candidate_count": len(products),
                "usage": result.usage,
                "model": client.model,
            }
            # schema 게이트용 Article JSON-LD. image_url·published_at은 임시값
            # (실제 대표 이미지는 Phase 3 AI 생성, 실제 발행일은 promote 시 확정).
            from datetime import date

            from builder import build_article_jsonld

            try:
                enriched_payload["schema_jsonld"] = build_article_jsonld(
                    meta=meta,
                    scenario={"slug": scenario_dict["slug"]},
                    site_base_url=SITE_ORIGIN,
                    image_url=f"{SITE_ORIGIN}/static/img/og-default.png",
                    published_at=date.today().isoformat(),
                )
            except ValueError as e:
                print(
                    f"{WARN} schema_jsonld 생성 실패(메타 필드 부족): {e} — validate schema 게이트 막힘"
                )
        else:
            enriched_payload = {
                "dry_run": True,
                "user_prompt_preview": result.user_prompt[:500],
                "system_blocks_count": len(result.system_blocks),
                "products_count": len(products),
            }

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


def cmd_promote(args: argparse.Namespace) -> int:
    """approved draft → articles + article_products → published (게시 경로 배선).

    검증·승인된 enriched_payload(본문·메타)로 article_fields를 조립한다:
    - body_html : markdown → HTML 변환 (검증된 body_md 그대로 — content_hash 무결)
    - slug      : scenario.slug (충돌 시 -2 …)
    - content_hash · disclosure_first · truth/approved 타임스탬프
    그 후 promote_to_article + link_article_products(featured → /go/ 제휴 링크 소스).
    """
    from datetime import datetime, timezone

    import markdown as md_lib  # BACKEND §10-1 1차 의존성

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

        # 검증된 body_md를 변형 없이 HTML 변환 (본문 무결성 — validated 본문 = published 본문)
        body_html = md_lib.markdown(body_md, extensions=["extra", "sane_lists"])

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
        print(f"     개념 이미지: {res['concept_image']}")
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

    # 카테고리 공개 승인 게이트 (세션 #18) — AI 자동승인 금지(§2-마·E7), 사용자 1클릭만 공개
    p_approve_cat = sub.add_parser(
        "approve-category", help="draft 카테고리 → published (사용자 1클릭 승인·공개)"
    )
    p_approve_cat.add_argument("slug", type=str, help="categories.slug")
    p_approve_cat.set_defaults(func=cmd_approve_category)

    p_unapprove_cat = sub.add_parser(
        "unapprove-category", help="published 카테고리 → draft (공개 취소·비공개)"
    )
    p_unapprove_cat.add_argument("slug", type=str, help="categories.slug")
    p_unapprove_cat.set_defaults(func=cmd_unapprove_category)

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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
