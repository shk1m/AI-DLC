# Performance Test Instructions

## Performance Requirements (NFR-01)

| 항목 | 목표값 | 측정 방법 |
|------|--------|-----------|
| 대시보드 초기 로딩 | ≤ 3초 | First Contentful Paint |
| 차트 데이터 렌더링 | ≤ 1초 | API 응답 + 렌더링 완료 |
| 챗봇 첫 토큰 응답 | ≤ 2초 | WebSocket 첫 토큰 수신 |
| 챗봇 전체 응답 | ≤ 5초 | 스트리밍 완료 |
| 시세 API 응답 (캐시 히트) | ≤ 500ms | HTTP 응답 시간 |
| 시세 API 응답 (캐시 미스) | ≤ 3초 | 외부 API 포함 |
| 대체 식자재 추천 | ≤ 2초 | Neptune 쿼리 + 계산 |

---

## 시연 환경 성능 테스트

### 1. API 응답 시간 측정

```bash
# 시세 API (캐시 워밍 후)
curl -w "\nTotal: %{time_total}s\n" http://localhost:8000/api/prices/vegetable

# 시세 히스토리 API
curl -w "\nTotal: %{time_total}s\n" "http://localhost:8000/api/prices/radish/history?period=3m"

# 헬스체크 (베이스라인)
curl -w "\nTotal: %{time_total}s\n" http://localhost:8000/health
```

### 2. 프론트엔드 로딩 성능

```bash
# Lighthouse CI (Chrome DevTools)
# 1. 브라우저에서 http://localhost:3000 열기
# 2. F12 → Lighthouse 탭 → Performance 측정
# 3. FCP (First Contentful Paint) < 3초 확인
```

### 3. WebSocket 스트리밍 성능

```bash
# 브라우저 DevTools > Network > WS 탭에서:
# 1. 챗봇 열기
# 2. 메시지 전송
# 3. 첫 프레임 수신 시간 확인 (< 2초)
# 4. 마지막 프레임 수신 시간 확인 (< 5초)
```

---

## 부하 테스트 (프로덕션 설계용, 시연에서는 선택)

### k6 스크립트 (참고용)

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // ramp up
    { duration: '1m', target: 10 },    // steady
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],  // 95% < 3초
    http_req_failed: ['rate<0.01'],     // 에러율 < 1%
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/prices/vegetable');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 3s': (r) => r.timings.duration < 3000,
  });
  sleep(1);
}
```

### 실행 방법 (k6 설치 필요)
```bash
k6 run load-test.js
```

---

## 성능 최적화 체크리스트

| 항목 | 구현 상태 | 효과 |
|------|:---------:|------|
| 시세 데이터 캐싱 (1시간 TTL) | ✅ | API 응답 500ms → 50ms |
| 비동기 병렬 호출 (asyncio.gather) | ✅ | 다중 API 호출 시간 단축 |
| Connection Pooling (SQLAlchemy) | ✅ | DB 연결 오버헤드 제거 |
| WebSocket 스트리밍 | ✅ | 체감 응답 시간 단축 |
| Next.js 코드 스플리팅 | ✅ | 초기 로딩 최적화 |
| Circuit Breaker | ✅ | 장애 시 빠른 Fallback |
