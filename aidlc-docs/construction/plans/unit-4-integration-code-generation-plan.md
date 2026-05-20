# Unit 4 (Integration) — Code Generation Plan

> **단일 진실 소스 (Single Source of Truth)**: 본 문서는 Unit 4 코드 생성의 단일 진실 소스입니다. Part 2(Generation) 단계는 본 문서의 단계를 순차적으로 실행하며, 완료된 단계는 즉시 [x]로 표시됩니다.

---

## 1. Unit Context (단위 컨텍스트)

### 1.1 Unit 정보
| 항목 | 내용 |
|---|---|
| **Unit ID** | Unit 4 |
| **Unit 이름** | Integration |
| **담당자** | 팀원 D (풀스택) |
| **Workspace Root** | `c:\Users\Administrator\Desktop\Projects\진진\AI-DLC_Challenge\AI-DLC-WELSTORY-DLC-SUMMIT\AI-DLC` |
| **프로젝트 유형** | Greenfield (multi-unit monolith) |
| **백엔드 위치** | `backend/` (Python FastAPI) |
| **데이터/스크립트 위치** | `data/`, `backend/scripts/` |

### 1.2 책임 범위 (unit-of-work.md 기반)
- 뉴스 크롤링 파이프라인 (EXT-04)
- S3 문서 저장소 (DL-04)
- 데이터 수집 및 정제
- 프론트-백엔드 API 연동 지원
- 통합 테스트
- Fallback 로직 (API 실패 시 캐시 전환)
- 시연용 데모 데이터 + 적재 스크립트
- 배포 환경 설정 (Docker Compose, .env)

### 1.3 담당 컴포넌트 (components.md / NFR / infrastructure-design 기반)
| ID | 컴포넌트 | 카테고리 | 코드 위치 |
|---|---|---|---|
| EXT-04 | NewsCrawler | 외부 어댑터 | `backend/app/adapters/crawler.py` |
| DL-04 | S3 Client | 데이터 레이어 | `backend/app/adapters/s3_client.py` |
| - | Circuit Breaker | Cross-cutting | `backend/app/core/circuit_breaker.py` |
| - | Cache Manager | Cross-cutting | `backend/app/core/cache_manager.py` |
| - | Fallback Chain | Cross-cutting | `backend/app/core/fallback.py` |
| - | Structured Logger | Cross-cutting | `backend/app/core/logging.py` |
| - | Correlation ID Middleware | Cross-cutting | `backend/app/core/middleware.py` |
| - | Demo Data Seeder | 데이터 | `backend/scripts/seed_demo_data.py` |
| - | Ontology Loader | 데이터 | `backend/scripts/load_ontology.py` |
| - | Integration Tests | 테스트 | `backend/tests/integration/` |
| - | Docker Compose | 배포 | `docker-compose.yml` |
| - | .env.example | 배포 | `.env.example` |

### 1.4 Story 매핑 (unit-of-work-story-map.md)
| # | Story | Epic | 산출물 |
|---|---|---|---|
| S-1 | 데이터 소스 API 키 발급 + 테스트 | 전체 | `.env.example`, 연결 확인 스크립트 |
| S-2 | 뉴스 크롤러 구현 | Epic 6 | `crawler.py` |
| S-3 | 온톨로지 데이터 적재 스크립트 | Epic 7 | `data/ontology/`, `scripts/load_ontology.py` |
| S-4 | 크롤링 데이터 정제 + KB 적재 | Epic 6 | 임베딩/S3 업로드 파이프라인 |
| S-5 | 프론트-백엔드 API 연동 지원 | 전체 | 통합 테스트 |
| S-6 | Fallback 로직 구현 | 전체 | `cache_manager.py`, `circuit_breaker.py`, `fallback.py` |
| S-7 | 시연 데이터 준비 + 최종 점검 | 전체 | `data/sample/`, `seed_demo_data.py` |

### 1.5 Acceptance Criteria 매핑 (Unit 4 담당 8개)
- **Epic 1 (1)**: 카테고리 트리 시드 (`food_categories` 시드 데이터)
- **Epic 2 (2)**: ① 뉴스-시세 시간 매핑 알고리즘 (BR-06-2 7일 윈도우) ② Fallback (캐시된 시세)
- **Epic 6 (3)**: ① 정부 보도자료 크롤링 (mafra.go.kr, mof.go.kr) ② 식자재 키워드 분류/태깅 (BR-06-3) ③ S3 업로드 + KB 동기화 트리거
- **Epic 7 (2)**: ① 50+ 식자재 노드 데이터 ② 4종 관계 (substitutable, sameCategory, nutritionSimilar, cookingCompatible) 적재

