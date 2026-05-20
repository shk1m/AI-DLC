import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings


def get_connection():
    """PostgreSQL 연결"""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        sslmode="require",
        cursor_factory=RealDictCursor,
    )


def init_tables(conn):
    """테이블 생성 (없으면)"""
    with conn.cursor() as cur:
        # recommend_menu_list (메뉴 세트 헤더)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommend_menu_list (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                recommendation_date DATE NOT NULL,
                meal_type VARCHAR(20) NOT NULL DEFAULT 'lunch',
                menu_name VARCHAR(200) NOT NULL,
                target_servings INTEGER NOT NULL DEFAULT 100,
                budget_per_serving INTEGER NOT NULL DEFAULT 4500,
                total_cost_per_serving NUMERIC(10, 2),
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(recommendation_date, meal_type, menu_name)
            );
        """)

        # recommend_set_menu (세트 내 개별 요리)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommend_set_menu (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                menu_id UUID NOT NULL REFERENCES recommend_menu_list(id) ON DELETE CASCADE,
                course_type VARCHAR(50) NOT NULL,
                dish_name VARCHAR(200) NOT NULL,
                description TEXT,
                estimated_cost NUMERIC(10, 2),
                calories NUMERIC(8, 2),
                protein NUMERIC(8, 2),
                carbohydrate NUMERIC(8, 2),
                fat NUMERIC(8, 2),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # material (각 요리의 재료)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS material (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                set_menu_id UUID NOT NULL REFERENCES recommend_set_menu(id) ON DELETE CASCADE,
                food_item_id UUID REFERENCES food_items(id),
                ingredient_name VARCHAR(100) NOT NULL,
                quantity VARCHAR(50),
                unit VARCHAR(20),
                is_main BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_recommend_menu_list_date ON recommend_menu_list(recommendation_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recommend_set_menu_menu_id ON recommend_set_menu(menu_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_material_set_menu_id ON material(set_menu_id);")

    conn.commit()
