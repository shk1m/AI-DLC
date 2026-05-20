# Integration Test Instructions

## Purpose
Unit 간 상호작용을 검증하여 전체 시스템이 올바르게 동작하는지 확인합니다.

---

## 사전 준비

```bash
# 1. Docker 인프라 시작
docker-compose up -d

# 2. 백엔드 서버 시작
cd backend
uvicorn app.main:app --reload --port 8000

# 3. 프론트엔드 서버 시작 (별도 터미널)
cd frontend
npm run dev
```

---

## Integration Test Scenarios

### Scenario 1: Frontend → Backend 시세 API 연동

**테스트 대상**: Unit 1 (Frontend) → Unit 2 (Backend PriceService)

```bash
# 1. 시세 API 직접 호출 확인
curl http://localhost:8000/api/prices/vegetable

# 2. 프론트엔드에서 카테고리 탭 클릭 시 데이터 로딩 확인
# 브라우저 DevTools > Network 탭에서 API 호출 확인
# Expected: GET /api/prices/{category} → 200 OK + JSON 응답
```

**Expected Results**:
- API 응답 시간 < 500ms (캐시 히트) 또는 < 3초 (캐시 미스)
- 응답 JSON에 `wholesale_price`, `retail_price`, `price_gap` 포함
- 프론트엔드 테이블에 데이터 정상 표시

---

### Scenario 2: Frontend → Backend 챗봇 WebSocket 연동

**테스트 대상**: Unit 1 (ChatBot) → Unit 2 (WebSocket) → Unit 3 (LangChain Agent)

```bash
# WebSocket 연결 테스트 (wscat 또는 브라우저)
# 브라우저에서 챗봇 열기 → 메시지 입력 → 스트리밍 응답 확인
```

**Test Steps**:
1. 프론트엔드에서 챗봇 플로팅 버튼 클릭
2. "고등어 현재 시세는?" 입력
3. 타이핑 애니메이션과 함께 응답 스트리밍 확인
4. 응답에 출처 정보 포함 확인

**Expected Results**:
- WebSocket 연결 성공 (101 Switching Protocols)
- 첫 토큰 응답 < 2초
- 전체 응답 < 5초
- 컨설턴트 스타일 구조 (분석 → 추천 → 근거)

---

### Scenario 3: Backend → External API 연동 (Circuit Breaker)

**테스트 대상**: Unit 2 (Adapters) → Unit 4 (CircuitBreaker) → External APIs

```bash
# KAMIS API 연동 확인
curl http://localhost:8000/api/prices/vegetable?use_cache=false

# Circuit Breaker 동작 확인 (API 실패 시뮬레이션)
# USE_MOCK=false 상태에서 잘못된 API 키로 테스트
# → 5회 실패 후 Circuit OPEN → Fallback 응답 확인
```

**Expected Results**:
- 정상: 외부 API 응답 → 캐시 저장 → 클라이언트 응답
- 실패: Circuit OPEN → 캐시된 데이터 반환 (stale)
- 캐시도 없음: "데이터 조회 불가" 메시지

---

### Scenario 4: 시세 차트 + Spike 뉴스 매핑

**테스트 대상**: Unit 1 (PriceChart) → Unit 2 (PriceService + NewsService)

```bash
# 시세 히스토리 + Spike 데이터 조회
curl "http://localhost:8000/api/prices/radish/history?period=3m"
```

**Test Steps**:
1. 프론트엔드에서 품목 선택 (예: 무)
2. 차트에 시세 추이 라인 표시 확인
3. Spike 포인트 (빨간 마커) 존재 확인
4. Spike 포인트 마우스 오버 → 뉴스 헤드라인 툴팁 표시

**Expected Results**:
- 차트 렌더링 < 1초
- Spike 마커가 Z-Score > 2.0 시점에 표시
- CustomTooltip에 뉴스 제목 + URL 표시

---

### Scenario 5: 원가 시뮬레이션 E2E

**테스트 대상**: Unit 1 (CostSimulator) → Unit 2 (RecipeService) → Unit 3 (Bedrock)

```bash
# 시뮬레이션 API 호출
curl -X POST http://localhost:8000/api/recipes/simulate \
  -H "Content-Type: application/json" \
  -d '{"servings": 1000, "budget": 4500000}'
```

**Test Steps**:
1. 프론트엔드에서 식수 1000 입력
2. 예산 4,500,000원 입력
3. "시뮬레이션" 버튼 클릭
4. 레시피 추천 목록 + 재료별 원가 표시 확인

**Expected Results**:
- 응답 시간 < 3초
- 레시피별 총 원가 ≤ 예산
- 1식 단가 표시
- 영양 정보 포함

---

## 통합 테스트 실행 (자동화)

```bash
cd backend

# 통합 테스트 실행 (tests/integration/)
pytest tests/integration/ -v --timeout=30

# 전체 테스트 (단위 + 통합)
pytest -v
```

---

## Cleanup

```bash
# 테스트 완료 후
docker-compose down
# 또는 데이터 유지하면서 중지
docker-compose stop
```
