# Step 5 Summary — Cache Manager

**Phase**: B  
**NFR**: PERF-05, BR-07, PBT-04

## Created files
- `backend/app/core/cache_manager.py` — `CacheBackend` Protocol, `InMemoryCacheBackend`, `CacheManager`, key helpers, singleton
- `backend/tests/unit/test_cache_manager.py` — 13 tests (basics + 2 PBT)

## Highlights
- **Protocol pattern**: 시연용 in-memory와 프로덕션용 Redis backend를 같은 인터페이스로 swap 가능
- **asyncio.Lock**: 비동기 동시 접근 안전성
- **TTL 상수**: BR-07-1~5 정확히 매핑 (TTL_PRICES=3600, TTL_NEWS=1800, TTL_ONTOLOGY/CATEGORIES=86400, TTL_TRENDS=21600)
- **Lazy expiration**: get 시 만료 검사
- **Negative caching 방지**: `get_or_set`에서 `None` 결과는 캐시 안 함
- **PBT round-trip + key isolation**: Hypothesis로 50회 임의 입력 검증
