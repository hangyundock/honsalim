"""collector.scenario_loader 회귀 테스트.

출처: ARCH §3 + BACKEND §2-1 + DB §7 [확정].
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

from collector.scenario_loader import (
    IN_PROGRESS_STATES,
    list_active_scenarios,
    next_scenarios_for_collection,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"
SEED_001 = PROJECT_ROOT / "sql" / "seeds" / "001_personas_scenarios.sql"


def _seeded_db() -> sqlite3.Connection:
    """in-memory SQLite + schema + seeds (personas 3, scenarios 10)."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    conn.executescript(SEED_001.read_text(encoding="utf-8"))
    return conn


class TestListActive:
    def test_loads_all_seed_scenarios(self) -> None:
        """seed 적용 후 active=1 시나리오 10개 모두 로드."""
        conn = _seeded_db()
        rows = list_active_scenarios(conn)
        assert len(rows) == 10

    def test_priority_descending(self) -> None:
        """priority DESC 정렬 검증."""
        conn = _seeded_db()
        rows = list_active_scenarios(conn)
        priorities = [r.priority for r in rows]
        assert priorities == sorted(priorities, reverse=True)

    def test_first_is_highest_priority(self) -> None:
        """최우선 시나리오 = priority 100 (wonroom-cheot-jachi-30)."""
        conn = _seeded_db()
        rows = list_active_scenarios(conn)
        assert rows[0].priority == 100
        assert rows[0].slug == "wonroom-cheot-jachi-30"

    def test_persona_slug_populated(self) -> None:
        conn = _seeded_db()
        rows = list_active_scenarios(conn)
        valid_personas = {"cheot-jachi", "homeoffice", "minimal-life"}
        for r in rows:
            assert r.persona_slug in valid_personas

    def test_inactive_excluded(self) -> None:
        """active=0 으로 한 시나리오는 결과에서 제외."""
        conn = _seeded_db()
        conn.execute("UPDATE scenarios SET active = 0 WHERE slug = 'wonroom-cheot-jachi-30'")
        conn.commit()
        rows = list_active_scenarios(conn)
        assert len(rows) == 9
        assert all(r.slug != "wonroom-cheot-jachi-30" for r in rows)


class TestNextForCollection:
    def test_empty_drafts_returns_all_active(self) -> None:
        """drafts 비어있을 때는 active 시나리오 모두 큐 대상."""
        conn = _seeded_db()
        queue = next_scenarios_for_collection(conn, limit=20)
        assert len(queue) == 10

    def test_in_progress_excluded(self) -> None:
        """drafts에 collected/enriched/validated/approved 진행 중이면 큐에서 제외."""
        conn = _seeded_db()
        # 1번 시나리오(wonroom-cheot-jachi-30)를 collected 상태로 진행 중으로 표시
        sid = conn.execute(
            "SELECT id FROM scenarios WHERE slug='wonroom-cheot-jachi-30'"
        ).fetchone()[0]
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (?, 'collected')", (sid,))
        conn.commit()
        queue = next_scenarios_for_collection(conn, limit=20)
        assert len(queue) == 9
        assert all(r.slug != "wonroom-cheot-jachi-30" for r in queue)

    def test_published_not_excluded(self) -> None:
        """published(발행됨)는 재집행 가능 — 큐에 다시 들어옴."""
        conn = _seeded_db()
        sid = conn.execute(
            "SELECT id FROM scenarios WHERE slug='wonroom-cheot-jachi-30'"
        ).fetchone()[0]
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (?, 'published')", (sid,))
        conn.commit()
        queue = next_scenarios_for_collection(conn, limit=20)
        assert any(r.slug == "wonroom-cheot-jachi-30" for r in queue)

    def test_rejected_not_excluded(self) -> None:
        """rejected는 재시도 가능."""
        conn = _seeded_db()
        sid = conn.execute(
            "SELECT id FROM scenarios WHERE slug='wonroom-cheot-jachi-30'"
        ).fetchone()[0]
        conn.execute("INSERT INTO drafts (scenario_id, status) VALUES (?, 'rejected')", (sid,))
        conn.commit()
        queue = next_scenarios_for_collection(conn, limit=20)
        assert any(r.slug == "wonroom-cheot-jachi-30" for r in queue)

    def test_in_progress_states_definition(self) -> None:
        """IN_PROGRESS_STATES가 의도한 4개와 일치."""
        assert IN_PROGRESS_STATES == ("collected", "enriched", "validated", "approved")

    def test_limit_respected(self) -> None:
        conn = _seeded_db()
        queue = next_scenarios_for_collection(conn, limit=3)
        assert len(queue) == 3


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
