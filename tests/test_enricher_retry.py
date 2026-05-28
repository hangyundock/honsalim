"""enricher.retry 회귀 — BACKEND §3-5 + §7-3 [확정] 재시도 정책.

anthropic SDK 미설치 환경에서도 mock 예외 클래스로 정책 검증.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from enricher.retry import RetryConfig, RetryExhausted, _with_jitter, retry_with_backoff


# Mock 예외 — anthropic.* 대체 (SDK 미설치 환경 회귀)
class MockRateLimit(Exception):
    pass


class MockOverload(Exception):
    pass


class MockTimeout(Exception):
    pass


class MockBadRequest(Exception):
    pass


class MockAPIError(Exception):
    pass


def _exc_kwargs() -> dict[str, Any]:
    return dict(
        rate_limit_exc=MockRateLimit,
        overload_exc=MockOverload,
        timeout_exc=MockTimeout,
        bad_request_exc=MockBadRequest,
        api_error_exc=MockAPIError,
    )


class _CallTracker:
    """fn 호출 횟수·sleep 호출 시각 추적."""

    def __init__(self, raises_seq: list[BaseException | None], result: Any = "OK") -> None:
        self.raises_seq = raises_seq
        self.result = result
        self.call_count = 0
        self.sleeps: list[float] = []

    def fn(self) -> Any:
        self.call_count += 1
        if self.call_count <= len(self.raises_seq):
            exc = self.raises_seq[self.call_count - 1]
            if exc is not None:
                raise exc
        return self.result

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


# ─── 기본 동작 ────────────────────────────────────────────────────────


class TestNormalReturn:
    def test_no_error_returns_immediately(self) -> None:
        t = _CallTracker(raises_seq=[None])
        result = retry_with_backoff(
            t.fn,
            **_exc_kwargs(),
            sleep_fn=t.sleep,
            rand_fn=lambda: 0.5,  # jitter 0
        )
        assert result == "OK"
        assert t.call_count == 1
        assert t.sleeps == []  # 재시도 없음 → sleep 없음


# ─── RateLimit (3회 재시도) ───────────────────────────────────────────


class TestRateLimit:
    def test_recover_after_one_retry(self) -> None:
        """첫 호출 RateLimit → 1회 sleep 후 재호출 성공."""
        t = _CallTracker(raises_seq=[MockRateLimit("429"), None])
        result = retry_with_backoff(
            t.fn,
            **_exc_kwargs(),
            sleep_fn=t.sleep,
            rand_fn=lambda: 0.5,  # jitter 0
        )
        assert result == "OK"
        assert t.call_count == 2
        # 첫 backoff = 1.0 (jitter 0)
        assert t.sleeps == [1.0]

    def test_recover_after_three_retries(self) -> None:
        """3회 RateLimit → 모두 sleep 후 4번째 성공."""
        t = _CallTracker(
            raises_seq=[MockRateLimit("429"), MockRateLimit("429"), MockRateLimit("429"), None]
        )
        result = retry_with_backoff(
            t.fn,
            **_exc_kwargs(),
            sleep_fn=t.sleep,
            rand_fn=lambda: 0.5,  # jitter 0
        )
        assert result == "OK"
        assert t.call_count == 4
        assert t.sleeps == [1.0, 2.0, 4.0]  # 백오프 명세 [확정]

    def test_exhausted_after_three_retries(self) -> None:
        """4회 연속 RateLimit → RetryExhausted."""
        t = _CallTracker(raises_seq=[MockRateLimit("429")] * 4)
        with raises(RetryExhausted):
            retry_with_backoff(
                t.fn,
                **_exc_kwargs(),
                sleep_fn=t.sleep,
                rand_fn=lambda: 0.5,
            )
        # 4번 호출 (첫 + 3 재시도), 3 sleep
        assert t.call_count == 4
        assert len(t.sleeps) == 3


# ─── Overloaded (1회 재시도) ──────────────────────────────────────────


class TestOverloaded:
    def test_recover_after_one_retry(self) -> None:
        t = _CallTracker(raises_seq=[MockOverload("529"), None])
        result = retry_with_backoff(
            t.fn,
            **_exc_kwargs(),
            sleep_fn=t.sleep,
            rand_fn=lambda: 0.5,
        )
        assert result == "OK"
        assert t.call_count == 2
        assert t.sleeps == [10.0]  # OverloadedError 백오프 10초 [확정]

    def test_exhausted_after_one_retry(self) -> None:
        t = _CallTracker(raises_seq=[MockOverload("529"), MockOverload("529")])
        with raises(RetryExhausted):
            retry_with_backoff(
                t.fn,
                **_exc_kwargs(),
                sleep_fn=t.sleep,
                rand_fn=lambda: 0.5,
            )
        assert t.call_count == 2
        assert t.sleeps == [10.0]


# ─── Timeout · BadRequest · API 기타 (즉시 fail) ──────────────────────


class TestNoRetryErrors:
    def test_timeout_no_retry(self) -> None:
        """APITimeoutError → 큐 잔류, 즉시 RuntimeError (재시도 안 함)."""
        t = _CallTracker(raises_seq=[MockTimeout("timeout")])
        with raises(RuntimeError):
            retry_with_backoff(
                t.fn,
                **_exc_kwargs(),
                sleep_fn=t.sleep,
            )
        assert t.call_count == 1
        assert t.sleeps == []

    def test_bad_request_no_retry(self) -> None:
        """BadRequestError → 프롬프트 점검 필요, 즉시 fail."""
        t = _CallTracker(raises_seq=[MockBadRequest("invalid prompt")])
        with raises(RuntimeError):
            retry_with_backoff(t.fn, **_exc_kwargs(), sleep_fn=t.sleep)
        assert t.call_count == 1
        assert t.sleeps == []

    def test_api_error_no_retry(self) -> None:
        """APIError 기타 → 큐 잔류, 즉시 fail."""
        t = _CallTracker(raises_seq=[MockAPIError("500")])
        with raises(RuntimeError):
            retry_with_backoff(t.fn, **_exc_kwargs(), sleep_fn=t.sleep)
        assert t.call_count == 1
        assert t.sleeps == []


# ─── 혼합 시나리오 ────────────────────────────────────────────────────


class TestMixedScenarios:
    def test_rate_limit_then_overload_independent_counters(self) -> None:
        """RateLimit 재시도와 Overloaded 재시도는 별도 카운터."""
        t = _CallTracker(
            raises_seq=[
                MockRateLimit("429"),  # 재시도 1 (rate=1)
                MockRateLimit("429"),  # 재시도 2 (rate=2)
                MockOverload("529"),  # 재시도 3 (overload=1)
                None,  # 성공
            ]
        )
        result = retry_with_backoff(
            t.fn,
            **_exc_kwargs(),
            sleep_fn=t.sleep,
            rand_fn=lambda: 0.5,
        )
        assert result == "OK"
        assert t.call_count == 4
        # sleeps: rate 1.0·2.0 + overload 10.0
        assert t.sleeps == [1.0, 2.0, 10.0]


# ─── Jitter ───────────────────────────────────────────────────────────


class TestJitter:
    def test_jitter_zero_when_rand_05(self) -> None:
        """rand()=0.5 → jitter delta = 0 → 원본 그대로."""
        assert _with_jitter(10.0, 0.1, rand=lambda: 0.5) == 10.0

    def test_jitter_negative_when_rand_0(self) -> None:
        """rand()=0 → -10% factor."""
        # factor 0.1 → delta = 10 * 0.1 * (2*0 - 1) = -1.0
        assert _with_jitter(10.0, 0.1, rand=lambda: 0.0) == 9.0

    def test_jitter_positive_when_rand_1(self) -> None:
        """rand()=1 → +10% factor."""
        # factor 0.1 → delta = 10 * 0.1 * (2*1 - 1) = +1.0
        assert _with_jitter(10.0, 0.1, rand=lambda: 1.0) == 11.0

    def test_jitter_clamped_at_zero(self) -> None:
        """음수가 되지 않음."""
        assert _with_jitter(0.5, 1.0, rand=lambda: 0.0) == 0.0


# ─── RetryConfig ──────────────────────────────────────────────────────


class TestRetryConfig:
    def test_defaults_match_backend_spec(self) -> None:
        """BACKEND §3-5 [확정] 명세 정합."""
        cfg = RetryConfig()
        assert cfg.rate_limit_backoffs == (1.0, 2.0, 4.0)
        assert cfg.overload_backoff == 10.0
        assert cfg.overload_max_retries == 1
        assert cfg.jitter_factor == 0.1


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
