# Step 6 Summary — Circuit Breaker

**Phase**: B  
**NFR**: AVAIL-03, NFR Design 1.1

## Created files
- `backend/app/core/circuit_breaker.py` — `CircuitBreaker`, `CircuitOpenError`, `CircuitBreakerRegistry`, `get_circuit_breaker()`
- `backend/tests/unit/test_circuit_breaker.py` — 11 tests (basics + registry + 1 PBT)

## Highlights
- **상태 머신**: CLOSED → OPEN → HALF_OPEN → CLOSED 정확 구현
- **HALF_OPEN 시험 호출**: 1건 성공 시 CLOSED, 실패 시 즉시 OPEN
- **asyncio.Lock**: 상태 전이 안전성 (실제 호출은 lock 밖)
- **Registry 싱글톤**: 5개 표준 CB 인스턴스 (`kamis`, `public_data`, `naver`, `neptune`, `bedrock`)
- **PBT invariant**: 임의 호출 시퀀스에서 `0 ≤ failure_count ≤ threshold` 검증
- **CircuitOpenError에 retry_after 포함** → 호출 측 백오프 가능
