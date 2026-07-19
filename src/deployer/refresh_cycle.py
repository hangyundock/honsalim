# 사유: subprocess git 호출은 인자 list로만 사용 — shell injection 위험 없음.
#       git은 PATH 검색(deployer 책임). 경로 인자는 코드 상수(build/site·functions/go)만.
"""deployer.refresh_cycle — 무인 일일 새로고침·자가복원·배포 사이클 (세션 #23, A안).

CLAUDE.md §0(무인·자가복원·안전 우선) + DECISIONS C6·C7(윈도우 스케줄러 자동 배포) 구현.
공개(published) 카테고리를 매일 새로고침하고, 가드레일 자가복원, 재빌드, 변경분만 자동 배포한다.

단계:
  1. refresh   : published 각 카테고리 collect_category(가격·판매량 갱신·비관련 옛 추천 prune).
                 한 카테고리 실패가 다음을 막지 않는다(실패 격리·무인 안전).
  2. self-heal : monitor(휴리스틱·무비용)로 '지금 가드레일 미달' published 검출 →
                 auto_killswitch면 자동 unapprove(fail-closed·미탐<오탐). 보고만도 선택 가능.
  3. build     : render_site(published만) + generate_go_function. 로컬·무비용.
  4. deploy    : build/site·functions/go 변경 시에만 commit + push origin main → CI 배포.
                 변경 없으면 배포 스킵(빈 배포 방지).

dry_run=True 기본 — 외부 영향(알리 호출·DB 쓰기·git push) 없이 현황·판정만(monitor는 read-only).
실제 사이클은 dry_run=False. LLM 미사용(refresh=수집·monitor=휴리스틱·build=렌더) → 일일 비용 ~$0.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from collector import category_collect
from common.proc import run_text
from deployer.git_push import git_push
from deployer.verify import verify_deploy
from writer import auto_publish, category_state

# CI(build.yml)가 검증·배포하는 산출물 — 루트 기준 상대 경로. build/site(정적)·functions/go(/go/ 함수).
DEPLOY_PATHS: tuple[str, ...] = ("build/site", "functions/go")


@dataclass
class RefreshOutcome:
    """카테고리 1개 새로고침 결과."""

    slug: str
    ok: bool
    received: int = 0
    linked: int = 0
    removed_stale: int = 0
    error: str | None = None


@dataclass
class CycleResult:
    """사이클 전체 결과 — 무인 로그·다이제스트용."""

    dry_run: bool
    published: list[str] = field(default_factory=list)
    refreshed: list[RefreshOutcome] = field(default_factory=list)
    flagged: list[dict[str, Any]] = field(default_factory=list)  # monitor 미달 published
    killswitched: list[str] = field(default_factory=list)  # 자동 비공개 처리됨
    built: bool = False
    go_count: int = 0
    changed: bool = False
    deployed: bool = False
    push_rc: int | None = None
    verify_status: int | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def refresh_errors(self) -> list[RefreshOutcome]:
        return [r for r in self.refreshed if not r.ok]


def _published_slugs(conn: Any) -> list[str]:
    """공개 카테고리 slug 목록(렌더 순서). categories 테이블 없으면 빈 목록(부분 DB 견고성·§0)."""
    if (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        ).fetchone()
        is None
    ):
        return []
    rows = conn.execute(
        "SELECT slug FROM categories WHERE status = 'published' ORDER BY display_order, id"
    ).fetchall()
    return [r[0] for r in rows]


def _git(args: list[str], *, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """git 서브프로세스 실행(인자 list — shell injection 없음). 호출자가 returncode 점검."""
    return run_text(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def detect_changes(project_root: Path, paths: tuple[str, ...] = DEPLOY_PATHS) -> tuple[bool, str]:
    """배포 산출물에 미커밋 변경이 있는지(git status --porcelain). 반환: (변경여부, 원문)."""
    proc = _git(["status", "--porcelain", "--", *paths], cwd=project_root)
    text = proc.stdout.strip()
    return bool(text), text


def run_refresh_cycle(
    conn: Any,
    *,
    project_root: Path,
    page_size: int = 30,
    refresh: bool = True,
    auto_killswitch: bool = True,
    do_build: bool = True,
    do_deploy: bool = True,
    dry_run: bool = True,
    deploy_remote: str = "origin",
    deploy_branch: str = "main",
    verify_url: str | None = None,
    commit_message: str | None = None,
    db_path: Path | None = None,
) -> CycleResult:
    """무인 새로고침·자가복원·빌드·배포 사이클 1회 실행. 단계별 실패 격리.

    dry_run=True: 외부 영향 없이 현황·판정만(monitor read-only). build/deploy는 not dry_run에서만.
    """
    result = CycleResult(dry_run=dry_run)
    import sqlite3

    if hasattr(conn, "row_factory"):
        conn.row_factory = sqlite3.Row

    # 1) 공개 카테고리 새로고침 (실패 격리)
    result.published = _published_slugs(conn)
    if refresh:
        for slug in result.published:
            try:
                cres = category_collect.collect_category(
                    conn, slug, dry_run=dry_run, page_size=page_size
                )
                result.refreshed.append(
                    RefreshOutcome(
                        slug=slug,
                        ok=True,
                        received=getattr(cres, "received", 0),
                        linked=getattr(cres, "linked", 0),
                        removed_stale=getattr(cres, "removed_stale", 0),
                    )
                )
            except Exception as e:  # 외부 API·데이터 등 — 한 건 실패가 사이클을 막지 않음(§0)
                result.refreshed.append(
                    RefreshOutcome(slug=slug, ok=False, error=f"{type(e).__name__}: {e}")
                )

    # 2) 가드레일 사후 감시 + 자가복원 (휴리스틱·무비용). monitor는 read-only.
    result.flagged = auto_publish.monitor(conn, use_llm=False)
    if auto_killswitch:
        for f in result.flagged:
            slug = f["slug"]
            if dry_run:
                result.notes.append(f"[DRY] 킬스위치 대상(미적용): {slug}")
                continue
            try:
                category_state.unapprove(conn, slug)
                result.killswitched.append(slug)
            except category_state.CategoryStateError as e:
                result.notes.append(f"킬스위치 스킵 {slug}: {e}")

    # 3) 빌드 (render + /go/ 함수). 로컬·무비용. dry_run에선 산출물 미변경(스킵).
    if do_build and not dry_run:
        from builder import go_function, renderer
        from common import db as _db

        try:
            # IndexNow 키 파일(<key>.txt) 생성용 env 보장 — 무인 경로는 secrets 미로드일 수
            # 있다(#45). 실패해도 빌드는 계속(키 파일만 생략·§0).
            from common import config as _config

            _config.load_secrets()
        except Exception:  # noqa: S110 — secrets 없음=키 파일 생략일 뿐, 빌드는 계속(§0)
            pass
        renderer.render_site(
            out_dir=project_root / "build" / "site",
            db_path=db_path or _db.DB_PATH,
            include_drafts=False,
        )
        gres = go_function.generate_go_function(conn, project_root)
        result.built = True
        result.go_count = int(gres.get("count", 0))

    # 4) 변경분만 배포 (commit + push → CI). dry_run에선 변경 감지만(read-only).
    result.changed, _txt = detect_changes(project_root)
    if do_deploy and not dry_run:
        if not result.changed:
            result.notes.append("배포 스킵 — 산출물 변경 없음")
        else:
            msg = (
                commit_message
                or f"[refresh-cycle {date.today().isoformat()}] published 자동 새로고침 배포"
            )
            add = _git(["add", "--", *DEPLOY_PATHS], cwd=project_root)
            if add.returncode != 0:
                result.notes.append(f"git add 실패: {add.stderr.strip()[:200]}")
                return result
            commit = _git(["commit", "-m", msg], cwd=project_root)
            if commit.returncode != 0:
                result.notes.append(
                    f"git commit 실패(변경 없음일 수 있음): {commit.stderr.strip()[:200]}"
                )
                return result
            push = git_push(
                cwd=project_root, remote=deploy_remote, branch=deploy_branch, dry_run=False
            )
            result.push_rc = push.returncode
            result.deployed = push.returncode == 0
            if not result.deployed:
                result.notes.append(
                    f"git push 실패 rc={push.returncode}: {push.stderr.strip()[:200]}"
                )
            else:
                if verify_url:
                    v = verify_deploy(verify_url, dry_run=False)
                    result.verify_status = v.status_code
                # 배포 성공 후 IndexNow 통지(#45) — deployed 확정 '이후'에만, 절대 전파 금지(§0)
                _notify_indexnow(result, project_root)

    return result


def _notify_indexnow(result: CycleResult, project_root: Path) -> None:
    """배포 성공 후속 IndexNow 통지 — 어떤 실패도 사이클 결과를 바꾸지 않는다(§0, 세션 #45).

    통지는 배포(push) 성공이 확정된 뒤에만 호출된다. CI 반영(1~2분)보다 핑이 먼저 나가도
    IndexNow는 즉시 크롤이 아닌 통지 프로토콜이라 무해 [추정]. 실패는 notes에만 기록.
    """
    try:
        from deployer import indexnow

        if not indexnow.indexnow_ready():
            result.notes.append("IndexNow 미설정 — 통지 생략")
            return
        urls = indexnow.sitemap_urls(project_root / "build" / "site")
        if not urls:
            result.notes.append("IndexNow 통지 생략 — sitemap URL 없음")
            return
        ok = indexnow.ping(urls)
        result.notes.append(f"IndexNow 통지 {'성공' if ok else '실패(무시)'} — {len(urls)} URL")
    except Exception as e:  # 어떤 예외도 배포 결과를 오염시키지 않음(§0)
        result.notes.append(f"IndexNow 오류(무시): {type(e).__name__}")


def cycle_report(result: CycleResult, ran_at: str) -> dict[str, Any]:
    """CycleResult → JSON 직렬화 가능한 다이제스트(대시보드 모니터링용). ran_at은 호출자가 주입."""
    return {
        "ran_at": ran_at,
        "dry_run": result.dry_run,
        "published": result.published,
        "refreshed": [
            {
                "slug": r.slug,
                "ok": r.ok,
                "received": r.received,
                "linked": r.linked,
                "removed_stale": r.removed_stale,
                "error": r.error,
            }
            for r in result.refreshed
        ],
        "refresh_ok": sum(1 for r in result.refreshed if r.ok),
        "refresh_fail": len(result.refresh_errors),
        "flagged": result.flagged,
        "killswitched": result.killswitched,
        "built": result.built,
        "go_count": result.go_count,
        "changed": result.changed,
        "deployed": result.deployed,
        "push_rc": result.push_rc,
        "verify_status": result.verify_status,
        "notes": result.notes,
        "had_issue": bool(result.refresh_errors)
        or bool(result.killswitched)
        or bool(result.flagged),
    }


def write_cycle_report(result: CycleResult, path: Path, ran_at: str) -> Path:
    """사이클 다이제스트를 JSON 파일로 저장(무인 모니터링·대시보드 데이터원). 반환: 경로."""
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cycle_report(result, ran_at), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
