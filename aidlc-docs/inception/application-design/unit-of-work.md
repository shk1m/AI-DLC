# Unit of Work 정의

## 분해 기준
- **기준**: 팀원 역할 기반 (4명 = 4 Units)
- **구조**: 모놀리식 FastAPI 내 논리적 모듈
- **API 계약**: 동시 개발 + 수시 싱크 (Iterative)

---

## Unit 1: Frontend (팀원 A - 프론트엔드)

### 책임 범위
- Next.js 14 프로젝트 전체
- 모든 프론트엔드 컴포넌트 (FE-01 ~ FE-07)
- UI/UX 디자인 및 인터랙션
- Tailwind CSS 스타일링
- Recharts 차트 구현
- WebSocket 클라이언트 (챗봇)
- 상태 관리

### 담당 컴포넌트
| ID | 컴포넌트 | 핵심 기능 |
|----|----------|-----------|
| FE-01 | DashboardLayout | Bento-box 레이아웃, 네비게이션 |
| FE-02 | PriceChart | 시세 차트 + CustomTooltip + Spike 마커 |
| FE-03 | CategoryFilter | 카테고리 탭, 필터링, 검색 |
| FE-04 | PriceTable | 도매/소매/Gap 테이블 |
| FE-05 | CostSimulator | 식수 입력, 원가 계산 UI |
| FE-06 | ChatBot | 플로팅 챗봇, 타이핑 애니메이션 |
| FE-07 | SubstituteRecommender | 대체 식자재 추천 표시 |

### 기술 스택
- Next.js 14, React, TypeScript
- Tailwind CSS, Recharts
- WebSocket (native or socket.io-client)

---

## Unit 2: Backend (팀원 B - 백엔드)

### 책임 범위
- FastAPI 서버 전체 구조
- API 엔드포인트 설계 및 구현
- 데이터 모델 (SQLAlchemy ORM)
- PostgreSQL 스키마 및 마이그레이션
- 외부 API 어댑터 (KAMIS, 공공데이터, 네이버)
- WebSocket 서버 (챗봇)
- 입력 검증 (Pydantic)
- 에러 핸들링

### 담당 컴포넌트
| ID | 컴포넌트 | 핵심 기능 |
|----|----------|-----------|
| BE-01 | PriceService | 시세 조회, Spike 감지, 캐싱 |
| BE-03 | RecipeService | 레시피 제안, 원가 계산 |
| BE-05 | NewsService | 뉴스 검색, 크롤링 |
| EXT-01 | KAMIS Adapter | 농산물 시세 API |
| EXT-02 | PublicData Adapter | 공공데이터 API |
| EXT-03 | Naver Adapter | 네이버 검색/데이터랩 |
| DL-01 | PostgreSQL | ORM 모델, 마이그레이션 |

### 기술 스택
- Python, FastAPI, Pydantic
- SQLAlchemy, Alembic
- httpx (비동기 HTTP 클라이언트)
- WebSocket (FastAPI native)

---

## Unit 3: AI/Data (팀원 C - AI/데이터)

### 책임 범위
- Amazon Bedrock 연동 (Claude LLM)
- Bedrock Knowledge Bases 구축 (RAG)
- LangChain Agent 구현
- Amazon Neptune 온톨로지 구축
- 벡터 임베딩 파이프라인
- AI 프롬프트 엔지니어링
- Guardrails 설정

### 담당 컴포넌트
| ID | 컴포넌트 | 핵심 기능 |
|----|----------|-----------|
| BE-02 | ChatService | LangChain Agent 실행, 대화 관리 |
| BE-04 | SubstituteService | 온톨로지 기반 대체 추천 |
| BE-06 | OntologyService | Neptune 쿼리, 관계 탐색 |
| BE-07 | LangChainAgent | Agent + Tools 오케스트레이션 |
| DL-02 | Neptune | 온톨로지 스키마, 데이터 적재 |
| DL-03 | Bedrock KB | Knowledge Base 구성, 문서 적재 |

### 기술 스택
- LangChain, boto3 (Bedrock)
- Gremlin (Neptune)
- Amazon Bedrock Guardrails

---

## Unit 4: Integration (팀원 D - 풀스택)

### 책임 범위
- 뉴스 크롤링 파이프라인
- 데이터 수집 및 정제
- 프론트-백엔드 API 연동 지원
- 통합 테스트
- 시연 준비 및 데모 데이터
- Fallback 로직 (API 실패 시 캐시 전환)
- 배포 환경 설정

### 담당 컴포넌트
| ID | 컴포넌트 | 핵심 기능 |
|----|----------|-----------|
| EXT-04 | NewsCrawler | 정부 보도자료 크롤링 |
| DL-04 | S3 | 문서/데이터 저장소 관리 |
| - | Integration | 프론트-백 연동, E2E 테스트 |
| - | Demo Data | 시연용 샘플 데이터 생성 |
| - | Fallback | API 실패 시 캐시 전환 로직 |

### 기술 스택
- Python (BeautifulSoup, Scrapy)
- boto3 (S3)
- pytest (통합 테스트)

---

## 코드 조직 전략 (Greenfield) - 실제 구현 반영

