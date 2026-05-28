"""tracker.report — 주간·월간 클릭 리포트 (BACKEND §2-8 [확정]).

데이터 집계 함수만 독립 작성. HTML 렌더는 dashboard 디자인 의존이라 placeholder.

함수:
- aggregate_weekly(conn, end_date)   : 최근 7일 클릭 집계
- aggregate_monthly(conn, year_month): 월간 클릭 집계
- top_articles_by_clicks(conn, since): 상위 슬러그 N개
- weekly(conn, end_date, render)     : BACKEND §2-8 진입점 — 집계 + (옵션) HTML 렌더
- render_html_stub(data)             : placeholder (Phase 3 dashboard 디자인 후 jinja2 통합)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any


@dataclass
class ClickAggregate:
    """단일 slug 집계 결과."""

    slug: str
    click_count: int
    unique_ua_count: int


@dataclass
class ReportData:
    """리포트 데이터 (HTML 렌더 입력)."""

    period: str  # "weekly" / "monthly"
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    total_clicks: int = 0
    total_unique_ua: int = 0
    by_slug: list[ClickAggregate] = field(default_factory=list)
    top_country: str | None = None  # 데이터 부족 시 None


def _validate_iso_date(d: str) -> None:
    """YYYY-MM-DD 형식 검증."""
    try:
        datetime.strptime(d, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"date 형식 오류 (YYYY-MM-DD 필요): {d!r}") from e


def aggregate_weekly(
    conn: sqlite3.Connection,
    end_date: str | None = None,
) -> ReportData:
    """end_date 기준 최근 7일 (end 포함) 클릭 집계.

    인자:
        conn: SQLite 연결 (clicks_daily 테이블 필요)
        end_date: 'YYYY-MM-DD'. None이면 오늘.

    반환: ReportData(period="weekly").
    """
    if end_date is None:
        end_date = date.today().isoformat()
    _validate_iso_date(end_date)
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    start = end - timedelta(days=6)
    return _aggregate_range(conn, start.isoformat(), end.isoformat(), period="weekly")


def aggregate_monthly(
    conn: sqlite3.Connection,
    year_month: str | None = None,
) -> ReportData:
    """달력 월 단위 집계 (1일~말일).

    인자:
        conn: SQLite 연결
        year_month: 'YYYY-MM'. None이면 이번 달.

    반환: ReportData(period="monthly").
    """
    if year_month is None:
        today = date.today()
        year_month = f"{today.year:04d}-{today.month:02d}"
    if len(year_month) != 7 or year_month[4] != "-":
        raise ValueError(f"year_month 형식 오류 (YYYY-MM 필요): {year_month!r}")
    try:
        year = int(year_month[:4])
        month = int(year_month[5:7])
    except ValueError as e:
        raise ValueError(f"year_month 파싱 실패: {year_month!r}") from e
    if not (1 <= month <= 12):
        raise ValueError(f"month 범위 오류: {month}")

    start = date(year, month, 1)
    if month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return _aggregate_range(conn, start.isoformat(), end.isoformat(), period="monthly")


def _aggregate_range(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    *,
    period: str,
) -> ReportData:
    """공통 집계 — start~end (양 끝 포함)."""
    rows = conn.execute(
        "SELECT slug, SUM(click_count) AS clicks, SUM(unique_ua_count) AS uu "
        "FROM clicks_daily WHERE date BETWEEN ? AND ? "
        "GROUP BY slug ORDER BY clicks DESC",
        (start_date, end_date),
    ).fetchall()

    by_slug = [
        ClickAggregate(
            slug=str(r[0]),
            click_count=int(r[1] or 0),
            unique_ua_count=int(r[2] or 0),
        )
        for r in rows
    ]

    total_clicks = sum(a.click_count for a in by_slug)
    total_unique_ua = sum(a.unique_ua_count for a in by_slug)

    # top_country: clicks_daily.top_country 최빈값 (1개만)
    country_row = conn.execute(
        "SELECT top_country, SUM(click_count) AS clicks "
        "FROM clicks_daily WHERE date BETWEEN ? AND ? "
        "AND top_country IS NOT NULL AND top_country <> '' "
        "GROUP BY top_country ORDER BY clicks DESC LIMIT 1",
        (start_date, end_date),
    ).fetchone()
    top_country = str(country_row[0]) if country_row else None

    return ReportData(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_clicks=total_clicks,
        total_unique_ua=total_unique_ua,
        by_slug=by_slug,
        top_country=top_country,
    )


def top_articles_by_clicks(
    conn: sqlite3.Connection,
    *,
    since_date: str,
    limit: int = 10,
) -> list[ClickAggregate]:
    """since_date 이후 클릭 상위 N개 slug.

    인자:
        conn: SQLite 연결
        since_date: 'YYYY-MM-DD' (포함)
        limit: 상위 N (기본 10)
    """
    _validate_iso_date(since_date)
    if limit <= 0:
        raise ValueError(f"limit 양수 필요: {limit}")

    rows = conn.execute(
        "SELECT slug, SUM(click_count) AS clicks, SUM(unique_ua_count) AS uu "
        "FROM clicks_daily WHERE date >= ? "
        "GROUP BY slug ORDER BY clicks DESC LIMIT ?",
        (since_date, limit),
    ).fetchall()
    return [
        ClickAggregate(
            slug=str(r[0]),
            click_count=int(r[1] or 0),
            unique_ua_count=int(r[2] or 0),
        )
        for r in rows
    ]


def render_html_stub(data: ReportData) -> str:
    """HTML 렌더 placeholder — Phase 3 dashboard 디자인 후 jinja2 통합 [관찰].

    현재는 plain text 요약만 반환. dashboard.render와 통합 시 본 함수가 jinja2 템플릿 호출.
    """
    lines = [
        f"[STUB] {data.period} 리포트 {data.start_date}~{data.end_date}",
        f"  total_clicks={data.total_clicks}",
        f"  total_unique_ua={data.total_unique_ua}",
        f"  top_country={data.top_country or '(없음)'}",
        f"  slug 수: {len(data.by_slug)}",
    ]
    for a in data.by_slug[:5]:
        lines.append(f"    - {a.slug}: clicks={a.click_count} uu={a.unique_ua_count}")
    if len(data.by_slug) > 5:
        lines.append(f"    ... 추가 {len(data.by_slug) - 5}건")
    return "\n".join(lines)


def weekly(
    conn: sqlite3.Connection,
    *,
    end_date: str | None = None,
    render: bool = False,
) -> dict[str, Any]:
    """BACKEND §2-8 진입점 — 주간 리포트.

    인자:
        conn: SQLite 연결
        end_date: 'YYYY-MM-DD' (None=오늘)
        render: True면 HTML stub도 함께 반환

    반환: {"data": ReportData, "html": str | None}
    """
    data = aggregate_weekly(conn, end_date)
    html = render_html_stub(data) if render else None
    return {"data": data, "html": html}


def monthly(
    conn: sqlite3.Connection,
    *,
    year_month: str | None = None,
    render: bool = False,
) -> dict[str, Any]:
    """BACKEND §2-8 진입점 — 월간 리포트."""
    data = aggregate_monthly(conn, year_month)
    html = render_html_stub(data) if render else None
    return {"data": data, "html": html}
