"""writer.keyword_queue 회귀 테스트 — 키워드 큐 추가·상태·시나리오 브리지 (세션 #25)."""

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


from writer import keyword_queue as kq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = PROJECT_ROOT / "sql" / "migrations"


def _db(with_persona: bool = True) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for v in ("001", "002", "003", "004", "005", "006", "007"):
        conn.executescript(next(MIGRATIONS.glob(f"{v}_*.sql")).read_text(encoding="utf-8"))
    if with_persona:
        conn.executescript(
            "INSERT INTO personas (slug, title_ko, description) VALUES ('jachi', '자취생', 'd');"
            "INSERT INTO personas (slug, title_ko, description) VALUES ('office', '홈오피스', 'd');"
        )
    conn.commit()
    return conn


class TestSlugify:
    def test_ascii_keyword(self) -> None:
        assert kq.slugify("Mini Fridge Guide") == "mini-fridge-guide"

    def test_korean_falls_back_to_hash(self) -> None:
        s = kq.slugify("자취생 전자레인지 추천")
        assert s.startswith("kw-")
        assert s == kq.slugify("자취생 전자레인지 추천")  # 결정적

    def test_different_korean_different_slug(self) -> None:
        assert kq.slugify("원룸 가습기") != kq.slugify("미니 건조기")

    @pytest.mark.parametrize(
        ("keyword", "bad_slug"),
        [
            ("1인용밥솥", "1"),  # 라이브 article 22 — 충돌해 `1-2`가 됐다
            ("TPU도마", "tpu"),  # 라이브 article 18
            ("32인치모니터암", "32"),  # 큐 대기 중 — 다음 발행에서 터질 예정이었다
            ("LED스탠드", "led"),
            ("USB허브", "usb"),
        ],
    )
    def test_partial_ascii_no_longer_produces_fragment_slug(
        self, keyword: str, bad_slug: str
    ) -> None:
        """★세션 #48 근본수정 — 한글이 버려지고 **남은 조각**이 slug가 되던 라이브 결함.

        옛 폴백은 '전부 유실'일 때만 걸려, 숫자·영문이 섞인 한글 키워드가 의미 없는 URL을 만들고
        서로 충돌했다('1…'로 시작하는 키워드는 전부 `1`).
        """
        s = kq.slugify(keyword)
        assert s != bad_slug, f"{keyword}가 아직 조각 slug({bad_slug})를 만든다"
        assert s.startswith("kw-")
        assert s == kq.slugify(keyword)  # 결정적

    def test_fragment_collision_is_gone(self) -> None:
        """조각 slug의 진짜 피해 — 서로 다른 키워드가 같은 slug로 충돌하던 것."""
        assert kq.slugify("1인용밥솥") != kq.slugify("1인가구책상")

    def test_lossless_ascii_is_preserved(self) -> None:
        """유실이 없으면 읽기 좋은 slug를 그대로 쓴다 — 과잉 폴백 방지."""
        assert kq.slugify("desk lamp") == "desk-lamp"
        assert kq.slugify("Office Chair 2026") == "office-chair-2026"

    def test_accent_decomposition_is_not_a_loss(self) -> None:
        """NFKD가 분해하는 결합 악센트는 '유실'이 아니다 — 폴백을 트리거하면 안 된다."""
        assert kq.slugify("café latte") == "cafe-latte"


class TestLegacyFragmentDetection:
    """★#48 — slugify 수정만으로는 부족했다. 큐에 **이미 굳은** 조각 slug를 식별해야 한다."""

    def test_detects_the_live_cases(self) -> None:
        assert kq.is_legacy_fragment_slug("32", "32인치모니터암")
        assert kq.is_legacy_fragment_slug("1", "1인용컴퓨터책상")
        assert kq.is_legacy_fragment_slug("tpu", "TPU도마")

    def test_accepts_uniqueness_suffix(self) -> None:
        """중복 회피로 `-2`가 붙은 형태도 같은 조각이다(라이브 article 22 = `1-2`)."""
        assert kq.is_legacy_fragment_slug("1-2", "1인용밥솥")

    def test_leaves_healthy_slugs_alone(self) -> None:
        assert not kq.is_legacy_fragment_slug("desk-lamp", "desk lamp")
        assert not kq.is_legacy_fragment_slug("kw-269a4bdb", "책상추천")

    def test_never_touches_a_deliberate_slug(self) -> None:
        """★운영자가 일부러 지정한 slug를 조각으로 오인해 덮어쓰면 안 된다."""
        assert not kq.is_legacy_fragment_slug("mini-rice-cooker", "1인용밥솥")
        assert not kq.is_legacy_fragment_slug("monitor-arm-32", "32인치모니터암")


