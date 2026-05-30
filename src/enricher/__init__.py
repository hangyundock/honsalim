"""enricher — Claude API 본문 생성.

출처: ARCH §3 + BACKEND §2-2·§3 + DECISIONS A·E·I [확정].
"""

from __future__ import annotations

from .category_writer import (
    CATEGORY_SYSTEM,
    build_category_prompt,
    generate_category_guide,
)
from .claude_client import (
    CACHED_SYSTEM_TEMPLATES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    ArticleResponseError,
    ClaudeClient,
    GenerateRequest,
    GenerateResult,
    build_system_blocks,
    build_user_prompt,
    is_truncated,
    split_article_response,
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
from .seo_directive import build_seo_directive
from .seo_regenerate import DEFAULT_MAX_ATTEMPTS, regenerate_until_seo_pass

__all__ = (
    "CACHED_SYSTEM_TEMPLATES",
    "CATEGORY_SYSTEM",
    "DEFAULT_CONFIG",
    "DEFAULT_MAX_ATTEMPTS",
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
    "ArticleResponseError",
    "ClaudeClient",
    "ExtractRequest",
    "ExtractResult",
    "GenerateRequest",
    "GenerateResult",
    "MetaExtractionError",
    "MetaExtractor",
    "RetryConfig",
    "RetryExhausted",
    "build_category_prompt",
    "build_seo_directive",
    "build_system_blocks",
    "build_user_prompt",
    "extract",
    "generate_category_guide",
    "is_truncated",
    "list_templates",
    "load",
    "normalize_meta",
    "parse_meta_json",
    "regenerate_until_seo_pass",
    "render",
    "retry_with_backoff",
    "split_article_response",
    "validate_meta",
    "verify_known_templates_present",
)
