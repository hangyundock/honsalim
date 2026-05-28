"""writer.state_machine 회귀 테스트 — DB §12 전이 매트릭스.

출처: DB.md §12 + BACKEND §2-4 [확정].

규칙: state_machine 변경 시 본 테스트 100% 통과 필수.
"""

from __future__ import annotations

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


from writer.state_machine import (
    ALL_STATES,
    VALID_TRANSITIONS,
    IllegalStateError,
    current_status,
    transition,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = PROJECT_ROOT / "sql" / "migrations" / "001_initial_schema.sql"


def _fresh_db() -> sqlite3.Connection:
    """in-memory SQLite + schema 1 적용."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_001.read_text(encoding="utf-8"))
    # 테스트용 persona + scenario 1건 + draft 1건
    conn.executescript("""
        INSERT INTO personas (slug, title_ko, description) VALUES ('test-p', 'P', 'desc');
        INSERT INTO scenarios (slug, title_ko, description, persona_id)
            VALUES ('test-s', 'S', 'sdesc', 1);
        INSERT INTO drafts (scenario_id, working_title, status)
            VALUES (1, 'test draft', 'collected');
        """)
    return conn


# ─── 매트릭스 self-consistency ───────────────────────────────────────


class TestMatrix:
    def test_all_states_have_entry(self) -> None:
        """6 상태 모두 전이 매트릭스에 정의됐는지."""
        expected = {"collected", "enriched", "validated", "approved", "published", "rejected"}
        assert ALL_STATES == expected

    def test_transitions_target_known_states(self) -> None:
        """모든 전이 대상이 알려진 상태인지."""
        for from_s, targets in VALID_TRANSITIONS.items():
            for to_s in targets:
                assert to_s in ALL_STATES, f"{from_s} → {to_s} (unknown)"

    def test_published_can_only_unpublish(self) -> None:
        """published는 rejected(unpublish)만 가능."""
        assert VALID_TRANSITIONS["published"] == frozenset({"rejected"})

    def test_rejected_can_recover(self) -> None:
        """rejected → collected 재시도 경로 존재."""
        assert "collected" in VALID_TRANSITIONS["rejected"]


# ─── 정상 전이 ────────────────────────────────────────────────────────


class TestValidTransitions:
    def test_full_lifecycle(self) -> None:
        conn = _fresh_db()
        for to_s in ["enriched", "validated", "approved", "published"]:
            transition(conn, 1, to_s)
            assert current_status(conn, 1) == to_s

    def test_enriched_to_rejected(self) -> None:
        conn = _fresh_db()
        transition(conn, 1, "enriched")
        transition(conn, 1, "rejected", reason="truth gate fail")
        assert current_status(conn, 1) == "rejected"
        row = conn.execute("SELECT status_reason FROM drafts WHERE id = 1").fetchone()
        assert row[0] == "truth gate fail"

    def test_rejected_to_collected_retry(self) -> None:
        conn = _fresh_db()
        transition(conn, 1, "enriched")
        transition(conn, 1, "rejected")
        transition(conn, 1, "collected")
        assert current_status(conn, 1) == "collected"

    def test_published_to_rejected_unpublish(self) -> None:
        conn = _fresh_db()
        for s in ["enriched", "validated", "approved", "published"]:
            transition(conn, 1, s)
        transition(conn, 1, "rejected", reason="unpublish")
        assert current_status(conn, 1) == "rejected"

    def test_approved_to_validated_unapprove(self) -> None:
        """BACKEND §9 unapprove — approved → validated 회귀 허용."""
        conn = _fresh_db()
        for s in ["enriched", "validated", "approved"]:
            transition(conn, 1, s)
        transition(conn, 1, "validated", reason="cli unapprove")
        assert current_status(conn, 1) == "validated"


# ─── 위반 전이 ────────────────────────────────────────────────────────


class TestIllegalTransitions:
    def test_skip_to_published(self) -> None:
        conn = _fresh_db()
        with raises(IllegalStateError):
            transition(conn, 1, "published")  # collected → published 불가

    def test_skip_validation(self) -> None:
        conn = _fresh_db()
        transition(conn, 1, "enriched")
        with raises(IllegalStateError):
            transition(conn, 1, "approved")  # enriched → approved 불가

    def test_backward_transition(self) -> None:
        conn = _fresh_db()
        transition(conn, 1, "enriched")
        transition(conn, 1, "validated")
        with raises(IllegalStateError):
            transition(conn, 1, "enriched")  # validated → enriched 역행 불가

    def test_unknown_state(self) -> None:
        conn = _fresh_db()
        with raises(IllegalStateError):
            transition(conn, 1, "deleted")  # 알려지지 않은 상태

    def test_unknown_draft_id(self) -> None:
        conn = _fresh_db()
        with raises(ValueError):
            transition(conn, 999, "enriched")  # 존재하지 않는 draft


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
    else:
        print("pytest 미설치 — pip install pytest 후 재실행")
