# NFR Design Patterns (비기능 설계 패턴)

---

## 1. 복원력 패턴 (Resilience Patterns)

### 1.1 Circuit Breaker (회로 차단기)
**적용 대상**: 외부 API 호출 (KAMIS, 공공데이터, 네이버)

```
상태: CLOSED → OPEN → HALF_OPEN → CLOSED

CLOSED (정상):
  - 요청 통과, 실패 카운트 추적
  - 실패 5회 연속 → OPEN 전환

OPEN (차단):
  - 요청 즉시 실패 (외부 호출 안 함)
  - 캐시된 데이터 반환 (Fallback)
  - 30초 후 → HALF_OPEN 전환

HALF_OPEN (시험):
  - 1개 요청만 통과
  - 성공 → CLOSED, 실패 → OPEN
```

### 1.2 Retry with Exponential Backoff
**적용 대상**: 모든 외부 API 호출

```
재시도 전략:
  - 최대 3회 재시도
  - 대기 시간: 1초 → 2초 → 4초 (exponential)
  - Jitter: ±500ms (thundering herd 방지)
  - 타임아웃: 개별 요청 5초, 전체 15초
```

### 1.3 Bulkhead (격벽)
**적용 대상**: 서비스 간 격리

```
격벽 구성:
  - 외부 API 호출: 동시 최대 10개 연결
  - Neptune 쿼리: 동시 최대 5개 연결
  - Bedrock 호출: 동시 최대 3개 연결
  - 각 격벽 독립 → 하나 실패해도 다른 서비스 영향 없음
```

### 1.4 Fallback (대체 응답)
**적용 대상**: 모든 외부 의존성

```
Fallback 체인:
  1. 실시간 API 호출 시도
  2. 실패 → 캐시된 데이터 반환 (stale 허용)
  3. 캐시 없음 → 기본 응답 ("데이터 조회 불가")
  4. 로그 기록 + 모니터링 알림
```

---

## 2. 성능 패턴 (Performance Patterns)

### 2.1 Cache-Aside (캐시 사이드)
**적용 대상**: 시세 데이터, 온톨로지, 카테고리

```
읽기:
  1. 캐시 조회
  2. 캐시 히트 → 즉시 반환
  3. 캐시 미스 → DB/API 조회 → 캐시 저장 → 반환

쓰기:
  1. DB/API 업데이트
  2. 캐시 무효화 (invalidate)

TTL 설정:
  - 시세 데이터: 1시간
  - 온톨로지: 24시간
  - 뉴스: 30분
  - 카테고리 트리: 24시간
```

### 2.2 Async Processing (비동기 처리)
**적용 대상**: 크롤링, 임베딩, 외부 API 병렬 호출

```
패턴:
  - FastAPI async/await 전면 활용
  - 독립 API 호출은 asyncio.gather()로 병렬화
  - 크롤링은 백그라운드 태스크 (BackgroundTasks)
  - 임베딩 적재는 비동기 배치 처리
```

### 2.3 Connection Pooling
**적용 대상**: PostgreSQL, Neptune

```
PostgreSQL:
  - SQLAlchemy async pool
  - pool_size: 10, max_overflow: 20
  - pool_timeout: 30초

Neptune:
  - Gremlin 연결 풀
  - max_connections: 5
```

### 2.4 Response Streaming
**적용 대상**: 챗봇 응답

```
WebSocket 스트리밍:
  - LLM 토큰 생성 즉시 전송
  - 클라이언트에서 점진적 렌더링
  - 타이핑 애니메이션 효과 자연스럽게 구현
```

---

## 3. 보안 패턴 (Security Patterns)

### 3.1 Input Validation Gateway
**적용 대상**: 모든 API 엔드포인트 (SECURITY-05)

```
계층:
  1. Pydantic 스키마 검증 (타입, 범위, 형식)
  2. 비즈니스 규칙 검증 (서비스 레이어)
  3. SQL Injection 방지 (SQLAlchemy 파라미터 바인딩)
  4. XSS 방지 (HTML 이스케이프)
```

### 3.2 Security Headers Middleware
**적용 대상**: Next.js 응답 (SECURITY-04)

```
미들웨어 설정:
  Content-Security-Policy: default-src 'self'; script-src 'self'
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
```

### 3.3 Secrets Management
**적용 대상**: API 키, DB 자격증명 (SECURITY-12)

```
시연 환경: .env 파일 (gitignore)
프로덕션: AWS Secrets Manager
  - 자동 로테이션 설정
  - 애플리케이션 시작 시 로드
  - 메모리에만 보관 (로그 미출력)
```

### 3.4 Global Error Handler (SECURITY-15)
```
패턴:
  - FastAPI exception_handler 등록
  - 모든 예외 → 구조화 로그 기록
  - 클라이언트 응답: 제네릭 메시지만 (스택 트레이스 X)
  - 500 에러: {"error": "Internal Server Error", "correlation_id": "xxx"}
  - 인증 실패 시: fail-closed (접근 거부)
```

---

## 4. 관찰성 패턴 (Observability Patterns)

### 4.1 Structured Logging (SECURITY-03)
```
로그 포맷 (JSON):
{
  "timestamp": "2026-05-20T12:00:00Z",
  "level": "INFO",
  "correlation_id": "uuid",
  "service": "price_service",
  "method": "get_current_prices",
  "duration_ms": 150,
  "message": "Price data fetched",
  "metadata": { "category": "seafood", "item_count": 25 }
}

금지 항목: 비밀번호, API 키, 개인정보
```

### 4.2 Correlation ID Middleware
```
흐름:
  1. 요청 수신 → X-Correlation-ID 헤더 확인
  2. 없으면 UUID 생성
  3. 모든 로그에 correlation_id 포함
  4. 외부 API 호출 시 헤더로 전파
  5. 응답에 X-Correlation-ID 포함
```

### 4.3 Health Check Endpoint
```
GET /health
응답:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "neptune": "ok",
    "bedrock": "ok",
    "cache": "ok"
  },
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## 5. 확장성 패턴 (Scalability Patterns)

### 5.1 Adapter Pattern (데이터 소스 확장)
```
인터페이스:
  class DataSourceAdapter(ABC):
    async def fetch_prices(category, date_range) -> List[PriceRecord]
    async def health_check() -> bool

구현체:
  - KamisAdapter(DataSourceAdapter)
  - PublicDataAdapter(DataSourceAdapter)
  - EkapepiaAdapter(DataSourceAdapter)

새 데이터 소스 추가:
  1. DataSourceAdapter 구현
  2. 설정에 등록
  3. 기존 코드 변경 없음
```

### 5.2 Strategy Pattern (Spike 감지 알고리즘 교체)
```
인터페이스:
  class SpikeDetector(ABC):
    def detect(timeseries: List[float]) -> List[SpikeEvent]

구현체:
  - ZScoreSpikeDetector (현재 기본)
  - IQRSpikeDetector (향후 추가 가능)
  - MLBasedSpikeDetector (향후 추가 가능)
```
