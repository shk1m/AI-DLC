"""
Circuit Breaker — 회로 차단기 패턴.

NFR Mapping:
- AVAIL-03: 외부 API 장애 자동 감지 + Fallback
- NFR Design 1.1: CLOSED → OPEN → HALF_OPEN → CLOSED 상태 머신

상태 전이:
  CLOSED:    정상. 실패 카운트 추적. failure_threshold 초과 → OPEN
  OPEN:      모든 호출 즉시 거부 (CircuitOpenError). recovery_timeout 후 → HALF_OPEN
  HALF_OPEN: 1개 시험 호출 허용. 성공 → CLOSED, 실패 → OPEN
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Circuit이 OPEN 상태일 때 호출 시 발생."""

    def __init__(self, name: str, retry_after: float) -> None:
        super().__init__(f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s")
        self.name = name
        self.retry_after = retry_after


class CircuitBreaker:
    """
    비동기 함수 호출에 회로 차단을 적용.

    Usage:
        cb = CircuitBreaker(name="kamis", failure_threshold=5, recovery_timeout=30)
        result = await cb.call(lambda: kamis_api.fetch_prices())
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> None:
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    # ---- public state inspection (테스트/모니터링용) ----
    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    # ---- core call wrapper ----
    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        외부 호출을 회로로 감싸 실행.

        Raises:
            CircuitOpenError: 회로가 OPEN인 경우
            (원본 예외): 실제 호출 실패 시
        """
        async with self._lock:
            self._maybe_transition_to_half_open()
            if self._state is CircuitState.OPEN:
                retry_after = self._time_until_recovery()
                logger.warning(
                    "circuit_open_reject",
                    cb_name=self.name,
                    retry_after_seconds=retry_after,
                )
                raise CircuitOpenError(self.name, retry_after)

        # 실제 호출은 lock 밖에서 (긴 대기 차단 방지)
        try:
            result = await func()
        except self.expected_exceptions as exc:
            await self._record_failure(exc)
            raise

        await self._record_success()
        return result

    # ---- state transitions ----
    def _maybe_transition_to_half_open(self) -> None:
        """OPEN 상태에서 recovery_timeout 경과 시 HALF_OPEN으로 전이."""
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if time.time() - self._opened_at >= self.recovery_timeout:
                logger.info("circuit_half_open", cb_name=self.name)
                self._state = CircuitState.HALF_OPEN

    def _time_until_recovery(self) -> float:
        if self._opened_at is None:
            return 0.0
        elapsed = time.time() - self._opened_at
        return max(0.0, self.recovery_timeout - elapsed)

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                logger.info("circuit_close_after_recovery", cb_name=self.name)
                self._state = CircuitState.CLOSED
                self._opened_at = None
            self._failure_count = 0

    async def _record_failure(self, exc: BaseException) -> None:
        async with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                # HALF_OPEN에서 실패 → 즉시 OPEN
                logger.warning(
                    "circuit_reopen",
                    cb_name=self.name,
                    error_type=type(exc).__name__,
                )
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                return

            self._failure_count += 1
            logger.warning(
                "circuit_failure",
                cb_name=self.name,
                failure_count=self._failure_count,
                threshold=self.failure_threshold,
                error_type=type(exc).__name__,
            )
            if self._failure_count >= self.failure_threshold:
                logger.error("circuit_open", cb_name=self.name)
                self._state = CircuitState.OPEN
                self._opened_at = time.time()

    # ---- test helpers ----
    def reset(self) -> None:
        """테스트에서 상태 초기화."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None


# ---------------------------------------------------------------------------
# Registry — Named circuit breakers (NFR Design 1.1)
# ---------------------------------------------------------------------------
class CircuitBreakerRegistry:
    """프로세스 전역 CB 인스턴스 관리."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            settings = get_settings()
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold or settings.cb_failure_threshold,
                recovery_timeout=recovery_timeout or settings.cb_recovery_timeout,
            )
        return self._breakers[name]

    def reset_all(self) -> None:
        for cb in self._breakers.values():
            cb.reset()

    def clear(self) -> None:
        self._breakers.clear()


_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    failure_threshold: int | None = None,
    recovery_timeout: float | None = None,
) -> CircuitBreaker:
    """등록된 또는 신규 CB를 가져옴.

    Standard names per NFR Design 1.1:
        - "kamis"        (5 failures, 30s recovery)
        - "public_data"  (5 failures, 30s recovery)
        - "naver"        (5 failures, 30s recovery)
        - "neptune"      (3 failures, 60s recovery)
        - "bedrock"      (3 failures, 60s recovery)
    """
    return _registry.get_or_create(name, failure_threshold, recovery_timeout)


def reset_circuit_breakers() -> None:
    """테스트에서 모든 CB 리셋."""
    _registry.reset_all()


def clear_circuit_breakers() -> None:
    """테스트에서 레지스트리 비움."""
    _registry.clear()


# --- Pre-defined instances for Unit 2 adapters ---
kamis_cb = get_circuit_breaker("kamis", failure_threshold=5, recovery_timeout=30)
public_data_cb = get_circuit_breaker("public_data", failure_threshold=5, recovery_timeout=30)
naver_cb = get_circuit_breaker("naver", failure_threshold=5, recovery_timeout=30)
neptune_cb = get_circuit_breaker("neptune", failure_threshold=3, recovery_timeout=60)
bedrock_cb = get_circuit_breaker("bedrock", failure_threshold=3, recovery_timeout=60)
