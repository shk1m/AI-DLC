/**
 * ============================================================================
 *  DLC (Data Lake Crew) — Frontend Type Definitions
 * ----------------------------------------------------------------------------
 *  이 파일은 프론트엔드(Unit 1)와 백엔드(Unit 2/3/4) 간 **API 계약(Contract)**
 *  역할을 합니다. 백엔드 팀이 FastAPI Pydantic 스키마를 작성할 때 본 인터페이스
 *  를 단일 진실 공급원(Single Source of Truth)으로 사용해 주세요.
 *
 *  - 모든 필드는 snake_case 가 아닌 camelCase 로 통일합니다 (FE 표준).
 *    백엔드는 Pydantic `alias_generator = to_camel` 을 사용해 매핑하세요.
 *  - 시간은 모두 ISO 8601 (UTC, e.g. "2026-05-20T13:30:00Z").
 *  - 모든 API 응답은 `ApiResponse<T>` 또는 `ApiError` 로 래핑됩니다.
 * ============================================================================
 */

// ─────────────────────────────────────────────────────────────────────────────
// 1. Domain — Category / Ingredient
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 식자재 대분류
 * 백엔드 ENUM과 1:1 매핑. 새로운 카테고리 추가 시 여기와 백엔드를 동시에 갱신.
 */
export type CategorySlug =
  | 'agriculture'   // 농산물
  | 'fishery'       // 수산물
  | 'processed'     // 가공식품
  | 'livestock'     // 축산물 (확장 예시)
  | string;         // 미래 확장 허용 (백엔드 추가 가능)

export interface Category {
  id: string;
  slug: CategorySlug;
  /** 화면 표시용 한글명 (예: "농산물") */
  name: string;
  /** 카테고리 아이콘 키 (Lucide React 아이콘명) */
  icon?: string;
  /** 하위 중분류 개수(요약용) */
  subCategoryCount?: number;
}

/**
 * 식자재 (개별 품목)
 * 카테고리 하위에 매달리며, 검색/선택의 기본 단위.
 */
