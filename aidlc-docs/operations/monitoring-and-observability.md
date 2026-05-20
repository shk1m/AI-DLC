# Monitoring & Observability — FoodLens

## SLO Definitions

| SLO | Target | Window | 측정 방법 |
|-----|--------|--------|-----------|
| 가용성 | 99.9% | 30일 | 성공 요청 / 전체 요청 |
| 응답 시간 (p95) | < 3초 | 30일 | API 응답 시간 |
| 에러율 | < 1% | 30일 | 5xx / 전체 응답 |
| 데이터 신선도 | < 1시간 | Rolling | 마지막 수집 시간 |

---

## Alerting Rules

### Critical (즉시 대응)
| Alert | 조건 | 대응 |
|-------|------|------|
| Service Down | 헬스체크 3회 연속 실패 | 서비스 재시작 |
| DB Unreachable | DB 연결 30초 이상 실패 | DB 상태 확인 |
| Bedrock Timeout | AI 응답 30초 초과 | Fallback 활성화 |

### Warning (알림)
| Alert | 조건 | 대응 |
|-------|------|------|
| High Error Rate | 5xx > 5% (5분간) | 로그 확인 |
| Latency Spike | p95 > 5초 (10분간) | 병목 분석 |
| Cache Miss High | 히트율 < 50% (15분간) | 캐시 워밍 |
| External API Fail | Circuit OPEN | Fallback 확인 |

---

## Dashboards

### Operational Dashboard
- 서비스 헬스 상태 (Backend + Frontend)
- 요청률 + 에러율 (실시간)
- 응답 시간 분포 (p50, p95, p99)
- Circuit Breaker 상태 (KAMIS, Naver, PublicData)
- 캐시 히트/미스 비율
- DB 커넥션 풀 사용률

### Business Dashboard
- 데이터 신선도 (소스별 마지막 수집 시간)
- 추적 품목 수 (카테고리별)
- 챗봇 사용량 (일별 질의 수)
- 시뮬레이션 사용량 (일별)
- 인기 검색 품목 Top 10

---

## Structured Logging (구현됨)

```json
{
  "timestamp": "2026-05-20T12:00:00Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "price_service",
  "method": "get_current_prices",
  "duration_ms": 150,
  "message": "Price data fetched successfully",
  "metadata": {
    "category": "vegetable",
    "item_count": 25,
    "cache_hit": true
  }
}
```

### 로그 보존 정책
| 환경 | 보존 기간 | 저장소 |
|------|-----------|--------|
| Local | 세션 동안 | stdout |
| Production | 90일 | CloudWatch Logs |
| Archive | 1년 | S3 Glacier |
