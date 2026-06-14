"""writer.auto_approve — 검증 통과 글의 fail-closed 자동 승인 (세션 #29 B-i).

사람 게이트 제거의 핵심: 적합성 검증 가능 + featured 적합일 때만 자동 승인, 나머지는 보류(사람).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from common import db
from writer import article_writer, state_machine
from writer import auto_approve as aa
from writer import keyword_queue as kq


def _make_validated_draft(
    conn: sqlite3.Connection,
    keyword: str | None = None,
    featured_names: tuple[str, ...] = (),
    *,
    set_validated: bool = True,
) -> int:
    """validated(또는 enriched) draft + enriched_payload featured + 선택 키워드 생성."""
    sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]
    did = article_writer.create_draft(conn, scenario_id=sid)
    if keyword is not None:
        kid = kq.get_or_create(conn, keyword, channel="ali")
        conn.execute("UPDATE drafts SET keyword_id=? WHERE id=?", (kid, did))
    state_machine.transition(conn, did, "enriched")
    ep = {
        "products": [
            {"name": n, "source_product_id": f"sp{i}", "source": "aliexpress"}
            for i, n in enumerate(featured_names)
        ]
    }
    article_writer.save_enriched(conn, did, ep)
    if set_validated:
        state_machine.transition(conn, did, "validated")
    conn.commit()
    return did


@pytest.fixture()
def conn(tmp_path: Path) -> sqlite3.Connection:
    p = tmp_path / "test.db"
    db.migrate(db_path=p)
    db.seed(db_path=p)
    return db.connect(p)


class TestEligible:
    def test_validated_mapped_relevant_is_eligible(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        ok, _reason = aa.eligible(conn, did)
        assert ok is True

    def test_not_validated_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("의자",), set_validated=False)
        ok, reason = aa.eligible(conn, did)
        assert ok is False
        assert "validated 아님" in reason

    def test_no_keyword_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, None, ("의자",))
        ok, reason = aa.eligible(conn, did)
        assert ok is False
        assert "키워드" in reason

    def test_unmapped_keyword_held(self, conn: sqlite3.Connection) -> None:
        # 카테고리에 없는 키워드 → 적합성 검증 불가 → 보류(fail-closed)
        did = _make_validated_draft(conn, "강아지 사료", ("강아지 사료 1kg",))
        ok, reason = aa.eligible(conn, did)
        assert ok is False
        assert "미매핑" in reason

    def test_offtarget_featured_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("화장 드레싱 의자",))
        ok, reason = aa.eligible(conn, did)
        assert ok is False
        assert "off-target" in reason


class TestAutoApprove:
    def test_approves_eligible_holds_rest(self, conn: sqlite3.Connection) -> None:
        good = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        bad = _make_validated_draft(conn, "컴퓨터의자", ("화장 드레싱 의자",))
        unmapped = _make_validated_draft(conn, "강아지 사료", ("사료",))
        res = aa.auto_approve(conn, apply=True)
        assert good in res["approved"]
        held_ids = {h["draft"] for h in res["held"]}
        assert bad in held_ids and unmapped in held_ids
        assert state_machine.current_status(conn, good) == "approved"
        assert state_machine.current_status(conn, bad) == "validated"
        assert state_machine.current_status(conn, unmapped) == "validated"

    def test_dry_run_does_not_transition(self, conn: sqlite3.Connection) -> None:
        good = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        res = aa.auto_approve(conn, apply=False)
        assert good in res["approved"]
        assert state_machine.current_status(conn, good) == "validated"  # apply=False면 전이 없음
