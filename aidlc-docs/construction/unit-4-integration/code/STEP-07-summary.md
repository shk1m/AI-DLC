# Step 7 Summary — Fallback Chain

**Phase**: B  
**NFR**: AVAIL-03, BR-06-5, SECURITY-09, SECURITY-15

## Created files
- `backend/app/core/fallback.py` — `FallbackChain[T]` (builder pattern), `FallbackResult`, `FallbackTier`
- `backend/tests/unit/test_fallback.py` — 10 tests

## Highlights
- **3-tier**: primary → cache (stale 허용) → default (fail-closed)
- **Builder pattern**: `with_primary().with_cache().with_default()`
- **Generic[T]**: 타입 안전성 (mypy 호환)
- **CircuitOpenError 통합**: 회로 열림도 primary 실패로 간주 → 자동 캐시 전환
- **Primary 성공 시 자동 캐시 write-through**
- **로그에는 error_type만**: 스택 트레이스 미노출 (SECURITY-09)
- **fail-closed**: 어떤 경우에도 예외 전파 X (default factory 보장) — `_allowed_exceptions`로 의도적 제외 가능