### 1.6 Unit 의존성 (unit-of-work-dependency.md)
| 의존 대상 | 결합도 | 인터페이스 | 비고 |
|---|---|---|---|
| Unit 2 (Backend) | 중간 | Python 함수 호출 (NewsService에서 NewsCrawler 사용) | 같은 프로세스. 인터페이스 합의: `crawl_government_press() -> List[NewsArticle]` |
| Unit 3 (AI/Data) | 낮음 | S3 버킷 / Neptune 데이터 포맷 | 데이터 스키마 합의 후 독립 |
| Unit 1 (Frontend) | 낮음 | 통합 테스트 디버깅 | 시연 시 지원 |

### 1.7 가정 (Assumptions)
- Unit 2가 정의할 도메인 모델 클래스 (`NewsArticle`, `FoodItem` 등)는 Unit 4에서 **임시로 같은 구조의 Pydantic/SQLAlchemy 모델**을 정의하고, 이후 Unit 2와 합의 시 통합한다 (iterative sync).
- Neptune/Bedrock KB 실접속이 어려운 시연 환경에서는 **Mock 클라이언트 모드**(환경변수 `USE_MOCK=true`)로 동작 가능해야 한다.
- Demo data는 KAMIS API 응답 포맷을 모사한 1주일치 시세 JSON을 포함한다.

---

## 2. 코드 위치 결정

### 2.1 디렉터리 구조 (Greenfield, multi-unit monolith)
```
<workspace-root>/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # (Unit 2 메인. Unit 4는 미들웨어/라이프사이클 훅 합의용 stub만)
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py              # ⬅ Unit 4 (EXT-04)
│   │   │   └── s3_client.py            # ⬅ Unit 4 (DL-04)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # ⬅ Unit 4 (settings/env)
│   │   │   ├── logging.py              # ⬅ Unit 4 (structlog)
│   │   │   ├── middleware.py           # ⬅ Unit 4 (correlation_id)
│   │   │   ├── circuit_breaker.py      # ⬅ Unit 4
│   │   │   ├── cache_manager.py        # ⬅ Unit 4
│   │   │   └── fallback.py             # ⬅ Unit 4
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── news.py                 # ⬅ Unit 4 (임시 NewsArticle, 추후 Unit 2와 합의)
│   │   └── services/
│   │       └── (Unit 2/3 영역)
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── seed_demo_data.py           # ⬅ Unit 4
│   │   └── load_ontology.py            # ⬅ Unit 4
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # ⬅ Unit 4 (Hypothesis 프로필)
│   │   ├── unit/
│   │   │   ├── test_circuit_breaker.py
│   │   │   ├── test_cache_manager.py
│   │   │   ├── test_fallback.py
│   │   │   └── test_crawler.py
│   │   └── integration/
│   │       ├── test_crawler_integration.py
│   │       ├── test_fallback_chain.py
│   │       └── test_seed_pipeline.py
│   ├── pyproject.toml                  # ⬅ Unit 4 (or requirements.txt)
│   ├── requirements.txt                # ⬅ Unit 4
│   └── README.md                       # ⬅ Unit 4 (시연 빠른 시작)
├── data/
│   ├── sample/
│   │   ├── kamis_prices_1week.json     # ⬅ Unit 4 (Fallback 캐시 시드)
│   │   ├── public_data_seafood.json    # ⬅ Unit 4
│   │   └── recipes.json                # ⬅ Unit 4
│   ├── ontology/
│   │   ├── food_nodes.json             # ⬅ Unit 4 (50+ 식자재)
│   │   └── food_edges.json             # ⬅ Unit 4 (4종 관계)
│   └── news/
│       └── samples/                    # ⬅ Unit 4 (크롤링 미작동 시 폴백)
├── docker-compose.yml                  # ⬅ Unit 4
├── .env.example                        # ⬅ Unit 4
├── .gitignore                          # ⬅ Unit 4
└── aidlc-docs/                         # 기존 (수정 X, 단 unit-4/code/ 요약 추가)
    └── construction/
        └── unit-4-integration/
            └── code/
                └── (단계별 마크다운 요약)
```

### 2.2 코드 위치 규칙 준수
- ✅ 애플리케이션 코드는 워크스페이스 루트 (`backend/`, `data/`, 루트 파일)
- ✅ 문서/요약은 `aidlc-docs/construction/unit-4-integration/code/` (마크다운만)
- ✅ `aidlc-docs/`에는 코드 미저장

---

## 3. 단계별 코드 생성 계획 (Generation Steps)

