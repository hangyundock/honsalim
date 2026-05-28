"""Schema.org JSON-LD 빌더 — Article 타입.

출처: POLICY §4 + VALIDATOR §8 + FRONTEND §5 [확정].

용도:
- enricher.meta_extractor 결과 + 시나리오 정보 → Schema.org Article JSON-LD 문자열
- validator.check_schema의 ARTICLE_REQUIRED 10필드 모두 충족
- 페이지 <head>에 <script type="application/ld+json"> 삽입용

키워드는 Schema.org 권장에 따라 쉼표 구분 문자열로 출력 (list 입력도 허용).
ItemList·Product·Review 등 다른 @type은 후속 (validator는 이미 지원).
"""

from __future__ import annotations

import json
from typing import Any

# POLICY §4 + VALIDATOR §8 ARTICLE_REQUIRED와 동일
REQUIRED_META_FIELDS: tuple[str, ...] = ("title", "meta_description")

DEFAULT_AUTHOR_NAME = "혼살림 운영자"
DEFAULT_PUBLISHER_NAME = "혼살림"
SCHEMA_CONTEXT = "https://schema.org"


def _normalize_keywords(value: Any) -> str | None:
    """meta_keywords를 Schema.org 권장 쉼표 구분 문자열로.

    str 입력은 그대로, list 입력은 쉼표로 join. 빈/None은 None 반환.
    """
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, list):
        joined = ", ".join(str(k).strip() for k in value if str(k).strip())
        return joined or None
    return str(value).strip() or None


def _validate_inputs(meta: dict[str, Any], scenario: dict[str, Any]) -> None:
    """필수 입력 검증 — 빌드 전 사전 차단."""
    missing_meta = [f for f in REQUIRED_META_FIELDS if not meta.get(f)]
    if missing_meta:
        raise ValueError(f"meta 필수 필드 누락: {missing_meta}")
    if not scenario.get("slug"):
        raise ValueError("scenario.slug 누락 — mainEntityOfPage URL 생성 불가")


def build_article_jsonld(
    meta: dict[str, Any],
    scenario: dict[str, Any],
    site_base_url: str,
    image_url: str,
    published_at: str,
    modified_at: str | None = None,
    author_name: str = DEFAULT_AUTHOR_NAME,
    publisher_name: str = DEFAULT_PUBLISHER_NAME,
) -> str:
    """Article JSON-LD 문자열 생성.

    인자:
        meta: meta_extractor 결과 (필수: title, meta_description / 선택: meta_keywords)
        scenario: {slug, ...} — slug로 mainEntityOfPage 생성
        site_base_url: "https://honsalim.com" (끝 슬래시 자동 처리)
        image_url: 대표 이미지 절대 URL
        published_at: ISO 8601 (예: "2026-05-28" 또는 "2026-05-28T11:00:00+09:00")
        modified_at: ISO 8601. None이면 published_at과 동일
        author_name: 기본 "혼살림 운영자" (Person)
        publisher_name: 기본 "혼살림" (Organization)

    반환: JSON 문자열 (한국어 보존, ensure_ascii=False).

    Raises:
        ValueError: 필수 입력 누락.
    """
    _validate_inputs(meta, scenario)

    base = site_base_url.rstrip("/")
    main_entity_url = f"{base}/articles/{scenario['slug']}"

    doc: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Article",
        "headline": str(meta["title"]),
        "description": str(meta["meta_description"]),
        "image": image_url,
        "datePublished": published_at,
        "dateModified": modified_at or published_at,
        "author": {"@type": "Person", "name": author_name},
        "publisher": {"@type": "Organization", "name": publisher_name},
        "mainEntityOfPage": main_entity_url,
    }

    keywords = _normalize_keywords(meta.get("meta_keywords"))
    if keywords:
        doc["keywords"] = keywords

    return json.dumps(doc, ensure_ascii=False, separators=(", ", ": "))
