"""
Fallback chain — `primary → cache → default` 3-tier graceful degradation.

NFR Mapping:
- AVAIL-03: 외부 API 실패 시 자동 캐시 전환
- BR-06-5: 크롤링 실패 시 캐시 데이터로 Fallback
- SECURITY-09: Fallback 시에도 스택 트레이스 미노출 (logger에는 type 만 기록)
- SECURITY-15: fail-closed — 모든 단계 실패 시 default value 반환 (예외 X)

Usage:
    chain = (
        FallbackChain[list[Price]](operation_name="kamis_prices")
        .with_primary(lambda: kamis.fetch())
        .with_cache(cache, key="prices:seafood:today", ttl=TTL_PRICES)
        .with_default([])
    )
    prices = await chain.execute()
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from app.core.cache_manager import CacheManager
from app.core.circuit_breaker import CircuitOpenError
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class FallbackTier(str, Enum):
    PRIMARY = "primary"
    CACHE = "cache"
    DEFAULT = "default"


@dataclass
class FallbackResult(Generic[T]):
    value: T
    tier: FallbackTier
    operation_name: str
    primary_error: str | None = None  # 디버깅용. 스택 트레이스 미포함.
    cache_error: str | None = None


@dataclass
class FallbackChain(Generic[T]):
    """
    Builder + Executor.

    호출 순서:
        1. primary() 호출 → 성공이면 캐시에 저장 후 반환
        2. 실패 시 cache.get() 시도 → 성공이면 반환 (stale 허용)
        3. 모두 실패 시 default 반환 (fail-closed)
    """

    operation_name: str
    _primary: Callable[[], Awaitable[T]] | None = None
    _cache: CacheManager | None = None
    _cache_key: str | None = None
    _cache_ttl: int = 0
    _default_factory: Callable[[], T] | None = None
    _allowed_exceptions: tuple[type[BaseException], ...] = field(
        default_factory=lambda: (Exception, CircuitOpenError)
    )

    # ---- Builder API ----
    def with_primary(self, func: Callable[[], Awaitable[T]]) -> FallbackChain[T]:
        self._primary = func
        return self

    def with_cache(
        self, cache: CacheManager, key: str, ttl: int
    ) -> FallbackChain[T]:
        self._cache = cache
        self._cache_key = key
        self._cache_ttl = ttl
        return self

    def with_default(self, value: T) -> FallbackChain[T]:
        self._default_factory = lambda: value
        return self

    def with_default_factory(self, factory: Callable[[], T]) -> FallbackChain[T]:
        self._default_factory = factory
        return self

    def with_allowed_exceptions(
        self, *exceptions: type[BaseException]
    ) -> FallbackChain[T]:
        self._allowed_exceptions = tuple(exceptions)
        return self

    # ---- Executor ----
    async def execute(self) -> FallbackResult[T]:
        if self._primary is None:
            raise ValueError("primary not configured")
        if self._default_factory is None:
            raise ValueError("default not configured")

        primary_error: str | None = None
        cache_error: str | None = None

        # Tier 1: PRIMARY
        try:
            value = await self._primary()
            # 성공 시 캐시에 저장 (있으면)
            if self._cache and self._cache_key:
                try:
                    await self._cache.set(self._cache_key, value, ttl=self._cache_ttl)
                except Exception as exc:  # noqa: BLE001
                    # 캐시 쓰기 실패는 무시 (warn만)
                    logger.warning(
                        "fallback_cache_write_failed",
                        operation=self.operation_name,
                        error_type=type(exc).__name__,
                    )
            return FallbackResult(
                value=value, tier=FallbackTier.PRIMARY, operation_name=self.operation_name
            )
        except self._allowed_exceptions as exc:
            primary_error = type(exc).__name__
            logger.warning(
                "fallback_primary_failed",
                operation=self.operation_name,
                error_type=primary_error,
            )

        # Tier 2: CACHE
        if self._cache and self._cache_key:
            try:
                cached = await self._cache.get(self._cache_key)
                if cached is not None:
                    logger.info(
                        "fallback_cache_hit",
                        operation=self.operation_name,
                        cache_key=self._cache_key,
                    )
                    return FallbackResult(
                        value=cached,
                        tier=FallbackTier.CACHE,
                        operation_name=self.operation_name,
                        primary_error=primary_error,
                    )
            except Exception as exc:  # noqa: BLE001
                cache_error = type(exc).__name__
                logger.warning(
                    "fallback_cache_read_failed",
                    operation=self.operation_name,
                    error_type=cache_error,
                )

        # Tier 3: DEFAULT
        logger.error(
            "fallback_default_used",
            operation=self.operation_name,
            primary_error=primary_error,
            cache_error=cache_error,
        )
        return FallbackResult(
            value=self._default_factory(),
            tier=FallbackTier.DEFAULT,
            operation_name=self.operation_name,
            primary_error=primary_error,
            cache_error=cache_error,
        )

    async def execute_value(self) -> T:
        """
        FallbackResult가 필요 없는 경우의 헬퍼.
        값만 반환 (어느 tier에서 왔는지 알고 싶지 않을 때).
        """
        result = await self.execute()
        return result.value
