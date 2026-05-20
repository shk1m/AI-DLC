import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


def get_connection():
    """PostgreSQL 연결 생성 (DB: ai-dlc)"""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        cursor_factory=RealDictCursor,
    )


def init_menu_table(conn):
    """recommend_menu_list 테이블 생성 (없으면 생성)"""
    with conn.cursor() as cur:
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
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommend_menu_list_date
            ON recommend_menu_list(recommendation_date);
        """)

    conn.commit()
