# Unit Test Execution

## Backend Unit Tests (Python - pytest + Hypothesis)

### 실행 방법

```bash
cd backend

# 가상환경 활성화
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 전체 단위 테스트 실행
pytest tests/unit/ -v

# PBT(Property-Based Testing) 통계 포함
pytest tests/unit/ --hypothesis-show-statistics

# 커버리지 포함
pytest tests/unit/ --cov=app --cov-report=html

# 특정 테스트 파일만 실행
pytest tests/unit/test_circuit_breaker.py -v
pytest tests/unit/test_cache_manager.py -v
```

### 테스트 목록 (97개)

| 테스트 파일 | 테스트 수 | 대상 컴포넌트 | PBT 포함 |
|-------------|:---------:|---------------|:--------:|
| `test_cache_manager.py` | 12 | CacheManager (TTL, 무효화) | ✓ |
| `test_circuit_breaker.py` | 14 | CircuitBreaker (상태 전이) | ✓ |
| `test_config.py` | 6 | Config (환경 변수 로딩) | - |
| `test_crawler.py` | 11 | NewsCrawler (파싱, 필터링) | ✓ |
| `test_fallback.py` | 13 | Fallback (체인, 캐시 전환) | ✓ |
| `test_logging.py` | 9 | StructuredLogger (JSON 포맷) | - |
| `test_middleware.py` | 7 | Middleware (CorrelationID) | - |
| `test_news_schema.py` | 16 | NewsArticle Schema (검증) | ✓ |
| `test_s3_client.py` | 9 | S3Client (업로드/다운로드) | - |
| **합계** | **97** | | |

### 예상 결과

```
========================= test session starts =========================
collected 97 items

tests/unit/test_cache_manager.py ............                    [ 12%]
tests/unit/test_circuit_breaker.py ..............                [ 27%]
tests/unit/test_config.py ......                                [ 33%]
tests/unit/test_crawler.py ...........                           [ 44%]
tests/unit/test_fallback.py .............                        [ 58%]
tests/unit/test_logging.py .........                             [ 67%]
tests/unit/test_middleware.py .......                            [ 74%]
tests/unit/test_news_schema.py ................                  [ 91%]
tests/unit/test_s3_client.py .........                           [100%]

========================= 97 passed in 12.5s ==========================
```

### PBT 준수 확인 (PBT-08: Shrinking & Reproducibility)

```bash
# Seed 기반 재현 가능성 확인
pytest tests/unit/ --hypothesis-seed=12345 -v

# 실패 시 shrunk 입력 확인
# Hypothesis가 자동으로 최소 반례를 출력
```

### 테스트 실패 시 대응

1. 실패 테스트 출력 확인
2. `--hypothesis-seed` 값으로 재현
3. 코드 수정 후 해당 테스트만 재실행
4. 전체 테스트 재실행으로 회귀 확인

---

## Frontend Unit Tests (TypeScript - fast-check)

### 실행 방법

```bash
cd frontend

# 타입 체크 (컴파일 검증)
npx tsc --noEmit

# 린트 검사
npm run lint
```

### 예상 결과
- `tsc --noEmit`: 에러 0개
- `next lint`: 경고/에러 0개
- `next build`: 성공 (First Load JS < 300kB)
