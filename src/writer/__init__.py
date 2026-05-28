"""writer — drafts 쓰기·상태 머신.

출처: ARCH §3 + BACKEND §2-4 + DB §5·§12 [확정].
"""

from __future__ import annotations

from .state_machine import (
    VALID_TRANSITIONS,
    IllegalStateError,
    current_status,
    transition,
)

__all__ = (
    "VALID_TRANSITIONS",
    "IllegalStateError",
    "transition",
    "current_status",
)