```
project-root/
├── .env.example                     # 환경 변수 템플릿 (루트)
├── .gitignore                       # 루트 gitignore
├── docker-compose.yml               # 전체 인프라 (PostgreSQL, Redis)
│
├── frontend/                        # Unit 1: Next.js 14
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx                # 메인 대시보드
│   ├── components/
│   │   ├── dashboard/              # FE-01~FE-07 컴포넌트
│   │   │   ├── DashboardLayout.tsx
│   │   │   ├── CategoryFilter.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── PriceChartTooltip.tsx
│   │   │   ├── PriceTable.tsx
│   │   │   ├── CostSimulator.tsx
│   │   │   ├── SubstituteRecommender.tsx
│   │   │   └── ChatBot.tsx
│   │   └── ui/                     # 공통 UI 컴포넌트
│   │       ├── BentoCard.tsx
│   │       ├── SectionHeader.tsx
│   │       └── SkeletonCard.tsx
│   ├── lib/                        # 유틸리티, 상태, API
│   │   ├── chatStream.ts           # WebSocket 스트리밍
│   │   ├── hooks.ts                # Custom hooks
│   │   ├── mockApi.ts              # Mock API (시연용)
│   │   ├── mockData.ts             # Mock 데이터
│   │   ├── store.ts                # Zustand 상태 관리
│   │   └── utils.ts                # 유틸리티 함수
│   ├── types/
│   │   └── index.ts                # TypeScript 타입 정의 (API 계약)
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                         # Unit 2 + 3 + 4: FastAPI
│   ├── app/
│   │   ├── main.py                 # FastAPI 앱 진입점
│   │   ├── config.py               # 앱 설정 (Unit 2)
│   │   ├── database.py             # DB 연결 (Unit 3)
│   │   ├── routers/                # API 라우터 (Unit 2)
│   │   │   ├── prices.py
│   │   │   ├── chat.py
│   │   │   ├── recipes.py
│   │   │   └── news.py
│   │   ├── services/               # 비즈니스 로직 (Unit 2 + 3)
│   │   │   ├── price_service.py
│   │   │   ├── recipe_service.py
│   │   │   ├── news_service.py
│   │   │   ├── bedrock_client.py       # Unit 3: Bedrock 연동
│   │   │   └── menu_generation_service.py  # Unit 3: AI 메뉴 생성
│   │   ├── models/                 # SQLAlchemy 모델 (Unit 2)
│   │   │   ├── food_item.py
│   │   │   ├── price_record.py
│   │   │   ├── spike_event.py
│   │   │   ├── news_article.py
│   │   │   ├── recipe.py
│   │   │   └── chat.py
│   │   ├── schemas/                # Pydantic 스키마 (Unit 2 + 4)
│   │   │   ├── price.py
│   │   │   ├── recipe.py
│   │   │   ├── news.py
│   │   │   └── common.py
│   │   ├── adapters/               # 외부 API 어댑터 (Unit 2 + 4)
│   │   │   ├── base.py             # 어댑터 인터페이스
│   │   │   ├── kamis.py            # Unit 2: KAMIS API
│   │   │   ├── naver.py            # Unit 2: 네이버 API
│   │   │   ├── public_data.py      # Unit 2: 공공데이터
│   │   │   ├── crawler.py          # Unit 4: 뉴스 크롤러
│   │   │   └── s3_client.py        # Unit 4: S3 클라이언트
│   │   ├── core/                   # Cross-cutting (Unit 4)
│   │   │   ├── aws.py              # AWS 클라이언트 (Unit 2)
│   │   │   ├── cache.py            # 캐시 (Unit 2 버전)
│   │   │   ├── cache_manager.py    # 캐시 매니저 (Unit 4 버전)
│   │   │   ├── circuit_breaker.py  # 회로 차단기
│   │   │   ├── config.py           # Core 설정
│   │   │   ├── fallback.py         # Fallback 로직
│   │   │   ├── logging.py          # 구조화 로깅
│   │   │   └── middleware.py       # 미들웨어 (Correlation ID 등)
│   │   └── db/                     # DB 설정 (Unit 2)
│   │       └── base.py
│   ├── alembic/                    # DB 마이그레이션 (Unit 2)
│   ├── scripts/                    # 데이터 적재 스크립트 (Unit 4)
│   │   ├── seed_demo_data.py
│   │   ├── load_ontology.py
│   │   └── verify_setup.py
│   ├── tests/                      # 테스트 (Unit 4)
│   │   ├── conftest.py
│   │   ├── unit/                   # 단위 테스트 + PBT
│   │   └── integration/            # 통합 테스트
│   ├── lambda_handler.py           # Unit 3: Lambda 핸들러
│   ├── template.yaml               # Unit 3: SAM 템플릿
│   ├── deploy.sh                   # Unit 3: 배포 스크립트
│   ├── init_db.sql                 # Unit 3: DB 초기화
│   ├── docker-compose.yml          # 백엔드 전용 Docker
│   ├── requirements.txt            # 의존성 (버전 고정)
│   └── pyproject.toml              # 프로젝트 메타데이터
│
├── data/                            # Unit 4: 샘플/시연 데이터
│   ├── ontology/                   # Neptune 적재용 데이터
│   │   ├── food_nodes.json         # 45개 식자재 노드
│   │   └── food_edges.json         # 30개 관계 엣지
│   └── news/samples/               # 뉴스 샘플 데이터
│       ├── naver_news.json
│       ├── mafra_news.json
│       └── mof_news.json
│
├── aidlc-docs/                      # AI-DLC 문서
└── .kiro/                           # AI-DLC 규칙
```
