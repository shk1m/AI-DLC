# Unit 01 — Frontend 개발 채팅 이력

> **세션**: AWS 사내 해커톤 — DLC (Data Lake Crew) MD/영양사 AI 단가 최적화 대시보드
> **담당**: Unit 1 (Frontend) — 팀원 A
> **기간**: 2026-05-20 (Wed)
> **결과 브랜치**: `unit01` (origin/unit01)
> **배포 URL**: http://dlc-frontend-alb-145465936.us-east-1.elb.amazonaws.com
> **참조 문서**: `aidlc-docs/inception/application-design/unit-of-work.md`

---

## 0. 세션 개요

본 세션은 **AI-DLC core-workflow 의 Construction → Code Generation 단계**에서, Unit 1(Frontend) 범위만을 대상으로 진행되었다. 사용자(프론트엔드 담당)가 명시적으로 요구한 **Step-by-Step 점진적 구현 원칙**과 **다른 unit(Backend/AI/Data/Integration) 영역 침범 금지 원칙**을 따라 작업했다.

### 핵심 산출물

- `frontend/` (Next.js 14 + React 18 + TypeScript strict)
- 7개 컴포넌트 (FE-01 ~ FE-07) 라이브 동작
- API 계약 명세 (`frontend/types/index.ts`)
- Async Mock API 레이어 (실 백엔드 교체 가능 시그니처)
- Zustand 단일 store (Bento-box 카드 간 상태 동기화)
- 단일 화면(viewport-fit) Bento-box 레이아웃
- Floating ChatBot (Bedrock 토큰 스트리밍 시뮬레이션)
- Dockerfile + ECS Fargate 배포 (ALB 포함)

---

## 1. 초기 요구사항 (User Prompt #1)

사용자는 Next.js 14 기반 단일 페이지 대시보드를 요청했다. 핵심 제약:

- 컨셉: **MD/영양사 전용 AI 단가 최적화 대시보드**. 시세·뉴스·레시피·온톨로지 데이터를 결합해 급식 메뉴 단가 최적화.
- 기술 스택: Next.js 14 (App Router) · React · TypeScript · Tailwind CSS · Recharts · Lucide React
- UI: **Bento-box 레이아웃** (좌측 카테고리 / 중앙 차트 / 우측 시뮬레이터·추천 / 우하단 플로팅 챗봇)
- 차트: 카테고리 탭 + 인터랙티브 라인차트 + **CustomTooltip 에서 Spike 시점 뉴스 헤드라인 표시**
- 챗봇: 플로팅 토글, **Bedrock 스트리밍 + 타이핑 효과 + 인라인 추천 칩**
- Mock Data First (백엔드 미연동 시연 가능)
- Component Separation (DashboardLayout / PriceChart / ChatBot 등 분리)

### 추가 요구사항 (사용자 명시)

1. **Strict TypeScript Interfaces**: 컴포넌트가 사용하는 모든 데이터의 타입을 별도 파일에 정의 → 백엔드 팀에 대한 **API 응답(JSON) 명세서 역할**
2. **Async Mocking & Loading State**: 정적 변수가 아닌 비동기 함수로 mock 래핑 → **로딩 스켈레톤 테스트 가능**
3. **State Management Architecture**: Zustand 활용. 좌측 탭 클릭 → 중앙 차트 + 우측 레시피 동시 갱신되는 **상태 공유 뼈대**
4. **Step-by-Step Implementation**: 첫 답변에서는 폴더 구조 + 타입 + 레이아웃 Skeleton만. 이후 꼬리 질문에 맞춰 컴포넌트를 하나씩 구현
5. **Unit of Work 기반 개발**: `unit-of-work.md` 의 Unit 1 (Frontend) 가이드 엄격 준수

---

## 2. Step 1 — Foundation (Skeleton)

### 생성된 파일 구조

```
frontend/
├── app/                    layout.tsx · page.tsx · globals.css
├── components/
│   ├── dashboard/          DashboardLayout(FE-01) + 6개 placeholder(FE-02~07)
│   └── ui/                 BentoCard · SectionHeader · SkeletonCard
├── lib/
│   ├── mockApi.ts          (async + 인공 latency + ApiResponse 래핑)
│   ├── mockData.ts         (15개 시세 시리즈, 뉴스, 레시피, 대체재)
│   ├── store.ts            (Zustand: selection slice + chat slice)
│   └── utils.ts
├── types/index.ts          (★ API 계약 — 30+ 인터페이스)
├── package.json
├── tsconfig.json (strict)
├── tailwind.config.ts
└── README.md
```

