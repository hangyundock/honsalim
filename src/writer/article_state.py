"""writer.article_state — 시나리오 글 공개 상태 전이 (published ↔ unpublished). 세션 #29.

``category_state``(카테고리)와 대칭. 무인 자동발행(B)에서 발행된 글에 문제가 생기면 사람 없이도
라이브에서 내릴 수 있는 안전 경로(§0 자가복원·발행후 안전망). 운영자가 수동으로 내릴 때도 사용.

articles.status는 'published'/'unpublished'/'archived' 3상태(001 schema CHECK). 비공개 전환 시
published_at=NULL로 비워 ``CHECK (published_at IS NULL OR status='published')``을 충족한다.
렌더러는 published만 렌더하므로 unpublish 후 재빌드하면 라이브에서 사라진다(republish로 되돌림).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, cast


class ArticleStateError(ValueError):
    """글 상태 전이 위반 (없음·이미 해당 상태 등)."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fetch(conn: sqlite3.Connection, slug: str) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id, title, status FROM articles WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        raise ArticleStateError(f"articles에 {slug!r} 없음")
    return cast(sqlite3.Row, row)


def unpublish(conn: sqlite3.Connection, slug: str, *, reason: str = "") -> dict[str, Any]:
    """published → unpublished (라이브 비공개). published가 아니면 거부.

    published_at=NULL (CHECK 충족). 렌더러가 published만 렌더 → 재빌드 시 라이브에서 제거.
    되돌리려면 republish. 반환: {slug, title, from, to, reason}.
    """
    row = _fetch(conn, slug)
    if row["status"] != "published":
        raise ArticleStateError(
            f"{slug!r} 상태={row['status']!r} — 비공개 대상 아님(published만 가능)"
        )
    conn.execute(
        "UPDATE articles SET status='unpublished', published_at=NULL, updated_at=? WHERE id=?",
        (_now_iso(), row["id"]),
    )
    conn.commit()
    return {
        "slug": slug,
        "title": row["title"],
        "from": "published",
        "to": "unpublished",
        "reason": reason,
    }


def republish(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    """unpublished/archived → published (재공개). 이미 published면 거부."""
    row = _fetch(conn, slug)
    if row["status"] == "published":
        raise ArticleStateError(f"{slug!r} 이미 published — 재공개 불필요")
    now = _now_iso()
    conn.execute(
        "UPDATE articles SET status='published', published_at=?, updated_at=? WHERE id=?",
        (now, now, row["id"]),
    )
    conn.commit()
    return {"slug": slug, "title": row["title"], "from": row["status"], "to": "published"}


def list_published(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """공개 중인 글 목록 (발행후 모니터·가시화용)."""
    conn.row_factory = sqlite3.Row
    return conn.execute(
        "SELECT id, slug, title, published_at FROM articles WHERE status='published' "
        "ORDER BY published_at DESC, id DESC"
    ).fetchall()
