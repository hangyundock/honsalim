"""Claude API 클라이언트 — Anthropic SDK 진입.

출처: BACKEND §3 [확정] + DECISIONS A·E·I [확정].

Phase 2 stub:
- 클라이언트 인스턴스 생성·캐시 친화 프롬프트 빌더 구현
- 실제 .messages.create() 호출은 활성화하지 않음 (API 비용·트레이드오프 사용자 결정 영역)
- generate_article()은 dry_run=True가 기본 — 빌드된 프롬프트만 반환
- dry_run=False 호출은 사용자가 명시적으로 선택해야 안전

BACKEND §3-1 매개변수:
- 모델 claude-haiku-4-5-20251001
- max_tokens 4096
- temperature 0.4

BACKEND §3-2 캐시 친화 구조:
- system: system_base + tone_examples (cache_control breakpoint)
- user: article_main 변수 치환
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import prompt_loader

# BACKEND §3-1 [확정]
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.4

# BACKEND §3-2 캐시 대상 — system 블록 첫 부분
CACHED_SYSTEM_TEMPLATES: tuple[str, ...] = ("system_base", "tone_examples")


@dataclass
class GenerateRequest:
    """본문 생성 요청 페이로드 — BACKEND §3-2 'user, 가변' 영역."""

    scenario: dict[str, Any]
    products: list[dict[str, Any]] = field(default_factory=list)
    photos: list[dict[str, Any]] = field(default_factory=list)
    related_scenarios: list[dict[str, Any]] = field(default_factory=list)
    persona: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerateResult:
    """본문 생성 결과 — stub에서는 prompt만 채워짐."""

    system_blocks: list[dict[str, Any]]
    user_prompt: str
    response_text: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    dry_run: bool = True


def build_system_blocks() -> list[dict[str, Any]]:
    """캐시 친화 system 블록 — BACKEND §3-4.

    Anthropic prompt caching의 cache_control breakpoint를 시뮬레이션.
    실제 SDK 호출 시 본 list를 messages.create(system=...) 인자로 전달.
    """
    blocks: list[dict[str, Any]] = []
    for name in CACHED_SYSTEM_TEMPLATES:
        blocks.append(
            {
                "type": "text",
                "text": prompt_loader.load(name),
                "cache_control": {"type": "ephemeral"},
            }
        )
    return blocks


def build_user_prompt(request: GenerateRequest) -> str:
    """user 프롬프트 = article_main 변수 치환 (BACKEND §3-2)."""
    return prompt_loader.render(
        "article_main",
        scenario=request.scenario,
        products=request.products,
        photos=request.photos,
        related_scenarios=request.related_scenarios,
        persona=request.persona,
    )


class ClaudeClient:
    """Anthropic SDK 래퍼 — Phase 2 stub.

    실제 API 호출은 dry_run=False 명시 시에만. 기본 동작은 프롬프트 빌드 + 반환.
    """

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
        self._sdk_client: Any = None  # lazy

    def _get_sdk_client(self) -> Any:
        """anthropic.Anthropic 인스턴스 lazy 생성. API 키 누락 시 RuntimeError."""
        if self._sdk_client is not None:
            return self._sdk_client
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError("anthropic SDK 미설치 — pip install anthropic") from e
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 누락 — config.load_secrets() 호출 필요")
        self._sdk_client = anthropic.Anthropic(api_key=self.api_key)
        return self._sdk_client

    def generate_article(self, request: GenerateRequest, dry_run: bool = True) -> GenerateResult:
        """본문 생성. dry_run=True (기본) — 프롬프트만 반환·API 호출 없음.

        BACKEND §3-5 에러 처리는 Phase 2 후반에 RateLimitError·OverloadedError 등 추가.
        """
        system_blocks = build_system_blocks()
        user_prompt = build_user_prompt(request)

        if dry_run:
            return GenerateResult(
                system_blocks=system_blocks,
                user_prompt=user_prompt,
                response_text=None,
                usage={},
                dry_run=True,
            )

        # 실제 호출 경로 — Phase 2 후반 활성 (현재는 명시적 사용자 승인 후만)
        client = self._get_sdk_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_blocks,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return GenerateResult(
            system_blocks=system_blocks,
            user_prompt=user_prompt,
            response_text="".join(
                block.text for block in response.content if hasattr(block, "text")
            ),
            usage={
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0),
            },
            dry_run=False,
        )