### 핵심 설계 포인트

- **API 계약 단일 진실 공급원**: `types/index.ts` 가 백엔드 Pydantic 스키마의 미러 대상
- **교체 가능한 Mock 레이어**: `NEXT_PUBLIC_USE_MOCK` 토글 환경변수
- **Zustand 단일 store**: devtools 활성, 컴포넌트 간 상태 동기화

### Step 1 검증 결과

| 검증 | 결과 |
|---|---|
| `tsc --noEmit` (strict) | ✅ |
| `next lint` | ✅ no warnings |
| `next build` | ✅ (`/` 14.9 kB / First Load JS 102 kB) |

---

## 3. Step 2~4 — Live Components

### Step 2 — CategoryFilter + PriceChart + PriceTable

- `lib/hooks.ts`: `useAsync` (race condition 방어), `useDebouncedValue`
- **CategoryFilter**: 카테고리 탭 + 250ms 디바운스 검색 + alias 매칭 + Zustand 동기화
- **PriceChart**: Recharts LineChart (도매/소매) + ReferenceDot Spike 마커
- **`PriceChartTooltip` (CustomTooltip)**:
  - 일반 시점 → 날짜 + 도매/소매/Gap + 변동률
  - **Spike 시점 → summary + 키워드 칩 + 뉴스 헤드라인 (최대 3건)**
- **PriceTable**: 최근 7일, 행 hover ↔ 차트 cursor 양방향 동기화

### Step 3 — CostSimulator + SubstituteRecommender

- **CostSimulator**: 식수 +/- 컨트롤, 레시피 카드, breakdown, AI rationale
- **SubstituteRecommender**: 활성 레시피 고가 재료 자동 픽, 유사도/품질 바, 시세보기/대화 액션

### Step 4 — Floating ChatBot

- `lib/chatStream.ts`: AsyncGenerator 기반 토큰 스트리밍 (Bedrock 시뮬레이션)
- **ChatBot**: framer-motion 플로팅 + 슬라이드-업 패널, 타이핑 cursor, 인라인 태그 칩, 인용 풋노트

### Step 2~4 검증 결과

| 검증 | 결과 |
|---|---|
| `tsc --noEmit` | ✅ |
| `next lint` | ✅ no warnings |
| `next build` | ✅ (`/` 162 kB / First Load JS 249 kB) |
| Dev server | ✅ http://localhost:3001 HTTP 200 |

### 데모 시나리오

1. 좌측 **농산물 → 양파** 클릭
2. 차트 빨간 Spike 점에 호버 → "산지 폭우 피해" 뉴스 헤드라인 등장
3. 우측 **소불고기 정식** 카드 클릭 → SubstituteRecommender 가 한우→돼지/닭 대체재 추천
4. "AI 유사 레시피" 버튼 → 챗봇 자동 오픈
5. **"양파 가격이 왜 올랐어?"** 추천 프롬프트 클릭 → 스트리밍 답변
6. 답변 속 "양파" 칩 클릭 → 좌측 selection 자동 변경 → 차트 갱신

---

## 4. UI/UX 한 판 가독성 개선 (User Prompt #3)

> **사용자**: "웹화면 배열이 아쉬워 이거 한판에 가독성 있게 구성하고싶은데.. 디자인이나 기능은 너무 좋으니 ui/ux만 개선해줘" (스크린샷 첨부)

### 진단

1. 세로 스크롤 발생 — 한 화면에 다 안 들어옴
2. 우측 빈 공간 — Substitute 카드가 짧아 휑함
3. KPI 4개 카드가 차트 위 큰 영역 차지
4. 카드 패딩이 일률적으로 두꺼움

### 변경사항

- 페이지 자체 스크롤 제거 (`html/body { overflow: hidden }`)
- `100vh - 56px` 고정 그리드, 5개 카드가 한 화면에 모두 배치
- 그리드 영역: `filter(full height) / chart(1.55fr) / sim / table(1fr) / sub`
- TopBar 80px → 56px
- 카드 패딩 `p-6` → `p-4`, KPI → 슬림 가로 strip
- 반응형 브레이크포인트(1480/1180/768) 정비
- 각 카드 내부에서만 자체 스크롤 (`.scroll-thin`)

