"""Cache Manager: 인메모리 캐시 (시연용). 프로덕션: Redis/ElastiCache

BR-07 캐싱 규칙 준수:
- 시세 데이터: 1시간
- 뉴스 데이터: 30분
- 온톨로지 데이터: 24시간
- 카테고리 트리: 24시간
- 검색어 트렌드: 6시간
"""

import asyncio
import time
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class CacheEntry:
    """캐시 엔트리 (값 + 만료 시간)"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class CacheManager:
    """인메모리 캐시 매니저 (Cache-Aside 패턴)

    시연 환경에서는 인메모리 dict 사용.
    프로덕션에서는 Redis/ElastiCache로 교체.
    """

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """캐시 조회. 만료된 항목은 None 반환."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            del self._store[key]
            return None
        logger.debug("cache_hit", key=key)
        return entry.value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """캐시 저장."""
        async with self._lock:
            self._store[key] = CacheEntry(value, ttl)
        logger.debug("cache_set", key=key, ttl=ttl)

    async def invalidate(self, pattern: str) -> None:
        """패턴 매칭으로 캐시 무효화."""
        async with self._lock:
            keys_to_delete = [
                k for k in self._store if pattern in k
            ]
            for key in keys_to_delete:
                del self._store[key]
        logger.info("cache_invalidated", pattern=pattern, count=len(keys_to_delete))

    async def get_or_set(
        self, key: str, factory: Callable, ttl: int
    ) -> Any:
        """캐시 조회 후 없으면 factory 실행하여 저장 (Cache-Aside)."""
        value = await self.get(key)
        if value is not None:
            return value

        # 캐시 미스 → factory 실행
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set(key, value, ttl)
        return value

    async def clear(self) -> None:
        """전체 캐시 초기화."""
        async with self._lock:
            self._store.clear()


# 싱글톤 인스턴스
cache_manager = CacheManager()
