"""cli 키워드 큐 명령 회귀 테스트 (세션 #25) — add·generate(dry)·list·reject.

LLM·외부 API는 호출하지 않는 경로만 (dry_run·검증·반려·목록).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import ClassVar

import pytest

import cli
from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    conn.executescript(
        "INSERT INTO personas (slug, title_ko, description) VALUES ('jachi', '자취생', 'd');"
        "INSERT INTO scenarios (slug, title_ko, description, persona_id) VALUES ('s1', 'S', 'd', 1);"
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def migrated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    p = tmp_path / "honsalim.db"
    _make_db(p)
    monkeypatch.setattr(db, "DB_PATH", p)
    return p


def _ns(**kw: object) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def _add_kw(keyword: str = "자취생 전자레인지 추천", channel: str = "ali") -> int:
    return cli.cmd_keyword_add(
        _ns(
            keyword=keyword,
            channel=channel,
            slug=None,
            budget_min=None,
            budget_max=None,
            note=None,
            score=0.0,
        )
    )


class TestKeywordAdd:
    def test_add_pending(self, migrated_db: Path) -> None:
        assert _add_kw() == 0
        conn = db.connect(migrated_db)
        n = conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE status='pending'").fetchone()[0]
        conn.close()
        assert n == 1

    def test_bad_channel_returns_2(self, migrated_db: Path) -> None:
        assert _add_kw(channel="naver") == 2


class TestKeywordGenerateDryRun:
    def test_dry_run_no_writes(self, migrated_db: Path) -> None:
        _add_kw("원룸 가습기")
        conn = db.connect(migrated_db)
        kid = conn.execute("SELECT id FROM keyword_queue").fetchone()[0]
        scen_before = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        conn.close()

        rc = cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=True))
        assert rc == 0

        conn = db.connect(migrated_db)
        # dry_run은 쓰기 없음: 새 시나리오·draft 미생성, 상태 pending 유지
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == scen_before
        assert conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == 0
        assert (
            conn.execute("SELECT status FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0]
            == "pending"
        )
        conn.close()

    def test_missing_id_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_keyword_generate(_ns(id=999, page_size=20, dry_run=True)) == 2


class TestKeywordList:
    def test_list_prints(self, migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _add_kw("선풍기")
        rc = cli.cmd_keyword_list(_ns(status=None))
        assert rc == 0
        assert "선풍기" in capsys.readouterr().out

    def test_list_empty(self, migrated_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.cmd_keyword_list(_ns(status=None)) == 0
        assert "없음" in capsys.readouterr().out


class TestReject:
    def _draft(self, dbpath: Path, status: str) -> int:
        conn = db.connect(dbpath)
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (1, ?)", (status,))
        conn.commit()
        did = conn.execute("SELECT id FROM drafts ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.close()
        return int(did)

    def test_reject_validated(self, migrated_db: Path) -> None:
        did = self._draft(migrated_db, "validated")
        assert cli.cmd_reject(_ns(draft=did, note="테스트")) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT status FROM drafts WHERE id=?", (did,)).fetchone()[0] == "rejected"
        )
        conn.close()

    def test_reject_approved_two_step(self, migrated_db: Path) -> None:
        did = self._draft(migrated_db, "approved")
        assert cli.cmd_reject(_ns(draft=did, note=None)) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT status FROM drafts WHERE id=?", (did,)).fetchone()[0] == "rejected"
        )
        conn.close()

    def test_reject_missing_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_reject(_ns(draft=999, note=None)) == 2


class TestKeywordDelete:
    def _kid_with_draft(self, dbpath: Path, status: str) -> tuple[int, int]:
        """키워드 + 그 키워드에 연결된 draft(status) 생성. (keyword_id, draft_id) 반환."""
        _add_kw("컴퓨터의자")
        conn = db.connect(dbpath)
        kid = conn.execute("SELECT id FROM keyword_queue ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, keyword_id) VALUES (1, ?, ?)", (status, kid)
        )
        did = conn.execute("SELECT id FROM drafts ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.execute("UPDATE keyword_queue SET status='drafted' WHERE id=?", (kid,))
        conn.commit()
        conn.close()
        return int(kid), int(did)

    def test_delete_keyword_and_unpublished_draft(self, migrated_db: Path) -> None:
        kid, did = self._kid_with_draft(migrated_db, "validated")
        assert cli.cmd_keyword_delete(_ns(id=kid)) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0] == 0
        )
        assert conn.execute("SELECT COUNT(*) FROM drafts WHERE id=?", (did,)).fetchone()[0] == 0
        conn.close()

    def test_delete_blocked_when_published(self, migrated_db: Path) -> None:
        kid, did = self._kid_with_draft(migrated_db, "published")
        assert cli.cmd_keyword_delete(_ns(id=kid)) == 2  # 라이브 보호 — 차단
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0] == 1
        )
        assert conn.execute("SELECT COUNT(*) FROM drafts WHERE id=?", (did,)).fetchone()[0] == 1
        conn.close()

    def test_delete_removes_derived_scenario(self, migrated_db: Path) -> None:
        """세션 #35: 키워드 삭제 시 파생 시나리오도 함께 삭제(세팅에 쓰레기 카드 잔존 방지)."""
        from writer import keyword_queue as kq

        _add_kw("리클라이너의자")
        conn = db.connect(migrated_db)
        kid = conn.execute("SELECT id FROM keyword_queue ORDER BY id DESC LIMIT 1").fetchone()[0]
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, keyword_id) VALUES (?, 'validated', ?)",
            (sid, kid),
        )
        conn.commit()
        conn.close()

        assert cli.cmd_keyword_delete(_ns(id=kid)) == 0
        conn = db.connect(migrated_db)
        assert conn.execute("SELECT COUNT(*) FROM scenarios WHERE id=?", (sid,)).fetchone()[0] == 0
        conn.close()

    def test_delete_keeps_scenario_referenced_by_article(self, migrated_db: Path) -> None:
        """글(article)이 걸린 시나리오는 키워드 삭제로도 지우지 않는다(라이브/잔존 글 보호·FK 안전)."""
        from writer import keyword_queue as kq

        _add_kw("책상의자")
        conn = db.connect(migrated_db)
        kid = conn.execute("SELECT id FROM keyword_queue ORDER BY id DESC LIMIT 1").fetchone()[0]
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        conn.execute(
            "INSERT INTO articles (slug, scenario_id, title, summary, body_md, body_html, "
            "meta_description, schema_jsonld, disclosure_first, content_hash, "
            "truth_check_passed_at, user_approved_at, status) VALUES "
            "(?, ?, 'T', 's', 'm', 'h', 'd', '{}', 'disc', 'hash', "
            "'2026-01-01', '2026-01-01', 'unpublished')",
            ("kw-x", sid),
        )
        conn.commit()
        conn.close()

        assert cli.cmd_keyword_delete(_ns(id=kid)) == 0
        conn = db.connect(migrated_db)
        # 시나리오 보존(글이 참조) — 키워드만 삭제됨
        assert conn.execute("SELECT COUNT(*) FROM scenarios WHERE id=?", (sid,)).fetchone()[0] == 1
        assert (
            conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0] == 0
        )
        conn.close()

    def test_delete_missing_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_keyword_delete(_ns(id=999)) == 2

    def test_delete_keyword_without_drafts(self, migrated_db: Path) -> None:
        _add_kw("선풍기")
        conn = db.connect(migrated_db)
        kid = conn.execute("SELECT id FROM keyword_queue ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.close()
        assert cli.cmd_keyword_delete(_ns(id=kid)) == 0
        conn = db.connect(migrated_db)
        assert (
            conn.execute("SELECT COUNT(*) FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0] == 0
        )
        conn.close()


class TestParserRegistration:
    def test_new_commands_registered(self) -> None:
        parser = cli.build_parser()
        # subparsers 액션에서 등록된 명령 이름 수집
        names: set[str] = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                names |= set(action.choices)
        assert {
            "keyword-add",
            "keyword-generate",
            "keyword-list",
            "keyword-delete",
            "keyword-requeue",
            "reject",
        } <= names


class TestGatherCandidatesHybrid:
    """Phase A — 쿠팡(수동) + 알리(데이터) 결합 후보 (세션 #28)."""

    def test_coupang_only_channel_no_ali(self, migrated_db: Path) -> None:
        from collector import coupang_manual as cm
        from writer import keyword_queue as kq

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "무선청소기", channel="coupang")
        cm.add_to_keyword(
            conn, kid, cm.build_manual_product("쿠팡청소기", "https://link.coupang.com/a/X")
        )
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, _ = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        assert [c["source"] for c in cands] == ["coupang"]  # 쿠팡 단독 — 알리 호출 없음

    def test_combines_coupang_and_ali(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from types import SimpleNamespace

        import collector.aliexpress as ali
        from collector import category_collect as cc
        from collector import coupang_manual as cm
        from common import config as cfg
        from writer import keyword_queue as kq

        ali_prod = {
            "source": "aliexpress",
            "source_product_id": "A1",
            "name": "알리 메쉬 사무용 의자",  # office-chair 적합성 통과(의자 포함·제외어 없음)
            "deeplink_url": "https://s.click.ali/A1",
            "deeplink_slug": "ali-A1",
            "affiliate_tag": "honsallim",
            "price_krw": 89000,
        }
        monkeypatch.setattr(
            ali, "query_products", lambda *a, **k: SimpleNamespace(products=[ali_prod])
        )
        monkeypatch.setattr(cfg, "load_secrets", lambda: None)
        monkeypatch.setattr(
            cc.time, "sleep", lambda *a, **k: None
        )  # 티어 간 sleep 제거(빠른 테스트)

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "컴퓨터의자", channel="both")  # office-chair 매핑 → 영어검색
        cm.add_to_keyword(
            conn, kid, cm.build_manual_product("쿠팡의자", "https://link.coupang.com/a/X")
        )
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, _ = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        sources = {c["source"] for c in cands}
        assert sources == {"coupang", "aliexpress"}  # 결합(하이브리드)

    def test_mapped_keyword_searches_via_category_english(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★세션 #30 근본수정 회귀: 알리 검색어 = 카테고리 영어 티어(한글 키워드 직접검색 금지).

        세션 #29 라이브가 적발한 결함(한글 '컴퓨터의자'로 알리 검색 → 폰케이스·티셔츠 잡동사니)
        의 재발 방지. office-chair로 매핑돼 영어 'office chair'/'ergonomic office chair'로 검색돼야.
        """
        import collector.aliexpress as ali
        from collector import category_collect as cc
        from common import config as cfg
        from writer import keyword_queue as kq

        queries: list[str] = []

        def fake_query(q: str, **kw: object) -> ali.QueryResult:
            queries.append(q)
            return ali.QueryResult(
                dry_run=False,
                request={},
                products=[
                    {
                        "source": "aliexpress",
                        "source_product_id": "A1",
                        "name": "메쉬 사무용 의자",
                        "deeplink_url": "https://s.click.ali/A1",
                        "deeplink_slug": "ali-A1",
                        "affiliate_tag": "honsallim",
                        "price_krw": 89000,
                    }
                ],
                resp_code="200",
            )

        monkeypatch.setattr(ali, "query_products", fake_query)
        monkeypatch.setattr(cfg, "load_secrets", lambda: None)
        monkeypatch.setattr(cc.time, "sleep", lambda *a, **k: None)

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "컴퓨터의자", channel="ali")
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, _ = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        # ★핵심: 한글 '컴퓨터의자'가 아니라 office-chair 영어 티어 검색어로 검색
        assert "컴퓨터의자" not in queries
        assert set(queries) == {"office chair", "ergonomic office chair"}
        assert [c["source"] for c in cands] == ["aliexpress"]

    def test_unmapped_keyword_skips_ali(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """미매핑 키워드는 알리 영어 검색어가 없으므로 알리를 호출하지 않고 건너뛴다(쿠팡 단독)."""
        import collector.aliexpress as ali
        from collector import coupang_manual as cm
        from writer import keyword_queue as kq

        def boom(*a: object, **k: object) -> object:
            raise AssertionError("미매핑 키워드는 알리를 호출하면 안 됨(한글 직접검색 금지)")

        monkeypatch.setattr(ali, "query_products", boom)

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "강아지 사료", channel="both")  # 어느 카테고리에도 미매핑
        cm.add_to_keyword(
            conn, kid, cm.build_manual_product("쿠팡사료", "https://link.coupang.com/a/Y")
        )
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, note = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        assert [c["source"] for c in cands] == ["coupang"]  # 알리 건너뜀 — 쿠팡 단독
        assert "건너뜀" in note


class TestGatherCandidatesVisionCatalog:
    """★세션 #45 근본수정 회귀: require 없는(비전 전담) 카테고리는 fresh 알리 검색 대신
    비전 검증 카탈로그(category_products)를 재사용한다.

    mini-rice-cooker(require_any=[])에서 fresh 검색을 쓰면 keyword_relevance.filter_products가
    사실상 무필터(전량 통과)라 오염 상품이 완전무인 발행까지 직행하던 구멍의 재발 방지.
    """

    @staticmethod
    def _seed_catalog(path: Path, *, products: int = 2, coupang: bool = False) -> None:
        conn = sqlite3.connect(str(path))
        conn.execute(
            "INSERT INTO categories (slug, name_ko, status) "
            "VALUES ('mini-rice-cooker', '미니 전기밥솥', 'published')"
        )
        cat_id = conn.execute("SELECT id FROM categories WHERE slug='mini-rice-cooker'").fetchone()[
            0
        ]

        def _add(pid_suffix: str, source: str, name: str, order: int) -> None:
            conn.execute(
                "INSERT INTO products (source, source_product_id, name, price_krw, "
                "deeplink_url, deeplink_slug, affiliate_tag) VALUES (?, ?, ?, ?, ?, ?, 'honsallim')",
                (
                    source,
                    pid_suffix,
                    name,
                    30000 + order,
                    f"https://link.example/{pid_suffix}",
                    f"{source[:4]}-{pid_suffix}",
                ),
            )
            pid = conn.execute(
                "SELECT id FROM products WHERE source=? AND source_product_id=?",
                (source, pid_suffix),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO category_products (category_id, product_id, tier, is_featured, "
                "display_order) VALUES (?, ?, 'budget', 0, ?)",
                (cat_id, pid, order),
            )

        for i in range(products):
            _add(f"R{i}", "aliexpress", f"미니 전기밥솥 {i}호 1.6L", i)
        if coupang:
            _add("C1", "coupang", "쿠팡존 밥솥(카테고리 페이지 전용)", 99)
        conn.commit()
        conn.close()

    def test_require_empty_category_reuses_catalog_not_fresh_search(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import collector.aliexpress as ali
        from writer import keyword_queue as kq

        def boom(*a: object, **k: object) -> object:
            raise AssertionError("require 없는 카테고리는 fresh 알리 검색을 호출하면 안 됨(#45)")

        monkeypatch.setattr(ali, "query_products", boom)
        self._seed_catalog(migrated_db, products=2, coupang=True)
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "미니압력밥솥", channel="ali")  # mini-rice-cooker 매핑
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, note = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        # 알리 카탈로그만 재사용 — 쿠팡 zone(카테고리 페이지 전용·수동 큐레이션)은 제외
        assert [c["source"] for c in cands] == ["aliexpress", "aliexpress"]
        assert all(str(c["deeplink_slug"]).startswith("alie-R") for c in cands)
        assert "카탈로그 재사용 2개" in note

    def test_empty_catalog_fails_closed_no_candidates(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """카탈로그 0개 — fresh 검색으로 대체하지 않고 후보 0(빈 글 차단이 LLM 비용 전 중단)."""
        import collector.aliexpress as ali
        from writer import keyword_queue as kq

        def boom(*a: object, **k: object) -> object:
            raise AssertionError("카탈로그가 비어도 fresh 검색 폴백 금지(무필터 오염 방지)")

        monkeypatch.setattr(ali, "query_products", boom)
        self._seed_catalog(migrated_db, products=0)
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "1인용밥솥", channel="ali")
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, note = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 20)
        assert cands == []
        assert "재사용 0개" in note

    def test_catalog_reuse_caps_at_double_page_size(self, migrated_db: Path) -> None:
        """상한 = page_size*2 — 검색 경로(티어 2 x page_size)와 동일 규모(프롬프트 과대 방지)."""
        from writer import keyword_queue as kq

        self._seed_catalog(migrated_db, products=3)
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "미니전기밥솥", channel="ali")
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        cands, note = cli._gather_keyword_candidates(db.connect(migrated_db), kw, 1)  # cap=2
        assert len(cands) == 2
        assert "상한" in note


class TestKeywordGenerateEmptyGuard:
    """상품 0개 키워드는 LLM 비용을 쓰기 전에 생성 중단(빈 글 방지·EVENTS #38).

    '책거치대'처럼 카테고리 미매핑 + 쿠팡 미선택이면 후보가 0개인데, 옛 코드는 그대로
    draft를 만들고 enrich(LLM 본문)까지 돌려 이미지·수익링크 없는 빈 글이 validated 됐다.
    무인 auto-cycle도 cmd_keyword_generate를 거치므로 이 한 곳에서 차단된다.
    """

    def test_zero_candidates_blocks_before_enrich(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from writer import keyword_queue as kq

        def boom_enrich(*a: object, **k: object) -> object:
            raise AssertionError("상품 0개인데 enrich(LLM 본문 생성)를 호출하면 안 됨")

        monkeypatch.setattr(cli, "cmd_enrich", boom_enrich)

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "강아지 사료", channel="ali")  # 미매핑·쿠팡 미선택 → 후보 0
        conn.close()

        rc = cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=False))

        assert rc == 3  # 빈 글 차단 종료 코드
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        n_drafts = int(conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0])
        conn.close()
        assert kw is not None and kw["status"] == "failed"  # 키워드는 failed로 빠짐
        assert n_drafts == 0  # 빈 draft가 생기지 않음


class TestGateRejectSelfHeal:
    """★세션 #41 — 게이트 반려 키워드 자가복원(§0 조용한 데드엔드 제거).

    옛 코드: 반려 시 status='drafted'로만 둬 auto_pick_keyword(pending만 픽)가 다시 보지 않아
    영구 방치·대시보드엔 '글 생성됨'으로 정상처럼 보임. 이제 상한 미만이면 pending 복귀(다음
    사이클 자동 재생성), 상한 도달이면 failed로 격리(자동 재시도 중단·digest/ALERT 노출).
    """

    _CAND: ClassVar[dict[str, object]] = {
        "source": "aliexpress",
        "source_product_id": "A1",
        "name": "메쉬 사무용 의자",
        "deeplink_url": "https://s.click.ali/A1",
        "deeplink_slug": "ali-A1",
        "affiliate_tag": "honsallim",
        "price_krw": 89000,
    }

    def _stub_pipeline(self, monkeypatch: pytest.MonkeyPatch, *, validate_rc: int) -> None:
        # 상품 확보·enrich(LLM 비용)를 우회하고 validate 결과만 강제 — 반려 분기만 검증.
        monkeypatch.setattr(
            cli, "_gather_keyword_candidates", lambda *a, **k: ([self._CAND], "후보 1개(테스트)")
        )
        monkeypatch.setattr(cli, "cmd_enrich", lambda *a, **k: 0)
        monkeypatch.setattr(cli, "cmd_validate", lambda *a, **k: validate_rc)

    def test_reject_requeues_to_pending_under_cap(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from writer import keyword_queue as kq

        self._stub_pipeline(monkeypatch, validate_rc=1)
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "메쉬의자", channel="ali")
        conn.close()

        rc = cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=False))
        assert rc == 0
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        assert kw["status"] == "pending"  # 데드엔드 아님 — 다음 사이클이 재생성한다
        assert kw["fail_count"] == 1

    def test_reject_escalates_to_failed_at_cap(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from writer import keyword_queue as kq

        self._stub_pipeline(monkeypatch, validate_rc=1)
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "메쉬의자", channel="ali")
        conn.close()

        for _ in range(3):  # keyword_max_gate_retries 기본 3
            cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=False))

        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        assert kw["status"] == "failed"  # 상한 도달 — 자동 재시도 중단(fail-loud)
        assert kw["fail_count"] == 3

    def test_pass_keeps_drafted(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from writer import keyword_queue as kq

        self._stub_pipeline(monkeypatch, validate_rc=0)  # 게이트 통과
        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "메쉬의자", channel="ali")
        conn.close()

        assert cli.cmd_keyword_generate(_ns(id=kid, page_size=20, dry_run=False)) == 0
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        assert kw["status"] == "drafted"  # 통과는 검토 대기(변경 없음)
        assert kw["fail_count"] == 0

    def test_digest_surfaces_gate_failed(self, migrated_db: Path) -> None:
        from writer import keyword_queue as kq

        conn = db.connect(migrated_db)
        kid = kq.add_keyword(conn, "메쉬의자", channel="ali")
        kq.set_status(conn, kid, "failed", "검증 반려 3회(상한 도달) — 수동 검토 필요")
        digest = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"held": [], "approved": []}, approved_n=0
        )
        conn.close()
        assert digest["queue_gate_failed"] == 1
        assert "메쉬의자" in digest["gate_failed_keywords"]


class TestKeywordRequeue:
    """★세션 #41 — 게이트 반려로 막힌 키워드 재시도 복구(remediation·쿠팡 배너 보존)."""

    def _stuck(self, dbpath: Path, *, draft_reason: str, kw_status: str = "drafted") -> int:
        """반려 draft가 걸린 키워드 생성. draft_reason으로 게이트/수동 반려 구분."""
        from writer import keyword_queue as kq

        conn = db.connect(dbpath)
        kid = kq.add_keyword(conn, "등받이의자", channel="both")
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, status_reason, keyword_id) "
            "VALUES (?, 'rejected', ?, ?)",
            (sid, draft_reason, kid),
        )
        conn.execute("UPDATE keyword_queue SET status=? WHERE id=?", (kw_status, kid))
        conn.commit()
        conn.close()
        return int(kid)

    def test_requeue_by_id_resets_to_pending(self, migrated_db: Path) -> None:
        from writer import keyword_queue as kq

        kid = self._stuck(migrated_db, draft_reason="validate_and_save → rejected")
        conn = db.connect(migrated_db)
        kq.bump_fail_count(conn, kid)  # fail_count=1
        conn.close()

        assert cli.cmd_keyword_requeue(_ns(id=kid)) == 0
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None
        assert kw["status"] == "pending"  # 재생성 대상 복귀
        assert kw["fail_count"] == 0  # 새 재시도 예산

    def test_requeue_bulk_only_gate_rejected(self, migrated_db: Path) -> None:
        """일괄 모드는 게이트 반려만 — 사람이 직접 반려한 키워드는 건드리지 않는다."""
        from writer import keyword_queue as kq

        gate = self._stuck(migrated_db, draft_reason="validate_and_save → rejected")
        conn = db.connect(migrated_db)
        # 사람이 대시보드에서 직접 반려한 키워드(의도적)는 제외돼야
        manual = kq.add_keyword(conn, "책상의자", channel="ali")
        sid = kq.ensure_scenario_for_keyword(conn, manual)
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, status_reason, keyword_id) "
            "VALUES (?, 'rejected', 'cli reject — dashboard 반려', ?)",
            (sid, manual),
        )
        conn.execute("UPDATE keyword_queue SET status='drafted' WHERE id=?", (manual,))
        conn.commit()
        conn.close()

        assert cli.cmd_keyword_requeue(_ns(id=None)) == 0
        conn = db.connect(migrated_db)
        gate_kw = kq.get_keyword(conn, gate)
        manual_kw = kq.get_keyword(conn, manual)
        conn.close()
        assert gate_kw is not None and gate_kw["status"] == "pending"  # 게이트 반려 → 복귀
        assert manual_kw is not None and manual_kw["status"] == "drafted"  # 수동 반려 → 유지

    def test_requeue_none_found(
        self, migrated_db: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert cli.cmd_keyword_requeue(_ns(id=None)) == 0
        assert "없음" in capsys.readouterr().out

    def _publish_article_for(self, dbpath: Path, kid: int, slug: str) -> None:
        """키워드에 발행된 글 연결 (promoted draft → published article)."""
        conn = db.connect(dbpath)
        sid = conn.execute("SELECT scenario_id FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0]
        conn.execute(
            "INSERT INTO articles (slug, scenario_id, title, summary, body_md, body_html, "
            "meta_description, schema_jsonld, disclosure_first, content_hash, "
            "truth_check_passed_at, user_approved_at, status, published_at) VALUES "
            "(?, ?, 'T', 's', 'm', 'h', 'd', '{}', 'disc', 'hash', "
            "'2026-01-01', '2026-01-01', 'published', '2026-01-01')",
            (slug, sid),
        )
        aid = conn.execute("SELECT id FROM articles ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO drafts (scenario_id, status, status_reason, keyword_id, "
            "promoted_article_id) VALUES (?, 'published', 'promoted to articles', ?, ?)",
            (sid, kid, aid),
        )
        conn.commit()
        conn.close()

    def test_requeue_by_id_blocked_when_published(self, migrated_db: Path) -> None:
        """발행된 글이 있는 키워드는 --id 재시도 차단 — 같은 주제 중복 글 방지(라이브 보호·§0)."""
        from writer import keyword_queue as kq

        kid = self._stuck(migrated_db, draft_reason="validate_and_save → rejected")
        self._publish_article_for(migrated_db, kid, "kw-pub-1")

        assert cli.cmd_keyword_requeue(_ns(id=kid)) == 2  # 차단
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None and kw["status"] == "drafted"  # 상태 불변

    def test_requeue_bulk_skips_when_latest_draft_published(self, migrated_db: Path) -> None:
        """과거 반려 이력이 있어도 최신 draft가 발행 성공이면 일괄 재시도 대상 아님(재트리거 방지)."""
        from writer import keyword_queue as kq

        kid = self._stuck(migrated_db, draft_reason="validate_and_save → rejected")
        self._publish_article_for(migrated_db, kid, "kw-pub-2")  # 최신 draft = published

        assert cli.cmd_keyword_requeue(_ns(id=None)) == 0
        conn = db.connect(migrated_db)
        kw = kq.get_keyword(conn, kid)
        conn.close()
        assert kw is not None and kw["status"] == "drafted"  # 발행 성공 키워드는 건드리지 않음

    def test_requeue_by_id_missing_returns_2(self, migrated_db: Path) -> None:
        assert cli.cmd_keyword_requeue(_ns(id=999)) == 2


class TestAutoCycleNotify:
    """★세션 #41 — 무인 사이클 텔레그램 자기보고(일일 리포트+경보·하트비트 겸용)."""

    @staticmethod
    def _digest(**over: object) -> dict[str, object]:
        d: dict[str, object] = {
            "made": 1,
            "approved_this_run": 1,
            "approved_pending_publish": 1,
            "queue_pending": 3,
            "queue_publishable": 3,
            "queue_retrying": 0,
            "queue_coupang_pending": 3,
            "queue_gate_failed": 0,
            "gate_failed_keywords": [],
            "abnormal": False,
        }
        d.update(over)
        return d

    def _capture(self, monkeypatch: pytest.MonkeyPatch, *, ready: bool = True) -> list[str]:
        from common import config, notify

        sent: list[str] = []

        def _fake_send(text: str) -> bool:
            sent.append(text)
            return True

        monkeypatch.setattr(config, "load_secrets", lambda: {})
        monkeypatch.setattr(notify, "telegram_ready", lambda: ready)
        monkeypatch.setattr(notify, "send_telegram", _fake_send)
        return sent

    def test_daily_report_sent(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._capture(monkeypatch)
        cli._auto_cycle_notify(self._digest(), publish_rc=0)
        assert len(sent) == 1
        assert "발행 완료" in sent[0]
        assert "조치 필요 없음" in sent[0]

    def test_unconfigured_no_send(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._capture(monkeypatch, ready=False)
        cli._auto_cycle_notify(self._digest(), publish_rc=0)
        assert sent == []

    def test_coupang_low_alert(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """쿠팡 첨부 소진 임박 미리 알림 — 수익 링크 끊김 방지(주인 지시·세션 #41)."""
        sent = self._capture(monkeypatch)
        cli._auto_cycle_notify(self._digest(queue_coupang_pending=1), publish_rc=0)
        assert "쿠팡 첨부 대기 1편뿐" in sent[0]

    def test_coupang_zero_alert(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._capture(monkeypatch)
        cli._auto_cycle_notify(self._digest(queue_coupang_pending=0), publish_rc=0)
        assert "쿠팡 첨부 대기 0편" in sent[0]

    def test_gate_failed_alert(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._capture(monkeypatch)
        cli._auto_cycle_notify(
            self._digest(queue_gate_failed=1, gate_failed_keywords=["메쉬의자"]),
            publish_rc=0,
        )
        assert "반려(검토 필요) 1건" in sent[0]
        assert "메쉬의자" in sent[0]

    def test_alerts_sent_even_when_daily_off(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """일일 리포트 OFF여도 경보(조치 필요)는 발송 — 무인 fail-loud 유지(§0)."""
        from common import settings as st

        sent = self._capture(monkeypatch)
        monkeypatch.setattr(
            st, "get", lambda k, d=None, **kw: False if k == "telegram_daily_report" else d
        )
        cli._auto_cycle_notify(self._digest(abnormal=True), publish_rc=None)
        assert len(sent) == 1
        assert "발행 0편 위험" in sent[0]

    def test_daily_off_no_alerts_no_send(
        self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from common import settings as st

        sent = self._capture(monkeypatch)
        monkeypatch.setattr(
            st, "get", lambda k, d=None, **kw: False if k == "telegram_daily_report" else d
        )
        cli._auto_cycle_notify(self._digest(), publish_rc=0)
        assert sent == []

    def test_publish_fail_alert(self, migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sent = self._capture(monkeypatch)
        cli._auto_cycle_notify(self._digest(), publish_rc=2)
        assert "발행 단계 실패" in sent[0]

    def test_digest_includes_coupang_pending(self, migrated_db: Path) -> None:
        """digest에 쿠팡 첨부 재고 집계 포함 — 알림·배너의 단일 소스."""
        from writer import keyword_queue as kq

        conn = db.connect(migrated_db)
        kq.add_keyword(conn, "메쉬의자", channel="both", target_products=[{"source": "coupang"}])
        kq.add_keyword(conn, "서재책상", channel="ali")
        digest = cli._auto_cycle_digest_and_alert(
            conn, made=0, ar={"held": [], "approved": []}, approved_n=0
        )
        conn.close()
        assert digest["queue_coupang_pending"] == 1
        assert digest["queue_pending"] == 2


class TestActionableFeedback:
    """★세션 #41 — 게이트 issue를 '어떻게 고칠지' 실행지시로 변환(재생성 성공률↑·무한 반려 방지)."""

    @staticmethod
    def _report(gate: str, issues: list[str]) -> dict[str, object]:
        return {"overall_pass": False, "gates": {gate: {"issues": issues}}}

    def test_headings_directive_includes_keyword(self) -> None:
        fb = cli._actionable_feedback(
            self._report("seo", ["headings_keyword_low: 소제목 내 대표키워드 0개 < 1개"]),
            "허리편한의자",
        )
        assert len(fb) == 1
        assert "허리편한의자" in fb[0]  # 어떤 키워드를 소제목에 넣을지 명시
        assert "소제목" in fb[0]
        assert "원인:" in fb[0]  # 원본 issue도 보존

    def test_first_person_directive(self) -> None:
        fb = cli._actionable_feedback(
            self._report("truth", ["first_person_forbidden: 2년 사용"]), "메쉬의자"
        )
        assert "삭제" in fb[0]
        assert "2년 사용" in fb[0]  # 문제 표현을 짚어줌

    def test_unknown_issue_passthrough(self) -> None:
        fb = cli._actionable_feedback(self._report("links", ["broken_link: /go/x"]), "x")
        assert fb == ["broken_link: /go/x"]  # 미지 코드는 원본 유지

    def test_no_primary_falls_back_raw(self) -> None:
        fb = cli._actionable_feedback(
            self._report("seo", ["headings_keyword_low: 소제목 내 대표키워드 0개 < 1개"]), ""
        )
        assert fb == ["headings_keyword_low: 소제목 내 대표키워드 0개 < 1개"]

    def test_dedupes(self) -> None:
        fb = cli._actionable_feedback(
            self._report("seo", ["density_high: 밀도 5%", "density_high: 밀도 5%"]), "kw"
        )
        assert len(fb) == 1