export interface Ingredient {
  id: string;
  categoryId: string;
  /** 표시명 (예: "양파") */
  name: string;
  /** 검색용 별칭 (예: ["양파", "onion", "Allium cepa"]) */
  aliases?: string[];
  /** 단위 (예: "kg", "마리", "박스") */
  unit: string;
  /** 온톨로지 노드 ID (Neptune) — RAG 추적용 */
  ontologyNodeId?: string;
  /** 썸네일 URL (선택) */
  imageUrl?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Price Series & Spike Events
// ─────────────────────────────────────────────────────────────────────────────

/** 시세 채널 — 도매/소매/Gap */
export type PriceChannel = 'wholesale' | 'retail' | 'gap';

/**
 * 단일 시세 데이터 포인트.
 * `isSpike: true` 인 경우 PriceChart 가 마커를 그리고
 * CustomTooltip 이 `spike` 객체의 뉴스/키워드를 함께 렌더링합니다.
 */
export interface PricePoint {
  /** ISO 날짜 (예: "2026-05-15") */
  date: string;
  /** 도매가 (KRW / unit) */
  wholesale: number;
  /** 소매가 (KRW / unit) */
  retail: number;
  /** retail - wholesale (서버 계산값, 클라이언트 신뢰) */
  gap: number;
  /** 전일 대비 변동률 (%) */
  changeRate?: number;
  /** Spike 이벤트 발생 여부 */
  isSpike?: boolean;
  /** Spike 이벤트 상세 (isSpike=true 일 때만 채워짐) */
  spike?: SpikeEvent;
}

/**
 * 가격 급등/급락 이벤트.
 * 백엔드 PriceService.detectSpike() 결과 + NewsService 매칭 결과의 결합체.
 */
export interface SpikeEvent {
  id: string;
  date: string;
  ingredientId: string;
  /** 'up' | 'down' */
  direction: 'up' | 'down';
  /** 변동률 (%) */
  magnitude: number;
  /** 한 줄 요약 (Bedrock 요약 결과) */
  summary: string;
  /** 키워드 태그 (트렌드 지수, 이슈) */
  keywords: string[];
  /** 관련 뉴스 (정렬: 영향도 desc, 최대 5건 권장) */
  news: NewsItem[];
}

/**
 * 차트에 들어갈 시계열 데이터.
 * `points` 는 날짜 오름차순으로 정렬되어 있어야 함.
 */
export interface PriceSeries {
  ingredientId: string;
  ingredientName: string;
  unit: string;
  /** 통계 요약 (KPI 카드용) */
  summary: PriceSeriesSummary;
  /** 시계열 본체 */
  points: PricePoint[];
}

export interface PriceSeriesSummary {
  /** 조회 구간 (예: "30D", "90D") */
  range: string;
  current: number;
  /** 평균가 (구간 내) */
  average: number;
  /** 최저/최고 */
  min: number;
  max: number;
  /** 구간 변동률 (%) */
  changeRate: number;
  /** Spike 발생 횟수 */
  spikeCount: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. News
// ─────────────────────────────────────────────────────────────────────────────

export interface NewsItem {
  id: string;
  title: string;
  /** 출처 매체 (예: "농민신문", "농림축산식품부") */
  source: string;
  /** 발행일 (ISO 8601) */
  publishedAt: string;
  url: string;
  /** 이슈 영향도 0~1 (백엔드 산출) */
  impactScore?: number;
  /** Bedrock 요약 (선택, 호버 시 표시) */
  summary?: string;
  /** 매칭된 키워드 */
  matchedKeywords?: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Recipe & Cost Simulation
// ─────────────────────────────────────────────────────────────────────────────

export interface RecipeIngredient {
  ingredientId: string;
  /** 재료 표시명 (캐시) */
  name: string;
  /** 1인분 기준 사용량 */
  quantityPerServing: number;
  unit: string;
  /** 현재 단가 (server-snapshot) */
  unitPrice: number;
}

export interface Recipe {
  id: string;
  name: string;
  /** 표준 1인분 식사로서의 분류 (예: "한식 백반", "분식") */
  cuisine?: string;
  /** 1인분 예상 원가 (KRW) — 서버 계산 */
  costPerServing: number;
  /** 식수 (default servings, UI 초기값 힌트) */
  defaultServings: number;
  ingredients: RecipeIngredient[];
  /** Bedrock 추천 신뢰도 (0~1) */
  confidence?: number;
  /** 추천 근거(요약) */
  rationale?: string;
}

/**
 * 원가 시뮬레이션 결과.
 * CostSimulator 에서 식수 입력 → POST /recipes/{id}/simulate 의 응답 타입.
 */
export interface CostSimulationResult {
  recipeId: string;
  servings: number;
  /** 총 원가 (KRW) */
  totalCost: number;
  /** 1인분 원가 */
  costPerServing: number;
  /** 재료별 원가 분해 */
  breakdown: Array<{
    ingredientId: string;
    name: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    subtotal: number;
    /** 직전 시뮬레이션 대비 단가 변동률 (%) */
    deltaRate?: number;
  }>;
  simulatedAt: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Substitute Recommendation
// ─────────────────────────────────────────────────────────────────────────────

export interface Substitute {
  /** 추천 대체 재료 */
  ingredient: Ingredient;
  /** 절감액 (KRW / 1인분) */
  savingPerServing: number;
  /** 절감률 (%) */
  savingRate: number;
  /** 온톨로지 기반 유사도 (0~1) */
  similarity: number;
  /** 영양/맛 유지 점수 (0~1) */
  qualityScore: number;
  /** 추천 사유 (Bedrock 생성) */
  rationale: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. ChatBot
// ─────────────────────────────────────────────────────────────────────────────

export type ChatRole = 'user' | 'assistant' | 'system';

/**
 * 챗봇 메시지.
 * `inlineTags` 는 답변 본문 안에 인라인 칩으로 렌더링되는 추천 식자재/레시피 등.
 */
export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  /** assistant 메시지가 스트리밍 중인지 여부 (typing animation) */
  isStreaming?: boolean;
  /** 답변 인라인 태그 (식자재 칩, 레시피 칩 등) */
  inlineTags?: ChatInlineTag[];
  /** RAG 출처 인용 (Bedrock KB) */
  citations?: ChatCitation[];
}

export interface ChatInlineTag {
  /** 태그 타입에 따라 클릭 시 다른 동작 */
  type: 'ingredient' | 'recipe' | 'category' | 'news';
  /** 표시 라벨 */
  label: string;
  /** 참조 ID (ingredientId, recipeId 등) */
  refId: string;
}

export interface ChatCitation {
  title: string;
  source: string;
  url?: string;
}

/**
 * WebSocket 스트리밍 청크 (Bedrock streaming → FastAPI WS → FE).
 * 백엔드 ChatService.stream() 의 단위 메시지.
 */
export type ChatStreamChunk =
  | { kind: 'token'; messageId: string; delta: string }
  | { kind: 'inline_tag'; messageId: string; tag: ChatInlineTag }
  | { kind: 'citation'; messageId: string; citation: ChatCitation }
  | { kind: 'done'; messageId: string }
  | { kind: 'error'; messageId: string; error: string };

// ─────────────────────────────────────────────────────────────────────────────
// 7. Generic API Response Wrappers
// ─────────────────────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  ok: true;
  data: T;
  /** 서버 응답 시각 (ISO 8601) */
  servedAt: string;
  /** 캐시 hit 여부 (디버깅/관측용) */
  cache?: 'hit' | 'miss' | 'stale';
}

export interface ApiError {
  ok: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  servedAt: string;
}

export type ApiResult<T> = ApiResponse<T> | ApiError;

/**
 * 페이지네이션 응답.
 * 검색/리스트 API 에서 사용.
 */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
