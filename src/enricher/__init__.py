"""enricher — Claude API 본문 생성.

출처: ARCH §3 + BACKEND §2-2·§3 + DECISIONS A·E·I [확정].
"""

from __future__ import annotations

from .claude_client import (
    CACHED_SYSTEM_TEMPLATES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    ClaudeClient,
    GenerateRequest,
    GenerateResult,
    build_system_blocks,
    build_user_prompt,
)
from .prompt_loader import (
    KNOWN_TEMPLATES,
    list_templates,
    load,
    render,
    verify_known_templates_present,
)

__all__ = (
    "ClaudeClient",
    "GenerateRequest",
    "GenerateResult",
    "build_system_blocks",
    "build_user_prompt",
    "DEFAULT_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "CACHED_SYSTEM_TEMPLATES",
    "KNOWN_TEMPLATES",
    "load",
    "render",
    "list_templates",
    "verify_known_templates_present",
)
