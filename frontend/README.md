# DLC Frontend (Unit 1)

> Data Lake Crew — MD/영양사 전용 AI 대시보드 프론트엔드.
> `aidlc-docs/inception/application-design/unit-of-work.md` 의 **Unit 1 (Frontend)** 범위만 담당합니다.

## Tech Stack

- Next.js 14 (App Router) + React 18 + TypeScript (strict)
- Tailwind CSS 3
- Recharts 2 (시세 차트)
- Zustand 4 (전역 상태)
- Framer Motion (인터랙션)
- Lucide React (아이콘)

## Quick Start

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

## Directory

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx          # DashboardLayout 마운트
│   └── globals.css       # Tailwind + Bento grid 토큰
├── components/
│   ├── dashboard/
│   │   ├── DashboardLayout.tsx     # FE-01 (Bento-box 껍데기)
│   │   ├── PriceChart.tsx          # FE-02 (skeleton)
│   │   ├── CategoryFilter.tsx      # FE-03 (skeleton)
│   │   ├── PriceTable.tsx          # FE-04 (skeleton)
│   │   ├── CostSimulator.tsx       # FE-05 (skeleton)
│   │   ├── ChatBot.tsx             # FE-06 (skeleton)
│   │   └── SubstituteRecommender.tsx # FE-07 (skeleton)
│   └── ui/
│       ├── BentoCard.tsx
│       ├── SectionHeader.tsx
│       └── SkeletonCard.tsx
├── lib/
│   ├── mockApi.ts        # 비동기 Mock API (백엔드 계약 준수)
│   ├── mockData.ts       # 시연용 시드 데이터
│   ├── store.ts          # Zustand 전역 store
│   └── utils.ts
├── types/
│   └── index.ts          # ★ API 계약 — 백엔드 팀 단일 진실 공급원
└── package.json
```

## API Contract

`frontend/types/index.ts` 가 백엔드 FastAPI 팀과의 **API 계약(Contract)** 입니다.
- 모든 응답은 `ApiResponse<T>` / `ApiError` 로 래핑
- 시간은 ISO 8601 (UTC)
- 필드명은 camelCase (Pydantic `alias_generator = to_camel` 사용 권장)

Mock 모드 토글:

```bash
NEXT_PUBLIC_USE_MOCK=true   # 기본값 (mockApi.ts 사용)
NEXT_PUBLIC_USE_MOCK=false  # 실 백엔드 (lib/api.ts 추가 예정)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Step-by-Step 개발 진척

- [x] **Step 1** — Foundation: 프로젝트 세팅, types, mockApi, store, BentoCard, DashboardLayout skeleton
- [ ] **Step 2** — CategoryFilter + PriceChart (Recharts + CustomTooltip + Spike news)
- [ ] **Step 3** — PriceTable + CostSimulator + SubstituteRecommender
- [ ] **Step 4** — ChatBot (스트리밍 + 타이핑 + 인라인 태그)
- [ ] **Step 5** — Polish (모션, 접근성, 데모 시나리오)

자세한 계획은 `aidlc-docs/construction/plans/code-generation-plan.md` 참고.

## 다른 Unit과의 경계

- **Unit 2 (Backend, FastAPI)**: `types/index.ts` 의 인터페이스를 Pydantic 스키마로 미러링.
- **Unit 3 (AI/Data)**: ChatBot 의 WebSocket 메시지는 `ChatStreamChunk` 타입을 따라야 함.
- **Unit 4 (Integration)**: `lib/mockApi.ts` 와 동일 시그니처의 `lib/api.ts` 작성 (Step 5 에서 통합).
