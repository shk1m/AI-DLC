# Monitoring & Alerting - 식견(FoodLens)

## SLO Definitions

| SLI | Target | Window | 측정 방법 |
|-----|--------|--------|-----------|
| Availability | 99.9% | 30일 | 성공 요청 / 전체 요청 |
| Latency (p95) | < 3초 | 30일 | API 응답 시간 |
| Error Rate | < 0.1% | 30일 | 5xx / 전체 응답 |
| Chatbot Response | < 5초 | 30일 | 첫 토큰 ~ 완료 |

---

## Alerting Rules

### Critical (즉시 대응)
| Alert | 조건 | 대응 |
|-------|------|------|
| Service Down | Health check 3회 연속 실패 | 서비스 재시작, 온콜 호출 |
| DB Connection Failed | PostgreSQL 연결 30초 이상 실패 | DB 상태 확인, 재연결 |
| Bedrock Unavailable | AI 응답 실패 5회 연속 | Fallback 모드 전환 |

### Warning (모니터링)
| Alert | 조건 | 대응 |
|-------|------|------|
| High Error Rate | 5xx > 1% (5분) | 로그 확인, 원인 분석 |
| Latency Spike | p95 > 3초 (10분) | 캐시 상태 확인 |
| Circuit Open | 외부 API 차단 상태 | API 상태 확인 |
| Cache Miss High | 히트율 < 80% (15분) | 캐시 워밍 실행 |

---

## Dashboards

### Operational Dashboard
- 서비스 상태 (UP/DOWN)
- 요청 수 / 에러율 (실시간)
- 응답 시간 분포 (p50, p95, p99)
- Circuit Breaker 상태 (CLOSED/OPEN/HALF_OPEN)
- 캐시 히트율
- DB 커넥션 풀 사용률

### Business Dashboard
- 일별 활성 사용자 수
- 챗봇 질의 수 / 응답 만족도
- 시뮬레이션 실행 횟수
- 대체 식자재 추천 활용률
- 데이터 신선도 (마지막 수집 시간)

---

## Log Management

### 로그 구조 (structlog JSON)
```json
{
  "timestamp": "2026-05-20T12:00:00Z",
  "level": "info",
  "correlation_id": "uuid-xxx",
  "service": "price_service",
  "method": "get_current_prices",
  "duration_ms": 150,
  "message": "Price data fetched"
}
```

### 로그 보존 정책
| 환경 | 보존 기간 | 저장소 |
|------|-----------|--------|
| 시연 | 7일 | 로컬 파일 |
| 프로덕션 | 90일 | CloudWatch Logs |
| 감사 로그 | 1년 | S3 (Glacier) |
