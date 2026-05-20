# Deployment Runbook - 식견(FoodLens)

## 시연 환경 배포 (localhost)

### Pre-Deployment Checklist
- [x] Docker Desktop 실행 중
- [x] AWS 자격증명 설정 (.env)
- [x] 네이버 API 키 설정 (.env)
- [x] PostgreSQL + Redis 컨테이너 실행 중
- [x] Backend 의존성 설치 완료
- [x] Frontend 의존성 설치 완료

### Deployment Steps

#### 1. 인프라 시작
```bash
cd AI-DLC
docker-compose up -d
# 확인: docker-compose ps → postgres(5432), redis(6379) Running
```

#### 2. 백엔드 시작
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
# 확인: http://localhost:8000/health → {"status": "healthy"}
# API 문서: http://localhost:8000/docs
```

#### 3. 프론트엔드 시작
```bash
cd frontend
npm run dev
# 확인: http://localhost:3000 → 대시보드 표시
```

#### 4. 시연 데이터 적재 (선택)
```bash
cd backend
python scripts/seed_demo_data.py
python scripts/load_ontology.py
```

---

## 프로덕션 배포 (AWS - 설계 문서)

### Infrastructure Provisioning
```bash
# CDK 또는 Terraform으로 프로비저닝
# VPC, ECS Cluster, RDS, Neptune, ElastiCache, S3, Bedrock KB
```

### Deployment Order (의존성 순서)
1. **Infrastructure**: VPC, Subnets, Security Groups
2. **Data Layer**: RDS PostgreSQL, Neptune, ElastiCache, S3
3. **AI Layer**: Bedrock Knowledge Base 구성, Guardrails 설정
4. **Backend**: ECS Fargate (FastAPI) 배포
5. **Frontend**: ECS Fargate (Next.js) 또는 S3+CloudFront 배포
6. **Lambda**: SAM deploy (크롤러, 메뉴 생성, Neptune 로더)
7. **DNS/CDN**: Route 53 + CloudFront 설정

### Post-Deployment Validation
- [ ] Health check 엔드포인트 응답 확인
- [ ] 시세 API 정상 응답 확인
- [ ] 챗봇 WebSocket 연결 확인
- [ ] 크롤링 Lambda 트리거 확인
- [ ] CloudWatch 로그 수집 확인

---

## Rollback Procedures

### 시연 환경
```bash
# 서버 중지
Ctrl+C (uvicorn, npm)

# Docker 중지
docker-compose down

# 이전 커밋으로 복원
git checkout <previous-commit>
```

### 프로덕션 (설계)
```bash
# ECS 롤백
aws ecs update-service --cluster foodlens --service backend --task-definition foodlens-backend:<previous-revision>

# DB 롤백 (필요 시)
alembic downgrade -1
```

### Rollback Triggers
- API 에러율 > 5% (5분 지속)
- 응답 시간 p95 > 5초 (5분 지속)
- Health check 3회 연속 실패
- 챗봇 WebSocket 연결 실패율 > 10%