---

## 5. .vscode 제외 + unit01 Push (User Prompt #4)

> **사용자**: ".vscode 해당 경로는 제외하고 올릴거야 gitignore에 추가해서 unit01 이라는 브랜치에 push해줘"

### 실행

1. 루트 `.gitignore` 생성 (`.vscode/`, `node_modules/`, `.next/`, env, 로그 등)
2. `git rm --cached .vscode/settings.json` (로컬 파일 보존)
3. 11개 파일 staging → 커밋 `chore(unit01): UI/UX 한 판 가독성 개선 + .gitignore 추가`
4. `git push origin unit01`

### 결과

| 항목 | 값 |
|---|---|
| 커밋 | `98a8bb3` on `unit01` |
| Push | `20c9975..98a8bb3 unit01 -> unit01` |
| GitHub | https://github.com/shk1m/AI-DLC/tree/unit01 |

---

## 6. ECS Fargate 배포 (User Prompt #5~8)

> **사용자**: "프론트엔드 도커파일 만들어서 ecs에 배포해주는 것까지 진행해줘. 내가 먼저 aws에 배포를 하고 이후 unit 2~과정 차례대로 자원을 배포할거야"

### 6.1 Dockerfile 작성

- Multi-stage build (deps → builder → runner)
- `output: 'standalone'` 활성화 (next.config.mjs)
- 최종 이미지 ~50MB (node:18-alpine + standalone 결과물만)
- non-root 사용자, HEALTHCHECK 포함

### 6.2 계정 전환

- 초기 시도: `859727130921` (shoo.kim, ap-northeast-2) — **잘못된 계정**
- 사용자가 올바른 자격증명 제공: `777836495456` (WSParticipantRole, us-east-1)
- 이전 계정의 ECR 리포지토리 정리

### 6.3 Docker 빌드 + ECR Push

- 첫 시도 실패: `npm ci --omit=dev` → tailwindcss(devDep) 누락 → 수정
- 두 번째 시도: 빌드 성공, 이미지 49.7MB
- ECR Push: `docker push` 로 직접 push → 성공 (digest: `sha256:dfe470e9...`)
- 병목 원인: Mac ARM64 → linux/amd64 크로스 빌드 시 QEMU 에뮬레이션 + 레이어 업로드 느림

### 6.4 ECS 인프라 구성 (scripts/ecs-deploy.sh)

| 단계 | 리소스 | 결과 |
|---|---|---|
| Step 1 | VPC/Subnet 조회 | `vpc-0cd044b14fe0b8ab5`, 8개 서브넷 |
| Step 2 | 보안 그룹 | `sg-05f41d6c19888fb50` (3000, 80 인바운드) |
| Step 3 | ECS Cluster | `dlc-cluster` 생성 |
| Step 4 | CloudWatch Log Group | `/ecs/dlc/unit01/frontend` |
| Step 5 | Task Execution Role | `ecsTaskExecutionRole` (기존 존재) |
| Step 6 | Task Definition | `dlc-unit01-frontend:1` (0.5 vCPU / 1GB) |
| Step 7 | ECS Service | `dlc-unit01-frontend-svc` 생성 |

### 6.5 ALB 추가 (User Prompt #8)

> **사용자**: "public lb를 넣고 외부에서 해당 웹사이트 접속 가능하게 지원해줘. 현재 http://54.162.9.103:3000 접속 안돼"

**원인**: ECS Task에 공인 IP가 붙었지만 보안 그룹/네트워크 이슈로 직접 접속 불안정.

**해결**: Application Load Balancer 추가.

| 단계 | 리소스 | 값 |
|---|---|---|
| ALB SG | `sg-0327d422ec965c87c` | HTTP:80 from 0.0.0.0/0 |
| ALB→ECS SG | 인바운드 추가 | ALB SG → ECS SG:3000 |
| Target Group | `dlc-unit01-frontend-tg` | IP type, port 3000, health check `/` |
| ALB | `dlc-frontend-alb` | internet-facing, 2 subnets |
| Listener | HTTP:80 | → Target Group:3000 |
| ECS Service | `dlc-unit01-frontend` | ALB Target Group 연결 |

