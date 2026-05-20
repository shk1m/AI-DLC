# 컴포넌트 의존성 (Component Dependencies)

---

## 의존성 매트릭스

### 프론트엔드 → 백엔드 의존성

| 프론트엔드 컴포넌트 | 호출 API | 프로토콜 |
|---------------------|----------|----------|
| FE-02: PriceChart | /api/prices/{item_id}/history | REST GET |
| FE-03: CategoryFilter | /api/ontology/categories | REST GET |
| FE-04: PriceTable | /api/prices/{category} | REST GET |
| FE-05: CostSimulator | /api/recipes/simulate | REST POST |
| FE-06: ChatBot | /ws/chat/{session_id} | WebSocket |
| FE-07: SubstituteRecommender | /api/substitutes/{item_id} | REST GET |

### 백엔드 서비스 간 의존성

```
LangChainAgent (BE-07)
    ├── PriceService (BE-01)
    ├── RecipeService (BE-03)
    ├── SubstituteService (BE-04)
    ├── NewsService (BE-05)
    └── OntologyService (BE-06)

ChatService (BE-02)
    └── LangChainAgent (BE-07)

SubstituteService (BE-04)
    ├── OntologyService (BE-06)
    └── PriceService (BE-01)

RecipeService (BE-03)
    └── PriceService (BE-01)

NewsService (BE-05)
    └── (독립 - 외부 API만 의존)

PriceService (BE-01)
    └── (독립 - 외부 API만 의존)

OntologyService (BE-06)
    └── (독립 - Neptune만 의존)
```

### 백엔드 → 데이터 레이어 의존성

| 서비스 | PostgreSQL | Neptune | Bedrock KB | S3 | 외부 API |
|--------|:----------:|:-------:|:----------:|:--:|:--------:|
| PriceService | ✓ (캐시) | - | - | - | KAMIS, 공공데이터 |
| ChatService | ✓ (이력) | - | ✓ (RAG) | - | - |
| RecipeService | ✓ (레시피) | - | - | - | - |
| SubstituteService | - | ✓ | - | - | - |
| NewsService | ✓ (메타) | - | ✓ (임베딩) | ✓ (원본) | 네이버, 크롤링 |
| OntologyService | - | ✓ | - | - | - |

---

## 데이터 흐름도

### 시세 데이터 흐름
```
KAMIS API / 공공데이터포털
        ↓
  [External Adapters]
        ↓
  PriceService (캐싱 + Spike 감지)
        ↓
  PostgreSQL (시세 이벤트 저장)
        ↓
  프론트엔드 (차트 + 테이블)
```

### 뉴스 데이터 흐름
```
네이버 API / 정부 보도자료
        ↓
  NewsService (수집 + 분류)
        ↓
  ┌─────────┬──────────────┐
  ↓         ↓              ↓
PostgreSQL  S3 (원본)    Bedrock KB
(메타데이터) (문서저장)   (벡터임베딩)
```

### AI 챗봇 데이터 흐름
```
사용자 질문 (WebSocket)
        ↓
  ChatService
        ↓
  LangChainAgent (질문 분석)
        ↓
  도구 선택 및 실행
  ┌──────┬──────┬──────┬──────┐
  ↓      ↓      ↓      ↓      ↓
Price  Recipe  Subst  News  Ontology
  ↓      ↓      ↓      ↓      ↓
  └──────┴──────┴──────┴──────┘
        ↓
  응답 생성 (Bedrock Claude)
        ↓
  스트리밍 응답 (WebSocket)
```

---

## 통신 프로토콜 요약

| 통신 경로 | 프로토콜 | 용도 |
|-----------|----------|------|
| 프론트 → 백엔드 (일반) | REST (HTTP/JSON) | 시세, 레시피, 대체식자재 |
| 프론트 → 백엔드 (챗봇) | WebSocket | 실시간 스트리밍 응답 |
| 백엔드 → PostgreSQL | SQLAlchemy ORM | 데이터 CRUD |
| 백엔드 → Neptune | Gremlin/openCypher | 그래프 쿼리 |
| 백엔드 → Bedrock | AWS SDK (boto3) | LLM 호출, KB 검색 |
| 백엔드 → 외부 API | HTTP Client (httpx) | KAMIS, 네이버, 공공데이터 |
