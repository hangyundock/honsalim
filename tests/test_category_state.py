"""writer.category_state — 카테고리 공개 승인 전이 회귀 (세션 #18).

draft ↔ published 전이·검증·승인 대기 목록. AI 자동승인 금지(§2-마·E7) 보장 확인.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from common import db
from writer import category_state


@pytest.fixture()
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    db_path = tmp_path / "test.db"
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    c = db.connect(db_path)
    try:
        yield c
    finally:
        c.close()


def _set_guide(conn: sqlite3.Connection, slug: str) -> None:
    """글 생성됨을 흉내 — guide_generated_at 채움(build-category가 채우는 컬럼)."""
    conn.execute(
        "UPDATE categories SET guide_generated_at = CURRENT_TIMESTAMP WHERE slug = ?", (slug,)
    )
    conn.commit()


class TestApprove:
    def test_seed_categories_start_as_draft(self, conn: sqlite3.Connection) -> None:
        # seed는 draft(미공개) — AI/수집이 자동 공개하지 않음(E7)
        row = conn.execute("SELECT status FROM categories WHERE slug='office-chair'").fetchone()
        assert row[0] == "draft"

    def test_approve_draft_to_published(self, conn: sqlite3.Connection) -> None:
        _set_guide(conn, "office-chair")
        res = category_state.approve(conn, "office-chair")
        assert res["from"] == "draft" and res["to"] == "published"
        assert res["warned"] is False
        row = conn.execute("SELECT status FROM categories WHERE slug='office-chair'").fetchone()
        assert row[0] == "published"

    def test_approve_without_guide_warns(self, conn: sqlite3.Connection) -> None:
        # 글 없이 승인 → 허용하되 warned=True (빈약 페이지 경고, 차단은 안 함)
        res = category_state.approve(conn, "desk")
        assert res["warned"] is True
        assert res["to"] == "published"

    def test_approve_already_published_raises(self, conn: sqlite3.Connection) -> None:
        category_state.approve(conn, "desk")
        with pytest.raises(category_state.CategoryStateError):
            category_state.approve(conn, "desk")

    def test_approve_unknown_slug_raises(self, conn: sqlite3.Connection) -> None:
        with pytest.raises(category_state.CategoryStateError):
            category_state.approve(conn, "no-such-category")


class TestUnapprove:
    def test_unapprove_published_to_draft(self, conn: sqlite3.Connection) -> None:
        category_state.approve(conn, "desk")
        res = category_state.unapprove(conn, "desk")
        assert res["from"] == "published" and res["to"] == "draft"
        row = conn.execute("SELECT status FROM categories WHERE slug='desk'").fetchone()
        assert row[0] == "draft"

    def test_unapprove_already_draft_raises(self, conn: sqlite3.Connection) -> None:
        with pytest.raises(category_state.CategoryStateError):
            category_state.unapprove(conn, "office-chair")


class TestPendingApproval:
    def test_only_draft_with_guide(self, conn: sqlite3.Connection) -> None:
        _set_guide(conn, "office-chair")  # draft + 글 → 승인 대기
        _set_guide(conn, "desk")
        category_state.approve(conn, "desk")  # published → 대기 제외
        pending = category_state.pending_approval(conn)
        slugs = {r["slug"] for r in pending}
        assert "office-chair" in slugs
        assert "desk" not in slugs  # published
        assert "monitor-stand" not in slugs  # draft지만 글 없음 (수집만)


class TestRobustness:
    def test_pending_approval_no_categories_table(self) -> None:
        # categories 미마이그레이션 부분 DB → 빈 목록(대시보드 견고성, §0). 예외 없이 안전.
        c = sqlite3.connect(":memory:")
        try:
            assert category_state.pending_approval(c) == []
        finally:
            c.close()