**이슈**: 기존 서비스가 draining 상태라 재생성 실패 → 새 서비스명(`dlc-unit01-frontend`)으로 JSON 파일 기반 생성하여 해결.

### 6.6 최종 배포 결과

| 항목 | 값 |
|---|---|
| **접속 URL** | **http://dlc-frontend-alb-145465936.us-east-1.elb.amazonaws.com** |
| 계정 | `777836495456` |
| 리전 | `us-east-1` |
| ECR 이미지 | `777836495456.dkr.ecr.us-east-1.amazonaws.com/dlc-unit01-frontend:latest` |
| ECS Cluster | `dlc-cluster` |
| ECS Service | `dlc-unit01-frontend` |
| Task Definition | `dlc-unit01-frontend:1` (0.5 vCPU / 1GB) |
| ALB | `dlc-frontend-alb-145465936.us-east-1.elb.amazonaws.com` |
| CloudWatch Logs | `/ecs/dlc/unit01/frontend` |
| 접속 테스트 | `curl` → **HTTP 200** ✅ |

---

## 7. 다른 Unit과의 경계 (협업 준수 사항)

본 세션은 **Unit 1 (Frontend) 영역만** 다뤘으며, 다른 unit 의 코드 또는 문서를 생성/수정하지 않았다.

### 공유 인프라 (다른 unit이 사용 가능)

```
Cluster : dlc-cluster
Region  : us-east-1
VPC     : vpc-0cd044b14fe0b8ab5
Subnets : subnet-0ccd1f9c1b50e60c4, subnet-049e22710f4cf19b8, ...
ALB     : dlc-frontend-alb (Listener Rule 추가로 /api/* 라우팅 가능)
```

### 백엔드 팀 연동 방법

- `types/index.ts` 의 인터페이스를 Pydantic 스키마로 미러링 (`alias_generator = to_camel`)
- ChatBot WebSocket 메시지는 `ChatStreamChunk` 타입 준수
- 백엔드 Task가 올라오면 프론트 `NEXT_PUBLIC_API_BASE_URL` 환경변수만 업데이트 + ECS force-new-deployment
- ALB에 `/api/*` Listener Rule 추가하여 백엔드 Target Group으로 라우팅

---

## 8. 생성된 스크립트 목록

| 파일 | 용도 |
|---|---|
| `scripts/deploy-unit01.sh` | ECR + ECS 전체 배포 (원스텝) |
| `scripts/ecs-deploy.sh` | ECS 인프라만 구성 (ECR push 이후) |
| `scripts/add-alb.sh` | ALB + Target Group + Service 재연결 |
| `scripts/get-url.sh` | 배포된 Task의 공인 IP 조회 |
| `scripts/create-svc.json` | ECS Service 생성 JSON (ALB 연결) |

---

## 9. 향후 작업

- [ ] **Step 5 — Polish**: Framer Motion 마이크로 인터랙션, 다크 모드, 접근성
- [ ] **백엔드 연동**: `lib/api.ts` 작성 + `NEXT_PUBLIC_USE_MOCK=false` 전환
- [ ] **CI/CD**: GitHub Actions → ECR push → ECS deploy 자동화
- [ ] **HTTPS**: ACM 인증서 + ALB HTTPS Listener (도메인 확보 시)
- [ ] **인프라 정리**: `terraform destroy` 또는 수동 삭제 스크립트

---

## 10. 참고 — 로컬 개발 명령

```bash
cd frontend
npm install
npm run dev         # http://localhost:3000
npm run typecheck   # tsc --noEmit (strict)
npm run lint        # next lint
npm run build       # next build (프로덕션 컴파일)
```

## 11. 참고 — 배포 명령 (수동)

```bash
# 환경변수 설정 (AWS 자격증명)
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# ECR 로그인
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 777836495456.dkr.ecr.us-east-1.amazonaws.com

# Docker 빌드 + Push
cd frontend
docker buildx build --platform linux/amd64 \
  -t 777836495456.dkr.ecr.us-east-1.amazonaws.com/dlc-unit01-frontend:latest \
  --push .

# ECS 서비스 강제 재배포
aws ecs update-service --region us-east-1 \
  --cluster dlc-cluster \
  --service dlc-unit01-frontend \
  --force-new-deployment
```
