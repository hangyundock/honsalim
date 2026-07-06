"""LLM 클라이언트 — 모델 라우팅 진입 (claude→Anthropic SDK, deepseek→OpenRouter).

출처: BACKEND §3 [확정] + DECISIONS A·E·I [확정] + 세션 #19 DeepSeek 전환.

구조:
- 클라이언트 인스턴스 생성·캐시 친화 프롬프트 빌더 구현
- generate_article()/generate_raw()은 dry_run=True가 기본 — 빌드된 프롬프트만 반환
- dry_run=False 호출은 사용자가 명시적으로 선택해야 안전 (외부 비용)
- build_llm_client가 모델명으로 백엔드 라우팅: "claude*"→Anthropic SDK, 그 외→OpenRouter REST

BACKEND §3-1 매개변수:
- 모델 deepseek/deepseek-v4-pro (세션 #19 주인 결정 2026-06-01, 전 K-Content 통일. OpenRouter 경유).
  비용 보호는 seo_regenerate 재시도 상한·게이트 과민완화로 별도 대응. 이미지는 Google Imagen 유지.
- max_tokens 8192
- temperature 0.4

BACKEND §3-2 캐시 친화 구조:
- system: system_base + tone_examples (cache_control breakpoint)
- user: article_main 변수 치환
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import prompt_loader

# BACKEND §3-1 [확정] — max_tokens는 라이브 검증으로 상향 [확정 2026-05-30]:
# 4096은 한국어 8섹션 본문 + META-JSON + FAQ 5개에 부족(응답 truncate → BODY-END 누락 → 분리 실패).
# 8192로 상향(헤드룸 확보). BACKEND §3-1 문서도 갱신 필요.
# 세션 #15: Haiku → Sonnet (카테고리 페이지 본문 품질 우선, 저볼륨이라 비용 부담 적음, 사용자 결정).
# 비용 과다청구 방지는 enricher.seo_regenerate(재시도 상한 2)·validator.seo(게이트 과민완화)로 대응.
# ★ 세션 #19 (주인 결정 2026-06-01, 전 K-Content 통일): 본문 생성 Sonnet → DeepSeek v4-pro.
#   OpenRouter 경유(키=OPENROUTER_API_KEY, 환경변수 또는 D:\secrets\.env 공유). 라우팅은 아래 build_llm_client.
#   모델명이 "claude"로 시작하면 Anthropic SDK, 그 외(deepseek 등)는 OpenRouter REST로 전송.
DEFAULT_MODEL = "deepseek/deepseek-v4-pro"
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.4

# system_base.md §2 출력 형식 구분자 [확정]
META_START = "---META-JSON-START---"
META_END = "---META-JSON-END---"
BODY_START = "---BODY-MARKDOWN-START---"
BODY_END = "---BODY-MARKDOWN-END---"


class ArticleResponseError(ValueError):
    """article_main 응답이 system §2 형식(META-JSON + BODY-MARKDOWN)을 벗어남."""


def _between(text: str, start: str, end: str) -> str | None:
    """start와 end 구분자 사이 텍스트 (없으면 None). strip 적용."""
    i = text.find(start)
    if i == -1:
        return None
    j = text.find(end, i + len(start))
    if j == -1:
        return None
    return text[i + len(start) : j].strip()


def split_article_response(response_text: str) -> tuple[dict[str, Any], str]:
    """article_main 응답을 (meta_dict, body_md)로 분리 — system §2 형식 [확정].

    META-JSON 블록은 JSON 파싱, BODY-MARKDOWN 블록은 그대로 본문. 형식 위반 시
    ArticleResponseError (메타 추출 fallback·재요청 판단은 호출자 책임).
    """
    meta_raw = _between(response_text, META_START, META_END)
    body_md = _between(response_text, BODY_START, BODY_END)
    if meta_raw is None:
        raise ArticleResponseError(f"META-JSON 블록 없음 ({META_START}…{META_END})")
    if not body_md:
        raise ArticleResponseError(f"BODY-MARKDOWN 블록 없음/빈값 ({BODY_START}…{BODY_END})")
    try:
        meta = json.loads(meta_raw)
    except json.JSONDecodeError as e:
        raise ArticleResponseError(f"META-JSON 파싱 실패: {e}") from e
    if not isinstance(meta, dict):
        raise ArticleResponseError(f"META-JSON 최상위가 객체 아님: {type(meta).__name__}")
    return meta, body_md


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
    # SEO 키워드 세트 {primary, secondary} (seo_keywords.gate_config 형태). 세션 #15.
    # 있으면 build_user_prompt가 2층 키워드 배치 지시를 프롬프트에 주입. 없으면 무영향.
    seo: dict[str, Any] = field(default_factory=dict)
    # 재생성 피드백 — 직전 생성의 게이트 미달 issues. 있으면 프롬프트에 보완 지시로 주입(세션 #33
    # 무인 자가복원 루프 — category_writer 패턴 미러). 없으면(첫 생성) 무영향.
    feedback: list[str] | None = None


@dataclass
class GenerateResult:
    """본문 생성 결과 — stub에서는 prompt만 채워짐."""

    system_blocks: list[dict[str, Any]]
    user_prompt: str
    response_text: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    dry_run: bool = True
    stop_reason: str | None = None  # 'end_turn' 정상 · 'max_tokens' 잘림(무인 진단)


def is_truncated(result: GenerateResult) -> bool:
    """응답이 max_tokens에서 잘렸는지 — 잘리면 본문 끝 구분자 누락으로 분리 실패."""
    return result.stop_reason == "max_tokens"


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
    """user 프롬프트 = article_main 변수 치환 (BACKEND §3-2).

    request.seo({primary, secondary})가 있으면 2층 키워드 배치 지시를 주입 (세션 #15).
    """
    from .seo_directive import build_seo_directive

    seo = request.seo or {}
    seo_directive = build_seo_directive(seo.get("primary"), seo.get("secondary"))
    prompt = prompt_loader.render(
        "article_main",
        scenario=request.scenario,
        products=request.products,
        photos=request.photos,
        related_scenarios=request.related_scenarios,
        persona=request.persona,
        seo_directive=seo_directive,
    )
    # 재생성 피드백 주입(세션 #33) — 직전 게이트 미달 issues를 보완 지시로. category_writer 미러.
    if request.feedback:
        prompt += "\n\n## 지난 생성의 게이트 미달 — 반드시 보완\n- " + "\n- ".join(request.feedback)
    return prompt


# ── LLM 백엔드 라우팅 (세션 #19) ──────────────────────────────────────────
# 본문 생성 모델을 claude-sonnet-4-6 → deepseek/deepseek-v4-pro로 전면 전환(주인 결정 2026-06-01).
# OpenRouter 응답을 Anthropic Message 형태(.content[0].text·.usage.*·.stop_reason)로 감싸
# 기존 파싱(split_article_response)·게이트·잘림감지(is_truncated)를 무수정 재사용한다.
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_SHARED_ENV = Path(r"D:\secrets\.env")  # K-Content 공유 OPENROUTER_API_KEY 위치


def is_anthropic_model(model: str) -> bool:
    """claude 계열이면 True(Anthropic SDK 경로). 그 외는 OpenRouter 경로."""
    return model.lstrip().startswith("claude")


def load_openrouter_key() -> str:
    """OPENROUTER_API_KEY 조회 — 환경변수 우선, 없으면 공유 .env에서 그 키만 읽음.

    값은 반환만 하고 로그·출력하지 않는다(POLICY §14-bis-1). 다른 비밀은 로드하지 않는다.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    try:
        for line in _SHARED_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("OPENROUTER_API_KEY") and "=" in stripped:
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def _system_to_text(system: Any) -> str:
    """system 블록(list[{text}]) 또는 문자열 → 평문. OpenRouter는 system을 messages로 보냄."""
    if isinstance(system, str):
        return system
    if isinstance(system, list):
        return "\n".join(b.get("text", "") for b in system if isinstance(b, dict))
    return ""


class _TextBlock:
    """Anthropic content 블록 호환(.type·.text)."""

    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text or ""


class _Usage:
    """Anthropic usage 호환(.input_tokens·.output_tokens)."""

    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens or 0
        self.output_tokens = output_tokens or 0


class _LLMResponse:
    """OpenRouter 응답을 Anthropic Message 형태로 감싼 호환 객체."""

    def __init__(
        self,
        text: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        stop_reason: str = "end_turn",
    ) -> None:
        self.content = [_TextBlock(text)]
        self.usage = _Usage(input_tokens, output_tokens)
        self.stop_reason = stop_reason


class _AnthropicBackend:
    """claude-* 모델 — Anthropic SDK. 재시도는 retry_with_backoff(SDK 예외)로."""

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key
        self._sdk: Any = None

    def _sdk_client(self) -> Any:
        if self._sdk is None:
            try:
                import anthropic
            except ImportError as e:
                raise RuntimeError("anthropic SDK 미설치 — pip install anthropic") from e
            if not self._api_key:
                raise RuntimeError("ANTHROPIC_API_KEY 누락 — config.load_secrets() 호출 필요")
            self._sdk = anthropic.Anthropic(api_key=self._api_key)
        return self._sdk

    def create(
        self, *, model: str, max_tokens: int, temperature: Any, system: Any, messages: Any
    ) -> Any:
        import anthropic

        from .retry import retry_with_backoff

        sdk = self._sdk_client()
        kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system is not None:
            kwargs["system"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature
        return retry_with_backoff(
            lambda: sdk.messages.create(**kwargs),
            rate_limit_exc=anthropic.RateLimitError,
            overload_exc=getattr(anthropic, "OverloadedError", anthropic.APIError),
            timeout_exc=anthropic.APITimeoutError,
            bad_request_exc=anthropic.BadRequestError,
            api_error_exc=anthropic.APIError,
        )


class _OpenRouterBackend:
    """deepseek 등 — OpenRouter REST(httpx). 429/5xx/timeout 재시도 내장(무인 견고성)."""

    def __init__(self, key_loader: Any = None) -> None:
        self._key_loader = key_loader or load_openrouter_key

    def create(
        self, *, model: str, max_tokens: int, temperature: Any, system: Any, messages: Any
    ) -> _LLMResponse:
        import json as _json

        import requests

        from .retry import DEFAULT_CONFIG, _with_jitter

        key = self._key_loader()
        if not key:
            raise RuntimeError(
                r"OPENROUTER_API_KEY 누락 — 환경변수 또는 D:\secrets\.env 확인 (DeepSeek 경유 키)"
            )
        chat: list[dict[str, Any]] = []
        sys_text = _system_to_text(system)
        if sys_text:
            chat.append({"role": "system", "content": sys_text})
        chat.extend(messages or [])
        payload: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": chat}
        if temperature is not None:
            payload["temperature"] = temperature
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        cfg = DEFAULT_CONFIG
        attempt = 0
        while True:
            try:
                resp = requests.post(
                    _OPENROUTER_URL, headers=headers, data=_json.dumps(payload), timeout=300.0
                )
            except requests.exceptions.Timeout as e:
                raise RuntimeError(f"OpenRouter 타임아웃 — 다음 실행 재시도 권장: {e}") from e
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"OpenRouter 연결 오류: {e}") from e
            # ★세션 #42: 제공자 풀 오류(403 'Provider returned error' — OpenRouter가 라우팅한
            # 특정 제공자의 거부)는 일시적 — 재시도하면 다른 제공자로 붙어 성공하는 게 보통.
            # 라이브 적발: DigitalOcean 403으로 무인 사이클 0편·키워드 격리. 진짜 인증 오류
            # (401·키 폐기)는 이 조건에 안 걸려 기존 fail-fast 유지(비용·무한루프 안전).
            provider_err = resp.status_code == 403 and "Provider returned error" in resp.text
            if resp.status_code == 429 or resp.status_code >= 500 or provider_err:
                if attempt < len(cfg.rate_limit_backoffs):
                    time.sleep(_with_jitter(cfg.rate_limit_backoffs[attempt], cfg.jitter_factor))
                    attempt += 1
                    continue
                raise RuntimeError(f"OpenRouter {resp.status_code} 재시도 소진: {resp.text[:200]}")
            if resp.status_code >= 400:
                raise RuntimeError(f"OpenRouter {resp.status_code}: {resp.text[:200]}")
            try:
                data = resp.json()
            except _json.JSONDecodeError as e:
                # 200인데 본문이 불완전/비JSON(프록시·스트림 잘림 등) — 일시적 가정, 백오프 재시도.
                # 소진 시 RuntimeError(호출 측 build_and_save가 재생성으로 흡수·자가복원 §0).
                if attempt < len(cfg.rate_limit_backoffs):
                    time.sleep(_with_jitter(cfg.rate_limit_backoffs[attempt], cfg.jitter_factor))
                    attempt += 1
                    continue
                raise RuntimeError(
                    f"OpenRouter 응답 JSON 파싱 실패(잘림 의심) 재시도 소진: {e}"
                ) from e
            choices = data.get("choices")
            if not choices:
                raise RuntimeError(f"OpenRouter 응답에 choices 없음: {data.get('error') or data}")
            message = choices[0].get("message") or {}
            usage = data.get("usage") or {}
            finish = choices[0].get("finish_reason")
            return _LLMResponse(
                message.get("content") or "",
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                "max_tokens" if finish == "length" else "end_turn",
            )


class _Messages:
    """SDK의 client.messages.create 인터페이스 호환 — 백엔드로 위임."""

    def __init__(self, backend: Any) -> None:
        self._backend = backend

    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: Any = None,
        system: Any = None,
        messages: Any = None,
    ) -> Any:
        return self._backend.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages or [],
        )


