# Deployment Runbook — FoodLens (식견)

## 시연 환경 배포 (Local Demo)

### Pre-Deployment Checklist
- [x] Docker Desktop 실행 중
- [x] `.env` 파일 생성 (USE_MOCK=true)
- [x] 포트 5432, 6379, 3000, 8000 사용 가능
- [x] Node.js 18+, Python 3.11+ 설치

### Deployment Steps

#### Step 1: 인프라 시작
```bash
cd AI-DLC
docker-compose up -d

# 확인
docker ps
# foodlens-postgres (5432) ✅
# foodlens-redis (6379) ✅
```

#### Step 2: 백엔드 시작
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Step 3: 프론트엔드 시작
```bash
cd frontend
npm install
npm run dev
```

#### Step 4: 검증
- http://localhost:8000/docs → Swagger UI ✅
- http://localhost:3000 → 대시보드 ✅

---

## 프로덕션 배포 (AWS - 설계)

### Pre-Deployment Checklist
- [ ] AWS 계정 + IAM 역할 준비
- [ ] VPC + 서브넷 프로비저닝
- [ ] RDS PostgreSQL 15 Multi-AZ 생성
- [ ] Neptune 클러스터 생성
- [ ] Bedrock Knowledge Base 구성
- [ ] S3 버킷 생성 + RAG 문서 업로드
- [ ] ECR 리포지토리 생성
- [ ] Secrets Manager에 API 키 등록
- [ ] CloudFront + ACM 인증서

### Deployment Order (의존성 순서)
```
1. VPC + Networking
2. RDS + Neptune + ElastiCache
3. S3 + Bedrock KB
4. ECS Cluster + Task Definitions
5. ALB + Target Groups
6. ECS Services (Backend → Frontend)
7. CloudFront Distribution
8. Route 53 DNS
9. CloudWatch Alarms
```

### Rollback Triggers
- Error rate > 5% for 5 minutes
- Latency p95 > 5000ms for 5 minutes
- Health check failures > 3 consecutive
- 500 에러 급증

### Rollback Steps
```bash
# ECS 서비스 이전 태스크 정의로 롤백
aws ecs update-service --cluster foodlens \
  --service backend --task-definition foodlens-backend:PREVIOUS_VERSION

# DB 마이그레이션 롤백 (필요 시)
cd backend && alembic downgrade -1
```

---

## 시연 시나리오 스크립트

### 시나리오 1: 시세 대시보드 (2분)
1. 대시보드 접속 → Bento-box 레이아웃 소개
2. 카테고리 탭 전환 (농산물 → 수산물 → 축산물)
3. 품목 선택 → 도매/소매/Gap 테이블 확인
4. 시세 추이 차트 → Spike 포인트 마우스 오버 → 뉴스 헤드라인 표시

### 시나리오 2: AI 챗봇 (2분)
1. 챗봇 플로팅 버튼 클릭 → 채팅창 열림
2. "고등어 현재 시세는?" → 컨설턴트 스타일 응답 (출처 포함)
3. "상추 대신 쓸 수 있는 식재료 추천해줘" → 대체 식자재 + 레시피 추천
4. "1000식 기준 이번 주 점심 메뉴 추천" → 예산 내 메뉴 조합

### 시나리오 3: 원가 시뮬레이션 (1분)
1. CostSimulator에서 식수 1000 입력
2. 예산 4,500,000원 설정
3. 시뮬레이션 실행 → 레시피별 원가 비교
4. 대체 식자재 적용 시 절감률 확인

### 시나리오 4: 기술 아키텍처 설명 (1분)
1. AWS 아키텍처 다이어그램 표시
2. Bedrock + RAG + Neptune 온톨로지 설명
3. Circuit Breaker + Fallback 패턴 설명
4. PBT 테스트 결과 (97개 통과) 시연
