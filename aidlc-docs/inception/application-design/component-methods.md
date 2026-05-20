# 컴포넌트 메서드 시그니처 (Component Methods)

> 참고: 상세 비즈니스 로직은 Functional Design (CONSTRUCTION) 단계에서 정의됩니다.

---

## BE-01: PriceService

```python
class PriceService:
    async def get_current_prices(category: str, subcategory: str = None) -> List[PriceItem]
    async def get_price_history(item_id: str, period: str, interval: str) -> PriceTimeSeries
    async def detect_spikes(item_id: str, period: str) -> List[SpikeEvent]
    async def get_price_gap(item_id: str) -> PriceGapInfo
    async def get_category_summary(category: str) -> CategoryPriceSummary
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| get_current_prices | 카테고리, 서브카테고리 | 품목별 현재가 목록 | 대시보드 테이블 데이터 |
| get_price_history | 품목ID, 기간, 간격 | 시계열 가격 데이터 | 차트 렌더링 |
| detect_spikes | 품목ID, 기간 | Spike 이벤트 목록 | 이상치 감지 |
| get_price_gap | 품목ID | 도매/소매 갭 정보 | Gap 분석 |
| get_category_summary | 카테고리 | 카테고리 요약 통계 | 대시보드 요약 |

---

## BE-02: ChatService

```python
class ChatService:
    async def process_message(session_id: str, message: str) -> AsyncGenerator[str, None]
    async def get_chat_history(session_id: str, limit: int = 20) -> List[ChatMessage]
    async def create_session() -> str
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| process_message | 세션ID, 메시지 | 스트리밍 응답 | WebSocket 챗봇 응답 |
| get_chat_history | 세션ID, 제한 | 대화 이력 | 이전 대화 로드 |
| create_session | - | 세션ID | 새 대화 시작 |

---

## BE-03: RecipeService

```python
class RecipeService:
    async def suggest_menu(servings: int, budget: float = None, constraints: dict = None) -> List[MenuSuggestion]
    async def calculate_cost(recipe_id: str, servings: int) -> CostSimulation
    async def compare_menus(recipe_ids: List[str], servings: int) -> MenuComparison
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| suggest_menu | 식수, 예산, 제약조건 | 메뉴 제안 목록 | AI 메뉴 추천 |
| calculate_cost | 레시피ID, 식수 | 원가 시뮬레이션 | 비용 계산 |
| compare_menus | 레시피ID 목록, 식수 | 메뉴 비교 | 옵션 비교 |

---

## BE-04: SubstituteService

```python
class SubstituteService:
    async def find_substitutes(item_id: str, reason: str = None) -> List[SubstituteItem]
    async def calculate_savings(original_id: str, substitute_id: str, servings: int) -> SavingsInfo
    async def suggest_alternative_recipe(original_item_id: str) -> List[AlternativeRecipe]
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| find_substitutes | 식자재ID, 사유 | 대체 식자재 목록 | 온톨로지 기반 추천 |
| calculate_savings | 원래ID, 대체ID, 식수 | 절감 정보 | 절감률 계산 |
| suggest_alternative_recipe | 원래 식자재ID | 대체 레시피 목록 | 레시피 추천 |

---

## BE-05: NewsService

```python
class NewsService:
    async def search_news(keyword: str, date_from: str = None, date_to: str = None) -> List[NewsArticle]
    async def get_news_for_spike(spike_event: SpikeEvent) -> List[NewsArticle]
    async def crawl_government_press() -> List[NewsArticle]
    async def get_trend_keywords(category: str) -> List[TrendKeyword]
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| search_news | 키워드, 기간 | 뉴스 목록 | 뉴스 검색 |
| get_news_for_spike | Spike 이벤트 | 관련 뉴스 | Spike-뉴스 매핑 |
| crawl_government_press | - | 보도자료 목록 | 정부 보도자료 수집 |
| get_trend_keywords | 카테고리 | 트렌드 키워드 | 네이버 데이터랩 |

---

## BE-06: OntologyService

```python
class OntologyService:
    async def get_substitutes(item_id: str) -> List[OntologyRelation]
    async def get_category_tree() -> CategoryTree
    async def get_item_relations(item_id: str, relation_type: str = None) -> List[OntologyRelation]
    async def search_items(query: str, category: str = None) -> List[FoodItem]
```

| 메서드 | 입력 | 출력 | 목적 |
|--------|------|------|------|
| get_substitutes | 식자재ID | 대체 관계 목록 | 대체 식자재 탐색 |
| get_category_tree | - | 분류 체계 트리 | 카테고리 필터 |
| get_item_relations | 식자재ID, 관계유형 | 관계 목록 | 관계 탐색 |
| search_items | 검색어, 카테고리 | 식자재 목록 | 식자재 검색 |

---

## BE-07: LangChainAgent

```python
class LangChainAgent:
    async def run(query: str, session_id: str) -> AsyncGenerator[AgentResponse, None]
    def get_available_tools() -> List[Tool]
```

### Agent Tools (도구 목록)
| 도구명 | 연결 서비스 | 기능 |
|--------|-------------|------|
| price_lookup | PriceService | 현재 시세 조회 |
| price_history | PriceService | 가격 추이 조회 |
| find_substitute | SubstituteService | 대체 식자재 검색 |
| suggest_recipe | RecipeService | 레시피 추천 |
| search_news | NewsService | 뉴스 검색 |
| calculate_cost | RecipeService | 원가 계산 |
| ontology_query | OntologyService | 식자재 관계 조회 |
