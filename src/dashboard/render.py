"""dashboard.render — drafts 단일 HTML 미리보기 (BACKEND §2-6 [확정]).

drafts(6 상태) 그룹별 카드 + 1클릭 승인 명령 표시. Jinja2 미사용, 단순 f-string + html.escape.
DECISIONS G3: Claude Design은 공개 사이트 5종만, dashboard는 stub HTML로 충분.
"""

from __future__ import annotations

import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from common import db
from writer import auto_publish, category_state

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


def _format_category_card(row: sqlite3.Row) -> str:
    """승인 대기 카테고리 카드 + approve-category 명령(복사 버튼). drafts 카드와 동형."""
    name = html.escape(row["name_ko"])
    slug = html.escape(row["slug"])
    title = html.escape(row["guide_title"] or "")
    gen = html.escape(row["guide_generated_at"] or "")
    pc = row["product_count"]
    approve_cmd = f"python -m honsalim approve-category {row['slug']}"
    return f"""
    <article class="card" data-status="cat-pending">
      <header style="border-left:4px solid #e8a33c;padding-left:8px">
        <h3>{name} <small>({slug})</small></h3>
        <small>{title} · 제품 {pc}개 · 생성 {gen}</small>
      </header>
      <div class="cmd"><code>{html.escape(approve_cmd)}</code> <button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent)">복사</button></div>
    </article>"""


def render_category_section(pending: list[sqlite3.Row]) -> str:
    """카테고리 승인 대기(draft+글 생성됨) 섹션. 없으면 빈 문자열."""
    if not pending:
        return ""
    cards = "\n".join(_format_category_card(r) for r in pending)
    return (
        f'<section class="status-group"><h2>카테고리 승인 대기 '
        f'<span class="count">{len(pending)}</span></h2>'
        f'<p class="reason">미리보기(<code>build/preview</code>) 검토 후 아래 명령으로 공개합니다 '
        f"— AI 자동승인 금지(§2-마·E7).</p>{cards}</section>"
    )


def _categories_table_exists(conn: sqlite3.Connection) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        ).fetchone()
        is not None
    )