> 각 단계는 Part 2에서 순차 실행됩니다. 완료 시 [x]로 마킹합니다.
> 각 단계는 `aidlc-docs/construction/unit-4-integration/code/STEP-{n}-summary.md`에 요약을 남깁니다.

### Phase A — 프로젝트 구조 셋업 (Project Structure Setup)

- [x] **Step 1**: 백엔드 프로젝트 골격 + 의존성 파일 생성
  - `backend/requirements.txt` (tech-stack-decisions.md의 버전 고정 목록)
  - `backend/pyproject.toml` (Black/Ruff 설정 + pytest)
  - `backend/.python-version` (3.11)
  - `backend/app/__init__.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`
  - `.gitignore`, `.env.example` (모든 API 키 + AWS 자격증명 자리표시자)
  - 검증: `pip install -r requirements.txt --dry-run` 로직 확인 (실제 설치는 Build & Test 단계에서)

- [x] **Step 2**: Settings/Config 모듈 생성
  - `backend/app/core/config.py`: Pydantic `BaseSettings`
  - 환경변수: `KAMIS_API_KEY`, `PUBLIC_DATA_API_KEY`, `NAVER_CLIENT_ID/SECRET`, `AWS_REGION`, `S3_BUCKET`, `BEDROCK_KB_ID`, `NEPTUNE_ENDPOINT`, `DATABASE_URL`, `USE_MOCK`, `LOG_LEVEL`
  - 시연 안전성을 위한 `USE_MOCK=true` 기본값
  - 관련 스토리: S-1

### Phase B — Cross-cutting Infrastructure (NFR Design 기반)

- [x] **Step 3**: Structured Logging (`logging.py`) 구현
  - `structlog` JSON 포맷
  - SECURITY-03 준수 (민감정보 마스킹)
  - 컨텍스트 변수: `correlation_id`, `service`, `method`, `duration_ms`
  - **Unit Test** (`test_logging.py`): 로그 출력 포맷, 마스킹 검증
  - 관련 NFR: OBS-01, SECURITY-03

- [x] **Step 4**: Correlation ID Middleware (`middleware.py`) 구현
  - FastAPI 미들웨어로 등록 가능한 형태
  - 요청 진입 시 `X-Correlation-ID` 추출 또는 UUID 생성
  - `request.state.correlation_id`에 바인딩
  - 응답 헤더에도 포함
  - **Unit Test**: 헤더 전파 동작 검증
  - 관련 NFR: OBS-02

- [x] **Step 5**: Cache Manager (`cache_manager.py`) 구현
  - 인메모리 캐시 (시연용) + Redis 어댑터 인터페이스 (프로덕션 설계)
  - 메서드: `get`, `set(ttl)`, `invalidate(pattern)`, `get_or_set(factory, ttl)`
  - TTL 정책: BR-07-1~5 (시세 1h, 뉴스 30m, 온톨로지 24h, 카테고리 24h, 트렌드 6h)
  - **Unit Test** (`test_cache_manager.py`):
    - 기본 get/set/expire
    - **PBT (Hypothesis)**: round-trip (set→get 동일성), TTL 무관 키 격리
  - 관련 NFR: PERF-05, BR-07, PBT-04

- [x] **Step 6**: Circuit Breaker (`circuit_breaker.py`) 구현
  - 상태 머신: CLOSED → OPEN → HALF_OPEN → CLOSED
  - 설정값: `failure_threshold`, `recovery_timeout`, `name`
  - 메서드: `async call(func, fallback=None)`
  - 5개 인스턴스 (`kamis_cb`, `public_data_cb`, `naver_cb`, `neptune_cb`, `bedrock_cb`) 팩토리
  - **Unit Test**:
    - 상태 전이 (성공/실패/복구)
    - **PBT**: invariant — failure_count는 [0, threshold] 범위 내
  - 관련 NFR: AVAIL-03, NFR Design 1.1

- [x] **Step 7**: Fallback 체인 (`fallback.py`) 구현
  - 데코레이터 형태 + 함수 형태 둘 다 제공
  - 체인: `primary() → cache_lookup() → default_response()`
  - 각 단계 결과/실패 로깅 (correlation_id 포함)
  - **Unit Test**: 각 단계 트리거 시나리오, 모두 실패 시 default 반환
  - 관련 NFR: AVAIL-03, BR-06-5

### Phase C — Schemas (Pydantic) 

- [x] **Step 8**: News 스키마 (`schemas/news.py`)
  - `NewsArticle` (id, title, url, source, published_at, keywords, related_items, summary)
  - `NewsSourceEnum` (NAVER, MAFRA, MOF)
  - 입력 검증: title ≤ 500자, url HTTPS만 (BR-08-7), keywords ≤ 50자
  - **Unit Test** + **PBT**: round-trip 직렬화/역직렬화 (PBT-08)
  - 관련 NFR: SECURITY-05, PBT-08

