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
    conn.executescript("""
        INSERT INTO personas (slug, title_ko, description) VALUES ('p1', 'P', 'd');
        INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);
        """)
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


# ─── validate_and_save — validator 4 게이트 통합 흐름 ─────────────────

GOOD_PAYLOAD_BODY = (
    "이 글은 쿠팡 파트너스 활동의 일환으로 일정 수수료를 받을 수 있습니다.\n"
    "\n# 본문 시작\n"
    "원룸 첫 자취 가이드입니다. 가격 290,000원 모델 추천.\n"
    "\n## 푸터\n"
    "본인은 쿠팡 파트너스 및 AliExpress 활동으로 수수료를 받을 수 있습니다."
)


def _good_article_jsonld() -> str:
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "원룸",
            "description": "가이드",
            "image": "https://honsalim.com/i.jpg",
            "datePublished": "2026-05-28",
            "dateModified": "2026-05-28",
            "author": {"@type": "Person", "name": "운영자"},
            "publisher": {"@type": "Organization", "name": "혼살림"},
            "mainEntityOfPage": "https://honsalim.com/articles/x",
        }
    )


def _draft_at_enriched(conn: sqlite3.Connection) -> int:
    """create → transition(enriched) 까지 진행한 draft."""
    did = article_writer.create_draft(conn, scenario_id=1)
    transition(conn, did, "enriched")
    return int(did)


