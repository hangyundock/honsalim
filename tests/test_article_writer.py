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
        # 세션 #15: seo 게이트 추가 (seo 설정 없으면 skip-pass). 게이트 집합 5종.
        assert set(rpt["gates"]) == {"truth", "schema", "disclosure", "links", "seo"}

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

    def test_extracts_aliexpress_disclosure(self) -> None:
        """제휴처 인지형 첫머리 — AliExpress 변형(쿠팡 미포함)도 표준 마커로 추출.

        근본 수정 회귀 가드: 이전엔 '쿠팡 파트너스' 키워드 강제로 None 반환 →
        promote 시 disclosure_first NOT NULL 위반. 표준 마커 기준으로 정정.
        """
        body = article_writer.apply_disclosure("# 알리 추천\n본문입니다.", sources={"aliexpress"})
        out = article_writer.extract_disclosure_first(body)
        assert out is not None
        assert "AliExpress" in out
        assert "수수료" in out
        assert "쿠팡 파트너스" not in out

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


class TestApplyDisclosure:
    """POLICY §2-2/§2-3 disclosure 자동 삽입 — 결과가 validator.disclosure를 통과해야 함."""

    def test_inserted_body_passes_validator(self) -> None:
        from validator.disclosure import check_disclosure

        body = "## 1. 누구를 위한 가이드\n원룸 자취 첫 살림 추천.\n\n## 2. 추천 상품\n..."
        out = article_writer.apply_disclosure(body)
        ok, report = check_disclosure(out)
        assert ok, report
        # 원본 본문 보존
        assert "누구를 위한 가이드" in out

    def test_first_keywords_in_head(self) -> None:
        out = article_writer.apply_disclosure("본문 시작\n\n본문 끝")
        assert all(k in out[:200] for k in article_writer.DISCLOSURE_FIRST_KEYWORDS)

    def test_footer_keywords_in_tail(self) -> None:
        out = article_writer.apply_disclosure("본문")
        assert all(k in out[-800:] for k in article_writer.DISCLOSURE_FOOTER_KEYWORDS)

    def test_idempotent_no_duplicate(self) -> None:
        once = article_writer.apply_disclosure("본문 내용")
        twice = article_writer.apply_disclosure(once)
        assert once == twice  # 이미 삽입돼 있으면 중복 추가 안 함
        # 첫머리 문구가 두 번 들어가지 않음
        assert twice.count("일정 수수료를 제공받습니다") == 1

    def test_aliexpress_source_uses_ali_disclosure(self) -> None:
        """알리 상품 글: 첫머리에 AliExpress 명시, 쿠팡 미명시 (공정위 정확성)."""
        from validator.disclosure import check_disclosure

        # 본문을 충분히 길게 — 짧으면 푸터(쿠팡 포함)가 head 범위로 끼어듦
        out = article_writer.apply_disclosure(
            "# 제목\n" + "본문 내용. " * 100, sources={"aliexpress"}
        )
        head = out[:200]
        assert "AliExpress" in head
        assert "쿠팡 파트너스" not in head  # 알리 글 첫머리엔 쿠팡 명시 안 함
        ok, rpt = check_disclosure(out)  # 푸터는 둘 다라 게이트 통과
        assert ok, rpt

    def test_both_sources_uses_both_disclosure(self) -> None:
        out = article_writer.apply_disclosure("본문", sources={"aliexpress", "coupang"})
        assert "쿠팡 파트너스" in out[:300] and "AliExpress" in out[:300]

    def test_first_disclosure_for_selection(self) -> None:
        fd = article_writer.first_disclosure_for
        assert fd({"aliexpress"}) == article_writer.FIRST_DISCLOSURE_ALI
        assert fd({"coupang"}) == article_writer.FIRST_DISCLOSURE_COUPANG
        assert fd(None) == article_writer.FIRST_DISCLOSURE_COUPANG  # 불명→쿠팡 기본
        assert fd({"aliexpress", "coupang"}) == article_writer.FIRST_DISCLOSURE_BOTH

    def test_nonstandard_model_disclosure_gets_standard(self) -> None:
        """모델이 임의로 쓴 비표준 disclosure(키워드는 있음)여도 표준 문구를 삽입 (POLICY §2-4)."""
        # 키워드(쿠팡 파트너스·수수료)는 있지만 표준 문구는 아님 — 라이브에서 실제 발생한 케이스
        model_written = "[광고 공시] 본 페이지는 쿠팡 파트너스 활동으로 일정 수수료를 받습니다.\n\n# 제목\n본문."
        out = article_writer.apply_disclosure(model_written)
        assert article_writer.FIRST_DISCLOSURE.split(".")[0] in out  # 표준 첫머리 삽입됨
        assert "일정 수수료를 제공받습니다" in out[:300]


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


