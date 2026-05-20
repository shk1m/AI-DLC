# 비즈니스 로직 모델 (Business Logic Model)

---

## 1. 가격 이상치(Spike) 감지 알고리즘

### 알고리즘: Z-Score 기반 이상치 감지
```
입력: item_id, period (기간)
출력: SpikeEvent[]

1. 해당 품목의 기간 내 가격 시계열 조회
2. 이동 평균(MA) 계산 (window = 7일)
3. 이동 표준편차(MSD) 계산 (window = 7일)
4. 각 데이터 포인트에 대해:
   z_score = (price - MA) / MSD
   IF |z_score| > 2.0:
     → SpikeEvent 생성 (급등: z > 2, 급락: z < -2)
5. Spike 이벤트에 대해 뉴스 매핑 실행
```

### 뉴스 매핑 로직
```
입력: SpikeEvent
출력: NewsArticle[]

1. Spike 발생일 기준 ±3일 범위 설정
2. 해당 품목 키워드로 뉴스 검색
3. 관련도 점수 계산 (키워드 매칭 + 시간 근접도)
4. 상위 3개 뉴스 매핑
```

---

## 2. 대체 식자재 추천 로직

### 알고리즘: 온톨로지 기반 다중 기준 추천
```
입력: item_id, reason (대체 사유)
출력: SubstituteItem[] (정렬됨)

1. Neptune에서 SUBSTITUTABLE 관계 탐색 (depth=1)
2. 추가로 NUTRITION_SIMILAR + COOKING_COMPATIBLE 관계 탐색
3. 후보 식자재 목록 생성
4. 각 후보에 대해 점수 계산:
   score = (similarity_score * 0.3)
         + (price_advantage * 0.4)
         + (availability * 0.2)
         + (nutrition_match * 0.1)
5. 점수 기준 내림차순 정렬
6. 상위 5개 반환 (가격 정보 포함)
```

### 가격 우위 계산
```
price_advantage = (original_price - substitute_price) / original_price
IF price_advantage < 0: 가격 불리 (점수 감점)
```

---

## 3. 원가 시뮬레이션 로직

### 알고리즘: 식수 기반 원가 계산
```
입력: recipe_id, servings, budget (선택)
출력: CostSimulation

1. 레시피의 재료 목록 조회
2. 각 재료의 현재 시세 조회 (PriceService)
3. 식수에 따른 필요 수량 계산:
   quantity_needed = recipe_quantity * (servings / recipe_base_servings)
4. 재료별 원가 계산:
   ingredient_cost = quantity_needed * unit_price
5. 총 원가 합산
6. 1식 단가 계산: total_cost / servings
7. IF budget 제공:
   budget_status = total_cost <= budget ? "예산 내" : "예산 초과"
   over_amount = max(0, total_cost - budget)
```

### 메뉴 추천 로직 (AI 기반)
```
입력: servings, budget, constraints (영양 제약 등)
출력: MenuSuggestion[]

1. 현재 시세 기준 가성비 높은 식자재 목록 생성
2. Bedrock Claude에 프롬프트 전송:
   - 컨텍스트: 현재 시세 데이터, 제철 식자재, 예산 제약
   - 요청: 영양 균형 + 예산 내 메뉴 조합 추천
3. AI 응답 파싱 → MenuSuggestion 구조화
4. 각 추천 메뉴에 대해 원가 시뮬레이션 실행
5. 예산 초과 메뉴 필터링
```

---

## 4. LangChain Agent 로직

### Agent 실행 흐름
```
입력: user_message, session_id
출력: AgentResponse (스트리밍)

1. 대화 이력 로드 (최근 10개 메시지)
2. 사용자 역할 확인 (영양사/MD/바이어)
3. Agent 실행:
   a. 질문 분석 (의도 파악)
   b. 필요한 도구 선택
   c. 도구 실행 (병렬 가능)
   d. 결과 종합
   e. 응답 생성 (컨설턴트 스타일)
4. 응답에 출처 정보 첨부
5. 신뢰도 점수 계산
6. 스트리밍 전송
```

### Agent 도구 선택 기준
| 질문 유형 | 선택 도구 | 예시 |
|-----------|-----------|------|
| 현재 가격 | price_lookup | "고등어 현재 시세는?" |
| 가격 추이 | price_history | "배추 3개월 추이" |
| 대체 식자재 | find_substitute | "상추 대신 뭘 쓸까?" |
| 레시피 추천 | suggest_recipe | "1000식 점심 메뉴 추천" |
| 뉴스/이슈 | search_news | "양파 가격 상승 원인" |
| 원가 계산 | calculate_cost | "이 레시피 500식 원가" |
| 관계 탐색 | ontology_query | "고등어와 비슷한 생선" |

### 응답 구조 (컨설턴트 스타일)
```
[분석]
- 현재 상황 요약 (데이터 기반)

[추천]
- 구체적 행동 제안 (1~3개)

[근거]
- 데이터 출처 및 수치
- 관련 뉴스/이벤트 (있을 경우)

[참고]
- 신뢰도: XX%
- 데이터 기준일: YYYY-MM-DD
- 출처: [API명]
```

---

## 5. 뉴스 크롤링 및 분류 로직

### 크롤링 스케줄
```
- 네이버 뉴스 API: 1시간마다 (키워드별)
- 정부 보도자료: 6시간마다
- 키워드 목록: 주요 식자재명 + "가격", "시세", "흉작", "풍작", "수입"
```

### 뉴스 분류 로직
```
입력: NewsArticle (원본)
출력: NewsArticle (분류 완료)

1. 제목 + 본문에서 식자재 키워드 추출
2. 키워드 매칭으로 관련 FoodItem 식별
3. 이벤트 유형 분류:
   - 가격 변동 (급등/급락)
   - 수급 이슈 (흉작/풍작/수입)
   - 정책 변경 (관세, 규제)
   - 자연재해 (태풍, 홍수, 가뭄)
4. 벡터 임베딩 생성 → Bedrock KB 적재
5. 메타데이터 → PostgreSQL 저장
```

---

## 6. 분류 체계 관리 로직

### 카테고리 트리 구조
```
ROOT
├── 농산물
│   ├── 엽경채류 (배추, 상추, 시금치...)
│   ├── 근채류 (무, 당근, 감자...)
│   ├── 과채류 (고추, 토마토, 오이...)
│   ├── 양념류 (마늘, 양파, 생강...)
│   └── 구황작물 (고구마, 감자...)
├── 수산물
│   ├── 어류 (고등어, 삼치, 갈치...)
│   ├── 갑각류 (새우, 게...)
│   ├── 패류 (전복, 굴, 조개...)
│   └── 해조류 (미역, 다시마...)
├── 축산물
│   ├── 소고기 (한우, 수입육...)
│   ├── 돼지고기 (삼겹살, 목살...)
│   ├── 닭고기 (통닭, 닭가슴살, 윙봉...)
│   └── 계란/유제품
├── 과일류
│   ├── 국산과일 (사과, 배, 감...)
│   └── 수입과일 (바나나, 오렌지...)
└── 가공식품
    ├── 조미료 (간장, 된장, 고추장...)
    ├── 유지류 (식용유, 참기름...)
    └── 기타 (밀가루, 설탕...)
```
