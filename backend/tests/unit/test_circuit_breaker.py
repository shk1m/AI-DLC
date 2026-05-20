"""Tests for app.core.circuit_breaker."""

from __future__ import annotations

import asyncio

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    clear_circuit_breakers,
    get_circuit_breaker,
)


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    clear_circuit_breakers()
    yield
    clear_circuit_breakers()


class _BoomError(RuntimeError):
    pass


async def _ok() -> int:
    return 1


async def _fail() -> int:
    raise _BoomError("boom")


class TestCircuitBreakerBasics:
    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValueError):
            CircuitBreaker(name="x", failure_threshold=0)
        with pytest.raises(ValueError):
            CircuitBreaker(name="x", recovery_timeout=0)

    async def test_starts_closed(self) -> None:
        cb = CircuitBreaker(name="x")
        assert cb.state is CircuitState.CLOSED
        assert cb.failure_count == 0

    async def test_successful_call_resets_failures(self) -> None:
        cb = CircuitBreaker(name="x", failure_threshold=3)
        with pytest.raises(_BoomError):
            await cb.call(_fail)
        assert cb.failure_count == 1
        await cb.call(_ok)
        assert cb.failure_count == 0
        assert cb.state is CircuitState.CLOSED

    async def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(name="x", failure_threshold=3)
        for _ in range(3):
            with pytest.raises(_BoomError):
                await cb.call(_fail)
        assert cb.state is CircuitState.OPEN

    async def test_open_circuit_rejects_calls(self) -> None:
        cb = CircuitBreaker(name="x", failure_threshold=2, recovery_timeout=10)
        for _ in range(2):
            with pytest.raises(_BoomError):
                await cb.call(_fail)
        # Now OPEN
        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(_ok)
        assert exc_info.value.name == "x"
        assert exc_info.value.retry_after > 0

    async def test_recovers_via_half_open(self) -> None:
        cb = CircuitBreaker(name="x", failure_threshold=2, recovery_timeout=0.05)
        for _ in range(2):
            with pytest.raises(_BoomError):
                await cb.call(_fail)
        assert cb.state is CircuitState.OPEN

        await asyncio.sleep(0.1)  # 충분히 대기
        # 다음 호출에서 HALF_OPEN 전이 + 성공 시 CLOSED
        result = await cb.call(_ok)
        assert result == 1
        assert cb.state is CircuitState.CLOSED

    async def test_half_open_failure_reopens(self) -> None:
        cb = CircuitBreaker(name="x", failure_threshold=2, recovery_timeout=0.05)
        for _ in range(2):
            with pytest.raises(_BoomError):
                await cb.call(_fail)
        await asyncio.sleep(0.1)
        # HALF_OPEN 상태에서 실패 → 즉시 OPEN
        with pytest.raises(_BoomError):
            await cb.call(_fail)
        assert cb.state is CircuitState.OPEN


class TestCircuitBreakerRegistry:
    def test_get_or_create_returns_same_instance(self) -> None:
        a = get_circuit_breaker("kamis")
        b = get_circuit_breaker("kamis")
        assert a is b

    def test_different_names_yield_different_instances(self) -> None:
        a = get_circuit_breaker("kamis")
        b = get_circuit_breaker("naver")
        assert a is not b


# ---------------------------------------------------------------------------
# Property-based: invariant — failure_count ∈ [0, threshold]
# ---------------------------------------------------------------------------
@pytest.mark.pbt
class TestCircuitBreakerPBT:
    @given(
        threshold=st.integers(min_value=1, max_value=20),
        outcomes=st.lists(st.booleans(), min_size=0, max_size=50),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    async def test_failure_count_invariant(
        self, threshold: int, outcomes: list[bool]
    ) -> None:
        """invariant: 어떤 호출 시퀀스든 0 ≤ failure_count ≤ threshold."""
        cb = CircuitBreaker(
            name="prop", failure_threshold=threshold, recovery_timeout=999
        )

        async def behaviour(succeed: bool) -> int:
            if not succeed:
                raise _BoomError("boom")
            return 1

        for ok in outcomes:
            try:
                await cb.call(lambda ok=ok: behaviour(ok))
            except (_BoomError, CircuitOpenError):
                pass
            assert 0 <= cb.failure_count <= threshold

        # 추가: OPEN 상태와 failure_count 일관성
        if cb.state is CircuitState.OPEN:
            assert cb.failure_count >= threshold or cb.failure_count == 0
