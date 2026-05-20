# FoodLens - 일일 메뉴 생성 Lambda (Unit 3)

농수산물 시세 데이터를 기반으로 Bedrock Claude가 급식 메뉴를 추천하고 DB에 저장하는 Lambda 함수입니다.

## 아키텍처

```
EventBridge (매일 06:00 UTC)
        ↓ 트리거
Lambda (menu-generation)
        ↓ 조회
PostgreSQL (price_records, food_items) ← Unit 4 크롤링 적재
        ↓ 프롬프트
Amazon Bedrock (Claude 3.5 Sonnet)
        ↓ 저장
PostgreSQL (recommended_menus, recommended_menu_items) ← 신규 테이블
```

## DB 테이블

### 읽기 (Unit 4가 관리)
- `food_items` - 식자재 마스터
- `price_records` - 시세 기록

### 쓰기 (이 Lambda가 관리)
- `recommended_menus` - 일일 추천 메뉴
- `recommended_menu_items` - 메뉴별 요리 상세

## 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
export DB_HOST=localhost
export DB_NAME=foodlens
export DB_USER=admin
export DB_PASSWORD=password
export AWS_REGION=us-east-1

# 3. 실행
python test_local.py
```

## 배포

```bash
# SAM CLI 필요
chmod +x deploy.sh

export DB_HOST=your-rds-endpoint
export DB_USER=your-user
export DB_PASSWORD=your-password

./deploy.sh
```

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| DB_HOST | PostgreSQL 호스트 | localhost |
| DB_PORT | PostgreSQL 포트 | 5432 |
| DB_NAME | 데이터베이스명 | foodlens |
| DB_USER | DB 사용자 | admin |
| DB_PASSWORD | DB 비밀번호 | - |
| AWS_REGION | AWS 리전 | us-east-1 |
| BEDROCK_MODEL_ID | Bedrock 모델 ID | anthropic.claude-3-5-sonnet-20241022-v2:0 |
| TARGET_SERVINGS | 목표 식수 | 100 |
| BUDGET_PER_SERVING | 1인당 예산(원) | 4500 |

## 수동 실행 (AWS CLI)

```bash
# 오늘 날짜로 실행
aws lambda invoke --function-name foodlens-menu-generation \
  --payload '{}' response.json

# 특정 날짜로 실행
aws lambda invoke --function-name foodlens-menu-generation \
  --payload '{"target_date": "2026-05-21"}' response.json
```
