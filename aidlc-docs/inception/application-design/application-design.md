# Application Design (통합 설계 문서)

---

## 1. 설계 결정 사항

| 결정 항목 | 선택 | 근거 |
|-----------|------|------|
| 프론트-백 통신 | REST + WebSocket 혼합 | 챗봇 스트리밍에 WebSocket 필요 |
| 백엔드 구조 | 모놀리식 FastAPI | 해커톤 시간 제약, 단일 서버 관리 용이 |
| 데이터 접근 | SQLAlchemy ORM 직접 사용 | 빠른 개발, Python 생태계 활용 |
| AI 체인 구성 | LangChain Agent 기반 | 도구 자동 선택으로 유연한 질의 처리 |

---

## 2. 시스템 아키텍처 요약

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                      │
│  Dashboard | PriceChart | ChatBot | CostSimulator | Filter    │
└──────────────────────┬───────────────────┬───────────────────┘
                       │ REST              │ WebSocket
                       ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Router Layer: /prices /chat /recipes /substitutes /news  │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Service Layer: Price|Chat|Recipe|Substitute|News|Ontology│ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Agent Layer: LangChain Agent + Tools                     │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Data Layer: SQLAlchemy ORM + Neptune Client + Bedrock    │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Adapter Layer: KAMIS | PublicData | Naver | Crawler      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
    ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
    │PostgreSQL│ │Neptune │ │Bedrock │ │External API│
    │  (RDS)   │ │(Graph) │ │(AI+KB) │ │(KAMIS etc.)│
    └──────────┘ └────────┘ └────────┘ └────────────┘
```

---

## 3. 컴포넌트 요약 (18개)

| 레이어 | 컴포넌트 수 | 주요 컴포넌트 |
|--------|:-----------:|---------------|
| 프론트엔드 | 7 | Dashboard, PriceChart, ChatBot, CostSimulator, CategoryFilter, PriceTable, SubstituteRecommender |
| 백엔드 서비스 | 7 | PriceService, ChatService, RecipeService, SubstituteService, NewsService, OntologyService, LangChainAgent |
| 데이터 레이어 | 4 | PostgreSQL, Neptune, Bedrock KB, S3 |
| 외부 어댑터 | 4 | KAMIS, PublicData, Naver, NewsCrawler |

---

## 4. 핵심 설계 원칙

1. **모놀리식 but 모듈화**: 단일 FastAPI 서버이지만 도메인별 라우터/서비스로 내부 분리
2. **Agent 중심 오케스트레이션**: LangChainAgent가 여러 서비스를 조합하여 복합 질의 처리
3. **외부 의존 격리**: 모든 외부 API는 Adapter를 통해 접근 (Fallback/캐싱 용이)
4. **단방향 의존**: 서비스 간 순환 의존 금지, 계층 구조 준수
5. **IT 비전문가 UX**: 모든 프론트엔드 컴포넌트는 직관적이고 단순한 인터랙션

---

## 5. 상세 문서 참조

- 컴포넌트 정의: [components.md](./components.md)
- 메서드 시그니처: [component-methods.md](./component-methods.md)
- 서비스 오케스트레이션: [services.md](./services.md)
- 의존성 매핑: [component-dependency.md](./component-dependency.md)
