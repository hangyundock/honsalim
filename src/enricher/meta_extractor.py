"""META-JSON 분리 추출 — body_md → title/summary/meta_description/keywords/faqs/schema 등.

출처: BACKEND §3-3 + §49 + FRONTEND §5·§6 + ARCH §296 [확정].

용도:
- article_main 응답의 META-JSON 블록 파싱 실패 시 fallback 재요청
- 또는 META-JSON과 BODY-MARKDOWN을 분리 단계로 처리

dry_run=True 기본 — 프롬프트만 빌드 반환. dry_run=False는 명시 승인 후만.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from . import prompt_loader
from .claude_client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    build_system_blocks,
)

# meta_extract.md 출력 형식 명시 필드
REQUIRED_META_FIELDS: tuple[str, ...] = (
    "title",
    "summary",
    "meta_description",
    "meta_keywords",
)

# FRONTEND §5 — 검색 결과 표시 길이 (한국어 기준)
TITLE_MAX = 60
SUMMARY_MIN = 80
SUMMARY_MAX = 180
META_DESCRIPTION_MIN = 80
META_DESCRIPTION_MAX = 160
KEYWORDS_MIN = 3
KEYWORDS_MAX = 10

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
_CODE_FENCE_OPEN_RE = re.compile(r"```(?:json)?\s*", re.IGNORECASE)
_CODE_FENCE_CLOSE_RE = re.compile(r"```\s*$")


class MetaExtractionError(ValueError):
    """META-JSON 추출·검증 실패."""


@dataclass
class ExtractRequest:
    """본문 메타 추출 요청 페이로드."""

    body_md: str
    persona: dict[str, Any] = field(default_factory=dict)
    scenario: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractResult:
    """추출 결과 — dry_run 시 extracted=None, response_text=None."""

    system_blocks: list[dict[str, Any]]
    user_prompt: str
    extracted: dict[str, Any] | None = None
    response_text: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    dry_run: bool = True


def build_user_prompt(request: ExtractRequest) -> str:
    """meta_extract.md를 body_md·persona·scenario 변수로 치환."""
    if not request.body_md.strip():
        raise MetaExtractionError("body_md 빈 입력 — 추출 불가")
    return prompt_loader.render(
        "meta_extract",
        body_md=request.body_md,
        persona=request.persona,
        scenario=request.scenario,
    )


def parse_meta_json(response_text: str) -> dict[str, Any]:
    """응답 텍스트에서 JSON 블록 추출·파싱.

    응답이 ```json ... ``` 코드 펜스로 감쌌어도 추출.
    """
    if not response_text or not response_text.strip():
        raise MetaExtractionError("응답 텍스트 비어 있음")

    text = _CODE_FENCE_OPEN_RE.sub("", response_text)
    text = _CODE_FENCE_CLOSE_RE.sub("", text)

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise MetaExtractionError("JSON 블록 발견 못함")

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise MetaExtractionError(f"JSON 파싱 실패: {e}") from e

    if not isinstance(data, dict):
        raise MetaExtractionError(f"JSON 최상위가 객체 아님: {type(data).__name__}")
    return data


def _keywords_as_list(value: Any) -> list[str]:
    """meta_keywords를 list[str]로 표준화. str(쉼표 구분) 또는 list 허용."""
    if isinstance(value, str):
        return [k.strip() for k in value.split(",") if k.strip()]
    if isinstance(value, list):
        return [str(k).strip() for k in value if str(k).strip()]
    raise MetaExtractionError(
        f"meta_keywords 형식 오류 (str 또는 list 필요): {type(value).__name__}"
    )


def validate_meta(meta: dict[str, Any]) -> None:
    """필수 필드 + 길이/개수 사전 검증.

    Raises:
        MetaExtractionError: 필드 누락 또는 길이/개수 위반.
    """
    missing = [f for f in REQUIRED_META_FIELDS if f not in meta or meta[f] in ("", None)]
    if missing:
        raise MetaExtractionError(f"필수 필드 누락: {missing}")

    title = str(meta["title"])
    if len(title) > TITLE_MAX:
        raise MetaExtractionError(f"title 길이 초과: {len(title)} > {TITLE_MAX}")

    summary = str(meta["summary"])
    if not (SUMMARY_MIN <= len(summary) <= SUMMARY_MAX):
        raise MetaExtractionError(
            f"summary 길이 위반: {len(summary)} (허용 {SUMMARY_MIN}~{SUMMARY_MAX})"
        )

    desc = str(meta["meta_description"])
    if not (META_DESCRIPTION_MIN <= len(desc) <= META_DESCRIPTION_MAX):
        raise MetaExtractionError(
            f"meta_description 길이 위반: {len(desc)} "
            f"(허용 {META_DESCRIPTION_MIN}~{META_DESCRIPTION_MAX})"
        )

    kw_list = _keywords_as_list(meta["meta_keywords"])
    if not (KEYWORDS_MIN <= len(kw_list) <= KEYWORDS_MAX):
        raise MetaExtractionError(
            f"meta_keywords 개수 위반: {len(kw_list)} (허용 {KEYWORDS_MIN}~{KEYWORDS_MAX})"
        )


def normalize_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """기본값 보강 + keywords list 표준화. 원본 dict는 변경하지 않음."""
    out = dict(meta)
    out.setdefault("faqs", [])
    out.setdefault("schema_recommended_review_eligible", [])
    out["meta_keywords"] = _keywords_as_list(out["meta_keywords"])
    return out


class MetaExtractor:
    """META-JSON 분리 추출 — claude_client 패턴 일관."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._sdk_client: Any = None

    def _get_sdk_client(self) -> Any:
        """모델 라우팅 LLM 클라이언트 lazy 생성 (claude→Anthropic SDK, 그 외→OpenRouter). 세션 #19."""
        if self._sdk_client is None:
            from enricher.claude_client import build_llm_client

            self._sdk_client = build_llm_client(self.model, self.api_key)
        return self._sdk_client

    def extract(self, request: ExtractRequest, dry_run: bool = True) -> ExtractResult:
        """body_md → META-JSON.

        dry_run=True (기본) — 프롬프트만 빌드해서 반환·API 호출 없음.
        dry_run=False — Claude API 호출 → JSON 파싱 → validate_meta → normalize.
        """
        system_blocks = build_system_blocks()
        user_prompt = build_user_prompt(request)

        if dry_run:
            return ExtractResult(
                system_blocks=system_blocks,
                user_prompt=user_prompt,
                extracted=None,
                response_text=None,
                usage={},
                dry_run=True,
            )

        client = self._get_sdk_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_blocks,
            messages=[{"role": "user", "content": user_prompt}],
        )
        response_text = "".join(block.text for block in response.content if hasattr(block, "text"))
        meta = parse_meta_json(response_text)
        validate_meta(meta)
        normalized = normalize_meta(meta)
        return ExtractResult(
            system_blocks=system_blocks,
            user_prompt=user_prompt,
            extracted=normalized,
            response_text=response_text,
            usage={
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0),
            },
            dry_run=False,
        )


def extract(
    body_md: str,
    persona: dict[str, Any] | None = None,
    scenario: dict[str, Any] | None = None,
    dry_run: bool = True,
    api_key: str | None = None,
) -> ExtractResult:
    """BACKEND §49 시그니처 — `meta_extractor.extract(body_md)` 호환 헬퍼."""
    request = ExtractRequest(
        body_md=body_md,
        persona=persona or {},
        scenario=scenario or {},
    )
    return MetaExtractor(api_key=api_key).extract(request, dry_run=dry_run)
