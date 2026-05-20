"""
AWS Lambda 핸들러 - 일일 메뉴 생성
food_items 데이터를 기반으로 Bedrock이 메뉴를 추천하고 3개 테이블에 저장

테이블 구조:
  - recommend_menu_list: 메뉴 세트 (예: "가을 제철 고등어 정식")
  - recommend_set_menu: 세트 내 개별 요리 (밥, 국, 주반찬, 부반찬, 김치)
  - material: 각 요리에 필요한 재료

트리거: EventBridge (매일 1회) 또는 수동 호출
"""
import json
import logging
from datetime import date

from config import settings
from menu_service import MenuGenerationService
from db import get_connection, init_tables

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda 엔트리포인트"""
    logger.info(f"Lambda 실행 시작: {json.dumps(event, default=str)}")

    target_date_str = event.get("target_date")
    target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()

    conn = None
    try:
        conn = get_connection()
        init_tables(conn)

        service = MenuGenerationService(conn)
        result = service.generate_daily_menu(target_date)

        logger.info(f"Lambda 실행 완료: {result}")
        return {
            "statusCode": 200,
            "body": json.dumps(result, ensure_ascii=False),
        }
    except Exception as e:
        logger.error(f"Lambda 실행 실패: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False),
        }
    finally:
        if conn:
            conn.close()
