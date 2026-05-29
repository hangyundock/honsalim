"""dashboard.render — drafts 단일 HTML 미리보기 (BACKEND §2-6 [확정]).

drafts(6 상태) 그룹별 카드 + 1클릭 승인 명령 표시. Jinja2 미사용, 단순 f-string + html.escape.
DECISIONS G3: Claude Design은 공개 사이트 5종만, dashboard는 stub HTML로 충분.
"""

from __future__ import annotations

import html
import sqlite3
from datetime import datetime
from pathlib import Path

from common import db

DEFAULT_OUTPUT = Path("data/dashboard/index.html")

STATUS_GROUPS: list[tuple[str, str]] = [
    ("validated", "검토 대기 (validated)"),
    ("enriched", "보강 완료 (enriched)"),
    ("collected", "수집됨 (collected)"),
    ("approved", "승인됨 (approved)"),
    ("published", "게시됨 (published)"),
    ("rejected", "반려됨 (rejected)"),
]

STATUS_COLORS: dict[str, str] = {
    "collected": "#9aa0a6",
    "enriched": "#1a73e8",
    "validated": "#34a853",
    "approved": "#e8a33c",
    "published": "#1a8a3a",
    "rejected": "#d93025",
}


def fetch_drafts_by_status(conn: sqlite3.Connection) -> dict[str, list[sqlite3.Row]]:
    """status별 drafts 그룹 (created_at DESC)."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, scenario_id, working_title, status, status_reason,
               created_at, updated_at, validation_report
        FROM drafts
        ORDER BY created_at DESC
        """).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = {s: [] for s, _ in STATUS_GROUPS}
    for r in rows:
        grouped.setdefault(r["status"], []).append(r)
    return grouped


def count_validation_fails_24h(conn: sqlite3.Connection) -> int:
    """validator fail 24h 카운트 (status='rejected' AND status_reason LIKE 'validator%')."""
    row = conn.execute("""
        SELECT COUNT(*) FROM drafts
        WHERE status = 'rejected'
          AND status_reason LIKE 'validator%'
          AND updated_at >= datetime('now', '-1 day')
        """).fetchone()
    return int(row[0]) if row else 0


def _format_card(row: sqlite3.Row) -> str:
    title = html.escape(row["working_title"] or f"(no title) #{row['id']}")
    status = row["status"]
    color = STATUS_COLORS.get(status, "#666")
    reason = html.escape(row["status_reason"] or "")
    created = html.escape(row["created_at"] or "")
    approve_cmd = f"python -m honsalim approve --draft {row['id']}" if status == "validated" else ""
    approve_html = (
        f'<div class="cmd"><code>{html.escape(approve_cmd)}</code> '
        f'<button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent)">복사</button></div>'
        if approve_cmd
        else ""
    )
    return f"""
    <article class="card" data-status="{status}">
      <header style="border-left:4px solid {color};padding-left:8px">
        <h3>#{row['id']} — {title}</h3>
        <small>scenario_id={row['scenario_id']} · {created} · {status}</small>
      </header>
      {f'<p class="reason">{reason}</p>' if reason else ''}
      {approve_html}
    </article>"""


def render_html(grouped: dict[str, list[sqlite3.Row]], fail_24h: int) -> str:
    """grouped drafts → 단일 HTML 문자열. BACKEND §490 빨간 배너 (fail 24h 3건+) 포함."""
    banner = ""
    if fail_24h >= 3:
        banner = f'<div class="banner-red">⚠ validator fail 24h: {fail_24h}건 — 검토 필요</div>'

    sections: list[str] = []
    total = sum(len(v) for v in grouped.values())
    for status, label in STATUS_GROUPS:
        items = grouped.get(status, [])
        if not items:
            continue
        cards = "\n".join(_format_card(r) for r in items)
        sections.append(
            f'<section class="status-group"><h2>{html.escape(label)} '
            f'<span class="count">{len(items)}</span></h2>{cards}</section>'
        )
    body = "\n".join(sections) if sections else "<p>drafts 없음</p>"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>혼살림 dashboard — {now}</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Pretendard',sans-serif;max-width:900px;margin:1em auto;padding:0 1em;color:#202124}}
  h1{{font-size:1.4em;margin-bottom:0.2em}}
  .banner-red{{background:#fce8e6;border:1px solid #d93025;color:#a50e0e;padding:0.6em 1em;border-radius:6px;margin:1em 0;font-weight:bold}}
  .status-group{{margin:1.4em 0}}
  .status-group h2{{font-size:1.1em;margin:0.4em 0;color:#3c4043}}
  .count{{font-size:0.8em;color:#999;font-weight:normal}}
  .card{{background:#fafafa;border:1px solid #e8eaed;border-radius:6px;padding:0.6em 1em;margin:0.4em 0}}
  .card h3{{margin:0;font-size:1em}}
  .card small{{color:#666;font-size:0.85em}}
  .reason{{font-size:0.9em;color:#5f6368;margin:0.4em 0}}
  .cmd{{background:#f1f3f4;padding:0.4em 0.6em;border-radius:4px;margin:0.4em 0;font-size:0.85em}}
  .cmd code{{user-select:all}}
  .cmd button{{margin-left:0.6em;padding:0.2em 0.6em;cursor:pointer}}
  .meta{{color:#999;font-size:0.8em;text-align:right;margin-top:2em}}
</style>
</head>
<body>
<h1>혼살림 dashboard</h1>
<p class="meta">생성 {now} · drafts {total}건</p>
{banner}
{body}
<p class="meta">BACKEND §2-6 [확정] · DECISIONS G3 (Claude Design 미사용, stub HTML)</p>
</body>
</html>
"""


def render_dashboard(
    conn: sqlite3.Connection | None = None,
    output_path: Path | str = DEFAULT_OUTPUT,
) -> Path:
    """drafts 조회 + HTML 생성 + 파일 저장. Returns: 저장된 경로.

    conn=None 이면 db.DB_PATH로 자동 연결 (CLI 진입점용).
    """
    own_conn = conn is None
    if conn is None:
        conn = db.connect(db.DB_PATH)
    try:
        grouped = fetch_drafts_by_status(conn)
        fail_24h = count_validation_fails_24h(conn)
        html_str = render_html(grouped, fail_24h)
    finally:
        if own_conn:
            conn.close()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_str, encoding="utf-8")
    return out