def _insert_product(
    conn: sqlite3.Connection,
    spid: str,
    *,
    source: str = "aliexpress",
    price: int = 10000,
) -> int:
    """products 테이블에 최소 필드 상품 1건 삽입 → id 반환 (link 테스트용)."""
    conn.execute(
        "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
        "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
        "VALUES (?, ?, ?, 'KRW', ?, ?, ?, 'honsalim', "
        "datetime('now'), datetime('now'), datetime('now'))",
        (
            source,
            str(spid),
            f"상품 {spid}",
            price,
            f"https://s.click.aliexpress.com/{spid}",
            f"ali-{spid}",
        ),
    )
    conn.commit()
    return int(
        conn.execute(
            "SELECT id FROM products WHERE source_product_id = ?", (str(spid),)
        ).fetchone()[0]
    )


def _published_article(conn: sqlite3.Connection, slug: str = "a1") -> int:
    did = _approved_draft_with_enrichment(conn)
    fields = {**_valid_article_fields(), "slug": slug}
    return article_writer.promote_to_article(conn, did, fields)


class TestUniqueArticleSlug:
    def test_returns_base_when_free(self) -> None:
        conn = _seeded_db()
        assert article_writer.unique_article_slug(conn, "homeoffice-50") == "homeoffice-50"

    def test_appends_suffix_on_collision(self) -> None:
        conn = _seeded_db()
        _published_article(conn, slug="homeoffice-50")
        assert article_writer.unique_article_slug(conn, "homeoffice-50") == "homeoffice-50-2"


class TestLinkArticleProducts:
    """featured(enriched_payload['products']) → article_products 연결 (DB §5)."""

    def test_links_featured_to_products_in_order(self) -> None:
        conn = _seeded_db()
        _insert_product(conn, "111")
        _insert_product(conn, "222")
        aid = _published_article(conn)
        featured = [
            {"source": "aliexpress", "source_product_id": "111"},
            {"source": "aliexpress", "source_product_id": "222"},
        ]
        linked, skipped = article_writer.link_article_products(conn, aid, featured)
        assert (linked, skipped) == (2, 0)
        rows = conn.execute(
            "SELECT display_order FROM article_products WHERE article_id = ? "
            "ORDER BY display_order",
            (aid,),
        ).fetchall()
        assert [r[0] for r in rows] == [0, 1]

    def test_skips_products_not_in_table(self) -> None:
        conn = _seeded_db()
        _insert_product(conn, "111")
        aid = _published_article(conn)
        featured = [
            {"source": "aliexpress", "source_product_id": "111"},
            {"source": "aliexpress", "source_product_id": "999"},  # products에 없음
        ]
        linked, skipped = article_writer.link_article_products(conn, aid, featured)
        assert (linked, skipped) == (1, 1)

    def test_skips_entry_without_source_product_id(self) -> None:
        conn = _seeded_db()
        aid = _published_article(conn)
        linked, skipped = article_writer.link_article_products(
            conn, aid, [{"source": "aliexpress"}]
        )
        assert (linked, skipped) == (0, 1)

    def test_replace_true_is_idempotent(self) -> None:
        conn = _seeded_db()
        _insert_product(conn, "111")
        aid = _published_article(conn)
        featured = [{"source": "aliexpress", "source_product_id": "111"}]
        article_writer.link_article_products(conn, aid, featured)
        article_writer.link_article_products(conn, aid, featured)  # 재게시
        cnt = conn.execute(
            "SELECT COUNT(*) FROM article_products WHERE article_id = ?", (aid,)
        ).fetchone()[0]
        assert cnt == 1  # PK 충돌·중복 없이 1건 유지

    def test_matches_by_source_when_provided(self) -> None:
        """같은 source_product_id라도 source 불일치면 매칭 안 됨."""
        conn = _seeded_db()
        _insert_product(conn, "111", source="aliexpress")
        aid = _published_article(conn)
        featured = [{"source": "coupang", "source_product_id": "111"}]
        linked, skipped = article_writer.link_article_products(conn, aid, featured)
        assert (linked, skipped) == (0, 1)


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
