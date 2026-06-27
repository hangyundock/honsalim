"""category_collect 회귀 — yml 로딩 + dry_run 안전 + (모킹) 수집·정제·티어·연결·정가저장.

라이브 HTTP는 호출하지 않는다(ali.query_products를 모킹). 실제 마이그레이션을 in-memory에
적용해 categories/category_products/products 스키마를 그대로 검증한다.
"""

from __future__ import annotations

import sqlite3
from typing import Any

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

from collector import aliexpress as ali
from collector import category_collect as cc
from common import db as _db


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for m in _db.discover_migrations():
        conn.executescript(m.path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO categories (slug, name_ko, status) VALUES ('office-chair', '사무용 의자', 'draft')"
    )
    conn.commit()
    return conn


def _item(pid: str, name: str, **extra: Any) -> dict[str, Any]:
    row = {
        "source": "aliexpress",
        "source_product_id": pid,
        "name": name,
        "price_krw": 50000,
        "deeplink_url": f"https://s.click.aliexpress.com/{pid}",
        "deeplink_slug": f"ali-{pid}",
        "affiliate_tag": "TRACK",
        "availability": "unknown",
    }
    row.update(extra)
    return row


class TestLoadSources:
    def test_office_chair_and_desk_defined(self) -> None:
        s = cc.load_sources()
        assert "office-chair" in s and "desk" in s
        oc = s["office-chair"]
        assert "의자" in oc.require_any
        assert set(oc.tiers) == {"budget", "premium"}
        assert oc.tiers["budget"].q == "office chair"
        assert oc.tiers["premium"].min_price == 100000

    def test_laptop_stand_uses_require_all_groups(self) -> None:
        # 세션 #19: '타입+대상' 동시 충족 그룹이 yml에서 파싱되는지
        s = cc.load_sources()
        assert "laptop-stand" in s
        ls = s["laptop-stand"]
        assert len(ls.require_all) == 2  # [노트북 계열] + [거치대 계열]
        assert any("노트북" in g for g in ls.require_all)
        assert any("거치대" in g for g in ls.require_all)

    def test_corrupted_yml_returns_empty_not_crash(self, tmp_path: Any) -> None:
        """★§0 방어(#36): 깨진 yml은 크래시(가드레일 전체 마비) 대신 빈 dict로 폴백한다."""
        p = tmp_path / "broken.yml"
        p.write_text("categories:\n  x: [unclosed\n    : : :\n", encoding="utf-8")
        assert cc.load_sources(path=p) == {}  # 예외 전파 없이 안전 폴백


class TestDryRun:
    def test_dry_run_no_db_write(self) -> None:
        conn = _conn()
        res = cc.collect_category(conn, "office-chair", dry_run=True)
        assert res.dry_run is True
        assert res.linked == 0
        assert len(res.terms) == 2
        assert conn.execute("SELECT COUNT(*) FROM category_products").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0

    def test_unknown_slug_raises(self) -> None:
        conn = _conn()
        try:
            cc.collect_category(conn, "no-such-cat", dry_run=True)
            raise AssertionError("KeyError 기대")
        except KeyError:
            pass


