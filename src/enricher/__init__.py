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
from .meta_extractor import (
    KEYWORDS_MAX,
    KEYWORDS_MIN,
    META_DESCRIPTION_MAX,
    META_DESCRIPTION_MIN,
    REQUIRED_META_FIELDS,
    SUMMARY_MAX,
    SUMMARY_MIN,
    TITLE_MAX,
    ExtractRequest,
    ExtractResult,
    MetaExtractionError,
    MetaExtractor,
    extract,
    normalize_meta,
    parse_meta_json,
    validate_meta,
)
from .prompt_loader import (
    KNOWN_TEMPLATES,
    list_templates,
    load,
    render,
    verify_known_templates_present,
)
from .retry import DEFAULT_CONFIG, RetryConfig, RetryExhausted, retry_with_backoff

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
    "ExtractRequest",
    "ExtractResult",
    "MetaExtractor",
    "MetaExtractionError",
    "REQUIRED_META_FIELDS",
    "TITLE_MAX",
    "SUMMARY_MIN",
    "SUMMARY_MAX",
    "META_DESCRIPTION_MIN",
    "META_DESCRIPTION_MAX",
    "KEYWORDS_MIN",
    "KEYWORDS_MAX",
    "extract",
    "parse_meta_json",
    "validate_meta",
    "normalize_meta",
    "RetryConfig",
    "RetryExhausted",
    "DEFAULT_CONFIG",
    "retry_with_backoff",
)
