"""Tests for app.core.fallback (FallbackChain)."""

from __future__ import annotations

import pytest

from app.core.cache_manager import CacheManager, InMemoryCacheBackend
from app.core.circuit_breaker import CircuitOpenError
from app.core.fallback import FallbackChain, FallbackTier


@pytest.fixture
def cache() -> CacheManager:
    return CacheManager(InMemoryCacheBackend())


class TestFallbackChain:
    async def test_missing_primary_raises(self, cache: CacheManager) -> None:
        chain = FallbackChain[int](operation_name="t").with_default(0)
        with pytest.raises(ValueError):
            await chain.execute()

    async def test_missing_default_raises(self, cache: CacheManager) -> None:
        async def primary() -> int:
            return 1

        chain = FallbackChain[int](operation_name="t").with_primary(primary)
        with pytest.raises(ValueError):
            await chain.execute()

    async def test_primary_success_writes_to_cache(self, cache: CacheManager) -> None:
        async def primary() -> dict:
            return {"v": 1}

        result = (
            await FallbackChain[dict](operation_name="t")
            .with_primary(primary)
            .with_cache(cache, "key", ttl=60)
            .with_default({})
            .execute()
        )
        assert result.tier is FallbackTier.PRIMARY
        assert result.value == {"v": 1}
        assert await cache.get("key") == {"v": 1}

    async def test_primary_fails_cache_hit(self, cache: CacheManager) -> None:
        await cache.set("key", {"cached": True}, ttl=60)

        async def primary() -> dict:
            raise RuntimeError("api down")

        result = (
            await FallbackChain[dict](operation_name="t")
            .with_primary(primary)
            .with_cache(cache, "key", ttl=60)
            .with_default({})
            .execute()
        )
        assert result.tier is FallbackTier.CACHE
        assert result.value == {"cached": True}
        assert result.primary_error == "RuntimeError"

    async def test_all_fail_returns_default(self, cache: CacheManager) -> None:
        async def primary() -> dict:
            raise RuntimeError("boom")

        result = (
            await FallbackChain[dict](operation_name="t")
            .with_primary(primary)
            .with_cache(cache, "missing-key", ttl=60)
            .with_default({"default": True})
            .execute()
        )
        assert result.tier is FallbackTier.DEFAULT
        assert result.value == {"default": True}
        assert result.primary_error == "RuntimeError"

    async def test_circuit_open_treated_as_primary_failure(self, cache: CacheManager) -> None:
        await cache.set("key", "stale-but-ok", ttl=60)

        async def primary() -> str:
            raise CircuitOpenError("kamis", retry_after=10.0)

        result = (
            await FallbackChain[str](operation_name="t")
            .with_primary(primary)
            .with_cache(cache, "key", ttl=60)
            .with_default("default")
            .execute()
        )
        assert result.tier is FallbackTier.CACHE
        assert result.value == "stale-but-ok"

    async def test_no_cache_configured_falls_to_default(self, cache: CacheManager) -> None:
        async def primary() -> int:
            raise ValueError("no")

        result = (
            await FallbackChain[int](operation_name="t")
            .with_primary(primary)
            .with_default(99)
            .execute()
        )
        assert result.tier is FallbackTier.DEFAULT
        assert result.value == 99

    async def test_default_factory(self, cache: CacheManager) -> None:
        async def primary() -> list[int]:
            raise RuntimeError("fail")

        calls = {"n": 0}

        def make_default() -> list[int]:
            calls["n"] += 1
            return [1, 2, 3]

        result = (
            await FallbackChain[list[int]](operation_name="t")
            .with_primary(primary)
            .with_default_factory(make_default)
            .execute()
        )
        assert result.value == [1, 2, 3]
        assert calls["n"] == 1

    async def test_execute_value_helper(self, cache: CacheManager) -> None:
        async def primary() -> str:
            return "ok"

        v = (
            await FallbackChain[str](operation_name="t")
            .with_primary(primary)
            .with_default("d")
            .execute_value()
        )
        assert v == "ok"

    async def test_unhandled_exception_propagates(self, cache: CacheManager) -> None:
        """allowed_exceptions에 포함되지 않은 예외는 전파."""

        class CustomCriticalError(BaseException):
            """BaseException은 기본 allowed_exceptions(Exception)에 포함되지 않음."""

        async def primary() -> int:
            raise CustomCriticalError("system-level")

        chain = (
            FallbackChain[int](operation_name="t")
            .with_primary(primary)
            .with_default(0)
        )
        with pytest.raises(CustomCriticalError):
            await chain.execute()
