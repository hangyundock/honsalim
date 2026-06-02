"""tracker.slug_map — SQLite(published 상품) → Cloudflare D1 slug_map UPSERT.

출처: DB §11-2 빌드 동기 흐름 + BACKEND §5 + go_gateway.js(소비자) [확정].

/go/<slug> 게이트웨이(go_gateway.js)는 D1 slug_map을 조회해 어필리에이트 deep link로
302한다. 이 모듈은 **게시(published)된 글에 연결된 상품**의 deeplink_slug→deeplink_url을
D1 slug_map에 UPSERT한다 — 게시되지 않은 딥링크는 노출하지 않는다(안전).

D1 쓰기는 외부 영향 — dry_run=True 기본(d1_aggregator와 동일). 라이브 실행은
wrangler d1 execute + 사용자 명시 승인 후 (CLAUDE.md §2-라 / DECISIONS H4).
"""

# ruff: noqa: S603, S608
# S603 사유: subprocess wrangler 호출 — 인자 list, shell injection 위험 없음.
# S608 사유: D1는 wrangler d1 execute --command 문자열 SQL만 지원(파라미터 바인딩 불가).
#   값은 모두 _sql_str로 escape — SQLite 문자열 리터럴은 작은따옴표 doubling이 완전한 escape
#   (리터럴 내부에서 특수문자는 작은따옴표뿐). int는 int() 캐스팅. 인젝션 차단됨.

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from common.proc import resolve_argv


@dataclass
class SlugMapSyncResult:
    """slug_map 동기화 결과 (dry_run plan 또는 실행 결과)."""

    dry_run: bool
    entries: list[dict] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    sql: str = ""
    stdout: str = ""
    stderr: str = ""
    error: str | None = None


# published article·카테고리에 연결된 상품 — 게시 안 된 딥링크 비노출 (POLICY §6 / 안전).
# 세션 #21: 메인 콘텐츠가 카테고리 페이지라 category_products(published 카테고리)도 UNION —
# 카테고리 제품 /go/ 클릭이 D1 slug_map 미스로 홈 fallback 되던 문제 근본수정.
_COLLECT_SQL = """
    SELECT DISTINCT p.deeplink_slug AS slug,
           p.deeplink_url,
           p.source,
           p.id AS product_id_local
    FROM products p
    JOIN article_products ap ON ap.product_id = p.id
    JOIN articles a ON a.id = ap.article_id
    WHERE a.status = 'published'
      AND p.deeplink_slug IS NOT NULL
      AND p.deeplink_url IS NOT NULL
    UNION
    SELECT DISTINCT p.deeplink_slug AS slug,
           p.deeplink_url,
           p.source,
           p.id AS product_id_local
    FROM products p
    JOIN category_products cp ON cp.product_id = p.id
    JOIN categories c ON c.id = cp.category_id
    WHERE c.status = 'published'
      AND p.deeplink_slug IS NOT NULL
      AND p.deeplink_url IS NOT NULL
    ORDER BY slug
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sql_str(value: str) -> str:
    """SQL 문자열 리터럴 — single-quote escape (인젝션 차단). 작은따옴표는 두 번."""
    return "'" + str(value).replace("'", "''") + "'"


def collect_slug_map_entries(conn: sqlite3.Connection) -> list[dict]:
    """published article에 연결된 상품 → slug_map 행 목록.

    반환: [{slug, deeplink_url, source, product_id_local}, ...] (slug 오름차순, 중복 제거).
    """
    prev = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(_COLLECT_SQL).fetchall()
    finally:
        conn.row_factory = prev
    return [
        {
            "slug": r["slug"],
            "deeplink_url": r["deeplink_url"],
            "source": r["source"],
            "product_id_local": r["product_id_local"],
        }
        for r in rows
    ]


def build_upsert_sql(entries: list[dict], *, now: str) -> str:
    """slug_map 다중행 UPSERT SQL 생성 (D1 호환, ON CONFLICT(slug)).

    값은 _sql_str로 escape — deep link·slug의 특수문자 인젝션 차단.
    product_id_local이 None이면 NULL.
    """
    rows: list[str] = []
    for e in entries:
        pid = e.get("product_id_local")
        pid_sql = str(int(pid)) if pid is not None else "NULL"
        rows.append(
            f"({_sql_str(e['slug'])}, {_sql_str(e['deeplink_url'])}, "
            f"{_sql_str(e['source'])}, {pid_sql}, {_sql_str(now)})"
        )
    values = ", ".join(rows)
    return (
        "INSERT INTO slug_map (slug, deeplink_url, source, product_id_local, updated_at) "
        f"VALUES {values} "
        "ON CONFLICT(slug) DO UPDATE SET "
        "deeplink_url = excluded.deeplink_url, "
        "source = excluded.source, "
        "product_id_local = excluded.product_id_local, "
        "updated_at = excluded.updated_at;"
    )


def sync_slug_map(
    conn: sqlite3.Connection,
    *,
    database_name: str = "honsalim-clicks",
    cwd: str | Path = ".",
    dry_run: bool = True,
    now: str | None = None,
    timeout: int = 60,
) -> SlugMapSyncResult:
    """published 상품 → D1 slug_map UPSERT (DB §11-2 빌드 동기).

    dry_run=True(기본): SQL·wrangler 명령만 빌드, 외부 호출/D1 쓰기 없음.
    dry_run=False: wrangler d1 execute 호출 (외부 영향 — 사용자 명시 승인 후).

    연결할 상품이 0개면 빈 결과(명령 없음) — 게시 글 없거나 상품 미연결.
    """
    now = now or _now_iso()
    entries = collect_slug_map_entries(conn)
    if not entries:
        return SlugMapSyncResult(
            dry_run=dry_run,
            entries=[],
            stdout="[NOTE] slug_map 대상 0개 — 게시 글의 연결 상품 없음 (동기화 생략)",
        )

    sql = build_upsert_sql(entries, now=now)
    cmd = ["wrangler", "d1", "execute", database_name, "--remote", "--command", sql]

    if dry_run:
        return SlugMapSyncResult(
            dry_run=True,
            entries=entries,
            command=cmd,
            sql=sql,
            stdout=f"[DRY] would upsert {len(entries)} slug → {database_name}",
        )

    try:
        proc = subprocess.run(
            resolve_argv(cmd),
            cwd=str(Path(cwd).resolve()),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return SlugMapSyncResult(
            dry_run=False,
            entries=entries,
            command=cmd,
            sql=sql,
            error=f"{type(e).__name__}: {e}",
        )

    return SlugMapSyncResult(
        dry_run=False,
        entries=entries,
        command=cmd,
        sql=sql,
        stdout=proc.stdout,
        stderr=proc.stderr,
        error=None if proc.returncode == 0 else f"wrangler rc={proc.returncode}",
    )
