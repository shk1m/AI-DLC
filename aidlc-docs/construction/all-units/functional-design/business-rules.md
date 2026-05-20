# 비즈니스 규칙 (Business Rules)

---

## BR-01: 가격 데이터 유효성

| 규칙 ID | 규칙 | 조건 |
|---------|------|------|
| BR-01-1 | 도매가는 0보다 커야 한다 | wholesale_price > 0 |
| BR-01-2 | 소매가는 도매가보다 크거나 같아야 한다 | retail_price >= wholesale_price |
| BR-01-3 | 가격 데이터는 30일 이내여야 유효하다 | date >= today - 30days |
| BR-01-4 | 동일 품목/날짜에 중복 가격 불가 | UNIQUE(item_id, date, source) |

---

## BR-02: Spike 감지 규칙

| 규칙 ID | 규칙 | 임계값 |
|---------|------|--------|
| BR-02-1 | Z-Score 절대값 2.0 이상이면 Spike | \|z_score\| >= 2.0 |
| BR-02-2 | 최소 7일 이상의 데이터가 있어야 감지 가능 | data_points >= 7 |
| BR-02-3 | 급등: z_score > 2.0 | positive spike |
| BR-02-4 | 급락: z_score < -2.0 | negative spike |
| BR-02-5 | 연속 Spike는 하나로 병합 (3일 이내) | merge_window = 3days |

---

## BR-03: 대체 식자재 추천 규칙

| 규칙 ID | 규칙 | 조건 |
|---------|------|------|
| BR-03-1 | 온톨로지에 관계가 있는 식자재만 추천 | has_relation = true |
| BR-03-2 | 대체 식자재의 현재 가격이 원래보다 비싸면 경고 표시 | substitute_price > original_price |
| BR-03-3 | 알레르기 유발 식품은 명시적 경고 | allergen_warning = true |
| BR-03-4 | 최대 5개까지 추천 | max_results = 5 |
| BR-03-5 | 유사도 점수 0.3 미만은 추천하지 않음 | similarity >= 0.3 |

---

## BR-04: 원가 시뮬레이션 규칙

| 규칙 ID | 규칙 | 조건 |
|---------|------|------|
| BR-04-1 | 식수는 1 이상이어야 한다 | servings >= 1 |
| BR-04-2 | 식수 최대 100,000식 | servings <= 100000 |
| BR-04-3 | 예산은 0보다 커야 한다 (입력 시) | budget > 0 |
| BR-04-4 | 가격 데이터 없는 재료는 "가격 미확인" 표시 | price_unavailable flag |
| BR-04-5 | 대량 구매 할인율 적용 (1000식 이상: 5%, 10000식 이상: 10%) | bulk_discount |

---

## BR-05: 챗봇 응답 규칙

| 규칙 ID | 규칙 | 조건 |
|---------|------|------|
| BR-05-1 | 모든 응답에 데이터 출처 명시 | source_required = true |
| BR-05-2 | 신뢰도 0.7 미만이면 "확인 필요" 경고 | confidence < 0.7 |
| BR-05-3 | 데이터 없는 품목 질문 시 "해당 품목 데이터 없음" 응답 | no_data_response |
| BR-05-4 | 응답 최대 길이 2000자 | max_length = 2000 |
| BR-05-5 | 컨설턴트 스타일 구조 필수 (분석→추천→근거) | response_format |
| BR-05-6 | 식자재/가격 외 질문은 범위 밖 안내 | out_of_scope |

---

## BR-06: 뉴스 크롤링 규칙

| 규칙 ID | 규칙 | 조건 |
|---------|------|------|
| BR-06-1 | 중복 뉴스 저장 금지 (URL 기준) | UNIQUE(url) |
| BR-06-2 | 7일 이상 된 뉴스는 Spike 매핑에서 제외 | age <= 7days |
| BR-06-3 | 식자재 키워드 1개 이상 포함된 뉴스만 저장 | keyword_count >= 1 |
| BR-06-4 | 크롤링 실패 시 3회 재시도 후 스킵 | max_retry = 3 |
| BR-06-5 | API 실패 시 캐시된 데이터로 Fallback | fallback_enabled = true |

---

## BR-07: 데이터 캐싱 규칙

| 규칙 ID | 규칙 | TTL |
|---------|------|-----|
| BR-07-1 | 시세 데이터 캐시 | 1시간 |
| BR-07-2 | 뉴스 데이터 캐시 | 30분 |
| BR-07-3 | 온톨로지 데이터 캐시 | 24시간 |
| BR-07-4 | 카테고리 트리 캐시 | 24시간 |
| BR-07-5 | 검색어 트렌드 캐시 | 6시간 |

---

## BR-08: 입력 검증 규칙 (SECURITY-05 준수)

| 규칙 ID | 대상 | 검증 |
|---------|------|------|
| BR-08-1 | item_id | UUID 형식 검증 |
| BR-08-2 | category | CategoryEnum 값만 허용 |
| BR-08-3 | period | "1w", "1m", "3m", "6m", "1y" 만 허용 |
| BR-08-4 | servings | 정수, 1~100000 범위 |
| BR-08-5 | budget | 양수 실수, 최대 1억 |
| BR-08-6 | message (챗봇) | 최대 1000자, HTML 태그 제거 |
| BR-08-7 | keyword (검색) | 최대 50자, 특수문자 이스케이프 |
