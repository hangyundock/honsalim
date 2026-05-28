"""Claude API 호출 재시도 정책 — BACKEND §3-5 + §7-3 [확정].

설계:
- 일반화된 wrapper — anthropic SDK 예외 클래스를 인자로 주입받음
- SDK 미설치 환경에서도 mock 예외로 회귀 테스트 가능
- ClaudeClient.generate_article(dry_run=False) 호출 경로에서 사용

재시도 정책 (BACKEND §3-5):
- RateLimitError → 백오프 (1·2·4초) 후 재시도 3회
- OverloadedError → 백오프 10초 후 1회 재시도
- APITimeoutError → 큐 잔류 + 다음 실행 재시도 (즉시 재시도 안 함)
- APIError 기타 → 로그 + 큐 잔류 (RuntimeError 전파)
- BadRequestError → 즉시 fail (프롬프트 오류 가능성)
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetryConfig:
    """BACKEND §3-5 + §7-3 [확정] 재시도 정책."""

    rate_limit_backoffs: tuple[float, ...] = (1.0, 2.0, 4.0)
    """RateLimitError 백오프 — 3회 재시도 (1·2·4초)."""

    overload_backoff: float = 10.0
    """OverloadedError 백오프 — 1회 재시도 (10초)."""

    overload_max_retries: int = 1
    """OverloadedError 최대 재시도 횟수."""

    jitter_factor: float = 0.1
    """백오프 ±10% 무작위 — BACKEND §7-3 [추정]."""


DEFAULT_CONFIG = RetryConfig()


class RetryExhausted(RuntimeError):
    """재시도 정책 소진."""


def _with_jitter(seconds: float, factor: float, rand: Callable[[], float] = random.random) -> float:
    """±factor 무작위 — 동시 호출 충돌 완화."""
    delta = seconds * factor * (2 * rand() - 1)
    return max(0.0, seconds + delta)


def retry_with_backoff(
    fn: Callable[[], Any],
    *,
    rate_limit_exc: type[BaseException],
    overload_exc: type[BaseException],
    timeout_exc: type[BaseException],
    bad_request_exc: type[BaseException],
    api_error_exc: type[BaseException],
    config: RetryConfig = DEFAULT_CONFIG,
    sleep_fn: Callable[[float], None] = time.sleep,
    rand_fn: Callable[[], float] = random.random,
) -> Any:
    """fn()을 BACKEND §3-5 정책으로 재시도.

    인자:
        fn: 호출 대상 (보통 lambda: client.messages.create(**kwargs))
        *_exc: anthropic SDK 예외 클래스 (mock 주입 가능)
        config: 재시도 임계값
        sleep_fn: 테스트용 mock (time.sleep 대체)
        rand_fn: 테스트용 mock (random.random 대체, jitter 결정성)

    반환: fn() 결과.

    Raises:
        RetryExhausted: 재시도 정책 소진
        RuntimeError: timeout·bad_request·api_error 즉시 또는 큐 잔류 신호
    """
    rate_attempts = 0
    overload_attempts = 0

    while True:
        try:
            return fn()
        except bad_request_exc as e:
            # 즉시 fail — 프롬프트 오류 가능성 (재시도해도 동일 결과)
            raise RuntimeError(f"BadRequestError — 프롬프트 점검 필요: {e}") from e
        except timeout_exc as e:
            # 큐 잔류 + 다음 실행 재시도 (즉시 재시도 안 함)
            raise RuntimeError(f"APITimeoutError — 다음 실행 재시도 권장: {e}") from e
        except rate_limit_exc as e:
            if rate_attempts < len(config.rate_limit_backoffs):
                sleep_fn(
                    _with_jitter(
                        config.rate_limit_backoffs[rate_attempts],
                        config.jitter_factor,
                        rand_fn,
                    )
                )
                rate_attempts += 1
                continue
            raise RetryExhausted(
                f"RateLimitError 재시도 {len(config.rate_limit_backoffs)}회 소진: {e}"
            ) from e
        except overload_exc as e:
            if overload_attempts < config.overload_max_retries:
                sleep_fn(_with_jitter(config.overload_backoff, config.jitter_factor, rand_fn))
                overload_attempts += 1
                continue
            raise RetryExhausted(
                f"OverloadedError 재시도 {config.overload_max_retries}회 소진: {e}"
            ) from e
        except api_error_exc as e:
            # 기타 APIError — 로그 + 큐 잔류 (즉시 fail, 재시도 안 함)
            raise RuntimeError(f"APIError 기타 — 큐 잔류: {e}") from e
