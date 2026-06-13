"""dashboard.queries — 운영 대시보드 읽기 데이터 레이어 (세션 #25).

PyQt에 비의존(테스트 가능). GUI(app.py)와 HTML 모니터(render.py) 양쪽이 쓸 수 있는 순수 함수.
기존 render.py의 데이터 함수(load_last_cycle 등)를 재사용하고, 키워드 큐·통계·카테고리 건강
데이터를 dict 형태로 추가한다. 모든 함수는 테이블 미존재(마이그레이션 전)에도 안전(§0).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from writer import auto_publish

from . import render

# render.py의 순수 데이터 함수 재노출 (중복 제거)
load_last_cycle = render.load_last_cycle


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def dashboard_stats(conn: sqlite3.Connection) -> dict[str, int]:
    """상단 통계 카드용 카운트. 테이블 없으면 해당 항목 0 (안전)."""

    def _count(sql: str) -> int:
        try:
            row = conn.execute(sql).fetchone()
            return int(row[0]) if row else 0
        except sqlite3.OperationalError:
            return 0

    return {
        "keywords_pending": _count("SELECT COUNT(*) FROM keyword_queue WHERE status='pending'"),
        "keywords_total": _count("SELECT COUNT(*) FROM keyword_queue"),
        "drafts_validated": _count("SELECT COUNT(*) FROM drafts WHERE status='validated'"),
        "drafts_approved": _count("SELECT COUNT(*) FROM drafts WHERE status='approved'"),
        "articles_published": _count("SELECT COUNT(*) FROM articles WHERE status='published'"),
        "categories_published": _count("SELECT COUNT(*) FROM categories WHERE status='published'"),
    }


def list_keywords(
    conn: sqlite3.Connection, status: str | None = None, limit: int = 500
) -> list[dict[str, Any]]:
    """키워드 큐 목록 (정렬: score·priority·id). status 지정 시 필터."""
    if not _table_exists(conn, "keyword_queue"):
        return []
    conn.row_factory = sqlite3.Row
    base = "SELECT * FROM keyword_queue"
    order = " ORDER BY score DESC, priority DESC, id LIMIT ?"
    if status:
        rows = conn.execute(base + " WHERE status = ?" + order, (status, limit)).fetchall()
    else:
        rows = conn.execute(base + order, (limit,)).fetchall()
    return [dict(r) for r in rows]


def list_queue(
    conn: sqlite3.Connection,
    statuses: tuple[str, ...] = ("validated", "approved", "published"),
    limit: int = 500,
) -> list[dict[str, Any]]:
    """발행 큐 — drafts(검토대기/승인/게시) + 연결 키워드 제목. 최신순."""
    if not _table_exists(conn, "drafts"):
        return []
    conn.row_factory = sqlite3.Row
    qmarks = ",".join("?" * len(statuses))
    has_kw = _table_exists(conn, "keyword_queue")
    # 키워드 큐(마이그레이션 007) 유무에 따라 컬럼/조인 분기 — 보간 값은 모두 코드 상수(주입 아님).
    # 001-only DB는 drafts.keyword_id 컬럼도 없으므로 NULL 별칭으로 대체.
    kw_select = "d.keyword_id, k.keyword" if has_kw else "NULL AS keyword_id, NULL AS keyword"
    kw_join = "LEFT JOIN keyword_queue k ON k.id = d.keyword_id" if has_kw else ""
    sql = f"SELECT d.id, d.working_title, d.status, d.status_reason, d.created_at, {kw_select} FROM drafts d {kw_join} WHERE d.status IN ({qmarks}) ORDER BY d.created_at DESC LIMIT ?"  # noqa: S608
    rows = conn.execute(sql, (*statuses, limit)).fetchall()
    return [dict(r) for r in rows]


def category_health(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """공개 카테고리 건강 — 추천수/전체수 + 가드레일 미달 사유(휴리스틱·무비용)."""
    if not _table_exists(conn, "categories"):
        return []
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT c.id, c.slug, c.name_ko, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id AND is_featured=1) "
        "AS featured, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id=c.id) AS total "
        "FROM categories c WHERE c.status='published' ORDER BY c.display_order, c.id"
    ).fetchall()
    # 사후 감시(LLM 미사용) — render.render_health_section과 동일 기준
    flags = {f["slug"]: f.get("reasons", []) for f in auto_publish.monitor(conn, use_llm=False)}
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["flagged"] = r["slug"] in flags
        d["reasons"] = flags.get(r["slug"], [])
        out.append(d)
    return out
