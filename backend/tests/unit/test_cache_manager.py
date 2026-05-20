"""
Tests for app.core.cache_manager — InMemoryCacheBackend + CacheManager.

PBT (Hypothesis): round-trip, TTL key isolation.
"""

from __future__ import annotations

import asyncio

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.core.cache_manager import (
    CacheManager,
    InMemoryCacheBackend,
    cache_key,
    deserialize_from_cache,
    serialize_for_cache,
)


@pytest.fixture
def cache() -> CacheManager:
    return CacheManager(InMemoryCacheBackend())


class TestCacheManagerBasics:
    async def test_get_returns_none_when_missing(self, cache: CacheManager) -> None:
        assert await cache.get("missing") is None

    async def test_set_and_get(self, cache: CacheManager) -> None:
        await cache.set("k1", {"hello": "world"}, ttl=60)
        assert await cache.get("k1") == {"hello": "world"}

    async def test_set_invalid_ttl_raises(self, cache: CacheManager) -> None:
        with pytest.raises(ValueError):
            await cache.set("k", "v", ttl=0)
        with pytest.raises(ValueError):
            await cache.set("k", "v", ttl=-1)

    async def test_delete_removes_value(self, cache: CacheManager) -> None:
        await cache.set("k", "v", ttl=60)
        await cache.delete("k")
        assert await cache.get("k") is None

    async def test_invalidate_pattern(self, cache: CacheManager) -> None:
        await cache.set("prices:seafood:2026-01", "a", ttl=60)
        await cache.set("prices:seafood:2026-02", "b", ttl=60)
        await cache.set("news:keyword:onion", "c", ttl=60)

        deleted = await cache.invalidate("prices:*")
        assert deleted == 2
        assert await cache.get("prices:seafood:2026-01") is None
        assert await cache.get("news:keyword:onion") == "c"

    async def test_get_or_set_cache_miss_calls_factory(self, cache: CacheManager) -> None:
        calls = {"n": 0}

        async def factory() -> dict[str, int]:
            calls["n"] += 1
            return {"value": 42}

        r1 = await cache.get_or_set("k", factory, ttl=60)
        r2 = await cache.get_or_set("k", factory, ttl=60)
        assert r1 == r2 == {"value": 42}
        assert calls["n"] == 1  # second call hits cache

    async def test_get_or_set_does_not_cache_none(self, cache: CacheManager) -> None:
        async def factory_returning_none() -> None:
            return None

        r = await cache.get_or_set("k", factory_returning_none, ttl=60)
        assert r is None
        assert await cache.get("k") is None

    async def test_ttl_expiration(self, cache: CacheManager) -> None:
        # set very short TTL — backend must expire on next get
        backend = InMemoryCacheBackend()
        await backend.set("k", "v", ttl=1)
        # manipulate stored expiry to past
        backend._store["k"].expires_at = 0.0  # noqa: SLF001
        assert await backend.get("k") is None

    async def test_concurrent_set_get(self, cache: CacheManager) -> None:
        async def writer(i: int) -> None:
            await cache.set(f"k{i}", i, ttl=60)

        async def reader(i: int) -> int | None:
            return await cache.get(f"k{i}")

        await asyncio.gather(*(writer(i) for i in range(50)))
        results = await asyncio.gather(*(reader(i) for i in range(50)))
        assert results == list(range(50))


class TestCacheKey:
    def test_cache_key_concatenates_with_colon(self) -> None:
        assert cache_key("prices", "seafood", 2026) == "prices:seafood:2026"

    def test_serialize_deserialize_round_trip(self) -> None:
        payload = {"a": 1, "b": [1, 2, {"c": "d"}]}
        raw = serialize_for_cache(payload)
        assert deserialize_from_cache(raw) == payload


# ---------------------------------------------------------------------------
# Property-based tests (PBT-04 round-trip)
# ---------------------------------------------------------------------------
@pytest.mark.pbt
class TestCacheManagerPBT:
    @given(
        key=st.text(min_size=1, max_size=80).filter(lambda s: ":" not in s and "*" not in s),
        value=st.one_of(
            st.integers(),
            st.text(max_size=100),
            st.lists(st.integers(), max_size=20),
            st.dictionaries(st.text(max_size=20), st.integers(), max_size=10),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_round_trip(self, key: str, value: object) -> None:
        backend = InMemoryCacheBackend()
        cache = CacheManager(backend)
        await cache.set(key, value, ttl=60)
        assert await cache.get(key) == value

    @given(
        keys=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda s: ":" not in s and "*" not in s),
            min_size=2,
            max_size=20,
            unique=True,
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_keys_are_independent(self, keys: list[str]) -> None:
        """invariant: 서로 다른 키는 독립적으로 동작 (덮어쓰기 없음)."""
        backend = InMemoryCacheBackend()
        cache = CacheManager(backend)
        for i, k in enumerate(keys):
            await cache.set(k, i, ttl=60)
        for i, k in enumerate(keys):
            assert await cache.get(k) == i
