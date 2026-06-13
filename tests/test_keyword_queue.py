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
            "SELECT title_ko, persona_id, budget_min_krw FROM scenarios WHERE id = ?", (sid,)
        ).fetchone()
        assert srow[0] == "자취생 전자레인지 추천"
        assert srow[1] == 1  # 첫 페르소나 (default)
        assert srow[2] == 10000
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


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