class TestValidateAndSave:
    def test_all_pass_transitions_to_validated(self) -> None:
        conn = _seeded_db()
        did = _draft_at_enriched(conn)
        payload = {
            "body_md": GOOD_PAYLOAD_BODY,
            "schema_jsonld": _good_article_jsonld(),
            "products": [],
        }
        overall, report = article_writer.validate_and_save(conn, did, payload)
        assert overall is True
        assert report["overall_pass"] is True
        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "validated"

    def test_truth_fail_transitions_to_rejected(self) -> None:
        conn = _seeded_db()
        did = _draft_at_enriched(conn)
        payload = {
            "body_md": "본 글은 AI로 작성되었습니다.",
            "schema_jsonld": _good_article_jsonld(),
            "products": [],
        }
        overall, report = article_writer.validate_and_save(conn, did, payload)
        assert overall is False
        assert report["gates"]["truth"]["pass"] is False
        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "rejected"

    def test_disclosure_fail_transitions_to_rejected(self) -> None:
        conn = _seeded_db()
        did = _draft_at_enriched(conn)
        payload = {
            "body_md": "일반 본문입니다. 가격 290,000원.",  # disclosure 키워드 없음
            "schema_jsonld": _good_article_jsonld(),
            "products": [],
        }
        overall, report = article_writer.validate_and_save(conn, did, payload)
        assert overall is False
        assert report["gates"]["disclosure"]["pass"] is False
        status = conn.execute("SELECT status FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        assert status == "rejected"

    def test_persists_validation_report(self) -> None:
        conn = _seeded_db()
        did = _draft_at_enriched(conn)
        payload = {
            "body_md": GOOD_PAYLOAD_BODY,
            "schema_jsonld": _good_article_jsonld(),
            "products": [],
        }
        article_writer.validate_and_save(conn, did, payload)
        raw = conn.execute("SELECT validation_report FROM drafts WHERE id = ?", (did,)).fetchone()[
            0
        ]
        rpt = json.loads(raw)
        assert rpt["overall_pass"] is True
        assert set(rpt["gates"]) == {"truth", "schema", "disclosure", "links"}

    def test_requires_enriched_status(self) -> None:
        """status='collected' 인 draft에 호출 시 IllegalStateError (state_machine 매트릭스)."""
        conn = _seeded_db()
        did = article_writer.create_draft(conn, scenario_id=1)  # collected
        payload = {
            "body_md": GOOD_PAYLOAD_BODY,
            "schema_jsonld": _good_article_jsonld(),
            "products": [],
        }
        with raises(IllegalStateError):
            article_writer.validate_and_save(conn, did, payload)


# ─── compute_content_hash — DB §4-1 본문 SHA256 ──────────────────────


class TestComputeContentHash:
    def test_returns_sha256_prefix_and_hex(self) -> None:
        h = article_writer.compute_content_hash("본문 텍스트")
        assert h.startswith("sha256:")
        hex_part = h.split(":", 1)[1]
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_deterministic_same_input(self) -> None:
        h1 = article_writer.compute_content_hash("같은 본문")
        h2 = article_writer.compute_content_hash("같은 본문")
        assert h1 == h2

    def test_different_body_different_hash(self) -> None:
        h1 = article_writer.compute_content_hash("본문 A")
        h2 = article_writer.compute_content_hash("본문 B")
        assert h1 != h2

    def test_korean_utf8_encoded(self) -> None:
        """한국어 UTF-8 인코딩 — manifest 포터블성."""
        # 같은 한국어 → 같은 hash (cp949 등 다른 인코딩이면 깨짐)
        h = article_writer.compute_content_hash("원룸 자취 30만원")
        # 알려진 SHA256 값과 비교 — 인코딩 안정성 회귀
        import hashlib

        expected = hashlib.sha256("원룸 자취 30만원".encode()).hexdigest()
        assert h == f"sha256:{expected}"

    def test_empty_body_handled(self) -> None:
        """빈 본문도 유효한 hash 반환 (예외 없이)."""
        h = article_writer.compute_content_hash("")
        # SHA256 of empty string is e3b0c442...
        assert h == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# ─── extract_disclosure_first — POLICY §2-2 첫머리 추출 ───────────────


class TestExtractDisclosureFirst:
    def test_extracts_standard_disclosure(self) -> None:
        body = (
            "이 글에는 쿠팡 파트너스 활동의 일환으로 일정 수수료를 제공받습니다.\n"
            "(구매자에게 추가 비용은 발생하지 않습니다.)\n\n"
            "# 본문 시작\n원룸 자취 가이드입니다."
        )
        out = article_writer.extract_disclosure_first(body)
        assert out is not None
        assert "쿠팡 파트너스" in out
        assert "수수료" in out

    def test_returns_none_when_both_keywords_missing(self) -> None:
        body = "안녕하세요. 일반 가이드입니다.\n\n본문 본문."
        assert article_writer.extract_disclosure_first(body) is None

    def test_returns_none_when_only_one_keyword(self) -> None:
        body = "쿠팡 파트너스 안내입니다.\n\n본문."
        # '수수료' 누락 → None
        assert article_writer.extract_disclosure_first(body) is None

    def test_returns_none_when_disclosure_buried_deep(self) -> None:
        """첫머리 300자 밖에 문구가 있으면 추출 안 함 (POLICY §2-4 위치 정확성)."""
        body = "다른 텍스트.\n\n" + ("패딩 " * 100) + "\n\n쿠팡 파트너스 수수료 안내."
        assert article_writer.extract_disclosure_first(body) is None

    def test_empty_body_returns_none(self) -> None:
        assert article_writer.extract_disclosure_first("") is None
        assert article_writer.extract_disclosure_first("   ") is None

    def test_returns_stripped_text(self) -> None:
        """앞뒤 공백·줄바꿈은 제거된 텍스트 반환."""
        body = "\n  이 글에는 쿠팡 파트너스 수수료 안내.  \n\n본문."
        out = article_writer.extract_disclosure_first(body)
        assert out is not None
        assert not out.startswith(" ")
        assert not out.endswith(" ")


class TestRecordScenarioCandidates:
    """collect-products → 시나리오 collected draft.raw_payload 후보 기록 (DB §5)."""

    @staticmethod
    def _candidates() -> list[dict[str, Any]]:
        return [
            {"source_product_id": "1", "deeplink_slug": "ali-1", "name": "A", "price_krw": 1000},
            {"source_product_id": "2", "deeplink_slug": "ali-2", "name": "B", "price_krw": 2000},
        ]

    def test_creates_draft_when_none(self) -> None:
        conn = _seeded_db()
        did = article_writer.record_scenario_candidates(conn, 1, self._candidates())
        row = conn.execute("SELECT status, raw_payload FROM drafts WHERE id = ?", (did,)).fetchone()
        assert row[0] == "collected"
        payload = json.loads(row[1])
        assert payload["source"] == "collect-products"
        assert payload["candidate_count"] == 2
        assert [c["deeplink_slug"] for c in payload["candidates"]] == ["ali-1", "ali-2"]

    def test_updates_existing_collected_draft(self) -> None:
        conn = _seeded_db()
        first = article_writer.create_draft(conn, scenario_id=1, raw_payload={"src": "old"})
        did = article_writer.record_scenario_candidates(conn, 1, self._candidates())
        assert did == first  # 새 draft 만들지 않고 기존 collected 갱신
        assert conn.execute("SELECT COUNT(*) FROM drafts WHERE scenario_id = 1").fetchone()[0] == 1
        payload = json.loads(
            conn.execute("SELECT raw_payload FROM drafts WHERE id = ?", (did,)).fetchone()[0]
        )
        assert payload["candidate_count"] == 2

    def test_does_not_touch_enriched_draft(self) -> None:
        """이미 enriched로 진행한 draft는 건드리지 않고 새 collected 생성."""
        conn = _seeded_db()
        old = article_writer.create_draft(conn, scenario_id=1, raw_payload={"src": "old"})
        transition(conn, old, "enriched")
        did = article_writer.record_scenario_candidates(conn, 1, self._candidates())
        assert did != old
        assert conn.execute("SELECT COUNT(*) FROM drafts WHERE scenario_id = 1").fetchone()[0] == 2


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
