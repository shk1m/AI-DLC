"""
AWS Lambda 핸들러 - 일일 메뉴 생성
EventBridge 스케줄러에 의해 매일 1회 트리거됨

트리거: EventBridge Rule (cron: 0 6 * * ? *)
입력: 크롤링 DB (PostgreSQL) - Unit 4가 적재한 농수산물 시세 데이터
출력: recommended_menus / recommended_menu_items 테이블에 저장
"""
import json
import logging
from datetime import date

from app.database import get_connection, init_menu_table
from app.services.menu_generation_service import MenuGenerationService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda 엔트리포인트"""
    logger.info(f"Lambda 실행 시작: event={json.dumps(event, default=str)}")

    # 날짜 지정 가능 (테스트용), 없으면 오늘
    target_date_str = event.get("target_date")
    target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()

    conn = None
    try:
        # DB 연결
        conn = get_connection()

        # recommend_menu_list 테이블 생성 (없으면)
        init_menu_table(conn)

        # 메뉴 생성 실행
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
