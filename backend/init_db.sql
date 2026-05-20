-- FoodLens DB 초기화 스크립트
-- DB명: ai-dlc

-- 데이터베이스 생성 (psql에서 실행)
-- CREATE DATABASE "ai-dlc";

-- 아래는 ai-dlc DB에 접속 후 실행

-- ============================================
-- Unit 4 크롤링 데이터 테이블 (참조용)
-- ============================================

CREATE TABLE IF NOT EXISTS food_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    unit VARCHAR(20) NOT NULL,
    season TEXT[],
    calories NUMERIC(8, 2),
    protein NUMERIC(8, 2),
    carbohydrate NUMERIC(8, 2),
    fat NUMERIC(8, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name);
CREATE INDEX IF NOT EXISTS idx_food_items_category ON food_items(category);

CREATE TABLE IF NOT EXISTS price_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES food_items(id),
    date DATE NOT NULL,
    wholesale_price NUMERIC(12, 2),
    retail_price NUMERIC(12, 2),
    unit VARCHAR(20),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_records_date ON price_records(date);
CREATE INDEX IF NOT EXISTS idx_price_records_item_id ON price_records(item_id);

-- ============================================
-- Unit 3 추천 메뉴 테이블 (신규)
-- ============================================

CREATE TABLE IF NOT EXISTS recommend_menu_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL DEFAULT 'lunch',
    menu_name VARCHAR(200) NOT NULL,
    target_servings INTEGER NOT NULL DEFAULT 100,
    budget_per_serving INTEGER NOT NULL DEFAULT 4500,
    total_cost_per_serving NUMERIC(10, 2),
    reasoning TEXT,
    course_type VARCHAR(50) NOT NULL,
    recipe_name VARCHAR(200) NOT NULL,
    description TEXT,
    ingredients JSONB NOT NULL DEFAULT '[]',
    steps JSONB NOT NULL DEFAULT '[]',
    estimated_cost_per_serving NUMERIC(10, 2),
    calories NUMERIC(8, 2),
    protein NUMERIC(8, 2),
    carbohydrate NUMERIC(8, 2),
    fat NUMERIC(8, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommend_menu_list_date ON recommend_menu_list(recommendation_date);
CREATE INDEX IF NOT EXISTS idx_recommend_menu_list_meal ON recommend_menu_list(recommendation_date, meal_type);
