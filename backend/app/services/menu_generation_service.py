import json
import logging
from datetime import date

from app.services.bedrock_client import bedrock_client
from app.services.price_service import PriceService
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 급식 전문 영양사 AI입니다.
현재 농수산물 시세 데이터를 기반으로 영양 균형이 잡히고 비용 효율적인 급식 메뉴를 추천합니다.

규칙:
1. 현재 시세가 저렴한 제철 식자재를 우선 활용합니다.
2. 한 끼 메뉴는 밥, 국/찌개, 주반찬, 부반찬, 김치로 구성합니다.
3. 영양 균형을 고려합니다 (단백질, 탄수화물, 지방, 식이섬유).
4. 1인당 예산 이내로 구성합니다.
5. 반드시 아래 JSON 형식으로만 응답합니다. 다른 텍스트 없이 JSON만 출력하세요.

응답 JSON 형식:
{
  "menu_name": "오늘의 추천 메뉴 (예: 가을 제철 고등어 정식)",
  "reasoning": "추천 이유 (시세 기반 설명, 2~3문장)",
  "total_cost_per_serving": 4200,
  "items": [
    {
      "course_type": "밥|국/찌개|주반찬|부반찬|김치",
      "recipe_name": "레시피명",
      "description": "간단한 설명",
      "ingredients": [
        {"name": "재료명", "quantity": "100g", "is_main": true}
      ],
      "steps": ["조리 단계1", "조리 단계2"],
      "estimated_cost_per_serving": 1500,
      "calories": 350,
      "protein": 20,
      "carbohydrate": 40,
      "fat": 10
    }
  ]
}"""


class MenuGenerationService:
    """Bedrock 기반 일일 메뉴 생성 서비스 (Lambda용)"""

    def __init__(self, conn):
        self.conn = conn
        self.price_service = PriceService(conn)

    def generate_daily_menu(self, target_date: date = None) -> dict:
        """메뉴 생성 → recommend_menu_list 테이블에 저장"""
        if target_date is None:
            target_date = date.today()

        logger.info(f"메뉴 생성 시작: {target_date}")

        # 1. 이미 해당 날짜 메뉴가 있는지 확인
        if self._menu_exists(target_date):
            logger.info(f"이미 {target_date} 메뉴가 존재합니다. 스킵.")
            return {"status": "skipped", "date": str(target_date), "reason": "already_exists"}

        # 2. 크롤링 DB에서 시세 데이터 조회
        prices = self.price_service.get_latest_prices(
            categories=["수산물", "채소류", "축산류", "과일류"]
        )
        price_context = self.price_service.format_prices_for_prompt(prices)

        # 3. Bedrock에 메뉴 추천 요청
        menu_data = self._request_menu(price_context)

        # 4. recommend_menu_list 테이블에 저장
        saved_count = self._save_menu(menu_data, target_date)

        logger.info(f"메뉴 생성 완료: {target_date}, {saved_count}건 저장")
        return {
            "status": "created",
            "date": str(target_date),
            "menu_name": menu_data.get("menu_name"),
            "item_count": saved_count,
        }

    def _menu_exists(self, target_date: date) -> bool:
        """해당 날짜에 이미 메뉴가 있는지 확인"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM recommend_menu_list WHERE recommendation_date = %s LIMIT 1",
                (target_date,)
            )
            return cur.fetchone() is not None

    def _request_menu(self, price_context: str) -> dict:
        """Bedrock Claude에 메뉴 추천 요청"""
        user_prompt = f"""아래 현재 시세 데이터를 참고하여 오늘의 급식 메뉴를 추천해주세요.

{price_context}

조건:
- {settings.target_servings}식 기준 점심 메뉴
- 1인당 예산: {settings.budget_per_serving:,}원 이내
- 구성: 밥 + 국/찌개 + 주반찬 + 부반찬 + 김치 (총 5가지)
- 현재 시세가 저렴한 식자재를 우선 활용
- 영양 균형 고려

JSON 형식으로만 응답해주세요."""

        response = bedrock_client.invoke(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
            temperature=0.7,
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """Bedrock 응답 JSON 파싱"""
        try:
            # ```json ... ``` 블록 처리
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)
            logger.info(f"메뉴 파싱 성공: {data.get('menu_name')}")
            return data
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"메뉴 응답 파싱 실패: {e}")
            return self._fallback_menu()

    def _fallback_menu(self) -> dict:
        """파싱 실패 시 기본 메뉴"""
        return {
            "menu_name": "기본 추천 메뉴",
            "reasoning": "AI 응답 파싱 실패로 기본 메뉴를 제공합니다.",
            "total_cost_per_serving": 4000,
            "items": [
                {
                    "course_type": "밥",
                    "recipe_name": "잡곡밥",
                    "description": "영양 잡곡밥",
                    "ingredients": [{"name": "쌀", "quantity": "150g", "is_main": True}],
                    "steps": ["쌀과 잡곡을 씻어 30분 불린다", "밥솥에 넣고 취사한다"],
                    "estimated_cost_per_serving": 800,
                    "calories": 300,
                    "protein": 6,
                    "carbohydrate": 65,
                    "fat": 2,
                }
            ],
        }

    def _save_menu(self, menu_data: dict, target_date: date) -> int:
        """추천 메뉴를 recommend_menu_list 테이블에 저장"""
        menu_name = menu_data.get("menu_name", "추천 메뉴")
        reasoning = menu_data.get("reasoning", "")
        total_cost = menu_data.get("total_cost_per_serving")
        items = menu_data.get("items", [])

        with self.conn.cursor() as cur:
            for item in items:
                cur.execute(
                    """
                    INSERT INTO recommend_menu_list
                        (recommendation_date, meal_type, menu_name, target_servings,
                         budget_per_serving, total_cost_per_serving, reasoning,
                         course_type, recipe_name, description,
                         ingredients, steps, estimated_cost_per_serving,
                         calories, protein, carbohydrate, fat)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        target_date,
                        "lunch",
                        menu_name,
                        settings.target_servings,
                        settings.budget_per_serving,
                        total_cost,
                        reasoning,
                        item.get("course_type", "기타"),
                        item.get("recipe_name", ""),
                        item.get("description", ""),
                        json.dumps(item.get("ingredients", []), ensure_ascii=False),
                        json.dumps(item.get("steps", []), ensure_ascii=False),
                        item.get("estimated_cost_per_serving"),
                        item.get("calories"),
                        item.get("protein"),
                        item.get("carbohydrate"),
                        item.get("fat"),
                    ),
                )

        self.conn.commit()
        return len(items)