def load_last_cycle(path: Path) -> dict[str, Any] | None:
    """무인 사이클 다이제스트 JSON 로드(없거나 깨지면 None — 견고성·§0)."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def render_cycle_section(report: dict[str, Any] | None) -> str:
    """무인 스케줄러 최근 실행 요약 섹션. report 없으면 '실행 기록 없음'."""
    if report is None:
        return (
            '<section class="status-group"><h2>무인 사이클 (최근 실행)</h2>'
            '<p class="reason">아직 실행 기록 없음 — 스케줄러 첫 실행 후 표시됩니다.</p></section>'
        )
    ran = html.escape(str(report.get("ran_at", "?")))
    dry = " · DRY(판정만)" if report.get("dry_run") else ""
    pub = len(report.get("published", []))
    ok = report.get("refresh_ok", 0)
    fail = report.get("refresh_fail", 0)
    ks = report.get("killswitched", []) or []
    deployed = report.get("deployed")
    verify = report.get("verify_status")
    changed = report.get("changed")
    rows = [
        f"<li>실행 시각: <b>{ran}</b>{dry}</li>",
        f"<li>공개 카테고리: {pub}개</li>",
        f"<li>새로고침: 성공 {ok} · 실패 {fail}</li>",
    ]
    if ks:
        rows.append(
            '<li class="alert">자가복원(자동 비공개): '
            + ", ".join(html.escape(str(s)) for s in ks)
            + "</li>"
        )
    fail_rows = [r for r in report.get("refreshed", []) if isinstance(r, dict) and not r.get("ok")]
    for r in fail_rows:
        rows.append(
            f'<li class="alert">새로고침 실패 {html.escape(str(r.get("slug")))}: '
            f'{html.escape(str(r.get("error") or ""))}</li>'
        )
    dep_txt = (
        "배포됨" if deployed else ("변경 없음(배포 안 함)" if not changed else "변경 있음·미배포")
    )
    vtxt = f" · verify {verify}" if verify is not None else ""
    rows.append(f"<li>배포: {dep_txt}{vtxt}</li>")
    return (
        '<section class="status-group"><h2>무인 사이클 (최근 실행)</h2>'
        f'<ul class="kv">{"".join(rows)}</ul></section>'
    )


def render_health_section(conn: sqlite3.Connection) -> tuple[str, int]:
    """공개 카테고리 건강 섹션 — 추천수·전체수 + 가드레일 미달 표시. 반환: (html, 미달수)."""
    if not _categories_table_exists(conn):
        return "", 0
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT c.slug, c.name_ko, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id AND is_featured=1) AS feat, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id) AS total "
        "FROM categories c WHERE c.status='published' ORDER BY c.display_order, c.id"
    ).fetchall()
    if not rows:
        return (
            '<section class="status-group"><h2>공개 카테고리 건강</h2>'
            '<p class="reason">공개 카테고리 없음.</p></section>',
            0,
        )
    # 사후 감시(휴리스틱·무비용) — 지금 가드레일 미달인 published만 사유 표시
    flags = {f["slug"]: f.get("reasons", []) for f in auto_publish.monitor(conn, use_llm=False)}
    cards = []
    for r in rows:
        slug = r["slug"]
        bad = slug in flags
        mark = "⚠ " if bad else "✓ "
        cls = ' class="alert"' if bad else ""
        reason = (
            f' — <span class="reason">{html.escape("; ".join(flags[slug]))} '
            f"→ 킬스위치: <code>unapprove-category {html.escape(slug)}</code></span>"
            if bad
            else ""
        )
        cards.append(
            f"<li{cls}>{mark}<b>{html.escape(r['name_ko'])}</b> "
            f"<small>({html.escape(slug)}) 추천 {r['feat']} · 전체 {r['total']}</small>{reason}</li>"
        )
    return (
        '<section class="status-group"><h2>공개 카테고리 건강 '
        f'<span class="count">{len(rows)}개</span></h2>'
        f'<ul class="kv">{"".join(cards)}</ul></section>',
        len(flags),
    )


def render_html(
    grouped: dict[str, list[sqlite3.Row]],
    fail_24h: int,
    category_html: str = "",
    cycle_html: str = "",
    health_html: str = "",
    autonomous_alert: str = "",
) -> str:
    """grouped drafts → 단일 HTML 문자열. BACKEND §490 빨간 배너 (fail 24h 3건+) 포함."""
    banner = ""
    if autonomous_alert:
        banner += autonomous_alert
    if fail_24h >= 3:
        banner += f'<div class="banner-red">⚠ validator fail 24h: {fail_24h}건 — 검토 필요</div>'

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
    # 무인 모니터링(사이클·건강)을 최상단, 그 다음 카테고리 승인 대기, 그 다음 drafts 흐름
    monitor_parts = [s for s in (cycle_html, health_html) if s]
    body_parts = monitor_parts + ([category_html] if category_html else []) + sections
    body = "\n".join(body_parts) if body_parts else "<p>대기 항목 없음</p>"
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
  .banner-amber{{background:#fef7e0;border:1px solid #e8a33c;color:#8a5a00;padding:0.6em 1em;border-radius:6px;margin:1em 0;font-weight:bold}}
  ul.kv{{list-style:none;padding:0;margin:0.4em 0}}
  ul.kv li{{padding:0.3em 0.6em;border-bottom:1px solid #eee;font-size:0.92em}}
  ul.kv li.alert{{background:#fef7e0;border-radius:4px}}
  ul.kv code{{background:#f1f3f4;padding:0.1em 0.3em;border-radius:3px}}
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
    cycle_report_path: Path | None = None,
) -> Path:
    """drafts·무인 사이클·공개 카테고리 건강 → 모니터링 HTML 생성·저장. Returns: 저장 경로.

    conn=None 이면 db.DB_PATH로 자동 연결 (CLI 진입점용). cycle_report_path 기본은
    data/refresh_cycle_last.json (DB와 같은 폴더) — 무인 스케줄러가 매 실행 후 갱신.
    """
    own_conn = conn is None
    if conn is None:
        conn = db.connect(db.DB_PATH)
    if cycle_report_path is None:
        cycle_report_path = db.DB_PATH.parent / "refresh_cycle_last.json"
    try:
        grouped = fetch_drafts_by_status(conn)
        fail_24h = count_validation_fails_24h(conn)
        category_html = render_category_section(category_state.pending_approval(conn))
        cycle_report = load_last_cycle(cycle_report_path)
        cycle_html = render_cycle_section(cycle_report)
        health_html, health_flags = render_health_section(conn)
        # 무인 경고 배너 — 최근 사이클 자가복원/실패 또는 지금 공개 카테고리 미달 시
        alerts = []
        if cycle_report and cycle_report.get("killswitched"):
            n = len(cycle_report["killswitched"])
            alerts.append(f"최근 사이클 자가복원(자동 비공개) {n}건")
        if cycle_report and cycle_report.get("refresh_fail"):
            alerts.append(f"새로고침 실패 {cycle_report['refresh_fail']}건")
        if health_flags:
            alerts.append(f"공개 카테고리 가드레일 미달 {health_flags}건")
        autonomous_alert = (
            f'<div class="banner-amber">⚠ 무인 점검: {" · ".join(alerts)} — 확인 권장</div>'
            if alerts
            else ""
        )
        html_str = render_html(
            grouped, fail_24h, category_html, cycle_html, health_html, autonomous_alert
        )
    finally:
        if own_conn:
            conn.close()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_str, encoding="utf-8")
    return out