class TestLegacySlugSelfRepair:
    """★#48 — 큐에 굳어 있던 조각 slug를 시나리오 생성 시점에 교정(자가복원·§0).

    라이브 실측: `32인치모니터암`이 slug `32`를 문 채 **시나리오 없이 대기** 중이었다.
    그대로 발행됐다면 `/articles/32/`가 됐다. 이 지점은 시나리오가 아직 없는 키워드만 도달하므로
    (글·라이브 URL 부재) 교정이 안전하다.
    """

    def test_pending_fragment_is_repaired_before_it_becomes_a_url(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "32인치모니터암", channel="ali", slug="32")
        assert (
            conn.execute("SELECT slug FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0] == "32"
        )

        sid = kq.ensure_scenario_for_keyword(conn, kid)
        scen_slug = conn.execute("SELECT slug FROM scenarios WHERE id=?", (sid,)).fetchone()[0]
        kw_slug = conn.execute("SELECT slug FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0]
        assert scen_slug != "32", "공개 URL 씨앗이 아직 조각이다"
        assert scen_slug.startswith("kw-") and kw_slug.startswith("kw-")
        conn.close()

    def test_existing_scenario_is_never_renamed(self) -> None:
        """★이미 시나리오(=글·라이브 URL)가 있으면 절대 건드리지 않는다."""
        conn = _db()
        kid = kq.add_keyword(conn, "TPU도마", channel="ali", slug="tpu")
        first = kq.ensure_scenario_for_keyword(conn, kid)
        before = conn.execute("SELECT slug FROM scenarios WHERE id=?", (first,)).fetchone()[0]
        again = kq.ensure_scenario_for_keyword(conn, kid)  # 재호출 = 재사용 경로
        after = conn.execute("SELECT slug FROM scenarios WHERE id=?", (again,)).fetchone()[0]
        assert again == first and after == before
        conn.close()

    def test_deliberate_slug_survives_scenario_creation(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "1인용밥솥", channel="ali", slug="mini-rice-cooker")
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        assert (
            conn.execute("SELECT slug FROM scenarios WHERE id=?", (sid,)).fetchone()[0]
            == "mini-rice-cooker"
        )
        conn.close()

    def test_new_keywords_never_get_a_fragment_in_the_first_place(self) -> None:
        """근본수정 확인 — 새로 등록되는 키워드는 조각 slug 자체가 안 생긴다."""
        conn = _db()
        kid = kq.add_keyword(conn, "32인치모니터암", channel="ali")
        slug = conn.execute("SELECT slug FROM keyword_queue WHERE id=?", (kid,)).fetchone()[0]
        assert slug.startswith("kw-")
        conn.close()


class TestAddKeyword:
    def test_insert_pending(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "자취생 전자레인지 추천", channel="ali")
        row = conn.execute(
            "SELECT keyword, status, channel FROM keyword_queue WHERE id = ?", (kid,)
        ).fetchone()
        assert row[0] == "자취생 전자레인지 추천"
        assert row[1] == "pending"
        assert row[2] == "ali"

    def test_empty_keyword_rejected(self) -> None:
        conn = _db()
        with raises(ValueError):
            kq.add_keyword(conn, "   ")

    def test_bad_channel_rejected(self) -> None:
        conn = _db()
        with raises(ValueError):
            kq.add_keyword(conn, "x", channel="naver")

    def test_slug_collision_suffixes(self) -> None:
        conn = _db()
        kq.add_keyword(conn, "Mini Fridge", slug="mini-fridge")
        kid2 = kq.add_keyword(conn, "Mini Fridge 2", slug="mini-fridge")
        slug2 = conn.execute("SELECT slug FROM keyword_queue WHERE id = ?", (kid2,)).fetchone()[0]
        assert slug2 == "mini-fridge-2"

    def test_target_products_serialized(self) -> None:
        conn = _db()
        tp = [{"source": "coupang", "name": "선풍기", "deeplink_url": "https://x"}]
        kid = kq.add_keyword(conn, "선풍기", channel="coupang", target_products=tp)
        raw = conn.execute(
            "SELECT target_products FROM keyword_queue WHERE id = ?", (kid,)
        ).fetchone()[0]
        assert json.loads(raw) == tp


class TestSetStatus:
    def test_transition(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "x")
        kq.set_status(conn, kid, "drafted", reason="generated")
        row = conn.execute(
            "SELECT status, status_reason FROM keyword_queue WHERE id = ?", (kid,)
        ).fetchone()
        assert row[0] == "drafted"
        assert row[1] == "generated"

    def test_bad_status_rejected(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "x")
        with raises(ValueError):
            kq.set_status(conn, kid, "bogus")


class TestEnsureScenario:
    def test_creates_and_links_scenario(self) -> None:
        conn = _db()
        kid = kq.add_keyword(
            conn, "자취생 전자레인지 추천", budget_min_krw=10000, budget_max_krw=80000
        )
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        assert sid > 0
        srow = conn.execute(
            "SELECT title_ko, persona_id, budget_min_krw, active FROM scenarios WHERE id = ?",
            (sid,),
        ).fetchone()
        assert srow[0] == "자취생 전자레인지 추천"
        assert srow[1] == 1  # 첫 페르소나 (default)
        assert srow[2] == 10000
        assert srow[3] == 0  # 세션 #35: 키워드 파생 시나리오는 비활성 — '내맘대로 세팅' 미노출
        # keyword_queue.scenario_id 연결됨
        linked = conn.execute(
            "SELECT scenario_id FROM keyword_queue WHERE id = ?", (kid,)
        ).fetchone()[0]
        assert linked == sid

    def test_reuses_existing_scenario(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "원룸 가습기")
        sid1 = kq.ensure_scenario_for_keyword(conn, kid)
        sid2 = kq.ensure_scenario_for_keyword(conn, kid)
        assert sid1 == sid2
        # 시나리오 1건만 생성
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 1

    def test_respects_keyword_persona(self) -> None:
        conn = _db()
        office_pid = conn.execute("SELECT id FROM personas WHERE slug='office'").fetchone()[0]
        kid = kq.add_keyword(conn, "재택 모니터암", persona_id=office_pid)
        sid = kq.ensure_scenario_for_keyword(conn, kid)
        pid = conn.execute("SELECT persona_id FROM scenarios WHERE id = ?", (sid,)).fetchone()[0]
        assert pid == office_pid

    def test_default_persona_slug(self) -> None:
        conn = _db()
        kid = kq.add_keyword(conn, "선풍기")
        sid = kq.ensure_scenario_for_keyword(conn, kid, default_persona_slug="office")
        pid = conn.execute("SELECT persona_id FROM scenarios WHERE id = ?", (sid,)).fetchone()[0]
        office_pid = conn.execute("SELECT id FROM personas WHERE slug='office'").fetchone()[0]
        assert pid == office_pid

    def test_no_persona_raises(self) -> None:
        conn = _db(with_persona=False)
        kid = kq.add_keyword(conn, "선풍기")
        with raises(ValueError):
            kq.ensure_scenario_for_keyword(conn, kid)


class TestGetOrCreate:
    def test_creates_when_absent(self) -> None:
        conn = _db()
        kid = kq.get_or_create(conn, "무선청소기", channel="both")
        assert kid > 0
        row = conn.execute(
            "SELECT keyword, channel FROM keyword_queue WHERE id = ?", (kid,)
        ).fetchone()
        assert row[0] == "무선청소기"
        assert row[1] == "both"

    def test_reuses_pending(self) -> None:
        conn = _db()
        a = kq.add_keyword(conn, "무선청소기", channel="ali")
        b = kq.get_or_create(conn, "무선청소기")
        assert a == b  # 같은 텍스트 pending 재사용(중복 생성 안 함)
        assert conn.execute("SELECT COUNT(*) FROM keyword_queue").fetchone()[0] == 1

    def test_empty_raises(self) -> None:
        conn = _db()
        with raises(ValueError):
            kq.get_or_create(conn, "  ")


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
