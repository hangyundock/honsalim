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
    "CACHED_SYSTEM_TEMPLATES",
    "DEFAULT_CONFIG",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "KEYWORDS_MAX",
    "KEYWORDS_MIN",
    "KNOWN_TEMPLATES",
    "META_DESCRIPTION_MAX",
    "META_DESCRIPTION_MIN",
    "REQUIRED_META_FIELDS",
    "SUMMARY_MAX",
    "SUMMARY_MIN",
    "TITLE_MAX",
    "ClaudeClient",
    "ExtractRequest",
    "ExtractResult",
    "GenerateRequest",
    "GenerateResult",
    "MetaExtractionError",
    "MetaExtractor",
    "RetryConfig",
    "RetryExhausted",
    "build_system_blocks",
    "build_user_prompt",
    "extract",
    "list_templates",
    "load",
    "normalize_meta",
    "parse_meta_json",
    "render",
    "retry_with_backoff",
    "validate_meta",
    "verify_known_templates_present",
)
