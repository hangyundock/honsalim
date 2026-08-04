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

# '보고서를 자동 생성' sentinel — None·""·깨진 JSON도 **테스트 입력값**이라 그것들과 겹치지 않는
# 별도 객체가 필요하다(#49: ""를 sentinel로 쓰다가 빈 문자열 케이스가 자동 생성으로 새어 통과).
_AUTO_REPORT = object()


def _seo_report(*, skipped: bool) -> dict:
    """운영에서 저장되는 validation_report의 최소 형태 (★세션 #49).

    운영은 `article_writer.validate_and_save`만이 validated로 전이시키며 **항상** 보고서를
    저장한다(실데이터 43/43). auto_approve가 'seo 게이트가 실제로 돌았는지'를 이 보고서로
    판정하므로, 테스트 픽스처도 보고서를 남겨야 운영과 같은 조건이 된다.
    """
    metrics = {"skipped": True} if skipped else {"primary": "테스트", "primary_freq": 5}
    return {"overall_pass": True, "gates": {"seo": {"issues": [], "metrics": metrics}}}


def _make_validated_draft(
    conn: sqlite3.Connection,
    keyword: str | None = None,
    featured_names: tuple[str, ...] = (),
    *,
    set_validated: bool = True,
    sources: tuple[str, ...] | None = None,
    seo_skipped: bool = False,
    validation_report: str | None | object = _AUTO_REPORT,
) -> int:
    """validated(또는 enriched) draft + enriched_payload featured + 선택 키워드 생성.

    sources: featured별 제휴처(aliexpress/coupang). None이면 전부 aliexpress(기존 호환).
    seo_skipped: seo 게이트가 skip된 채 validated된 상태 재현(#49 미매핑 생성 경로).
    validation_report: 생략(기본)이면 seo_skipped에 맞춰 자동 생성. 값을 주면 그대로 저장 —
        None·""(빈 문자열)·깨진 JSON 같은 손상 사례를 그대로 재현하기 위해 sentinel과 분리한다.
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
    if validation_report is _AUTO_REPORT:
        article_writer.save_validation_report(conn, did, _seo_report(skipped=seo_skipped))
    else:
        conn.execute(
            "UPDATE drafts SET validation_report = ? WHERE id = ?", (validation_report, did)
        )
    if set_validated:
        state_machine.transition(conn, did, "validated")
    conn.commit()
    return did


@pytest.fixture()
def conn(tmp_path: Path) -> sqlite3.Connection:
    p = tmp_path / "test.db"
    db.migrate(db_path=p)
    db.seed(db_path=p)
    c = db.connect(p)
    # ★세션 #45: 자동 승인은 '공개 카테고리' 전제(category_draft 보류) — seed는 §2-마에 따라
    # 전부 draft로 만들므로, 운영 현실(매핑 카테고리=published)을 반영해 공개로 올려 둔다.
    # draft 보류 동작 자체는 TestEligible.test_draft_category_held가 별도 검증.
    c.execute("UPDATE categories SET status='published'")
    c.commit()
    return c


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

    def test_draft_category_held(self, conn: sqlite3.Connection) -> None:
        # ★세션 #45: 매핑돼도 카테고리가 draft(비공개)면 보류 — 공개 허브 없는 고아 글이
        # 완전무인으로 발행되는 것 차단. 카테고리 공개 승인(사람 게이트) 후 자동 해소.
        conn.execute("UPDATE categories SET status='draft' WHERE slug='office-chair'")
        conn.commit()
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        ok, reason, code = aa.eligible(conn, did)
        assert ok is False
        assert code == "category_draft"
        assert "비공개" in reason
        # 카테고리를 공개하면 같은 draft가 자동 승인 가능해진다(보류 해소 경로)
        conn.execute("UPDATE categories SET status='published' WHERE slug='office-chair'")
        conn.commit()
        ok2, _r, code2 = aa.eligible(conn, did)
        assert ok2 is True and code2 == "ok"

    def test_missing_category_row_fail_open(self, conn: sqlite3.Connection) -> None:
        # 행이 아예 없으면(미프로비저닝 DB) 막지 않음 — 과차단은 무인 승인 흐름을 죽인다(§0)
        conn.execute("DELETE FROM categories WHERE slug='office-chair'")
        conn.commit()
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is True and code == "ok"


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


class TestSeoUnverified:
    """★세션 #49 — 'validated = 5게이트 통과'가 깨지는 구멍 봉인.

    미매핑 키워드로 만든 글은 seo_cfg가 비어 validator seo 게이트가 **skip(=pass 취급)** 된 채
    validated가 된다. auto_approve는 게이트를 재검증하지 않으므로, 나중에 그 키워드를 씨앗에
    추가(매핑)하는 순간 미검증 글이 그대로 무인 자동 발행된다 — 08-04 draft #48이 실제 이 상태.
    """

    def test_seo_skipped_draft_is_held(self, conn: sqlite3.Connection) -> None:
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",), seo_skipped=True)
        ok, reason, code = aa.eligible(conn, did)
        assert ok is False
        assert code == "seo_unverified"
        assert "재생성" in reason

    def test_seo_measured_draft_still_eligible(self, conn: sqlite3.Connection) -> None:
        """정상(게이트 실측) 글은 그대로 승인 — 과차단 회귀 방지."""
        did = _make_validated_draft(conn, "컴퓨터의자", ("인체공학 사무용 의자",))
        ok, reason, code = aa.eligible(conn, did)
        assert ok is True, reason
        assert code == "ok"

    def test_mapping_added_later_does_not_auto_publish_unverified(
        self, conn: sqlite3.Connection
    ) -> None:
        """★재발 방지 핵심: 미매핑 상태로 생성 → 나중에 매핑돼도 자동 발행되면 안 된다.

        매핑을 추가하면 'unmapped' 보류는 풀리지만 seo는 여전히 미검증이므로 보류가 유지돼야
        한다. 이 단언이 없으면 씨앗 보강이 곧 미달 글 발행 트리거가 된다(#49 draft #48).
        """
        did = _make_validated_draft(conn, "메쉬의자", ("인체공학 사무용 의자",), seo_skipped=True)
        # 매핑은 정상(메쉬의자 ∈ office-chair secondary) — 그래도 seo 미검증이라 보류
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "seo_unverified"
        res = aa.auto_approve(conn, apply=True)
        assert did not in res["approved"]
        assert {h["draft"]: h["code"] for h in res["held"]}.get(did) == "seo_unverified"

    @pytest.mark.parametrize(
        "report",
        [None, "", "{잘못된 json", '{"gates": {}}', '{"gates": {"seo": {}}}'],
    )
    def test_missing_or_broken_report_is_held(
        self, conn: sqlite3.Connection, report: str | None
    ) -> None:
        """보고서가 없거나 깨졌으면 '검증을 확인할 수 없음' → 보류(fail-closed·미탐<오탐)."""
        did = _make_validated_draft(
            conn, "컴퓨터의자", ("인체공학 사무용 의자",), validation_report=report
        )
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "seo_unverified"

    def test_unmapped_reported_before_seo_unverified(self, conn: sqlite3.Connection) -> None:
        """미매핑이면서 seo skip인 글(=생성 직후 상태)은 더 실행 가능한 'unmapped'로 보고한다."""
        did = _make_validated_draft(conn, "강아지 사료", ("사료",), seo_skipped=True)
        ok, _reason, code = aa.eligible(conn, did)
        assert ok is False and code == "unmapped"
