# Step 2 Summary — Settings/Config 모듈

**Phase**: A — Project Structure Setup  
**Story**: S-1  
**NFR**: SECURITY-12 (Secrets Management)

## Created files
- `backend/app/core/config.py` — Pydantic `Settings` + `get_settings()` (lru_cache) + `reset_settings_cache()`
- `backend/tests/unit/test_config.py` — 5개 단위 테스트

## Highlights
- **SecretStr** 으로 모든 자격증명 래핑 → `repr()`/로그에 자동 마스킹 (SECURITY-12)
- `is_mock`, `has_aws_credentials`, `has_naver_credentials` 헬퍼로 호출 측에서 안전하게 분기
- `naver_auth_headers()` 메서드: 자격증명 없을 때 `ValueError` (fail-closed, SECURITY-15)
- `model_config`로 `.env` + `.env.local` 자동 로드 (extra=ignore — 추가 변수 무시)
- `lru_cache` 싱글톤 패턴 → FastAPI `Depends(get_settings)` 호환