class _RoutedClient:
    """모델에 맞는 백엔드로 라우팅하는 LLM 클라이언트(.messages.create)."""

    def __init__(self, backend: Any) -> None:
        self.messages = _Messages(backend)


def build_llm_client(model: str = DEFAULT_MODEL, api_key: str | None = None) -> Any:
    """모델 라우팅 LLM 클라이언트 생성 — claude→Anthropic SDK, 그 외→OpenRouter(DeepSeek)."""
    backend: Any = _AnthropicBackend(api_key) if is_anthropic_model(model) else _OpenRouterBackend()
    return _RoutedClient(backend)


class ClaudeClient:
    """LLM 클라이언트 래퍼 — 모델 라우팅(claude→Anthropic SDK, deepseek→OpenRouter, 세션 #19).

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
        """모델 라우팅 LLM 클라이언트 lazy 생성 (claude→Anthropic SDK, 그 외→OpenRouter)."""
        if self._sdk_client is None:
            self._sdk_client = build_llm_client(self.model, self.api_key)
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

        # 실제 호출 — 모델 라우팅(claude→Anthropic, deepseek→OpenRouter). 재시도는 백엔드 내부.
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
            stop_reason=getattr(response, "stop_reason", None),
        )

    def generate_raw(
        self, system_text: str, user_prompt: str, dry_run: bool = True
    ) -> GenerateResult:
        """범용 1회 생성 — 임의 system+user 프롬프트로 호출 (세션 #15 카테고리 가이드 등).

        generate_article과 동일한 모델·재시도 정책을 쓰되 프롬프트 조립을 호출 측이 책임진다.
        dry_run=True면 호출 없이 프롬프트만 반환(비용 0).
        """
        system_blocks = [
            {"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}
        ]
        if dry_run:
            return GenerateResult(
                system_blocks=system_blocks,
                user_prompt=user_prompt,
                response_text=None,
                usage={},
                dry_run=True,
            )

        # 실제 호출 — 모델 라우팅(claude→Anthropic, deepseek→OpenRouter). 재시도는 백엔드 내부.
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
            stop_reason=getattr(response, "stop_reason", None),
        )
