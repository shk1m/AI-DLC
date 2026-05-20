# 서비스 정의 및 오케스트레이션 (Services)

---

## 서비스 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (모놀리식)                      │
├─────────────────────────────────────────────────────────┤
│  [Router Layer]                                          │
│  /api/prices  /api/chat  /api/recipes  /api/news        │
├─────────────────────────────────────────────────────────┤
│  [Service Layer]                                         │
│  PriceService | ChatService | RecipeService | NewsService│
│  SubstituteService | OntologyService                     │
├─────────────────────────────────────────────────────────┤
│  [Agent Layer]                                           │
│  LangChainAgent (도구 기반 오케스트레이션)                  │
├─────────────────────────────────────────────────────────┤
│  [Data Layer - SQLAlchemy ORM]                           │
│  PostgreSQL | Neptune Client | Bedrock Client | S3       │
├─────────────────────────────────────────────────────────┤
│  [External Adapters]                                     │
│  KAMIS | PublicData | Naver | Crawler                    │
└─────────────────────────────────────────────────────────┘
```

---

## 서비스 오케스트레이션 패턴

### 패턴 1: 시세 대시보드 조회 (동기 REST)
```
Client → GET /api/prices/{category}
       → PriceService.get_current_prices()
       → KAMIS API / PublicData API (캐시 우선)
       → Response: PriceItem[]
```

### 패턴 2: 시세 차트 + Spike 뉴스 (동기 REST, 병렬 호출)
```
Client → GET /api/prices/{item_id}/history?period=3m
       → PriceService.get_price_history() [병렬]
       → PriceService.detect_spikes() [병렬]
       → NewsService.get_news_for_spike() [Spike별]
       → Response: { timeSeries, spikes: [{date, news[]}] }
```

### 패턴 3: AI 챗봇 대화 (WebSocket 스트리밍)
```
Client → WS /ws/chat/{session_id}
       → ChatService.process_message()
       → LangChainAgent.run()
       → Agent가 도구 선택 및 실행:
         - price_lookup → PriceService
         - find_substitute → SubstituteService
         - suggest_recipe → RecipeService
         - search_news → NewsService
       → 스트리밍 응답 (토큰 단위)
```

### 패턴 4: 비용 시뮬레이션 (동기 REST)
```
Client → POST /api/recipes/simulate
       → RecipeService.suggest_menu(servings, budget)
       → PriceService.get_current_prices() [재료별]
       → RecipeService.calculate_cost()
       → Response: CostSimulation
```

### 패턴 5: 대체 식자재 추천 (동기 REST)
```
Client → GET /api/substitutes/{item_id}
       → SubstituteService.find_substitutes()
       → OntologyService.get_substitutes() [Neptune 쿼리]
       → PriceService.get_current_prices() [대체 품목별]
       → SubstituteService.calculate_savings()
       → Response: SubstituteItem[]
```

### 패턴 6: 뉴스 크롤링 (백그라운드 작업)
```
Scheduler (EventBridge/APScheduler)
       → NewsService.crawl_government_press()
       → NewsService.search_news() [키워드별]
       → 벡터 임베딩 → Bedrock KB 적재
       → 메타데이터 → PostgreSQL 저장
```

---

## API 라우터 구조

```python
# main.py
app = FastAPI()

# 라우터 등록
app.include_router(price_router, prefix="/api/prices", tags=["prices"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(recipe_router, prefix="/api/recipes", tags=["recipes"])
app.include_router(substitute_router, prefix="/api/substitutes", tags=["substitutes"])
app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(ontology_router, prefix="/api/ontology", tags=["ontology"])

# WebSocket
app.add_websocket_route("/ws/chat/{session_id}", chat_websocket_endpoint)
```

---

## 서비스 간 의존성 규칙

| 규칙 | 설명 |
|------|------|
| 단방향 의존 | 서비스 간 순환 의존 금지 |
| Agent 중심 | LangChainAgent만 여러 서비스를 조합 가능 |
| 서비스 독립 | 각 서비스는 독립적으로 테스트 가능 |
| 외부 어댑터 격리 | 외부 API 호출은 Adapter를 통해서만 |
