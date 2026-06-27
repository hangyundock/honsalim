"""cli 키워드 큐 명령 회귀 테스트 (세션 #25) — add·generate(dry)·list·reject.

LLM·외부 API는 호출하지 않는 경로만 (dry_run·검증·반려·목록).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

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
