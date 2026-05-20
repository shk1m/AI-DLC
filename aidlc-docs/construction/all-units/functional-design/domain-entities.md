# 도메인 엔티티 (Domain Entities)

---

## 1. 식자재 도메인

### FoodItem (식자재)
```
FoodItem {
  id: UUID
  name: string                    # 품목명 (예: "고등어", "배추")
  category: CategoryEnum          # 대분류 (농산물, 수산물, 축산물, 가공식품)
  subcategory: string             # 소분류 (엽경채류, 근채류 등)
  unit: string                    # 단위 (kg, 마리, 박스)
  season: string[]                # 제철 시즌 (["3월","4월","5월"])
  nutrition: NutritionInfo        # 영양 정보
  created_at: datetime
  updated_at: datetime
}
```

### CategoryEnum
```
CategoryEnum {
  GRAIN       = "구황작물"
  SEAFOOD     = "수산물"
  VEGETABLE   = "채소류"
  FRUIT       = "과일류"
  LIVESTOCK   = "축산류"
  PROCESSED   = "가공식품"
}
```

### NutritionInfo (영양 정보)
```
NutritionInfo {
  calories: float       # kcal/100g
  protein: float        # g/100g
  carbohydrate: float   # g/100g
  fat: float            # g/100g
  fiber: float          # g/100g
}
```

---

## 2. 가격 도메인

### PriceRecord (시세 기록)
```
PriceRecord {
  id: UUID
  item_id: UUID (FK → FoodItem)
  date: date
  wholesale_price: float          # 도매가
  retail_price: float             # 소매가
  price_gap: float                # 갭 (소매-도매)/도매 * 100
  source: DataSourceEnum          # 데이터 출처
  created_at: datetime
}
```

### SpikeEvent (가격 이상치 이벤트)
```
SpikeEvent {
  id: UUID
  item_id: UUID (FK → FoodItem)
  date: date
  spike_type: SpikeTypeEnum       # 급등/급락
  magnitude: float                # 변동 크기 (%)
  baseline_price: float           # 기준 가격
  spike_price: float              # 이상치 가격
  news_articles: NewsArticle[]    # 매핑된 뉴스
  detected_at: datetime
}
```

### SpikeTypeEnum
```
SpikeTypeEnum {
  SURGE = "급등"
  DROP  = "급락"
}
```

### DataSourceEnum
```
DataSourceEnum {
  KAMIS       = "KAMIS"
  PUBLIC_DATA = "공공데이터포털"
  EKAPEPIA    = "축산유통정보"
  SFISH       = "수산물유통정보"
}
```

---

## 3. 뉴스 도메인

### NewsArticle (뉴스 기사)
```
NewsArticle {
  id: UUID
  title: string                   # 헤드라인
  url: string                     # 원문 URL
  source: NewsSourceEnum          # 출처
  published_at: datetime          # 발행일
  keywords: string[]              # 추출 키워드
  related_items: UUID[]           # 관련 식자재 ID
  summary: string                 # 요약 (AI 생성)
  created_at: datetime
}
```

### NewsSourceEnum
```
NewsSourceEnum {
  NAVER       = "네이버뉴스"
  MAFRA       = "농림축산식품부"
  MOF         = "해양수산부"
}
```

---

## 4. 레시피 도메인

### Recipe (레시피)
```
Recipe {
  id: UUID
  name: string                    # 레시피명
  description: string             # 설명
  category: string                # 분류 (한식, 양식 등)
  servings: int                   # 기본 인분
  ingredients: RecipeIngredient[] # 재료 목록
  steps: string[]                 # 조리 순서
  nutrition_per_serving: NutritionInfo
  created_at: datetime
}
```

### RecipeIngredient (레시피 재료)
```
RecipeIngredient {
  item_id: UUID (FK → FoodItem)
  quantity: float                 # 수량
  unit: string                    # 단위
  is_main: boolean                # 주재료 여부
  substitutable: boolean          # 대체 가능 여부
}
```

---

## 5. 시뮬레이션 도메인

### CostSimulation (원가 시뮬레이션)
```
CostSimulation {
  id: UUID
  recipe_id: UUID (FK → Recipe)
  servings: int                   # 식수
  total_cost: float               # 총 원가
  cost_per_serving: float         # 1식 단가
  ingredient_costs: IngredientCost[]
  simulated_at: datetime
}
```

### IngredientCost (재료별 원가)
```
IngredientCost {
  item_id: UUID (FK → FoodItem)
  item_name: string
  quantity_needed: float          # 필요 수량
  unit_price: float               # 단가
  total_price: float              # 소계
  price_source: DataSourceEnum
}
```

---

## 6. 온톨로지 도메인 (Neptune Graph)

### FoodNode (식자재 노드)
```
FoodNode {
  id: string                      # Neptune vertex ID
  item_id: UUID                   # RDB FoodItem 참조
  name: string
  category: CategoryEnum
  properties: {
    nutrition: NutritionInfo
    season: string[]
    cooking_methods: string[]     # 조리법 (볶음, 구이, 찜 등)
  }
}
```

### 관계 유형 (Edge Types)
```
SUBSTITUTABLE {                   # 대체 가능
  similarity_score: float         # 유사도 (0~1)
  reason: string                  # 대체 사유
}

SAME_CATEGORY {                   # 같은 분류
  category: string
}

NUTRITION_SIMILAR {               # 영양 유사
  similarity_score: float
}

COOKING_COMPATIBLE {              # 조리 호환
  compatible_methods: string[]
}
```

---

## 7. 채팅 도메인

### ChatSession (채팅 세션)
```
ChatSession {
  id: UUID
  user_role: UserRoleEnum         # 사용자 역할
  created_at: datetime
  last_active: datetime
  messages: ChatMessage[]
}
```

### ChatMessage (채팅 메시지)
```
ChatMessage {
  id: UUID
  session_id: UUID (FK → ChatSession)
  role: MessageRoleEnum           # user/assistant
  content: string
  sources: string[]               # 참조 출처
  confidence: float               # 신뢰도 (0~1)
  tools_used: string[]            # 사용된 Agent 도구
  created_at: datetime
}
```

### UserRoleEnum
```
UserRoleEnum {
  NUTRITIONIST = "영양사"
  MD           = "MD"
  BUYER        = "바이어"
}
```
