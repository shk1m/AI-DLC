# Logical Components (논리 컴포넌트)

---

## 시스템 논리 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                          │
│  [Security Headers] [Rate Limiter] [Correlation ID] [Validator]  │
├─────────────────────────────────────────────────────────────────┤
│                        Service Layer                              │
│  [PriceService] [ChatService] [RecipeService] [SubstituteService]│
│  [NewsService] [OntologyService]                                 │
├─────────────────────────────────────────────────────────────────┤
│                        Cross-Cutting Layer                        │
│  [Cache Manager] [Circuit Breaker] [Logger] [Error Handler]      │
├─────────────────────────────────────────────────────────────────┤
│                        Data Access Layer                          │
│  [ORM (SQLAlchemy)] [Neptune Client] [Bedrock Client] [S3 Client]│
├─────────────────────────────────────────────────────────────────┤
│                        External Adapter Layer                     │
│  [KAMIS] [PublicData] [Naver] [Crawler] + [Circuit Breaker each] │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Cache Manager (캐시 관리자)

### 책임
- 캐시 읽기/쓰기/무효화
- TTL 관리
- 캐시 키 생성 전략

### 구현
```python
class CacheManager:
    """인메모리 캐시 (시연용). 프로덕션: Redis/ElastiCache"""
    
    async def get(key: str) -> Optional[Any]
    async def set(key: str, value: Any, ttl: int) -> None
    async def invalidate(pattern: str) -> None
    async def get_or_set(key: str, factory: Callable, ttl: int) -> Any
```

### 캐시 키 전략
```
prices:{category}:{date}          → 시세 데이터
prices:{item_id}:history:{period} → 시세 추이
ontology:categories               → 카테고리 트리
ontology:substitutes:{item_id}    → 대체 식자재
news:{keyword}:{date}             → 뉴스 검색 결과
```

---

## 2. Circuit Breaker Manager

### 책임
- 외부 서비스별 회로 차단기 관리
- 상태 전이 (CLOSED → OPEN → HALF_OPEN)
- Fallback 실행

### 구현
```python
class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, 
                 recovery_timeout: int = 30):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    async def call(self, func: Callable, fallback: Callable = None) -> Any
    def record_success(self) -> None
    def record_failure(self) -> None
```

### 인스턴스
| 이름 | 대상 | 실패 임계 | 복구 시간 |
|------|------|-----------|-----------|
| kamis_cb | KAMIS API | 5회 | 30초 |
| public_data_cb | 공공데이터 API | 5회 | 30초 |
| naver_cb | 네이버 API | 5회 | 30초 |
| neptune_cb | Neptune | 3회 | 60초 |
| bedrock_cb | Bedrock | 3회 | 60초 |

---

## 3. Request Validator (요청 검증기)

### 책임
- Pydantic 스키마 기반 입력 검증
- 비즈니스 규칙 검증
- 악의적 입력 차단

### 구현
```python
# FastAPI 자동 검증 (Pydantic)
class PriceQueryParams(BaseModel):
    category: CategoryEnum
    period: Literal["1w", "1m", "3m", "6m", "1y"] = "1m"
    
    @field_validator("category")
    def validate_category(cls, v):
        if v not in CategoryEnum:
            raise ValueError("Invalid category")
        return v

class ChatMessageInput(BaseModel):
    content: str = Field(max_length=1000)
    
    @field_validator("content")
    def sanitize_content(cls, v):
        # HTML 태그 제거, XSS 방지
        return bleach.clean(v, tags=[], strip=True)
```

---

## 4. Structured Logger

### 책임
- JSON 구조화 로그 출력
- Correlation ID 자동 포함
- 민감 정보 마스킹

### 구현
```python
import structlog

logger = structlog.get_logger()

# 미들웨어에서 correlation_id 바인딩
structlog.contextvars.bind_contextvars(
    correlation_id=request.headers.get("X-Correlation-ID", str(uuid4()))
)

# 사용
logger.info("price_fetched", category="seafood", item_count=25, duration_ms=150)
```

---

## 5. Global Error Handler

### 책임
- 모든 미처리 예외 포착
- 구조화 로그 기록
- 안전한 클라이언트 응답 생성
- Fail-closed 보장

### 구현
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = request.state.correlation_id
    logger.error("unhandled_exception", 
                 error=str(exc), 
                 correlation_id=correlation_id,
                 path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "correlation_id": correlation_id
        }
    )
```

---

## 6. WebSocket Manager (챗봇)

### 책임
- WebSocket 연결 관리
- 세션별 연결 추적
- 스트리밍 응답 전송
- 연결 해제 처리

### 구현
```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket) -> None
    async def disconnect(self, session_id: str) -> None
    async def send_token(self, session_id: str, token: str) -> None
    async def send_done(self, session_id: str, sources: List[str]) -> None
```

---

## 7. Background Task Scheduler

### 책임
- 뉴스 크롤링 스케줄링
- 캐시 워밍
- 데이터 동기화

### 구현 (시연용: APScheduler)
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 뉴스 크롤링: 1시간마다
scheduler.add_job(news_service.crawl_all, 'interval', hours=1)

# 시세 캐시 워밍: 30분마다
scheduler.add_job(price_service.warm_cache, 'interval', minutes=30)
```

---

## 8. Rate Limiter (프로덕션 설계)

### 책임
- API 호출 빈도 제한
- 사용자별/IP별 제한
- 429 Too Many Requests 응답

### 설계 (시연에서는 미구현, 문서화)
```
제한 정책:
  - 일반 API: 100 req/min per IP
  - 챗봇: 20 msg/min per session
  - 시뮬레이션: 10 req/min per session
```

---

## 컴포넌트 통합 흐름 예시

### 시세 조회 요청 흐름
```
1. [Correlation ID Middleware] → ID 생성/전파
2. [Request Validator] → Pydantic 검증
3. [PriceService] → 비즈니스 로직
4. [Cache Manager] → 캐시 확인
5. (캐시 미스) → [Circuit Breaker] → [KAMIS Adapter]
6. [Structured Logger] → 요청/응답 로그
7. (에러 시) → [Global Error Handler] → 안전한 응답
```