### Phase D — External Adapters (EXT-04, DL-04)

- [x] **Step 9**: S3 Client (`adapters/s3_client.py`) — DL-04
  - 비동기 boto3 (`aioboto3`) 또는 동기 boto3 + `asyncio.to_thread` 래퍼
  - 메서드: `upload_text(key, content, metadata)`, `upload_json(key, obj)`, `download(key)`, `list_objects(prefix)`
  - Mock 모드: `USE_MOCK=true`이면 로컬 파일시스템 (`./.mock-s3/`)에 기록
  - Circuit Breaker 적용 안 함 (Bedrock CB와 묶지 않음, 독립 격벽)
  - **Unit Test**: Mock 모드 read/write, 메타데이터 보존
  - 관련 NFR: AVAIL-03, MAINT-04

- [x] **Step 10**: News Crawler (`adapters/crawler.py`) — EXT-04
  - 추상 인터페이스 `BaseCrawler` (parse_listing, parse_article)
  - 구현체: `MafraCrawler`, `MofCrawler`
  - HTTP: `httpx` async client + Retry+Backoff (3회, 1s/2s/4s + jitter)
  - 파싱: `BeautifulSoup4`
  - 식자재 키워드 추출 → `related_items` 매핑 (BR-06-3)
  - URL 중복 제거 (BR-06-1)
  - Circuit Breaker 적용 (`naver_cb` 별도, mafra/mof 자체 cb)
  - 결과: `List[NewsArticle]`
  - **사이트 미접근 시 Fallback**: `data/news/samples/*.json` 사용
  - **Unit Test**:
    - 모킹된 HTML 응답 파싱
    - 키워드 매칭 정확도
    - **PBT**: invariant — 반환된 NewsArticle은 모두 valid (Pydantic 검증 통과)
  - 관련 NFR: AVAIL-03, NFR Design 1.2/1.3, BR-06

### Phase E — Demo Data + Seeding Scripts

- [x] **Step 11**: 카테고리 + 식자재 시드 데이터 작성
- [x] **Step 12**: 시세 캐시 시드 (`data/sample/kamis_prices_1week.json`, `public_data_seafood.json`)
- [x] **Step 13**: 온톨로지 데이터 (`data/ontology/food_nodes.json`, `food_edges.json`)
- [x] **Step 14**: 뉴스 샘플 데이터 (`data/news/samples/`)
- [x] **Step 15**: 적재 스크립트 (`backend/scripts/seed_demo_data.py`)
- [x] **Step 16**: 온톨로지 적재 스크립트 (`backend/scripts/load_ontology.py`)

### Phase F — Integration Tests

- [x] **Step 17**: 통합 테스트: Crawler → S3 → DB 파이프라인
- [x] **Step 18**: 통합 테스트: Fallback 체인 E2E
- [x] **Step 19**: 통합 테스트: 시드 파이프라인 멱등성
- [x] **Step 20**: Docker Compose (`docker-compose.yml`)
- [x] **Step 21**: 빠른 시작 README (`backend/README.md`)
- [x] **Step 22**: Deployment Verification 스크립트 (`backend/scripts/verify_setup.py`)
- [x] **Step 23**: 단계별 코드 요약 문서 종합
  - 다음 Unit/Build & Test 단계로 인계할 인터페이스 명세
  - 관련 NFR: MAINT-04 (API 문서)

---

## 4. 단계 ↔ Story / NFR / Acceptance 추적성 매트릭스

| Step | Story | NFR | Acceptance Criteria |
|---|---|---|---|
| 1 | S-1 | MAINT-05 | - |
| 2 | S-1 | SECURITY-12, MAINT-05 | - |
| 3 | (전체 지원) | OBS-01, SECURITY-03 | - |
| 4 | (전체 지원) | OBS-02 | - |
| 5 | S-6 | PERF-05, BR-07 | - |
| 6 | S-6 | AVAIL-03 | Epic 2 Fallback |
| 7 | S-6 | AVAIL-03 | Epic 2 Fallback |
| 8 | S-2, S-4 | SECURITY-05, PBT-08 | Epic 6 (뉴스 메타 저장) |
| 9 | S-4 | AVAIL-03 | Epic 6 (S3 업로드) |
| 10 | S-2 | AVAIL-03, BR-06 | Epic 6 (mafra/mof 크롤링, 키워드 분류) |
| 11 | S-7 | - | Epic 1 (카테고리 트리) |
| 12 | S-7 | AVAIL-03 | Epic 2 (Fallback 데이터) |
| 13 | S-3 | - | Epic 7 (50+ 노드 + 4종 관계) |
| 14 | S-7 | - | Epic 2/6 (뉴스 샘플) |
| 15 | S-7 | - | 전체 시드 |
| 16 | S-3 | - | Epic 7 적재 |
| 17 | S-2, S-4 | NFR-04 | Epic 6 |
| 18 | S-6 | NFR-04 | Epic 2 Fallback |
| 19 | S-7 | NFR-04 | 전체 |
| 20 | S-1 | MAINT-05 | - |
| 21 | S-1 | MAINT-04 | - |
| 22 | S-1 | OBS-03 | - |
| 23 | (요약) | MAINT-04 | - |

