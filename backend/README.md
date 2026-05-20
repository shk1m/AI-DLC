# FoodLens Backend

MD/영양사/바이어용 AI 대시보드 + 챗봇 백엔드 (FastAPI + LangChain)

## 🚀 빠른 시작 (시연 환경)

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 AWS/Naver 자격증명 입력
```

**최소 설정 (Mock 모드 시연):**
```env
USE_MOCK=true
DATABASE_URL=postgresql+asyncpg://admin:foodlens_dev@localhost:5432/foodlens
```

**Naver API 사용 시:**
```env
USE_MOCK=false
NAVER_CLIENT_ID=<발급받은 Client ID>
NAVER_CLIENT_SECRET=<발급받은 Client Secret>
```

### 2. Docker 서비스 시작 (PostgreSQL + Redis)

```bash
docker-compose up -d
docker-compose ps  # healthy 확인
```

### 3. 의존성 설치

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 4. DB 마이그레이션 (Unit 2 alembic 작업 완료 후)

```bash
alembic upgrade head
```

### 5. 데모 데이터 시딩

```bash
# 시딩 미리보기 (dry-run)
python -m backend.scripts.seed_demo_data --dry-run

# 실제 시딩
python -m backend.scripts.seed_demo_data

# 온톨로지 적재 검증
python -m backend.scripts.load_ontology
```

### 6. 시연 환경 사전 점검

```bash
python -m backend.scripts.verify_setup
```

### 7. 백엔드 서버 시작

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. 접속 확인

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

---

## 🧪 테스트 실행

```bash
# 단위 테스트
pytest tests/unit -v

# 통합 테스트
pytest tests/integration -v -m integration

# 전체 + 커버리지
pytest --cov=app --cov-report=term-missing

# PBT만
pytest -m pbt -v

# CI 모드 (Hypothesis 200회)
HYPOTHESIS_PROFILE=ci pytest -m pbt
```

---

## 📁 Unit 4 담당 파일

```
backend/app/
├── core/
│   ├── config.py          # Settings (Pydantic + SecretStr)
│   ├── logging.py         # structlog (JSON + 민감정보 마스킹)
│   ├── middleware.py       # Correlation ID
│   ├── cache_manager.py   # Cache-Aside (인메모리 ↔ Redis)
│   ├── circuit_breaker.py # Circuit Breaker 상태 머신
│   └── fallback.py        # 3-tier Fallback 체인
├── adapters/
│   ├── crawler.py         # EXT-04 (Naver/Mafra/Mof 크롤러)
│   └── s3_client.py       # DL-04 (AWS S3 / Mock)
└── schemas/
    └── news.py            # NewsArticle Pydantic 스키마

backend/scripts/
├── seed_demo_data.py      # 시연 데이터 시딩
├── load_ontology.py       # Neptune 온톨로지 적재
└── verify_setup.py        # 시연 사전 점검

data/
├── ontology/
│   ├── food_nodes.json    # 45+ 식자재 노드
│   └── food_edges.json    # 30+ 관계 (4종)
└── news/samples/          # Fallback 뉴스 샘플
```

---

## 🔀 Unit 4 ↔ 타 Unit 인터페이스 합의 지점

| 인터페이스 | Unit 4 (제공) | 상대 Unit (소비) |
|---|---|---|
| `NewsCrawlerService.crawl_all()` | `List[NewsArticle]` | Unit 2 `NewsService.crawl_government_press()` |
| `CacheManager` | 싱글톤 `get_cache_manager()` | Unit 2/3 모든 서비스 |
| `FallbackChain` | builder 패턴 | Unit 2 어댑터 |
| `get_circuit_breaker(name)` | CB 인스턴스 | Unit 2 외부 API 어댑터 |
| `S3` (mock) | `get_s3_client()` | Unit 3 RAG KB 파이프라인 |
| `data/ontology/*.json` | JSON 파일 | Unit 3 Neptune 적재 |
| `data/news/samples/*.json` | JSON 파일 | Unit 3 Bedrock KB 시드 |

> 16:30 통합 테스트 싱크포인트 전까지 `app/schemas/news.py`의 `NewsArticle`은 임시. Unit 2와 합의 후 단일 모델로 통합.

---

## 🔒 보안 노트

- `.env` 파일은 git에 커밋하지 마세요 (`.gitignore`에 명시됨)
- Naver API 자격증명이 노출됐다면 [네이버 개발자 센터](https://developers.naver.com/apps)에서 즉시 Secret 갱신
- AWS 자격증명은 IAM 최소 권한 원칙 적용 (infrastructure-design.md §5 참조)


## 🤖 AI/Lambda Services (Unit 03)

### Bedrock 메뉴 생성 서비스
- `app/services/bedrock_client.py` - Amazon Bedrock Claude 연동
- `app/services/menu_generation_service.py` - AI 기반 메뉴/레시피 생성
- `app/services/price_service.py` - 시세 데이터 조회 (Unit 03 버전)

### Lambda 배포 (비동기 작업용)
- `lambda/lambda_handler.py` - Lambda 핸들러
- `lambda/template.yaml` - SAM 템플릿
- `lambda/deploy.sh` - 배포 스크립트

### 로컬 테스트
```bash
python test_local.py
```