class TestLiveMocked:
    def test_collect_filters_links_and_persists_discount(self, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            if "ergonomic" in q:  # premium 티어
                items = [
                    _item(
                        "P1",
                        "인체공학 사무용 의자",
                        price_krw=150000,
                        original_price_krw=200000,
                        discount_pct=25,
                    ),
                    _item("X1", "의자 발받침 쿠션", price_krw=120000),  # '발받침' exclude
                ]
            else:  # budget 티어
                items = [
                    _item("P2", "메쉬 컴퓨터 의자", price_krw=50000),
                    _item("Z1", "노트북 거치대", price_krw=40000),  # '의자' 미포함 → 제외
                ]
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        res = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        # P1(premium)·P2(budget) 통과. X1(발받침 exclude)·Z1(의자 미포함) 제외.
        assert res.relevant == 2
        assert res.linked == 2
        rows = conn.execute(
            "SELECT p.source_product_id, cp.tier FROM category_products cp "
            "JOIN products p ON p.id = cp.product_id ORDER BY cp.display_order"
        ).fetchall()
        assert {r[0]: r[1] for r in rows} == {"P2": "budget", "P1": "premium"}
        # 정가/할인 영속화 (products_store 정합)
        op = conn.execute(
            "SELECT original_price_krw, discount_pct FROM products WHERE source_product_id = 'P1'"
        ).fetchone()
        assert tuple(op) == (200000, 25)

    def test_vision_gate_drops_offtarget(self, monkeypatch: Any) -> None:
        """세션 #35: vision_gate ON이면 키워드 필터는 통과해도 비전이 카테고리 불일치를 드롭."""
        if pytest is None:  # pragma: no cover
            return
        from collector import vision_relevance as vr

        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            if "ergonomic" in q:  # premium — 키워드는 통과('의자')하나 비전이 드롭할 항목
                items = [_item("D1", "의자 ZZDROP", image_url_external="http://x/d1.jpg")]
            else:  # budget — 정상
                items = [_item("P2", "메쉬 컴퓨터 의자", image_url_external="http://x/p2.jpg")]
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)
        # vision_gate ON + 네트워크/Anthropic 모킹 (a[4]=prompt에 상품명 포함 → ZZDROP면 탈락)
        monkeypatch.setattr(
            "common.settings.get",
            lambda key, default=None: {"vision_gate": True, "vision_gate_cap": 40}.get(
                key, default
            ),
        )
        monkeypatch.setattr(vr, "_resolve_key", lambda k: "test-key")  # 키 있다고 가정
        monkeypatch.setattr(
            vr, "_fetch_image", lambda url, timeout=15.0: (b"\xff\xd8\xff", "image/jpeg")
        )
        monkeypatch.setattr(
            vr,
            "_call_vision",
            lambda *a, **k: (
                '{"ok": false, "reason": "딴거"}'
                if "ZZDROP" in a[4]
                else '{"ok": true, "reason": "ok"}'
            ),
        )

        res = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        assert res.vision_dropped == 1
        kept = {
            r[0]
            for r in conn.execute(
                "SELECT p.source_product_id FROM category_products cp "
                "JOIN products p ON p.id = cp.product_id"
            ).fetchall()
        }
        assert "P2" in kept and "D1" not in kept

    def test_dedup_same_product_across_tiers(self, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            # 동일 제품 P1이 두 티어 검색에 모두 등장
            return ali.QueryResult(
                dry_run=False,
                request={},
                products=[_item("P1", "메쉬 사무용 의자")],
                resp_code="200",
            )

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        res = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        assert res.linked == 1  # 중복 제외 — 한 번만 연결
        assert conn.execute("SELECT COUNT(*) FROM category_products").fetchone()[0] == 1

    def test_recollect_removes_stale_catalog(self, monkeypatch: Any) -> None:
        """재수집 정합화(세션 #19): 이전엔 잡혔다가 이번엔 안 잡힌 카탈로그 상품을 자동 제거.

        필터를 강화해 재수집하면 옛 오염(예 캠핑 테이블)이 idempotent하게 청소되는지 검증.
        """
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()
        state = {"run": 0}

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            items = [_item("P1", "메쉬 사무용 의자")]
            if state["run"] == 0:
                items.append(_item("P2", "가죽 사무용 의자"))  # 1차에만 등장 → 2차에 제거되어야
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        r1 = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        assert r1.removed_stale == 0
        ids1 = {
            r[0]
            for r in conn.execute(
                "SELECT p.source_product_id FROM category_products cp "
                "JOIN products p ON p.id = cp.product_id"
            )
        }
        assert ids1 == {"P1", "P2"}

        state["run"] = 1
        r2 = cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        ids2 = {
            r[0]
            for r in conn.execute(
                "SELECT p.source_product_id FROM category_products cp "
                "JOIN products p ON p.id = cp.product_id"
            )
        }
        assert ids2 == {"P1"}  # 오염(P2) 청소됨 — 재수집 idempotent
        assert r2.removed_stale == 1

    def test_recollect_preserves_featured_picks(self, monkeypatch: Any) -> None:
        """정합화는 카탈로그(is_featured=0)만 비우고 추천 6선(is_featured=1)은 보존."""
        if pytest is None:  # pragma: no cover
            return
        conn = _conn()

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            return ali.QueryResult(
                dry_run=False,
                request={},
                products=[_item("P1", "메쉬 사무용 의자")],
                resp_code="200",
            )

        monkeypatch.setattr(cc.ali, "query_products", fake_query)
        monkeypatch.setattr("common.config.load_secrets", lambda *a, **k: None)

        cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)
        cid = conn.execute("SELECT id FROM categories WHERE slug='office-chair'").fetchone()[0]
        conn.execute("UPDATE category_products SET is_featured = 1 WHERE category_id = ?", (cid,))
        conn.commit()

        cc.collect_category(conn, "office-chair", dry_run=False, sleep=0)  # 재수집
        feat = conn.execute(
            "SELECT COUNT(*) FROM category_products WHERE category_id = ? AND is_featured = 1",
            (cid,),
        ).fetchone()[0]
        assert feat == 1  # 추천(featured) 보존 — ON CONFLICT가 is_featured를 내리지 않음