---

## 5. Extension Compliance 사전 점검

### 5.1 Security Baseline (Enabled)
| Rule | 적용 | 근거 |
|---|---|---|
| SECURITY-03 | ✅ Step 3 | structlog JSON 로그 |
| SECURITY-05 | ✅ Step 8 | Pydantic 입력 검증 (NewsArticle, URL, 길이) |
| SECURITY-09 | ✅ Step 7 | Fallback에서 스택 트레이스 미노출 |
| SECURITY-10 | ✅ Step 1 | requirements.txt 버전 고정 |
| SECURITY-11 | ✅ Phase B 전체 | core/ 모듈 분리 |
| SECURITY-12 | ✅ Step 2 | Secrets는 env, .env.example만 git 저장 |
| SECURITY-15 | ✅ Step 7 | fail-closed (default response 반환, 예외 전파 X) |
| SECURITY-01/06/07/08 | N/A (시연 환경) | 프로덕션 설계 문서로 이미 NFR Design에 명시 |

### 5.2 Property-Based Testing (Enabled)
| 대상 | Step | 속성 |
|---|---|---|
| Cache Manager | 5 | round-trip, TTL key isolation |
| Circuit Breaker | 6 | invariant (failure_count 범위) |
| NewsArticle 스키마 | 8 | round-trip 직렬화 |
| Crawler | 10 | invariant (모든 결과 Pydantic valid) |

→ Step 1에서 `conftest.py`에 Hypothesis 프로필 (dev: max_examples=50, ci: 200) 등록.

---

## 6. 위험 및 완화 전략

| 위험 | 영향 | 완화 |
|---|---|---|
| KAMIS/공공데이터 API 키 미발급 | 시연 실패 | Step 12의 시드 캐시로 Fallback. `USE_MOCK=true`로 외부 호출 차단 가능 |
| Neptune 접근 불가 | 온톨로지 미작동 | Step 16 적재 스크립트는 Mock 모드에서 JSON 덤프만 검증 |
| Bedrock KB 동기화 지연 | RAG 미작동 | Step 9에서 S3 업로드 후 sync 트리거는 Unit 3와 합의 (Unit 4는 업로드까지만 보장) |
| Unit 2 모델과 충돌 | 통합 실패 | Step 8 schemas는 임시. 16:30 통합 테스트 싱크포인트에서 Unit 2와 통합 |

---

## 7. 완료 기준 (Definition of Done)

- [ ] §3의 23개 Step 모두 [x]
- [ ] Unit 4 담당 Story (S-1 ~ S-7) 모두 [x]
- [ ] Unit 4 담당 Acceptance Criteria 8개 모두 구현 또는 시드로 충족
- [ ] 모든 Unit Test 작성 완료 (실행은 Build & Test 단계)
- [ ] PBT 4종 작성 완료
- [ ] Integration Test 3개 작성 완료
- [ ] Demo data 시드 가능 (멱등성 보장)
- [ ] `aidlc-docs/construction/unit-4-integration/code/code-summary.md` 생성

---

## 8. 추정 규모

| 카테고리 | 예상 파일 수 | 예상 LOC |
|---|---|---|
| 코어 모듈 (config, logging, middleware, CB, cache, fallback) | 6 | ~600 |
| 어댑터 (crawler, s3) | 2 | ~400 |
| 스키마 | 1 | ~100 |
| 시드/적재 스크립트 | 2 | ~300 |
| 데이터 (JSON) | 8 | (데이터) |
| 단위 테스트 | 8 | ~600 |
| 통합 테스트 | 3 | ~300 |
| 배포/문서 | 4 | ~200 |
| **합계** | **34** | **~2,500 LOC + 데이터** |

---

> **승인 요청**: 본 계획서를 검토 후 승인 또는 수정 요청해 주세요. 승인 시 Part 2 (Generation)으로 진행하여 Step 1부터 순차 실행합니다.
