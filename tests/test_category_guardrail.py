"""writer.category_guardrail + auto_publish — fail-closed 자동 게시 가드레일 회귀 (세션 #22).

E7(사람 1건 승인)을 대체하는 자동 판정의 안전성: 깨끗하면 통과, 오염·무결성 결함·
LLM NO/오류/불명확·글 없음은 전부 보류(미탐<오탐). 통과만 published 전이.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from common import db
from writer import article_writer, auto_publish, category_guardrail, category_state

CLEAN_PROSE = "도마는 매일 쓰는 주방 도구다. 재질과 크기를 기준으로 고른다. 위생 관리가 중요하다."


class _Resp:
    """generate_raw 반환 호환 — guardrail은 .response_text만 읽음."""

    def __init__(self, text: str) -> None:
        self.response_text = text


class FakeLLM:
    """generate_raw 흉내 — no_idx의 번호만 NO, 나머지 YES. raise_exc/garbage로 실패 주입."""

    def __init__(
        self,
        *,
        no_idx: set[int] | None = None,
        raise_exc: Exception | None = None,
        garbage: bool = False,
    ) -> None:
        self.no_idx = no_idx or set()
        self.raise_exc = raise_exc
        self.garbage = garbage
        self.calls = 0

    def generate_raw(self, system_text: str, user_prompt: str, dry_run: bool = False) -> _Resp:
        self.calls += 1
        if self.raise_exc:
            raise self.raise_exc
        n = len(re.findall(r"^\s*\d+\.", user_prompt, re.M))
        if self.garbage:
            return _Resp("판정 불가합니다")
        return _Resp(
            "\n".join(f"{i}:{'NO' if i in self.no_idx else 'YES'}" for i in range(1, n + 1))
        )


@pytest.fixture()
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    p = tmp_path / "t.db"
    db.migrate(db_path=p)
    db.seed(db_path=p)
    c = db.connect(p)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()


def _cat_id(conn: sqlite3.Connection, slug: str) -> int:
    return int(conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()[0])


def _add_product(
    conn: sqlite3.Connection,
    pid: int,
    name: str,
    *,
    price: int = 10000,
    deeplink: str | None = None,
    tag: str = "honsallim",
) -> int:
    slug = f"ali-{pid}"
    url = deeplink if deeplink is not None else f"https://s.click.aliexpress.com/s/{pid}"
    conn.execute(
        "INSERT INTO products (source, source_product_id, name, price_krw, deeplink_url, "
        "deeplink_slug, affiliate_tag, availability) VALUES ('aliexpress',?,?,?,?,?,?,'in_stock')",
        (str(pid), name, price, url, slug, tag),
    )
    return int(conn.execute("SELECT id FROM products WHERE deeplink_slug=?", (slug,)).fetchone()[0])


def _link(
    conn: sqlite3.Connection,
    cat_id: int,
    prod_id: int,
    *,
    tier: str = "budget",
    featured: bool = False,
    order: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO category_products (category_id, product_id, tier, is_featured, display_order) "
        "VALUES (?,?,?,?,?)",
        (cat_id, prod_id, tier, 1 if featured else 0, order),
    )


def _set_guide(conn: sqlite3.Connection, slug: str, prose: str = CLEAN_PROSE) -> None:
    gmd = article_writer.apply_disclosure(prose, sources={"aliexpress"})
    conn.execute(
        "UPDATE categories SET guide_md=?, guide_title='도마 고르는 법', "
        "guide_generated_at=CURRENT_TIMESTAMP WHERE slug=?",
        (gmd, slug),
    )
    conn.commit()


def _setup_clean(
    conn: sqlite3.Connection,
    slug: str = "cutting-board",
    *,
    n_featured: int = 4,
    n_catalog: int = 2,
    tag: str = "honsallim",
) -> int:
    """깨끗한 도마 카테고리 — 추천 n_featured개 + 카탈로그 n_catalog개 + 글."""
    cid = _cat_id(conn, slug)
    _set_guide(conn, slug)
    pid = 0
    for i in range(n_featured):
        pid += 1
        p = _add_product(conn, 1000 + pid, f"원목 도마 {i}호 주방용", price=10000 + pid, tag=tag)
        _link(conn, cid, p, tier="budget" if i % 2 == 0 else "premium", featured=True, order=i)
    for i in range(n_catalog):
        pid += 1
        p = _add_product(conn, 1000 + pid, f"실리콘 도마 카탈로그 {i}", price=5000 + pid, tag=tag)
        _link(conn, cid, p, tier="budget", featured=False, order=100 + i)
    conn.commit()
    return cid


class TestGuardrailPass:
    def test_clean_category_passes(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert gr.passed, gr.reasons
        assert all(gr.checks.values()), gr.checks

    def test_safety_gates_actually_run(self, conn: sqlite3.Connection) -> None:
        # 깨끗한 글은 truth/disclosure/links 재검증 통과
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert gr.checks["safety_gates"] is True


class TestGuardrailHold:
    def test_no_guide_held(self, conn: sqlite3.Connection) -> None:
        cid = _cat_id(conn, "cutting-board")
        _link(conn, cid, _add_product(conn, 2001, "원목 도마 주방용"), featured=True)
        _link(
            conn,
            cid,
            _add_product(conn, 2002, "대나무 도마"),
            tier="premium",
            featured=True,
            order=1,
        )
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert any("글 없음" in r for r in gr.reasons)

    def test_missing_disclosure_guide_held(self, conn: sqlite3.Connection) -> None:
        # 대가성 고지(공정위) 없는 글 → disclosure 재검증 실패 → 보류(안전 게이트 게이팅 확인)
        _setup_clean(conn)
        conn.execute(
            "UPDATE categories SET guide_md='도마는 주방 도구다.', "
            "guide_generated_at=CURRENT_TIMESTAMP WHERE slug='cutting-board'"
        )
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert gr.checks["safety_gates"] is False
        assert any("게이트" in r for r in gr.reasons)

    def test_featured_contamination_heuristic_held(self, conn: sqlite3.Connection) -> None:
        cid = _setup_clean(conn)
        bad = _add_product(conn, 3001, "스테인리스 거치대 정리대 선반")  # 도마X·제외어
        _link(conn, cid, bad, tier="premium", featured=True, order=9)
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert gr.checks["relevance_heuristic"] is False
        assert any(("거치대" in p or "정리대" in p) for p in gr.flagged_products)

    def test_catalog_contamination_rate_held(self, conn: sqlite3.Connection) -> None:
        cid = _setup_clean(conn, n_featured=4, n_catalog=0)  # 추천 4개만(전부 깨끗)
        _link(conn, cid, _add_product(conn, 3101, "주방 거치대 선반"), featured=False, order=50)
        conn.commit()  # 1/5 = 20% > 5%
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert any("오염율" in r for r in gr.reasons)

    def test_llm_two_no_verdicts_held(self, conn: sqlite3.Connection) -> None:
        # LLM이 추천 2건 이상 NO → 체계적 오염으로 보고 보류(임계 _LLM_HOLD_THRESHOLD=2)
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM(no_idx={2, 3}))
        assert not gr.passed
        assert gr.checks["relevance_llm"] is False
        assert any("LLM 검수" in r and "2건" in r for r in gr.reasons)

    def test_llm_single_no_tolerated(self, conn: sqlite3.Connection) -> None:
        # LLM이 추천 1건만 NO → 노이즈/비결정 가능성으로 관용(통과), 단 flagged에 기록(사후 가시화)
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM(no_idx={2}))
        assert gr.passed, gr.reasons
        assert gr.checks["relevance_llm"] is True
        assert len(gr.flagged_products) == 1

    def test_llm_error_held_failclosed(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        gr = category_guardrail.check(
            conn, "cutting-board", FakeLLM(raise_exc=RuntimeError("timeout"))
        )
        assert not gr.passed
        assert gr.checks["relevance_llm"] is False
        assert any("LLM 검수 오류" in r for r in gr.reasons)

    def test_llm_garbage_response_held_failclosed(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM(garbage=True))
        assert not gr.passed
        assert gr.checks["relevance_llm"] is False

    def test_llm_client_missing_held(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        gr = category_guardrail.check(conn, "cutting-board", None, use_llm=True)
        assert not gr.passed
        assert any("client 없음" in r for r in gr.reasons)

    def test_duplicate_deeplink_held(self, conn: sqlite3.Connection) -> None:
        cid = _cat_id(conn, "cutting-board")
        _set_guide(conn, "cutting-board")
        _link(
            conn,
            cid,
            _add_product(conn, 4001, "원목 도마 1", deeplink="https://x/same"),
            featured=True,
        )
        _link(
            conn,
            cid,
            _add_product(conn, 4002, "원목 도마 2", deeplink="https://x/same"),
            tier="premium",
            featured=True,
            order=1,
        )
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert gr.checks["featured_integrity"] is False

    def test_missing_tracking_tag_held(self, conn: sqlite3.Connection) -> None:
        cid = _cat_id(conn, "cutting-board")
        _set_guide(conn, "cutting-board")
        _link(conn, cid, _add_product(conn, 4101, "원목 도마 1", tag=""), featured=True)
        _link(
            conn,
            cid,
            _add_product(conn, 4102, "원목 도마 2", tag=""),
            tier="premium",
            featured=True,
            order=1,
        )
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert gr.checks["featured_integrity"] is False

    def test_single_featured_held(self, conn: sqlite3.Connection) -> None:
        cid = _cat_id(conn, "cutting-board")
        _set_guide(conn, "cutting-board")
        _link(conn, cid, _add_product(conn, 4201, "원목 도마 1"), featured=True)
        conn.commit()
        gr = category_guardrail.check(conn, "cutting-board", FakeLLM())
        assert not gr.passed
        assert gr.checks["featured_integrity"] is False


class TestAutoPublish:
    def test_passed_gets_published(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        res = auto_publish.auto_publish(conn, ["cutting-board"], FakeLLM())
        assert res[0]["published"] is True
        st = conn.execute("SELECT status FROM categories WHERE slug='cutting-board'").fetchone()[0]
        assert st == "published"

    def test_held_stays_draft(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        res = auto_publish.auto_publish(conn, ["cutting-board"], FakeLLM(no_idx={1, 2}))
        assert res[0]["published"] is False
        st = conn.execute("SELECT status FROM categories WHERE slug='cutting-board'").fetchone()[0]
        assert st == "draft"

    def test_dry_run_does_not_publish(self, conn: sqlite3.Connection) -> None:
        _setup_clean(conn)
        res = auto_publish.auto_publish(conn, ["cutting-board"], FakeLLM(), apply=False)
        assert res[0]["passed"] is True and res[0]["published"] is False
        st = conn.execute("SELECT status FROM categories WHERE slug='cutting-board'").fetchone()[0]
        assert st == "draft"

    def test_monitor_flags_now_contaminated_published(self, conn: sqlite3.Connection) -> None:
        cid = _setup_clean(conn)
        category_state.approve(conn, "cutting-board")  # 공개 상태로
        bad = _add_product(conn, 5001, "스테인리스 거치대 정리대")  # 사후 오염 주입
        _link(conn, cid, bad, tier="premium", featured=True, order=9)
        conn.commit()
        flags = auto_publish.monitor(conn, use_llm=False)
        assert any(f["slug"] == "cutting-board" for f in flags)