class TestSearchTiers:
    """search_tiers(세션 #30) — 키워드 경로가 재사용하는 영어 티어 검색(정제·DB 무관·순수)."""

    def test_uses_english_q_dedups_and_skips_filter(self, monkeypatch: Any) -> None:
        if pytest is None:  # pragma: no cover
            return
        queries: list[str] = []

        def fake_query(q: str, **kw: Any) -> ali.QueryResult:
            queries.append(q)
            if "ergonomic" in q:  # premium 티어
                items = [_item("P1", "인체공학 의자"), _item("DUP", "메쉬 의자")]
            else:  # budget 티어
                items = [_item("DUP", "메쉬 의자"), _item("X1", "폰케이스")]  # 중복·off-target
            return ali.QueryResult(dry_run=False, request={}, products=items, resp_code="200")

        monkeypatch.setattr(cc.ali, "query_products", fake_query)

        spec = cc.load_sources()["office-chair"]
        rows, received = cc.search_tiers(spec, sleep=0)
        # ① 한글 아닌 카테고리 영어 검색어로 검색
        assert set(queries) == {"office chair", "ergonomic office chair"}
        ids = [r["source_product_id"] for r in rows]
        # ② 티어 간 중복(DUP)은 한 번만
        assert ids.count("DUP") == 1
        # ③ 필터는 안 함 — off-target('폰케이스')도 원시로 포함(정제는 호출자 몫=keyword_relevance)
        assert set(ids) == {"P1", "DUP", "X1"}
        # ④ received는 수신 총건(중복 포함)
        assert received == 4


