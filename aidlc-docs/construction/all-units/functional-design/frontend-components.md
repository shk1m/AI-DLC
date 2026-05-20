# 프론트엔드 컴포넌트 상세 설계

---

## 컴포넌트 계층 구조

```
app/page.tsx
└── DashboardLayout
    ├── Header (서비스 로고 + 사용자 역할 선택)
    ├── CategoryTabs (농산물 | 수산물 | 축산물 | 가공식품)
    ├── MainContent (Bento Grid)
    │   ├── PriceChart (시세 추이 차트)
    │   ├── PriceTable (도매/소매/Gap 테이블)
    │   ├── CostSimulator (원가 시뮬레이션)
    │   └── SubstituteRecommender (대체 식자재)
    └── ChatBot (플로팅, 독립)
```

---

## FE-01: DashboardLayout

### Props
```typescript
interface DashboardLayoutProps {
  children: React.ReactNode
}
```

### State
```typescript
{
  activeCategory: CategoryEnum    // 현재 선택된 카테고리
  selectedItem: FoodItem | null   // 선택된 품목
  userRole: UserRoleEnum          // 사용자 역할
}
```

---

## FE-02: PriceChart

### Props
```typescript
interface PriceChartProps {
  itemId: string
  period: '1w' | '1m' | '3m' | '6m' | '1y'
}
```

### State
```typescript
{
  chartData: PriceTimeSeries | null
  spikes: SpikeEvent[]
  loading: boolean
  hoveredSpike: SpikeEvent | null
}
```

### CustomTooltip 동작
```
일반 포인트 hover:
  → 날짜 + 도매가 + 소매가 표시

Spike 포인트 hover:
  → 날짜 + 가격 + 변동률
  → 뉴스 헤드라인 (최대 3개)
  → 각 헤드라인 클릭 → 원문 URL 이동
```

### API 연동
- GET `/api/prices/{itemId}/history?period={period}`
- 응답: `{ timeSeries: [], spikes: [{ date, news[] }] }`

---

## FE-03: CategoryFilter

### Props
```typescript
interface CategoryFilterProps {
  onCategoryChange: (category: CategoryEnum) => void
  onSearch: (query: string) => void
}
```

### State
```typescript
{
  activeTab: CategoryEnum
  searchQuery: string
}
```

### 인터랙션
- 탭 클릭 → 카테고리 전환 (애니메이션)
- 검색 입력 → 디바운스 300ms → 필터링

---

## FE-04: PriceTable

### Props
```typescript
interface PriceTableProps {
  category: CategoryEnum
  searchQuery?: string
  onItemSelect: (item: FoodItem) => void
}
```

### State
```typescript
{
  items: PriceItem[]
  sortBy: 'name' | 'wholesale' | 'retail' | 'gap'
  sortOrder: 'asc' | 'desc'
  loading: boolean
}
```

### 테이블 컬럼
| 컬럼 | 타입 | 정렬 가능 |
|------|------|:---------:|
| 품목명 | string | ✓ |
| 도매가 | number (원) | ✓ |
| 소매가 | number (원) | ✓ |
| Gap (%) | number | ✓ |
| 전일 대비 | number (↑↓) | ✓ |

---

## FE-05: CostSimulator

### Props
```typescript
interface CostSimulatorProps {
  selectedItem?: FoodItem
}
```

### State
```typescript
{
  servings: number              // 식수 입력
  budget: number | null         // 예산 (선택)
  results: CostSimulation | null
  suggestions: MenuSuggestion[]
  loading: boolean
}
```

### 사용자 흐름
1. 식수 입력 (숫자 입력 + 프리셋 버튼: 100/1000/10000)
2. 예산 입력 (선택)
3. "시뮬레이션" 버튼 클릭
4. 결과 표시: 레시피 목록 + 재료별 원가 + 총 원가

### API 연동
- POST `/api/recipes/simulate` body: `{ servings, budget, constraints }`

---

## FE-06: ChatBot

### Props
```typescript
interface ChatBotProps {
  // 독립 컴포넌트, props 없음
}
```

### State
```typescript
{
  isOpen: boolean               // 챗봇 열림/닫힘
  messages: ChatMessage[]       // 대화 이력
  inputValue: string            // 입력 중인 메시지
  isTyping: boolean             // AI 타이핑 중
  sessionId: string             // WebSocket 세션
}
```

### 인터랙션
- 플로팅 버튼 클릭 → 챗봇 열림 (slide-up 애니메이션)
- 메시지 전송 → WebSocket으로 전달
- AI 응답 → 토큰 단위 타이핑 애니메이션
- 출처 표시 → 접이식 "출처 보기" 섹션

### WebSocket 연동
- 연결: `ws://localhost:8000/ws/chat/{sessionId}`
- 전송: `{ type: "message", content: string }`
- 수신: `{ type: "token" | "done" | "source", content: string }`

---

## FE-07: SubstituteRecommender

### Props
```typescript
interface SubstituteRecommenderProps {
  itemId: string
  itemName: string
}
```

### State
```typescript
{
  substitutes: SubstituteItem[]
  loading: boolean
  selectedSubstitute: SubstituteItem | null
}
```

### 표시 정보
- 대체 식자재명
- 현재 가격 vs 원래 가격
- 절감률 (%)
- 유사도 점수
- 대체 사유 (온톨로지 관계)

### API 연동
- GET `/api/substitutes/{itemId}`
