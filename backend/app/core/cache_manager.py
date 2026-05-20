"""
Cache Manager — Cache-Aside pattern.

NFR Mapping:
- PERF-05: 시세 API 응답 ≤500ms (캐시 히트 시)
- BR-07: TTL 정책 (시세 1h, 뉴스 30m, 온톨로지/카테고리 24h, 트렌드 6h)

시연 환경: 인메모리 구현 (`InMemoryCacheBackend`).
프로덕션 설계: Redis/ElastiCache 백엔드 (`RedisCacheBackend` 인터페이스만 제공).
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# BR-07: TTL 정책 (단위: 초)
TTL_PRICES = 60 * 60  # 1 hour
TTL_NEWS = 30 * 60  # 30 minutes
TTL_ONTOLOGY = 24 * 60 * 60  # 24 hours
TTL_CATEGORIES = 24 * 60 * 60  # 24 hours
TTL_TRENDS = 6 * 60 * 60  # 6 hours


# ---------------------------------------------------------------------------
# Backend Protocol
# ---------------------------------------------------------------------------
class CacheBackend(Protocol):
    """캐시 백엔드 인터페이스 (in-memory / redis 등 교체 가능)."""

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def keys(self, pattern: str) -> list[str]: ...
    async def clear(self) -> None: ...


# ---------------------------------------------------------------------------
# In-Memory Backend (시연용)
# ---------------------------------------------------------------------------
@dataclass
class _Entry:
    value: Any
    expires_at: float  # unix ts


@dataclass
class InMemoryCacheBackend:
    """
    Thread/async-safe in-memory cache.
    asyncio.Lock으로 동시 접근 보호.
    """

    _store: dict[str, _Entry] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.time():
                # lazy expiration
                self._store.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        if ttl <= 0:
            raise ValueError("TTL must be positive")
        async with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.time() + ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def keys(self, pattern: str) -> list[str]:
        async with self._lock:
            return [k for k in self._store if fnmatch.fnmatchcase(k, pattern)]

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()


# ---------------------------------------------------------------------------
# Cache Manager (front)
# ---------------------------------------------------------------------------
class CacheManager(Generic[T]):
    """
    Cache-Aside 패턴 wrapper.

    Usage:
        cache = CacheManager(InMemoryCacheBackend())
        data = await cache.get_or_set("prices:seafood:2026-05-20", fetch_fn, ttl=TTL_PRICES)
    """

    def __init__(self, backend: CacheBackend) -> None:
        self._backend = backend

    async def get(self, key: str) -> Any | None:
        value = await self._backend.get(key)
        if value is None:
            logger.debug("cache_miss", key=key)
        else:
            logger.debug("cache_hit", key=key)
        return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self._backend.set(key, value, ttl)
        logger.debug("cache_set", key=key, ttl=ttl)

    async def delete(self, key: str) -> None:
        await self._backend.delete(key)
        logger.debug("cache_delete", key=key)

    async def invalidate(self, pattern: str) -> int:
        """glob 패턴(`prices:*`)에 매칭되는 모든 키 삭제. 반환: 삭제된 키 수."""
        keys = await self._backend.keys(pattern)
        for k in keys:
            await self._backend.delete(k)
        logger.info("cache_invalidate", pattern=pattern, count=len(keys))
        return len(keys)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int,
    ) -> Any:
        """캐시 미스 시 factory 호출 → 결과를 set 후 반환."""
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        # None 결과는 캐시하지 않음 (negative caching 방지)
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def clear(self) -> None:
        await self._backend.clear()


# ---------------------------------------------------------------------------
# Key builders (consistent naming)
# ---------------------------------------------------------------------------
def cache_key(*parts: str | int) -> str:
    """일관된 캐시 키 생성. 예: cache_key('prices', 'seafood', '2026-05-20')"""
    return ":".join(str(p) for p in parts)


def serialize_for_cache(value: Any) -> str:
    """JSON 직렬화 (Redis 등에서 사용)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def deserialize_from_cache(raw: str) -> Any:
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_default_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """프로세스 전역 CacheManager 싱글톤 (FastAPI Depends 호환)."""
    global _default_manager
    if _default_manager is None:
        _default_manager = CacheManager(InMemoryCacheBackend())
    return _default_manager


def reset_cache_manager() -> None:
    """테스트에서 싱글톤 초기화."""
    global _default_manager
    _default_manager = None
