# Unit of Work - Story Map

---

## Epic → Unit 매핑

| Epic | Unit 1 (Frontend) | Unit 2 (Backend) | Unit 3 (AI/Data) | Unit 4 (Integration) |
|------|:-----------------:|:----------------:|:----------------:|:--------------------:|
| Epic 1: 시세 대시보드 | ●(UI) | ●(API) | - | ○(연동) |
| Epic 2: 시세 그래프+Spike | ●(차트) | ●(Spike감지) | - | ●(뉴스매핑) |
| Epic 3: 메뉴/시뮬레이션 | ●(UI) | ●(계산API) | ●(AI추천) | - |
| Epic 4: 대체 식자재 | ●(UI) | ○(API) | ●(온톨로지) | - |
| Epic 5: AI 챗봇 | ●(챗봇UI) | ●(WebSocket) | ●(Agent) | ○(연동) |
| Epic 6: 뉴스 크롤링 | - | ●(뉴스API) | ●(KB적재) | ●(크롤러) |
| Epic 7: 온톨로지 | - | - | ●(Neptune) | ●(데이터적재) |

● = 주 담당, ○ = 보조/지원

---

## Unit별 Story 할당 상세

### Unit 1 (Frontend) - 팀원 A
| 우선순위 | Story | Epic | 산출물 |
|----------|-------|------|--------|
| 1 | 대시보드 레이아웃 구현 | Epic 1 | DashboardLayout 컴포넌트 |
| 2 | 시세 차트 + Spike 툴팁 | Epic 2 | PriceChart + CustomTooltip |
| 3 | 카테고리 필터 + 테이블 | Epic 1 | CategoryFilter + PriceTable |
| 4 | 챗봇 UI + 타이핑 효과 | Epic 5 | ChatBot 컴포넌트 |
| 5 | 비용 시뮬레이터 UI | Epic 3 | CostSimulator 컴포넌트 |
| 6 | 대체 식자재 추천 UI | Epic 4 | SubstituteRecommender |
| 7 | UI 폴리싱 + 반응형 | 전체 | 최종 스타일링 |

### Unit 2 (Backend) - 팀원 B
| 우선순위 | Story | Epic | 산출물 |
|----------|-------|------|--------|
| 1 | FastAPI 프로젝트 구조 셋업 | 전체 | main.py, 라우터, 모델 |
| 2 | 시세 조회 API (KAMIS 연동) | Epic 1 | /api/prices 엔드포인트 |
| 3 | Spike 감지 + 뉴스 매핑 API | Epic 2 | /api/prices/{id}/history |
| 4 | WebSocket 챗봇 엔드포인트 | Epic 5 | /ws/chat/{session_id} |
| 5 | 비용 시뮬레이션 API | Epic 3 | /api/recipes/simulate |
| 6 | 대체 식자재 API | Epic 4 | /api/substitutes/{id} |
| 7 | 뉴스 검색 API | Epic 6 | /api/news |

### Unit 3 (AI/Data) - 팀원 C
| 우선순위 | Story | Epic | 산출물 |
|----------|-------|------|--------|
| 1 | Neptune 온톨로지 스키마 설계 | Epic 7 | 그래프 스키마 + 초기 데이터 |
| 2 | Bedrock Knowledge Base 구성 | Epic 5,6 | KB + S3 소스 문서 |
| 3 | LangChain Agent + Tools 구현 | Epic 5 | agent.py + tools/ |
| 4 | 대체 식자재 추천 로직 (Neptune) | Epic 4 | SubstituteService |
| 5 | AI 메뉴/레시피 추천 로직 | Epic 3 | RecipeService (AI 부분) |
| 6 | 프롬프트 최적화 + Guardrails | Epic 5 | 프롬프트 템플릿 |
| 7 | 챗봇 응답 품질 튜닝 | Epic 5 | 테스트 + 개선 |

### Unit 4 (Integration) - 팀원 D
| 우선순위 | Story | Epic | 산출물 |
|----------|-------|------|--------|
| 1 | 데이터 소스 API 키 발급 + 테스트 | 전체 | API 키, 연결 확인 |
| 2 | 뉴스 크롤러 구현 | Epic 6 | crawler.py |
| 3 | 온톨로지 데이터 적재 스크립트 | Epic 7 | data/scripts/ |
| 4 | 크롤링 데이터 정제 + KB 적재 | Epic 6 | 임베딩 파이프라인 |
| 5 | 프론트-백엔드 API 연동 지원 | 전체 | 통합 디버깅 |
| 6 | Fallback 로직 구현 | 전체 | 캐시 전환 로직 |
| 7 | 시연 데이터 준비 + 최종 점검 | 전체 | 데모 시나리오 데이터 |

---

## 수용 기준 커버리지 검증

| Epic | 총 수용 기준 | Unit 1 | Unit 2 | Unit 3 | Unit 4 |
|------|:------------:|:------:|:------:|:------:|:------:|
| Epic 1 | 7 | 4 | 2 | 0 | 1 |
| Epic 2 | 7 | 3 | 2 | 0 | 2 |
| Epic 3 | 7 | 2 | 2 | 3 | 0 |
| Epic 4 | 6 | 1 | 1 | 4 | 0 |
| Epic 5 | 9 | 3 | 1 | 5 | 0 |
| Epic 6 | 7 | 0 | 2 | 2 | 3 |
| Epic 7 | 6 | 0 | 0 | 4 | 2 |
| **합계** | **49** | **13** | **10** | **18** | **8** |
