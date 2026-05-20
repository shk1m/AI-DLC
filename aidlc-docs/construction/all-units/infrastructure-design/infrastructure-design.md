# Infrastructure Design (인프라 설계)

---

## 1. 환경 구분

| 환경 | 용도 | 인프라 |
|------|------|--------|
| **Local (시연)** | 해커톤 시연, 개발 | localhost, Docker Compose |
| **Production (설계)** | 프로덕션 배포 | AWS 완전 관리형 |

---

## 2. 로컬 시연 환경 (실제 구현)

### 아키텍처
```
┌─────────────────────────────────────────────┐
│              Developer Machine               │
├─────────────────────────────────────────────┤
│                                             │
│  [Next.js Dev Server]  ←→  [FastAPI Server] │
│   localhost:3000            localhost:8000   │
│                                    │        │
│                          ┌─────────┼────────┤
│                          │         │        │
│                          ▼         ▼        │
│                    [PostgreSQL] [Redis]      │
│                    localhost:5432  :6379     │
│                          (Docker)           │
└──────────────────────────┼──────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        [AWS Bedrock] [AWS Neptune] [External APIs]
        (Cloud)       (Cloud)       (KAMIS, Naver)
```

### Docker Compose 구성
```yaml
services:
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: foodlens
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

### 로컬에서 AWS 서비스 접근
| AWS 서비스 | 접근 방식 | 비고 |
|-----------|-----------|------|
| Bedrock | boto3 (직접 호출) | AWS 자격증명 필요 |
| Neptune | boto3 + Gremlin endpoint | VPC 피어링 또는 퍼블릭 엔드포인트 |
| S3 | boto3 (직접 호출) | 버킷 생성 필요 |
| Secrets Manager | 로컬: .env 파일 대체 | 프로덕션만 SM 사용 |

---

## 3. 프로덕션 환경 (설계 문서)

### AWS 아키텍처 다이어그램

```
                    [Route 53]
                        │
                    [CloudFront]
                    (CDN + WAF)
                        │
              ┌─────────┴─────────┐
              │                   │
    [ALB - Frontend]      [ALB - Backend]
              │                   │
    [ECS Fargate]         [ECS Fargate]
    (Next.js SSR)         (FastAPI)
    Auto Scaling          Auto Scaling
              │                   │
              └─────────┬─────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    [RDS PostgreSQL]  [Neptune]   [ElastiCache]
    (Multi-AZ)        (Cluster)   (Redis Cluster)
    (Encrypted)       (Encrypted) 
         │              │              
    [S3 Bucket]    [Bedrock]     [OpenSearch]
    (RAG Docs)     (Claude+KB)   (Logs)
         │              │
    [EventBridge]  [Bedrock Guardrails]
    (Scheduler)    (AI Safety)
         │
    [Lambda]
    (Crawler)
```

### 서비스 매핑 상세

| 논리 컴포넌트 | AWS 서비스 | 구성 | 비고 |
|--------------|-----------|------|------|
| Frontend Server | ECS Fargate | 2 vCPU, 4GB RAM | Next.js SSR |
| Backend Server | ECS Fargate | 4 vCPU, 8GB RAM | FastAPI + LangChain |
| 관계형 DB | RDS PostgreSQL 15 | db.r6g.large, Multi-AZ | 암호화 at rest |
| 그래프 DB | Neptune | db.r5.large | Gremlin endpoint |
| 캐시 | ElastiCache Redis | cache.r6g.large | 클러스터 모드 |
| 객체 저장소 | S3 | Standard | 버전 관리 활성화 |
| AI/LLM | Bedrock Claude 3.5 Sonnet | On-demand | 한국어 최적 |
| RAG | Bedrock Knowledge Bases | S3 소스 | 자동 동기화 |
| AI 안전 | Bedrock Guardrails | 커스텀 정책 | 환각 통제 |
| 크롤러 | Lambda | Python 3.11, 512MB | EventBridge 트리거 |
| 스케줄러 | EventBridge Scheduler | Cron 표현식 | 크롤링 주기 |
| CDN | CloudFront | 글로벌 엣지 | 정적 자산 캐싱 |
| WAF | AWS WAF | 관리형 규칙 | SQL Injection, XSS 방지 |
| DNS | Route 53 | 호스팅 존 | 도메인 관리 |
| 비밀 관리 | Secrets Manager | 자동 로테이션 | API 키, DB 자격증명 |
| 로그 | CloudWatch Logs | 90일 보존 | 구조화 로그 |
| 모니터링 | CloudWatch Metrics | 커스텀 대시보드 | 알람 설정 |
| 알림 | SNS | 이메일/Slack | 장애 알림 |

---

## 4. 네트워크 설계 (프로덕션)

### VPC 구성
```
VPC: 10.0.0.0/16

Public Subnets (2 AZ):
  - 10.0.1.0/24 (AZ-a) → ALB, NAT Gateway
  - 10.0.2.0/24 (AZ-b) → ALB, NAT Gateway

Private Subnets (2 AZ):
  - 10.0.10.0/24 (AZ-a) → ECS Tasks, Lambda
  - 10.0.11.0/24 (AZ-b) → ECS Tasks, Lambda

Data Subnets (2 AZ):
  - 10.0.20.0/24 (AZ-a) → RDS, Neptune, ElastiCache
  - 10.0.21.0/24 (AZ-b) → RDS, Neptune, ElastiCache
```

### Security Groups
| SG | 인바운드 | 소스 |
|----|----------|------|
| ALB-SG | 80, 443 | 0.0.0.0/0 |
| ECS-SG | 3000, 8000 | ALB-SG |
| RDS-SG | 5432 | ECS-SG |
| Neptune-SG | 8182 | ECS-SG |
| Redis-SG | 6379 | ECS-SG |

---

## 5. IAM 정책 (최소 권한, SECURITY-06)

### ECS Task Role (Backend)
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:Retrieve",
    "bedrock:ApplyGuardrail"
  ],
  "Resource": [
    "arn:aws:bedrock:*:*:model/anthropic.claude-3-5-sonnet*",
    "arn:aws:bedrock:*:*:knowledge-base/*"
  ]
}
```

### Lambda Role (Crawler)
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject"
  ],
  "Resource": "arn:aws:s3:::foodlens-rag-docs/*"
}
```

---

## 6. 비용 추정 (월간, 프로덕션)

| 서비스 | 예상 비용 | 비고 |
|--------|-----------|------|
| ECS Fargate (Frontend) | ~$50 | 2 tasks |
| ECS Fargate (Backend) | ~$100 | 2 tasks |
| RDS PostgreSQL | ~$150 | db.r6g.large, Multi-AZ |
| Neptune | ~$200 | db.r5.large |
| ElastiCache Redis | ~$80 | cache.r6g.large |
| Bedrock (Claude) | ~$100 | 사용량 기반 |
| S3 + CloudFront | ~$20 | 저용량 |
| Lambda + EventBridge | ~$5 | 저빈도 |
| 기타 (WAF, Route53 등) | ~$30 | |
| **합계** | **~$735/월** | |

---

## 7. 시연 환경 빠른 시작 가이드

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env에 AWS 자격증명, API 키 입력

# 2. Docker 서비스 시작
docker-compose up -d

# 3. DB 마이그레이션
cd backend && alembic upgrade head

# 4. 백엔드 시작
uvicorn app.main:app --reload --port 8000

# 5. 프론트엔드 시작
cd frontend && npm run dev

# 6. 브라우저 접속
# http://localhost:3000
```
