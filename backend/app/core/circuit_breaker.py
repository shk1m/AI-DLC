"""Circuit Breaker: 외부 API 호출 복원력 패턴

상태 전이: CLOSED → OPEN → HALF_OPEN → CLOSED
- CLOSED: 정상 동작, 실패 카운트 추적
- OPEN: 요청 차단, Fallback 반환 (30초 후 HALF_OPEN)
- HALF_OPEN: 1개 요청 시험, 성공→CLOSED, 실패→OPEN
"""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerError(Exception):
    """회로 차단 시 발생하는 예외"""
    pass


class CircuitBreaker:
    """외부 서비스별 회로 차단기

    Args:
        name: 서비스 식별자
        failure_threshold: OPEN 전환 실패 횟수 (기본 5)
        recovery_timeout: HALF_OPEN 전환 대기 시간 (초, 기본 30)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0
        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable,
        fallback: Optional[Callable] = None,
        *args,
        **kwargs,
    ) -> Any:
        """회로 차단기를 통한 함수 호출

        Args:
            func: 실행할 비동기 함수
            fallback: 차단 시 대체 함수
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(
                        "circuit_breaker_half_open",
                        name=self.name,
                    )
                else:
                    logger.warning(
                        "circuit_breaker_rejected",
                        name=self.name,
                        state=self.state,
                    )
                    if fallback:
                        return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            logger.error(
                "circuit_breaker_failure",
                name=self.name,
                error=str(e),
                failure_count=self.failure_count,
            )
            if fallback:
                return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
            raise

    async def _record_success(self) -> None:
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("circuit_breaker_closed", name=self.name)

    async def _record_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_opened",
                    name=self.name,
                    failure_count=self.failure_count,
                )

    def _should_attempt_recovery(self) -> bool:
        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN


# 사전 정의된 Circuit Breaker 인스턴스
kamis_cb = CircuitBreaker("kamis", failure_threshold=5, recovery_timeout=30)
public_data_cb = CircuitBreaker("public_data", failure_threshold=5, recovery_timeout=30)
naver_cb = CircuitBreaker("naver", failure_threshold=5, recovery_timeout=30)
neptune_cb = CircuitBreaker("neptune", failure_threshold=3, recovery_timeout=60)
bedrock_cb = CircuitBreaker("bedrock", failure_threshold=3, recovery_timeout=60)
