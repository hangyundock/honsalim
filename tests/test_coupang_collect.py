"""collector.coupang 회귀 — 딥링크 파싱 + yml 로딩 + 매핑 + dry_run 안전 + 적재·연결.

API 미사용(수동 부트스트랩)이라 HTTP 모킹 없이 실제 yml + 실제 마이그레이션(in-memory)으로 검증.
"""

from __future__ import annotations

import sqlite3

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

from collector import coupang
from common import db as _db


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO categories (slug, name_ko, status) VALUES ('monitor-arm', '모니터암', 'published')"
    )
    conn.commit()
    return conn


class TestExtractShortcode:
    def test_basic(self) -> None:
        assert coupang.extract_shortcode("https://link.coupang.com/a/ehtwmQRZAG") == "ehtwmQRZAG"

    def test_strips_query_and_trailing(self) -> None:
        assert coupang.extract_shortcode("https://link.coupang.com/a/ABC123?foo=bar") == "ABC123"
        assert coupang.extract_shortcode("https://link.coupang.com/a/ABC123/") == "ABC123"

    def test_non_matching_returns_none(self) -> None:
        assert coupang.extract_shortcode("https://www.coupang.com/vp/products/123") is None
        assert coupang.extract_shortcode("") is None


class TestLoadSources:
    def test_monitor_arm_defined(self) -> None:
        # yml 내용에 독립적 — 모니터암 쿠팡 상품이 1개 이상, 구조가 유효한지만 검증
        specs = coupang.load_coupang_sources(slug="monitor-arm")
        assert len(specs) >= 1
        for s in specs:
            assert s.category == "monitor-arm"
            assert s.code  # 딥링크 코드 추출됨
            assert s.coupang_url.startswith("https://link.coupang.com/a/")
        assert any(s.image_url for s in specs)  # 이미지 그리드용 상품 존재

    def test_slug_filter(self) -> None:
        assert coupang.load_coupang_sources(slug="no-such-cat") == []
        assert all(
            s.category == "monitor-arm" for s in coupang.load_coupang_sources(slug="monitor-arm")
        )


class TestMap:
    def test_map_fields(self) -> None:
        spec = coupang.CoupangSpec(
            category="monitor-arm",
            name="테스트 모니터암",
            coupang_url="https://link.coupang.com/a/XYZ",
            code="XYZ",
            price_krw=20990,
            original_price_krw=33400,
            note="로켓배송",
        )
        row = coupang.map_coupang_product(spec)
        assert row["source"] == "coupang"
        assert row["source_product_id"] == "XYZ"
        assert row["deeplink_slug"] == "cp-XYZ"
        assert row["deeplink_url"].endswith("XYZ")
        assert row["affiliate_tag"] == coupang.COUPANG_PARTNER_TAG
        # 할인율 = 정가>판매가일 때 계산: (33400-20990)/33400 ≈ 37%
        assert row["discount_pct"] == 37
        # 가짜 신호 금지 + 이미지 미저장(§9 함정3)
        assert row["sales_volume"] is None
        assert row["evaluate_rate"] is None
        assert row["image_url_external"] is None

    def test_no_discount_when_no_original(self) -> None:
        spec = coupang.CoupangSpec(
            category="x", name="n", coupang_url="u", code="C", price_krw=10000
        )
        assert coupang.map_coupang_product(spec)["discount_pct"] is None

    def test_image_url_flows_through(self) -> None:
        # 쿠팡 링크생성기가 제공한 공식 이미지 URL이 image_url_external로 흐름(hotlink·세션 #24)
        img = "https://ads-partners.coupang.com/banners/abc.jpg?w=200"
        spec = coupang.CoupangSpec(category="x", name="n", coupang_url="u", code="C", image_url=img)
        assert coupang.map_coupang_product(spec)["image_url_external"] == img

    def test_image_empty_is_none(self) -> None:
        # 이미지 미제공 시 None(빈 값) — 카드는 텍스트로 graceful degrade
        spec = coupang.CoupangSpec(category="x", name="n", coupang_url="u", code="C")
        assert coupang.map_coupang_product(spec)["image_url_external"] is None


