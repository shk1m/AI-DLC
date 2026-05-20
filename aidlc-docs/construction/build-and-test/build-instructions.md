# Build Instructions

## Prerequisites

| 항목 | 요구사항 |
|------|----------|
| **Node.js** | 18.x 이상 |
| **Python** | 3.11+ (3.12 권장) |
| **Docker** | Docker Desktop + Docker Compose |
| **AWS CLI** | v2 (Bedrock/Neptune 접근용) |
| **OS** | Windows 10+, macOS, Linux |
| **RAM** | 최소 8GB |
| **Disk** | 최소 2GB 여유 공간 |

## Environment Variables

`.env.example`을 복사하여 `.env` 생성 후 아래 값 설정:

```bash
cp .env.example .env
```

### 필수 환경 변수
| 변수 | 설명 | 예시 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql+asyncpg://admin:password@localhost:5432/foodlens` |
| `AWS_REGION` | AWS 리전 | `ap-northeast-2` |
| `AWS_ACCESS_KEY_ID` | AWS 자격증명 | (시크릿) |
| `AWS_SECRET_ACCESS_KEY` | AWS 자격증명 | (시크릿) |
| `NAVER_CLIENT_ID` | 네이버 API 클라이언트 ID | (시크릿) |
| `NAVER_CLIENT_SECRET` | 네이버 API 시크릿 | (시크릿) |
| `USE_MOCK` | Mock 모드 (시연용) | `true` |

---

## Build Steps

### 1. 인프라 시작 (Docker)

```bash
# 프로젝트 루트에서
docker-compose up -d

# 확인
docker-compose ps
# postgres (5432), redis (6379) 실행 확인
```

### 2. Backend 빌드

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# DB 마이그레이션
alembic upgrade head

# 시연 데이터 적재 (선택)
python scripts/seed_demo_data.py
python scripts/load_ontology.py

# 서버 시작
uvicorn app.main:app --reload --port 8000
```

**빌드 성공 확인**:
- `http://localhost:8000/docs` 접속 → Swagger UI 표시
- `http://localhost:8000/health` → `{"status": "healthy"}` 응답

### 3. Frontend 빌드

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev

# 또는 프로덕션 빌드
npm run build
npm start
```

**빌드 성공 확인**:
- `http://localhost:3000` 접속 → 대시보드 표시
- 콘솔에 에러 없음
- `next build` 성공 시: `✓ Compiled successfully`

### 4. 전체 시스템 검증

```bash
# 백엔드 헬스체크
curl http://localhost:8000/health

# 프론트엔드 접속
# 브라우저에서 http://localhost:3000 열기

# API 연동 확인 (Mock 모드)
curl http://localhost:8000/api/prices/vegetable
```

---

## Troubleshooting

### Docker 관련
| 문제 | 해결 |
|------|------|
| Port 5432 already in use | `docker-compose down` 후 재시작, 또는 로컬 PostgreSQL 중지 |
| Permission denied | Docker Desktop 실행 확인, WSL2 모드 확인 |

### Backend 관련
| 문제 | 해결 |
|------|------|
| ModuleNotFoundError | `pip install -r requirements.txt` 재실행 |
| DB connection refused | Docker PostgreSQL 실행 확인, DATABASE_URL 확인 |
| AWS credential error | `.env`에 AWS 자격증명 설정, `USE_MOCK=true`로 우회 |

### Frontend 관련
| 문제 | 해결 |
|------|------|
| next: command not found | `npm install` 재실행 |
| TypeScript errors | `npx tsc --noEmit`으로 타입 에러 확인 |
| Port 3000 in use | `npm run dev -- -p 3001`로 포트 변경 |
