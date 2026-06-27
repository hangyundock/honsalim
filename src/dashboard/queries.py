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
    """키워드 큐 목록. 정렬: **미리선택(쿠팡 등 target_products) 있는 키워드 우선** → score → priority → id.

    auto_pick_keyword와 동일 정렬(화면 맨 위 = 자동 선정 대상). 쿠팡 세팅한 키워드가
    검색량 높은 알리 추천보다 먼저 와 '글 생성'에 쿠팡이 포함됨(세션 #28 Part2). status 지정 시 필터.
    """
    if not _table_exists(conn, "keyword_queue"):
        return []
    conn.row_factory = sqlite3.Row
    base = "SELECT * FROM keyword_queue"
    order = (
        " ORDER BY (target_products IS NOT NULL AND target_products NOT IN ('', '[]')) DESC, "
        "score DESC, priority DESC, id LIMIT ?"
    )
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


SITE_ORIGIN = "https://honsallim.com"


def list_articles(
    conn: sqlite3.Connection,
    statuses: tuple[str, ...] = ("published", "unpublished", "archived"),
    limit: int = 500,
) -> list[dict[str, Any]]:
    """발행 글 관리 목록 — articles(공개/비공개/보관) + 라이브 URL. 공개 먼저·최신 발행순 (세션 #37).

    완전 무인 발행의 '사후 검토' 화면용: 자동 발행된 글을 사람이 목록·링크로 확인하고
    비공개(내리기)/재공개한다. 렌더러는 published만 렌더하므로 unpublished는 라이브에 없다
    (live_url은 published 글의 실제 주소, 비공개 글은 참고용). 테이블 없으면 [] (안전·§0).
    """
    if not _table_exists(conn, "articles"):
        return []
    conn.row_factory = sqlite3.Row
    qmarks = ",".join("?" * len(statuses))
    # 보간되는 qmarks는 상태 수만큼의 '?'(값 주입 아님)·값은 파라미터로 — list_queue와 동일 안전 패턴.
    sql = f"SELECT id, slug, title, status, published_at, updated_at FROM articles WHERE status IN ({qmarks}) ORDER BY (status = 'published') DESC, COALESCE(published_at, updated_at) DESC, id DESC LIMIT ?"  # noqa: S608
    rows = conn.execute(sql, (*statuses, limit)).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["live_url"] = f"{SITE_ORIGIN}/articles/{r['slug']}/"
        out.append(d)
    return out


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


def google_usage(conn: sqlite3.Connection) -> dict[str, Any]:
    """Google(Imagen) 이번 달 추정 사용량 + 상한 대비 — 대시보드 표시용 (세션 #36).

    구글 실제 청구액은 단순 API 키로 못 가져와 우리 호출수에 단가를 곱해 **추정**한다('추정' 명시·§0).
    상한(설정 google_spend_cap_usd)>0이면 사용률(%)·임박(≥80%) 경고를 함께 반환. last_429_at이
    있으면 최근 한도초과(429) 발생 = 결제/상한 상향 필요 신호.
    """
    from common import settings
    from writer import api_usage

    s = api_usage.month_summary(conn, "google_imagen")
    cap = float(settings.get("google_spend_cap_usd", 0.0) or 0.0)
    used = float(s["est_cost_usd"])
    pct = (used / cap * 100.0) if cap > 0 else None
    return {
        "images": int(s["images"]),
        "used_usd": used,
        "cap_usd": cap,
        "pct": pct,
        "near_or_over": bool(pct is not None and pct >= 80.0),
        "last_429_at": s["last_429_at"],
    }