class TestCollect:
    def test_dry_run_no_db_write(self) -> None:
        conn = _conn()
        res = coupang.collect_coupang(conn, "monitor-arm", dry_run=True)
        assert res.dry_run is True
        assert res.linked == 0
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
        conn.close()

    def test_live_upsert_and_link(self) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()
        n = len(coupang.load_coupang_sources(slug="monitor-arm"))
        res = coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        assert res.linked == n
        assert res.upserted == n
        # products: 전부 source='coupang' + cp- slug(=/go/ 라우팅 가능)
        cnt = conn.execute("SELECT COUNT(*) FROM products WHERE source='coupang'").fetchone()[0]
        assert cnt == n
        slugs = [
            r[0] for r in conn.execute("SELECT deeplink_slug FROM products WHERE source='coupang'")
        ]
        assert slugs and all(s.startswith("cp-") for s in slugs)
        conn.close()

    def test_idempotent_relink(self) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()
        n = len(coupang.load_coupang_sources(slug="monitor-arm"))
        coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        coupang.collect_coupang(conn, "monitor-arm", dry_run=False)  # 재적재
        # 중복 행 없이 n건 유지(ON CONFLICT)
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM category_products cp JOIN products p ON p.id=cp.product_id "
                "WHERE p.source='coupang'"
            ).fetchone()[0]
            == n
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM products WHERE source='coupang'").fetchone()[0] == n
        )
        conn.close()

    def test_prune_removes_stale(self) -> None:
        # 정합화: yml에 없는 옛 쿠팡 연결은 재적재 시 제거(idempotent·§0)
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()
        cid = conn.execute("SELECT id FROM categories WHERE slug='monitor-arm'").fetchone()[0]
        conn.execute(
            "INSERT INTO products (source, source_product_id, name, deeplink_url, deeplink_slug, "
            "affiliate_tag, created_at, updated_at, last_seen_at) VALUES "
            "('coupang','OLD','옛 쿠팡 상품','https://link.coupang.com/a/OLD','cp-OLD','AF',"
            "datetime('now'),datetime('now'),datetime('now'))"
        )
        pid = conn.execute("SELECT id FROM products WHERE source_product_id='OLD'").fetchone()[0]
        conn.execute(
            "INSERT INTO category_products (category_id, product_id, tier, is_featured) "
            "VALUES (?,?,NULL,0)",
            (cid, pid),
        )
        conn.commit()
        res = coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        assert res.pruned >= 1
        # 옛 링크(OLD)는 제거됨
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM category_products WHERE product_id=?", (pid,)
            ).fetchone()[0]
            == 0
        )
        conn.close()

    def test_skips_unknown_category(self) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON")
        for m in _db.discover_migrations():
            conn.executescript(m.path.read_text(encoding="utf-8"))
        conn.commit()
        # monitor-arm 카테고리 미시드 → 적재는 되나 연결은 skip
        res = coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        assert res.linked == 0
        assert "monitor-arm" in res.skipped_no_category
        conn.close()


class TestGuardAgainstAliPipeline:
    """★세션 #24 재발방지 가드 — 알리 재수집/재빌드 리셋이 쿠팡 링크를 지우지 않아야 한다(§0)."""

    def test_ali_recollect_preserves_coupang_link(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        if pytest is None:  # pragma: no cover
            return
        from collector import category_collect as cc

        conn = _conn()
        # 1) 쿠팡 상품 적재·연결 (monitor-arm)
        n = len(coupang.load_coupang_sources(slug="monitor-arm"))
        coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        assert (
            conn.execute("SELECT COUNT(*) FROM products WHERE source='coupang'").fetchone()[0] == n
        )

        # 2) 알리 재수집(모킹) — monitor-arm 카탈로그를 알리 상품으로 재구성
        def fake_query(q: str, **kw):  # type: ignore[no-untyped-def]
            from collector import aliexpress as ali

            items = [
                {
                    "source": "aliexpress",
                    "source_product_id": "A1",
                    "name": "싱글 모니터암 데스크 마운트",
                    "price_krw": 20000,
                    "deeplink_url": "https://s.click.aliexpress.com/A1",
                    "deeplink_slug": "ali-A1",
                    "affiliate_tag": "honsallim",
                    "availability": "unknown",
                }
            ]
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)
        cc.collect_category(conn, "monitor-arm", dry_run=False, sleep=0)

        # 3) 쿠팡 링크 보존 + 알리 카탈로그 신규 — 둘 다 존재
        coup = conn.execute(
            "SELECT COUNT(*) FROM category_products cp JOIN products p ON p.id=cp.product_id "
            "WHERE p.source='coupang'"
        ).fetchone()[0]
        ali_cnt = conn.execute(
            "SELECT COUNT(*) FROM category_products cp JOIN products p ON p.id=cp.product_id "
            "WHERE p.source='aliexpress'"
        ).fetchone()[0]
        assert coup == n, "쿠팡 링크가 알리 재수집에 지워짐 (가드 실패)"
        assert ali_cnt >= 1
        conn.close()

    def test_featured_reset_preserves_coupang(self) -> None:
        """category_page_builder 6선 리셋(_RESET_FEATURED_SQL)이 쿠팡 연결을 보존(알리 한정)."""
        if pytest is None:  # pragma: no cover
            return
        from enricher import category_page_builder as cpb

        conn = _conn()
        n = len(coupang.load_coupang_sources(slug="monitor-arm"))
        coupang.collect_coupang(conn, "monitor-arm", dry_run=False)
        cid = conn.execute("SELECT id FROM categories WHERE slug='monitor-arm'").fetchone()[0]
        # 알리 6선 리셋 실행 — 쿠팡 행은 건드리면 안 됨
        conn.execute(cpb._RESET_FEATURED_SQL, (cid,))
        conn.commit()
        cnt = conn.execute(
            "SELECT COUNT(*) FROM category_products cp JOIN products p ON p.id=cp.product_id "
            "WHERE p.source='coupang'"
        ).fetchone()[0]
        assert cnt == n, "쿠팡 링크가 6선 리셋에 지워짐 (가드 실패)"
        conn.close()


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
