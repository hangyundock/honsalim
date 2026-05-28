"""tracker.d1_aggregator — Cloudflare D1 clicks → 일별 집계 → SQLite.

출처: BACKEND §2-8 + §4-1·§4-3 + DB §11 [확정].

D1 API 의존 — 실제 호출은 dry_run=False + 사용자 명시 승인 후.
현재 stub은 인터페이스와 plan 출력만. wrangler d1 execute 명령 빌드 + 결과 형식 정의.
"""

# ruff: noqa: S603
# 사유: subprocess wrangler 호출 — 인자 list, shell injection 위험 없음.

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AggregateResult:
    """일별 집계 결과."""

    dry_run: bool
    date: str
    command: list[str]
    rows_inserted: int = 0
    stdout: str = ""
    stderr: str = ""
    error: str | None = None


@dataclass
class ExportResult:
    """SQLite 동기화 결과."""

    dry_run: bool
    articles_updated: int = 0
    aggregates_loaded: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def _validate_date(date: str) -> None:
    """ISO 8601 날짜 형식 검증 (YYYY-MM-DD)."""
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise ValueError(f"date 형식 오류 (YYYY-MM-DD 필요): {date!r}")
    try:
        int(date[:4])
        int(date[5:7])
        int(date[8:10])
    except ValueError as e:
        raise ValueError(f"date 숫자 파싱 실패: {date!r}") from e


def aggregate(
    date: str,
    *,
    database_id: str = "honsalim-clicks",
    cwd: str | Path = ".",
    dry_run: bool = True,
    timeout: int = 60,
) -> AggregateResult:
    """D1 clicks 테이블에서 일별 집계 → D1 clicks_daily INSERT.

    인자:
        date: 'YYYY-MM-DD' (집계 대상 날짜, KST)
        database_id: wrangler d1 database 이름 또는 ID
        cwd: 작업 디렉토리 (wrangler.toml 위치)
        dry_run: True면 명령 빌드만, False면 wrangler d1 execute 호출
        timeout: subprocess 타임아웃

    반환: AggregateResult.

    Raises:
        ValueError: date 형식 오류 또는 database_id 빈 값
    """
    _validate_date(date)
    if not database_id:
        raise ValueError("database_id 빈 값")

    # D1 §11 — clicks_daily UPSERT 패턴
    sql = (
        "INSERT INTO clicks_daily (date, slug, clicks) "
        "SELECT ?1 AS date, slug, COUNT(*) AS clicks "
        "FROM clicks WHERE substr(timestamp, 1, 10) = ?1 GROUP BY slug "
        "ON CONFLICT(date, slug) DO UPDATE SET clicks = excluded.clicks"
    )
    cmd = [
        "wrangler",
        "d1",
        "execute",
        database_id,
        "--remote",
        "--command",
        sql,
    ]
    cwd_str = str(Path(cwd).resolve())

    if dry_run:
        return AggregateResult(
            dry_run=True,
            date=date,
            command=cmd,
            stdout=f"[DRY] would run: wrangler d1 execute {database_id} (date={date})",
        )

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd_str,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return AggregateResult(
            dry_run=False,
            date=date,
            command=cmd,
            error=f"{type(e).__name__}: {e}",
        )

    return AggregateResult(
        dry_run=False,
        date=date,
        command=cmd,
        stdout=proc.stdout,
        stderr=proc.stderr,
        rows_inserted=-1,  # wrangler 출력 파싱은 Phase 2 후반
    )


def export_to_sqlite(
    aggregates: list[dict[str, Any]] | None = None,
    *,
    db_path: str | Path | None = None,
    dry_run: bool = True,
) -> ExportResult:
    """D1 집계 결과 → SQLite articles.view_count_cached UPDATE.

    인자:
        aggregates: [{slug, clicks}, ...]. None이면 dry_run plan만 반환.
        db_path: SQLite 경로. None이면 common.db.DB_PATH 사용.
        dry_run: True면 UPDATE 안 함 (plan 반환)

    반환: ExportResult.

    Raises:
        ValueError: aggregates 형식 오류
    """
    aggregates = aggregates or []
    for entry in aggregates:
        if "slug" not in entry or "clicks" not in entry:
            raise ValueError(f"aggregate 필수 키 누락 (slug·clicks): {entry}")

    if dry_run:
        return ExportResult(
            dry_run=True,
            aggregates_loaded=list(aggregates),
            articles_updated=len(aggregates),
        )

    if db_path is None:
        from common.db import DB_PATH

        db_path = DB_PATH

    conn = sqlite3.connect(str(db_path))
    try:
        updated = 0
        for entry in aggregates:
            cur = conn.execute(
                "UPDATE articles SET view_count_cached = ? WHERE slug = ?",
                (int(entry["clicks"]), str(entry["slug"])),
            )
            updated += cur.rowcount
        conn.commit()
        return ExportResult(
            dry_run=False,
            aggregates_loaded=list(aggregates),
            articles_updated=updated,
        )
    finally:
        conn.close()
