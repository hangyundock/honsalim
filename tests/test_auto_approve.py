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
    sources: tuple[str, ...] | None = None,
) -> int:
    """validated(또는 enriched) draft + enriched_payload featured + 선택 키워드 생성.

    sources: featured별 제휴처(aliexpress/coupang). None이면 전부 aliexpress(기존 호환).
    """
    sid = conn.execute("SELECT id FROM scenarios ORDER BY id LIMIT 1").fetchone()[0]
    did = article_writer.create_draft(conn, scenario_id=sid)
    if keyword is not None:
        kid = kq.get_or_create(conn, keyword, channel="ali")
        conn.execute("UPDATE drafts SET keyword_id=? WHERE id=?", (kid, did))
    state_machine.transition(conn, did, "enriched")
    srcs = sources if sources is not None else tuple("aliexpress" for _ in featured_names)
    ep = {
        "products": [
            {"name": n, "source_product_id": f"sp{i}", "source": srcs[i]}
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
        ok, _reason, _code = aa.eligible(conn, did)
        assert ok is True

    def test_not_validated_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("의자",), set_validated=False)
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is False
        assert "validated 아님" in reason

    def test_no_keyword_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, None, ("의자",))
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is False
        assert "키워드" in reason

    def test_unmapped_keyword_held(self, conn: sqlite3.Connection) -> None:
        # 카테고리에 없는 키워드 → 적합성 검증 불가 → 보류(fail-closed)
        did = _make_validated_draft(conn, "강아지 사료", ("강아지 사료 1kg",))
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is False
        assert "미매핑" in reason

    def test_offtarget_featured_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("화장 드레싱 의자",))
        ok, reason, _code = aa.eligible(conn, did)
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


class TestCoupangExempt:
    """세션 #39: 수동 쿠팡 배너는 사람이 고른 것이라 자동승인 적합성 검사 면제(수집 단계 정책과 일치).

    무중력의자·리클라이너처럼 카테고리 exclude_terms(리클라이너·쿠션·소파)와 충돌하는 키워드의
    주인 큐레이션 쿠팡 상품이 거부돼 무인 발행이 영구 보류되던 문제(라이브 적발) 근본 수정.
    """

    # 카테고리 exclude(리클라이너·쿠션)에 걸리는, 진짜 무중력의자(릴클라이너형) 상품명
    OFFTARGET = "홈스퍼니처 접이식 무중력 리클라이너 의자 + 헤드 쿠션 풀세트"

    def test_offtarget_coupang_banner_is_exempt(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "무중력의자", (self.OFFTARGET,), sources=("coupang",))
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is True, reason

    def test_same_name_aliexpress_still_held(self, conn: sqlite3.Connection) -> None:
        # ali 자동수집은 면제 아님 — 동일 상품명이라도 적합성 검사로 보류돼야 함
        did = _make_validated_draft(conn, "무중력의자", (self.OFFTARGET,), sources=("aliexpress",))
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is False
        assert "off-target" in reason

    def test_mixed_coupang_offtarget_plus_ali_ontarget_eligible(
        self, conn: sqlite3.Connection
    ) -> None:
        # 실제 draft #12 재현: 쿠팡 off-target + ali on-target → 쿠팡 면제 후 off-target 0 → eligible
        did = _make_validated_draft(
            conn,
            "무중력의자",
            (self.OFFTARGET, "인체공학 사무용 의자"),
            sources=("coupang", "aliexpress"),
        )
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is True, reason

    def test_mixed_coupang_exempt_but_ali_offtarget_still_held(
        self, conn: sqlite3.Connection
    ) -> None:
        # 쿠팡은 면제돼도 ali가 off-target이면 여전히 보류 — 면제가 ali 안전망을 무력화하지 않음
        did = _make_validated_draft(
            conn,
            "무중력의자",
            (self.OFFTARGET, "캠핑 낚시 야외 접이식 푸프"),
            sources=("coupang", "aliexpress"),
        )
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is False
        assert "off-target" in reason


class TestNewlyMappedKeywords:
    """세션 #39: 무인 큐에 있으나 미매핑(cat=None)이라 자동승인이 무조건 보류하던 사무의자 키워드를
    office-chair secondary에 추가 → 매핑되어 정상 적합성 검사·발행 가능."""

    @pytest.mark.parametrize("kw", ["메쉬의자", "허리편한의자", "학생용의자"])
    def test_newly_mapped_office_chair_keyword_eligible(
        self, conn: sqlite3.Connection, kw: str
    ) -> None:
        did = _make_validated_draft(conn, kw, ("인체공학 사무용 의자",))
        ok, reason, _code = aa.eligible(conn, did)
        assert ok is True, reason


class TestReasonCode:
    """세션 #39: 보류 사유를 machine-readable code로 — 무인 알림이 '의도적 보류(min_published)
    vs 문제 보류(unmapped/offtarget…)'를 로그 파싱 없이 코드로 분류·집계(오경보 방지)."""

    def test_eligible_ok_code(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is True and code == "ok"

    def test_unmapped_code(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "강아지 사료", ("강아지 사료 1kg",))
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "unmapped"

    def test_offtarget_code(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("화장 드레싱 의자",))
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "offtarget"

    def test_featured_zero_code(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ())
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "featured_zero"

    def test_min_published_hold_is_coded_intentional(self, conn: sqlite3.Connection) -> None:
        # min_published 미달 보류는 code='min_published'(정상) — 알림이 '문제'로 오인하면 안 됨
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        res = aa.auto_approve(conn, apply=True, min_published=5)
        assert res["approved"] == []
        assert did in {h["draft"] for h in res["held"]}
        assert all(h["code"] == "min_published" for h in res["held"])

    def test_problem_hold_carries_specific_code(self, conn: sqlite3.Connection) -> None:
        good = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        unmapped = _make_validated_draft(conn, "강아지 사료", ("사료",))
        res = aa.auto_approve(conn, apply=True)
        assert good in res["approved"]
        codes = {h["draft"]: h["code"] for h in res["held"]}
        assert codes.get(unmapped) == "unmapped"
