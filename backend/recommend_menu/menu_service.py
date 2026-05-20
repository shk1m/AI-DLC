import json
import logging
from datetime import date

import boto3

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 급식 전문 영양사 AI입니다.
제공된 식자재 목록으로 만들 수 있는 영양 균형 잡힌 급식 메뉴를 추천합니다.

규칙:
1. 한 끼 메뉴는 밥, 국/찌개, 주반찬, 부반찬, 김치로 구성합니다.
2. 100식 기준, 1인당 예산 4,500원 이내로 구성합니다.
3. 영양 균형을 고려합니다.
4. 반드시 아래 JSON 형식으로만 응답합니다. 다른 텍스트 없이 JSON만 출력하세요.

응답 JSON 형식:
{
  "menus": [
    {
      "menu_name": "메뉴 세트명 (예: 가을 제철 고등어 정식)",
      "reasoning": "추천 이유 (2~3문장)",
      "total_cost_per_serving": 4200,
      "dishes": [
        {
          "course_type": "밥|국/찌개|주반찬|부반찬|김치",
          "dish_name": "요리명",
          "description": "간단한 설명",
          "estimated_cost": 800,
          "calories": 300,
          "protein": 6,
          "carbohydrate": 65,
          "fat": 2,
          "ingredients": [
            {"name": "재료명", "quantity": "150", "unit": "g", "is_main": true}
          ]
        }
      ]
    }
  ]
}"""


class MenuGenerationService:
    def __init__(self, conn):
        self.conn = conn
        self.bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def generate_daily_menu(self, target_date: date = None) -> dict:
        if target_date is None:
            target_date = date.today()

        logger.info(f"메뉴 생성 시작: {target_date}")

        # 1. 이미 해당 날짜 메뉴 있는지 확인
        if self._menu_exists(target_date):
            return {"status": "skipped", "date": str(target_date), "reason": "already_exists"}

        # 2. food_items 조회
        food_items = self._get_food_items()

        # 3. Bedrock에 메뉴 추천 요청
        menu_data = self._request_menu(food_items)

        # 4. 3개 테이블에 저장
        saved = self._save_menus(menu_data, target_date)

        logger.info(f"메뉴 생성 완료: {target_date}, {saved}개 세트 저장")
        return {"status": "created", "date": str(target_date), "menu_count": saved}

    def _menu_exists(self, target_date: date) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM recommend_menu_list WHERE recommendation_date = %s LIMIT 1",
                (target_date,)
            )
            return cur.fetchone() is not None

    def _get_food_items(self) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, category, subcategory, unit FROM food_items ORDER BY category, name")
            return [dict(row) for row in cur.fetchall()]

    def _request_menu(self, food_items: list[dict]) -> dict:
        food_text = "\n".join(
            f"- {item['name']} ({item['category']}/{item['subcategory']}, 단위: {item['unit']})"
            for item in food_items
        )

        user_prompt = f"""아래 식자재 목록으로 만들 수 있는 점심 급식 메뉴 {settings.menu_count}세트를 추천해주세요.

## 보유 식자재
{food_text}

조건:
- {settings.target_servings}식 기준
- 1인당 예산: {settings.budget_per_serving:,}원 이내
- 각 세트: 밥 + 국/찌개 + 주반찬 + 부반찬 + 김치 (5가지)
- 영양 균형 고려
- 재료는 위 식자재 목록에서만 사용

JSON 형식으로만 응답해주세요."""

        response = self.bedrock.converse(
            modelId=settings.bedrock_model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 4096, "temperature": 0.7},
        )

        raw = response["output"]["message"]["content"][0]["text"]
        return self._parse_response(raw)

    def _parse_response(self, response: str) -> dict:
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"파싱 실패: {e}")
            return {"menus": []}

    def _save_menus(self, menu_data: dict, target_date: date) -> int:
        """3개 테이블에 저장: recommend_menu_list → recommend_set_menu → material"""
        food_item_map = self._get_food_item_map()
        saved_count = 0

        with self.conn.cursor() as cur:
            for menu in menu_data.get("menus", []):
                # 1. recommend_menu_list 저장
                cur.execute("""
                    INSERT INTO recommend_menu_list
                        (recommendation_date, meal_type, menu_name, target_servings,
                         budget_per_serving, total_cost_per_serving, reasoning)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    target_date,
                    "lunch",
                    menu.get("menu_name", "추천 메뉴"),
                    settings.target_servings,
                    settings.budget_per_serving,
                    menu.get("total_cost_per_serving"),
                    menu.get("reasoning", ""),
                ))
                menu_id = cur.fetchone()["id"]

                # 2. recommend_set_menu 저장 (각 요리)
                for dish in menu.get("dishes", []):
                    cur.execute("""
                        INSERT INTO recommend_set_menu
                            (menu_id, course_type, dish_name, description,
                             estimated_cost, calories, protein, carbohydrate, fat)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        menu_id,
                        dish.get("course_type", "기타"),
                        dish.get("dish_name", ""),
                        dish.get("description", ""),
                        dish.get("estimated_cost"),
                        dish.get("calories"),
                        dish.get("protein"),
                        dish.get("carbohydrate"),
                        dish.get("fat"),
                    ))
                    set_menu_id = cur.fetchone()["id"]

                    # 3. material 저장 (각 재료)
                    for ing in dish.get("ingredients", []):
                        ing_name = ing.get("name", "")
                        food_item_id = food_item_map.get(ing_name)

                        cur.execute("""
                            INSERT INTO material
                                (set_menu_id, food_item_id, ingredient_name,
                                 quantity, unit, is_main)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            set_menu_id,
                            food_item_id,
                            ing_name,
                            ing.get("quantity"),
                            ing.get("unit"),
                            ing.get("is_main", False),
                        ))

                saved_count += 1

        self.conn.commit()
        return saved_count

    def _get_food_item_map(self) -> dict:
        """식자재명 → UUID 매핑"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM food_items")
            return {row["name"]: row["id"] for row in cur.fetchall()}
