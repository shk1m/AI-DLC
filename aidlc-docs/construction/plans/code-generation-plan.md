# Code Generation Plan — Unit 1 (Frontend)

> **Scope**: Unit 1 (Frontend) only — per `aidlc-docs/inception/application-design/unit-of-work.md`.
> **Target Path**: `frontend/` at workspace root.
> **Strategy**: Step-by-Step (사용자 지시) — 한 답변에 모두 만들지 않고, 단계별로 꼬리 질문에 맞춰 진행.

---

## Step 1 — Foundation (현재 단계)
- [x] Next.js 14 (App Router) + TypeScript 부트스트랩 설정 파일 생성
  - [x] `frontend/package.json`
  - [x] `frontend/tsconfig.json`
  - [x] `frontend/next.config.mjs`
  - [x] `frontend/postcss.config.mjs`
  - [x] `frontend/tailwind.config.ts`
  - [x] `frontend/.gitignore`
  - [x] `frontend/.eslintrc.json`
- [x] Tailwind 글로벌 스타일 + 디자인 토큰 (`frontend/app/globals.css`)
- [x] App Router root (`frontend/app/layout.tsx`, `frontend/app/page.tsx`)
- [x] **Strict TypeScript Interfaces (API 계약 명세)** — `frontend/types/index.ts`
  - [x] `Category`, `Ingredient`, `PricePoint`, `SpikeEvent`, `NewsItem`
  - [x] `PriceSeries`, `Recipe`, `RecipeIngredient`, `CostSimulationResult`
  - [x] `Substitute`, `ChatMessage`, `ChatStreamChunk`
  - [x] API Response wrapper (`ApiResponse<T>`, `ApiError`)
- [x] **Async Mock API** (백엔드 통신 흉내, 로딩 스켈레톤 테스트 가능) — `frontend/lib/mockApi.ts`
  - [x] `fetchCategories`, `fetchIngredients`, `fetchPriceSeries`
  - [x] `fetchRecipes`, `fetchSubstitutes`, `fetchNewsForSpike`
  - [x] 인공 latency + ApiResponse 래핑 + 일부 호출 실패 시뮬레이션 옵션
- [x] **Zustand 전역 상태** — `frontend/lib/store.ts`
  - [x] selectedCategoryId, selectedIngredientId, selectedDate
  - [x] activeRecipeId, isChatOpen, chatMessages
  - [x] hover/selection actions (Bento-box 컴포넌트 간 동기화)
- [x] **Bento-box DashboardLayout Skeleton** — `frontend/components/dashboard/DashboardLayout.tsx`
  - [x] 좌측: CategoryFilter 슬롯
  - [x] 중앙 상단: PriceChart 슬롯
  - [x] 중앙 하단: PriceTable 슬롯
  - [x] 우측 상단: CostSimulator 슬롯
  - [x] 우측 하단: SubstituteRecommender 슬롯
  - [x] 플로팅: ChatBot 슬롯
- [x] 각 슬롯에 들어갈 7개 컴포넌트 placeholder (skeleton 카드 + TODO 주석)
- [x] 공통 UI: `SkeletonCard`, `BentoCard`, `SectionHeader`

---

## Step 2 — CategoryFilter + PriceChart (완료)
- [x] `lib/hooks.ts` — useAsync, useDebouncedValue
- [x] `CategoryFilter`: 탭 + 검색(디바운스) + 동적 카테고리/재료 로딩 + Zustand 동기화
- [x] `PriceChart`: Recharts LineChart, Spike ReferenceDot, **CustomTooltip + 뉴스 헤드라인/키워드**
- [x] KPI 미니카드 (현재가 / 평균 / 최저 / 최고 + 변동률)
- [x] 차트 hover → focusedDate 전역 동기화

## Step 3 — PriceTable + CostSimulator + SubstituteRecommender (완료)
- [x] `PriceTable`: 최근 7일 도매/소매/Gap, 행 호버 ↔ 차트 cursor 양방향
- [x] `CostSimulator`: 식수 +/-, 레시피 카드, breakdown, rationale, 챗봇 트리거
- [x] `SubstituteRecommender`: 활성 레시피 고가 재료 자동 선택, 유사도/품질 바, 시세보기/대화 액션

## Step 4 — Floating ChatBot (완료)
- [x] `lib/chatStream.ts`: AsyncGenerator 기반 토큰 스트리밍 (Bedrock 시뮬레이션)
- [x] `ChatBot`: framer-motion 플로팅 + 슬라이드-업 패널
- [x] 타이핑 cursor + 인라인 태그 칩 (클릭 시 Zustand selection 변경)
- [x] 인용(Citations) 풋노트 + 추천 프롬프트
- [x] store: `appendChatCitation` 추가

## Step 5 — Polish
- [ ] Framer Motion 인터랙션
- [ ] 다크 모드 토큰 정리
- [ ] 접근성 (ARIA, keyboard nav)
- [ ] 데모용 Mock 시나리오 풍부화
