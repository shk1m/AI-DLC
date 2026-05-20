# Step 3 Summary — Structured Logging

**Phase**: B — Cross-cutting Infrastructure  
**Story**: (전체 지원)  
**NFR**: OBS-01, SECURITY-03

## Created files
- `backend/app/core/logging.py` — `configure_logging()`, `get_logger()`, `_mask_sensitive` processor
- `backend/tests/unit/test_logging.py` — 6 tests (마스킹 / JSON 파싱 / nested dict / 토큰 패턴)

## Highlights
- **Sensitive key masking** (정규식): `api_key`, `password`, `secret`, `token`, `authorization`, `client_secret` 등을 자동 `***REDACTED***`
- **Sensitive value heuristic**: 32자 이상 + 토큰 패턴이면 마스킹 (실제 키가 평문 value로 들어가도 보호)
- **Nested dict recursive masking**
- **JSON renderer (prod) / Console renderer (dev)** 토글: `ENABLE_STRUCTURED_LOGS`
- `merge_contextvars` 프로세서로 향후 Step 4의 correlation_id 자동 주입 준비
