"""writer — drafts 쓰기·상태 머신.

출처: ARCH §3 + BACKEND §2-4 + DB §5·§12 [확정].
"""

from __future__ import annotations

from .article_writer import (
    create_draft,
    promote_to_article,
    save_enriched,
    save_validation_report,
)
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
    "create_draft",
    "save_enriched",
    "save_validation_report",
    "promote_to_article",
)
