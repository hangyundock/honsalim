"""writer.article_state — 글 공개 상태 전이 (published ↔ unpublished). 세션 #29 발행후 안전망.

B 자동발행에서 나쁜 글이 나가면 사람 없이도(또는 운영자가 수동으로) 라이브에서 내릴 수 있어야 한다.
종단 검증: unpublish → 재빌드 → 라이브(build)에서 글이 사라짐(되돌리면 republish).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from common import db
from writer import article_state


def _seed_published_article(db_path: Path, slug: str = "test-article") -> None:
    db.migrate(db_path=db_path)
    db.seed(db_path=db_path)
    conn = db.connect(db_path)
    try:
        sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO articles (slug, scenario_id, title, summary, body_md, body_html, "
            "meta_description, schema_jsonld, disclosure_first, status, published_at, "
            "content_hash, truth_check_passed_at, user_approved_at) "
            "VALUES (?, ?, '제목', '요약', '본문', '<p>본문</p>', '메타', '{}', '고지', "
            "'published', '2026-06-14T00:00:00Z', 'h', '2026-06-14T00:00:00Z', "
            "'2026-06-14T00:00:00Z')",
            (slug, sid),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    _seed_published_article(p)
    return p


class TestUnpublish:
    def test_unpublish_sets_status_and_clears_published_at(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            res = article_state.unpublish(conn, "test-article", reason="off-target")
            assert res["to"] == "unpublished"
            row = conn.execute(
                "SELECT status, published_at FROM articles WHERE slug='test-article'"
            ).fetchone()
            assert row[0] == "unpublished"
            assert row[1] is None  # CHECK(published_at IS NULL OR status='published') 충족
        finally:
            conn.close()

    def test_unpublish_nonexistent_raises(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            with pytest.raises(article_state.ArticleStateError):
                article_state.unpublish(conn, "no-such-slug")
        finally:
            conn.close()

    def test_unpublish_twice_raises(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            article_state.unpublish(conn, "test-article")
            with pytest.raises(article_state.ArticleStateError):
                article_state.unpublish(conn, "test-article")  # 이미 unpublished
        finally:
            conn.close()


class TestRepublish:
    def test_republish_restores_published(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            article_state.unpublish(conn, "test-article")
            res = article_state.republish(conn, "test-article")
            assert res["to"] == "published"
            row = conn.execute(
                "SELECT status, published_at FROM articles WHERE slug='test-article'"
            ).fetchone()
            assert row[0] == "published"
            assert row[1] is not None  # 재공개 시 published_at 다시 채움
        finally:
            conn.close()

    def test_republish_already_published_raises(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            with pytest.raises(article_state.ArticleStateError):
                article_state.republish(conn, "test-article")
        finally:
            conn.close()


class TestRenderExclusion:
    """종단: unpublish → 재빌드 → 라이브에서 글 제거(발행후 안전망 실증)."""

    def test_unpublished_article_removed_from_build(self, tmp_path: Path) -> None:
        from builder import renderer

        p = tmp_path / "test.db"
        _seed_published_article(p, slug="render-test")
        s1 = renderer.render_site(out_dir=tmp_path / "site1", db_path=p)
        assert s1["articles_published"] == 1
        assert (tmp_path / "site1" / "articles" / "render-test" / "index.html").exists()

        conn = db.connect(p)
        try:
            article_state.unpublish(conn, "render-test")
        finally:
            conn.close()

        s2 = renderer.render_site(out_dir=tmp_path / "site2", db_path=p)
        assert s2["articles_published"] == 0
        assert not (tmp_path / "site2" / "articles" / "render-test" / "index.html").exists()
