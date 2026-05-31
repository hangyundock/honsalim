"""writer.category_state — 카테고리 공개 상태 전이 (draft ↔ published).

drafts의 state_machine과 대칭. categories.status는 'draft'(미공개·승인 대기) /
'published'(공개) 2상태(migration 002 CHECK 제약). AI는 절대 published로 전이하지
않으며(§2-마·E7 자동승인 금지), 공개는 사용자 승인(approve)만, 비공개 전환은
unapprove로 되돌린다. 글 재생성(category_page_builder) 시 status는 draft로 유지된다.
"""

from __future__ import annotations

import sqlite3
from typing import Any, cast


class CategoryStateError(ValueError):
    """카테고리 상태 전이 위반 (존재하지 않음·이미 해당 상태 등)."""


def _fetch(conn: sqlite3.Connection, slug: str) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, name_ko, status, guide_generated_at FROM categories WHERE slug = ?",
        (slug,),
    ).fetchone()
    if row is None:
        raise CategoryStateError(f"categories에 {slug!r} 없음 — seed/수집 필요")
    return cast(sqlite3.Row, row)


def approve(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    """draft → published (사용자 1클릭 승인). 이미 published면 거부.

    글(guide_generated_at)이 없는 채로 승인하면 빈약한 페이지 위험이 있으므로
    warned 플래그로 가시화한다(차단은 하지 않음 — 최종 판단은 사용자).
    반환: {slug, name, from, to, warned}.
    """
    row = _fetch(conn, slug)
    if row["status"] == "published":
        raise CategoryStateError(f"{slug!r} 이미 published — 승인 불필요")
    warned = row["guide_generated_at"] is None
    conn.execute("UPDATE categories SET status = 'published' WHERE id = ?", (row["id"],))
    conn.commit()
    return {
        "slug": slug,
        "name": row["name_ko"],
        "from": "draft",
        "to": "published",
        "warned": warned,
    }


def unapprove(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    """published → draft (공개 취소·비공개 전환). 이미 draft면 거부."""
    row = _fetch(conn, slug)
    if row["status"] == "draft":
        raise CategoryStateError(f"{slug!r} 이미 draft — 취소할 공개 없음")
    conn.execute("UPDATE categories SET status = 'draft' WHERE id = ?", (row["id"],))
    conn.commit()
    return {"slug": slug, "name": row["name_ko"], "from": "published", "to": "draft"}


def pending_approval(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """승인 대기 목록 = status='draft' AND 글 생성됨(guide_generated_at NOT NULL).

    수집만 되고 글이 없는 draft는 제외(아직 검토 대상 아님). 대시보드·CLI 가시화용.
    """
    conn.row_factory = sqlite3.Row
    # categories 미마이그레이션(부분 DB) 시 빈 목록 — 대시보드는 drafts라도 표시(무인 견고성·§0)
    if (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        ).fetchone()
        is None
    ):
        return []
    return conn.execute(
        "SELECT id, slug, name_ko, guide_title, guide_generated_at, "
        "(SELECT COUNT(*) FROM category_products WHERE category_id = categories.id) "
        "AS product_count "
        "FROM categories "
        "WHERE status = 'draft' AND guide_generated_at IS NOT NULL "
        "ORDER BY guide_generated_at DESC"
    ).fetchall()
