import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class PriceService:
    """크롤링 DB에서 시세 데이터 조회"""

    def __init__(self, conn):
        self.conn = conn

    def get_latest_prices(self, categories: list[str] = None, limit: int = 80) -> list[dict]:
        """최근 7일 시세 데이터 조회 (Unit 4가 적재한 데이터)"""
        week_ago = date.today() - timedelta(days=7)

        query = """
            SELECT
                fi.name,
                fi.category,
                fi.subcategory,
                fi.unit,
                pr.wholesale_price,
                pr.retail_price,
                pr.date,
                pr.source
            FROM price_records pr
            JOIN food_items fi ON fi.id = pr.item_id
            WHERE pr.date >= %s
        """
        params = [week_ago]

        if categories:
            query += " AND fi.category = ANY(%s)"
            params.append(categories)

        query += " ORDER BY pr.date DESC LIMIT %s"
        params.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        logger.info(f"시세 데이터 조회: {len(rows)}건")
        return [dict(row) for row in rows]

    def format_prices_for_prompt(self, prices: list[dict]) -> str:
        """시세 데이터를 Bedrock 프롬프트용 텍스트로 변환"""
        if not prices:
            return "현재 시세 데이터가 없습니다. 일반적인 제철 식자재 기준으로 메뉴를 추천해주세요."

        lines = ["## 현재 농수산물 시세 (최근 7일 기준)\n"]
        seen = set()

        for item in prices:
            key = item["name"]
            if key in seen:
                continue
            seen.add(key)

            price_info = f"- {item['name']} ({item['category']}): "
            if item.get("retail_price"):
                price_info += f"소매가 {item['retail_price']:,.0f}원/{item.get('unit', 'kg')}"
            if item.get("wholesale_price"):
                price_info += f", 도매가 {item['wholesale_price']:,.0f}원"
            price_info += f" (기준일: {item['date']})"
            lines.append(price_info)

        return "\n".join(lines)