class TestAppendCategorySource:
    """append_category_source — provision-category 자동 yml 등록 (세션 #36 근본수정)."""

    def _spec(self) -> cc.CategorySpec:
        from collector.keyword_map import SearchTerm

        return cc.CategorySpec(
            slug="mini-rice-cooker",
            require_any=(),
            require_all=(),
            exclude_terms=("미니어처", "인형"),
            tiers={
                "budget": SearchTerm(q="mini rice cooker", min_price=15000, max_price=45000),
                "premium": SearchTerm(q="smart rice cooker", min_price=45001, max_price=120000),
            },
        )

    def test_appends_and_is_loadable(self, tmp_path: Any) -> None:
        p = tmp_path / "cs.yml"
        p.write_text(
            "categories:\n  office-chair:\n    require_any: [의자]\n    tiers:\n"
            '      budget: {q: "office chair", min: 1, max: 2}\n',
            encoding="utf-8",
        )
        added = cc.append_category_source("mini-rice-cooker", "미니 전기밥솥", self._spec(), path=p)
        assert added is True
        loaded = cc.load_sources(path=p)
        assert "office-chair" in loaded  # 기존 항목 보존
        assert "mini-rice-cooker" in loaded
        s = loaded["mini-rice-cooker"]
        assert s.require_any == ()  # #36: 관련성은 비전 게이트 전담
        assert "미니어처" in s.exclude_terms
        assert s.tiers["budget"].q == "mini rice cooker"
        assert s.tiers["premium"].max_price == 120000

    def test_idempotent_does_not_duplicate(self, tmp_path: Any) -> None:
        p = tmp_path / "cs.yml"
        p.write_text("categories:\n", encoding="utf-8")
        assert cc.append_category_source("mini-rice-cooker", "밥솥", self._spec(), path=p) is True
        # 두 번째 호출 = 사람 수정 보존(멱등) → 추가 안 함
        assert cc.append_category_source("mini-rice-cooker", "밥솥", self._spec(), path=p) is False
        assert p.read_text(encoding="utf-8").count("  mini-rice-cooker:") == 1

    def test_missing_file_returns_false(self, tmp_path: Any) -> None:
        assert (
            cc.append_category_source("x", "엑스", self._spec(), path=tmp_path / "nope.yml")
            is False
        )

    def test_sanitizes_yaml_breaking_terms(self, tmp_path: Any) -> None:
        """제외어·검색어의 yaml 특수문자를 걸러 깨진 yml(가드레일 전체 다운)을 막는다(#36·§0)."""
        from collector.keyword_map import SearchTerm

        spec = cc.CategorySpec(
            slug="x",
            require_any=(),
            require_all=(),
            exclude_terms=("정상어", "나쁜,콤마", "대[괄]호", "콜론:있음"),
            tiers={"budget": SearchTerm(q='quote"here', min_price=1, max_price=2)},
        )
        p = tmp_path / "cs.yml"
        p.write_text("categories:\n", encoding="utf-8")
        assert cc.append_category_source("x", "엑스", spec, path=p) is True
        loaded = cc.load_sources(path=p)  # 깨지지 않고 정상 로드돼야 함
        assert "x" in loaded
        joined = "".join(loaded["x"].exclude_terms)
        assert "정상어" in loaded["x"].exclude_terms
        assert not any(c in joined for c in ",[]:")  # 특수문자 제외어는 버려짐
        assert '"' not in loaded["x"].tiers["budget"].q  # q 따옴표 제거됨

    def test_idempotent_with_inline_comment(self, tmp_path: Any) -> None:
        """슬러그 줄에 인라인 주석(# ...)이 있어도 멱등 — 중복 추가 안 함(#36 리뷰 적발)."""
        p = tmp_path / "cs.yml"
        p.write_text(
            "categories:\n  mini-rice-cooker:  # 사람이 단 주석\n    require_any: []\n",
            encoding="utf-8",
        )
        assert cc.append_category_source("mini-rice-cooker", "밥솥", self._spec(), path=p) is False
        assert p.read_text(encoding="utf-8").count("  mini-rice-cooker:") == 1

    def test_q_backslash_stripped(self, tmp_path: Any) -> None:
        """q의 백슬래시를 제거해 yaml 이중따옴표 이스케이프(\\n 등) 오염을 막는다(#36 리뷰 적발)."""
        from collector.keyword_map import SearchTerm

        spec = cc.CategorySpec(
            slug="y",
            require_any=(),
            require_all=(),
            exclude_terms=(),
            tiers={"budget": SearchTerm(q="rice\\ncooker", min_price=1, max_price=2)},
        )
        p = tmp_path / "cs.yml"
        p.write_text("categories:\n", encoding="utf-8")
        assert cc.append_category_source("y", "와이", spec, path=p) is True
        q = cc.load_sources(path=p)["y"].tiers["budget"].q
        assert "\\" not in q and "\n" not in q  # 백슬래시·개행 제거됨

    def test_no_tmp_file_left_behind(self, tmp_path: Any) -> None:
        """원자적 쓰기 후 .tmp 잔여 파일이 남지 않는다."""
        p = tmp_path / "cs.yml"
        p.write_text("categories:\n", encoding="utf-8")
        cc.append_category_source("mini-rice-cooker", "밥솥", self._spec(), path=p)
        assert not (tmp_path / "cs.yml.tmp").exists()


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
