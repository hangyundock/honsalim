"""writer.article_writer 회귀 테스트 — drafts 생성·업데이트·articles 승격.

출처: BACKEND §2-4 + DB §4·§5·§8 [확정].
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from writer import IllegalStateError, article_writer
from writer.state_machine import transition

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"


def _seeded_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    conn.executescript(
        """
        INSERT INTO personas (slug, title_ko, description) VALUES ('p1', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);
        """
    )
    conn.commit()
    return conn


def _approved_draft_with_enrichment(conn: sqlite3.Connection) -> int:
    """create → enriched → validated → approved 까지 진행한 draft 반환."""
    did = article_writer.create_draft(conn, scenario_id=1, raw_payload={"src": "test"})
    transition(conn, did, "enriched")
    article_writer.save_enriched(conn, did, {"title": "T", "body_md": "..."})
    transition(conn, did, "validated")
    article_writer.save_validation_report(conn, did, {"truth": "pass"})
    transition(conn, did, "approved")
    return int(did)


def _valid_article_fields(scenario_id: int = 1) -> dict[str, Any]:
    return {
        "slug": "test-article",
        "scenario_id": scenario_id,
        "title": "테스트 글",
        "summary": "요약",
        "body_md": "# 본문",
        "body_html": "<h1>본문</h1>",
        "meta_description": "메타",
        "schema_jsonld": '{"@type":"Article"}',
        "disclosure_first": "쿠팡 파트너스 활동 수수료 안내",
        "content_hash": "abc123",
        "truth_check_passed_at": "2026-05-28T12:00:00Z",
        "user_approved_at": "2026-05-28T12:05:00Z",
    }


class TestCreateDraft:
    def test_inserts_collected_status(self) -> None:
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1)
        assert did > 0
        row = conn.execute("SELECT status, scenario_id FROM drafts WHERE id = ?", (did,)).fetchone()
        assert row[0] == "collected"
        assert row[1] == 1

    def test_raw_payload_serialized(self) -> None:
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1, raw_payload={"k": "v"})
        row = conn.execute("SELECT raw_payload FROM drafts WHERE id = ?", (did,)).fetchone()
        assert json.loads(row[0]) == {"k": "v"}

    def test_working_title_optional(self) -> None:
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1, working_title="제목 후보")
        row = conn.execute("SELECT working_title FROM drafts WHERE id = ?", (did,)).fetchone()
        assert row[0] == "제목 후보"


class TestSaveEnriched:
    def test_updates_enriched_payload(self) -> None:
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1)
        article_writer.save_enriched(conn, did, {"title": "T", "body": "b"})
        row = conn.execute("SELECT enriched_payload FROM drafts WHERE id = ?", (did,)).fetchone()
        assert json.loads(row[0]) == {"title": "T", "body": "b"}


class TestSaveValidationReport:
    def test_updates_validation_report(self) -> None:
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1)
        article_writer.save_validation_report(conn, did, {"truth": "pass", "schema": "fail"})
        row = conn.execute("SELECT validation_report FROM drafts WHERE id = ?", (did,)).fetchone()
        rpt = json.loads(row[0])
        assert rpt["truth"] == "pass"
        assert rpt["schema"] == "fail"


class TestPromoteToArticle:
    def test_promote_success_full_lifecycle(self) -> None:
        conn = _seeded_db()
        did = _approved_draft_with_enrichment(conn)
        article_id = article_writer.promote_to_article(conn, did, _valid_article_fields())
        assert article_id > 0

        # articles INSERT 확인
        art = conn.execute(
            "SELECT slug, status, scenario_id FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        assert art[0] == "test-article"
        assert art[1] == "published"
        assert art[2] == 1

        # drafts 상태 전이 + promoted_article_id 설정
        draft_row = conn.execute(
            "SELECT status, promoted_article_id FROM drafts WHERE id = ?", (did,)
        ).fetchone()
        assert draft_row[0] == "published"
        assert draft_row[1] == article_id

    def test_promote_creates_article_history(self) -> None:
        conn = _seeded_db()
        did = _approved_draft_with_enrichment(conn)
        article_id = article_writer.promote_to_article(conn, did, _valid_article_fields())
        rows = conn.execute(
            "SELECT event_type, actor, diff_summary FROM article_history WHERE article_id = ?",
            (article_id,),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "created"
        assert rows[0][1] == "user"
        assert f"draft_id={did}" in rows[0][2]

    def test_promote_requires_approved_status(self) -> None:
        """status != 'approved' 인 draft promote → IllegalStateError."""
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1)  # collected 상태
        with raises(IllegalStateError):
            article_writer.promote_to_article(conn, did, _valid_article_fields())

    def test_promote_validates_required_fields(self) -> None:
        """필수 필드 누락 시 ValueError."""
        conn = _seeded_db()
        did = _approved_draft_with_enrichment(conn)
        incomplete = _valid_article_fields()
        del incomplete["title"]
        del incomplete["body_md"]
        with raises(ValueError):
            article_writer.promote_to_article(conn, did, incomplete)


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
