"""drafts.status 6 상태 전이 머신.

출처: DB.md §12 [확정] + BACKEND §2-4 [확정].

전이도 (DB §12-1):
    collector → collected → enriched → validated → approved → published
                  ▲           │           │           │
                  │           ▼           ▼           ▼
                  └──── rejected ◄────────┴───────────┘
                  └── 재수집 시 ─┘

DB §12-2 전이 매트릭스:
    collected  → enriched
    enriched   → validated | rejected
    validated  → approved  | rejected
    approved   → published
    published  → rejected      (unpublish)
    rejected   → collected     (재시도)
"""

from __future__ import annotations

import sqlite3

# DB §12-2 전이 매트릭스
VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "collected": frozenset({"enriched"}),
    "enriched": frozenset({"validated", "rejected"}),
    "validated": frozenset({"approved", "rejected"}),
    "approved": frozenset({"published"}),
    "published": frozenset({"rejected"}),  # unpublish
    "rejected": frozenset({"collected"}),  # 재수집·재시도
}

ALL_STATES: frozenset[str] = frozenset(VALID_TRANSITIONS.keys())


class IllegalStateError(ValueError):
    """전이 매트릭스 위반."""


def current_status(conn: sqlite3.Connection, draft_id: int) -> str:
    """drafts.status 조회. 존재하지 않으면 ValueError."""
    row = conn.execute("SELECT status FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if row is None:
        raise ValueError(f"draft id={draft_id} not found")
    return str(row[0])


def transition(
    conn: sqlite3.Connection,
    draft_id: int,
    to_status: str,
    reason: str | None = None,
) -> tuple[str, str]:
    """drafts.status 전이.

    1. 현재 상태 SELECT (DB §12-3)
    2. 전이 매트릭스 lookup → 허용 안 되면 IllegalStateError
    3. UPDATE drafts SET status·status_reason — trigger가 updated_at 자동 갱신

    반환: (from_status, to_status).
    """
    if to_status not in ALL_STATES:
        raise IllegalStateError(f"unknown status: {to_status}")

    from_status = current_status(conn, draft_id)
    allowed = VALID_TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise IllegalStateError(
            f"invalid transition draft_id={draft_id}: "
            f"{from_status} → {to_status} (allowed: {sorted(allowed)})"
        )

    conn.execute(
        "UPDATE drafts SET status = ?, status_reason = ? WHERE id = ?",
        (to_status, reason, draft_id),
    )
    conn.commit()
    return from_status, to_status
