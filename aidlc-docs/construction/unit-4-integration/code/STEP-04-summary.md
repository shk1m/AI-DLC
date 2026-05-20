# Step 4 Summary — Correlation ID Middleware

**Phase**: B  
**NFR**: OBS-02

## Created files
- `backend/app/core/middleware.py` — `CorrelationIdMiddleware`, `get_correlation_id()`, `_is_valid_correlation_id()`
- `backend/tests/unit/test_middleware.py` — 8 tests

## Highlights
- **헤더 주입 방지**: 영숫자/하이픈/언더스코어, 64자 이내만 수용 → 그 외는 UUID4로 교체
- **structlog contextvars 바인딩**: 모든 후속 로그에 `correlation_id`/`method`/`path` 자동 포함
- **응답 헤더 전파**: 클라이언트도 trace ID 확보
- **요청 종료 시 contextvars 정리**: 다음 요청으로 누수 방지
