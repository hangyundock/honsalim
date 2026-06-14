"""writer.article_guardrail — 발행된 글 사후 점검·자동 비공개 (세션 #29 B-i 발행후 안전망).

무인 B에서 나쁜 글(깨진 제휴·off-target 상품)을 사람 없이 자동 적발·비공개하는지 실증.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from common import db
from writer import article_guardrail


def _make_published_article(
    conn: object, slug: str, products: list[tuple[str, int | None]], keyword: str | None = None
) -> int:
    """published 글 + 상품 연결(+선택 키워드 추적) 생성.

    products=[(name, price_or_None)]. 딥링크·트래킹태그는 항상 유효(NOT NULL 제약).
    price=None이면 무결성 미달 케이스. keyword 주면 drafts.promoted_article_id로 추적 연결.
    """
    sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]  # type: ignore[attr-defined]
    cur = conn.execute(  # type: ignore[attr-defined]
        "INSERT INTO articles (slug, scenario_id, title, summary, body_md, body_html, "
        "meta_description, schema_jsonld, disclosure_first, status, published_at, "
        "content_hash, truth_check_passed_at, user_approved_at) "
        "VALUES (?, ?, 'T', 'S', 'B', '<p>B</p>', 'M', '{}', 'D', 'published', "
        "'2026-06-14T00:00:00Z', 'h', '2026-06-14T00:00:00Z', '2026-06-14T00:00:00Z')",
        (slug, sid),
    )
    aid = int(cur.lastrowid)
    for i, (name, price) in enumerate(products):
        spid = f"{slug}-p{i}"
        pcur = conn.execute(  # type: ignore[attr-defined]
            "INSERT INTO products (source, source_product_id, name, currency, price_krw, "
            "deeplink_url, deeplink_slug, affiliate_tag, created_at, updated_at, last_seen_at) "
            "VALUES ('aliexpress', ?, ?, 'KRW', ?, ?, ?, 'honsalim', "
            "datetime('now'), datetime('now'), datetime('now'))",
            (spid, name, price, f"https://s.click.aliexpress.com/{spid}", f"ali-{spid}"),
        )
        pid = int(pcur.lastrowid)
        conn.execute(  # type: ignore[attr-defined]
            "INSERT INTO article_products (article_id, product_id, display_order) VALUES (?, ?, ?)",
            (aid, pid, i),
        )
    if keyword is not None:
        from writer import keyword_queue as kq

        kid = kq.get_or_create(conn, keyword, channel="ali")  # type: ignore[arg-type]
        conn.execute(  # type: ignore[attr-defined]
            "INSERT INTO drafts (scenario_id, status, keyword_id, promoted_article_id) "
            "VALUES (?, 'published', ?, ?)",
            (sid, kid, aid),
        )
    conn.commit()  # type: ignore[attr-defined]
    return aid


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    db.migrate(db_path=p)
    db.seed(db_path=p)
    return p


class TestCheck:
    def test_clean_article_passes(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(
                conn, "clean", [("인체공학 사무용 의자", 80000)], keyword="컴퓨터의자"
            )
            gr = article_guardrail.check(conn, "clean")
            assert gr.passed
            assert gr.checks["integrity"] is True
            assert gr.checks.get("relevance") is True
        finally:
            conn.close()

    def test_no_products_fails_integrity(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(conn, "empty", [])
            gr = article_guardrail.check(conn, "empty")
            assert not gr.passed
            assert gr.checks["integrity"] is False
        finally:
            conn.close()

    def test_null_price_fails_integrity(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(conn, "noprice", [("의자", None)])
            gr = article_guardrail.check(conn, "noprice")
            assert not gr.passed
            assert gr.checks["integrity"] is False
        finally:
            conn.close()

    def test_offtarget_products_fail_relevance(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            # 가격·딥링크는 정상(무결성 통과) → 관련성만 실패하도록 격리
            _make_published_article(
                conn, "offtarget", [("화장 드레싱 의자", 50000)], keyword="컴퓨터의자"
            )
            gr = article_guardrail.check(conn, "offtarget")
            assert not gr.passed
            assert gr.checks["integrity"] is True
            assert gr.checks["relevance"] is False
        finally:
            conn.close()

    def test_no_keyword_skips_relevance(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(conn, "nokw", [("의자", 50000)])  # 키워드 추적 없음
            gr = article_guardrail.check(conn, "nokw")
            assert gr.passed
            assert "relevance" not in gr.checks  # 관련성 판단 보류
        finally:
            conn.close()


class TestMonitor:
    def test_auto_unpublish_takes_down_failing(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(
                conn, "good", [("인체공학 사무용 의자", 80000)], keyword="컴퓨터의자"
            )
            _make_published_article(
                conn, "bad", [("화장 드레싱 의자", 50000)], keyword="컴퓨터의자"
            )
            res = article_guardrail.monitor(conn, auto_unpublish=True)
            assert res["checked"] == 2
            assert "bad" in res["unpublished"]
            assert "good" not in res["unpublished"]
            assert (
                conn.execute("SELECT status FROM articles WHERE slug='bad'").fetchone()[0]
                == "unpublished"
            )
            assert (
                conn.execute("SELECT status FROM articles WHERE slug='good'").fetchone()[0]
                == "published"
            )
        finally:
            conn.close()

    def test_report_only_does_not_unpublish(self, db_path: Path) -> None:
        conn = db.connect(db_path)
        try:
            _make_published_article(
                conn, "bad2", [("화장 드레싱 의자", 50000)], keyword="컴퓨터의자"
            )
            res = article_guardrail.monitor(conn, auto_unpublish=False)
            assert any(f["slug"] == "bad2" for f in res["failed"])
            assert res["unpublished"] == []
            assert (
                conn.execute("SELECT status FROM articles WHERE slug='bad2'").fetchone()[0]
                == "published"
            )
        finally:
            conn.close()
