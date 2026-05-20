"""
Lambda - recommend_menu_list 데이터를 Neptune에 그래프로 저장

노드:
  - Menu (메뉴명)
  - Cost (1인당 비용)

엣지:
  - Menu --[1인당가격]--> Cost
"""
import json
import logging

import psycopg2
from psycopg2.extras import RealDictCursor
from gremlin_python.driver import client as gremlin_client
from gremlin_python.driver.serializer import GraphSONSerializersV2d0

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 설정
import os

DB_HOST = os.environ.get("DB_HOST", "ai-dlc-db.cwzuko60yxak.us-east-1.rds.amazonaws.com")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "aidlc")
DB_USER = os.environ.get("DB_USER", "dbadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "AiDlc2026Pass!")
NEPTUNE_ENDPOINT = os.environ.get("NEPTUNE_ENDPOINT", "ai-dlc-neptune.cluster-cwzuko60yxak.us-east-1.neptune.amazonaws.com")
NEPTUNE_PORT = int(os.environ.get("NEPTUNE_PORT", "8182"))


def handler(event, context):
    logger.info(f"Lambda 시작: {json.dumps(event, default=str)}")

    conn = None
    gremlin = None
    try:
        # 1. PostgreSQL에서 recommend_menu_list 조회
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            sslmode="require", cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        cur.execute("SELECT id, menu_name, total_cost_per_serving FROM recommend_menu_list")
        menus = cur.fetchall()
        cur.close()
        conn.close()
        conn = None

        if not menus:
            return {"statusCode": 200, "body": json.dumps({"status": "no_data"})}

        # 2. Neptune Gremlin 연결
        neptune_url = f"wss://{NEPTUNE_ENDPOINT}:{NEPTUNE_PORT}/gremlin"
        gremlin = gremlin_client.Client(
            neptune_url, "g",
            message_serializer=GraphSONSerializersV2d0()
        )

        created_nodes = 0
        created_edges = 0

        for menu in menus:
            menu_name = menu["menu_name"]
            cost = float(menu["total_cost_per_serving"]) if menu["total_cost_per_serving"] else 0
            menu_id = str(menu["id"])

            # Menu 노드 생성 (중복 방지)
            gremlin.submit(
                "g.V().has('Menu','menu_id',menu_id).fold()"
                ".coalesce(unfold(), addV('Menu').property('menu_id',menu_id).property('name',name))",
                {"menu_id": menu_id, "name": menu_name}
            ).all().result()
            created_nodes += 1

            # Cost 노드 생성 (비용 값 자체가 노드)
            cost_id = f"cost_{int(cost)}"
            gremlin.submit(
                "g.V().has('Cost','cost_id',cost_id).fold()"
                ".coalesce(unfold(), addV('Cost').property('cost_id',cost_id).property('amount',amount))",
                {"cost_id": cost_id, "amount": cost}
            ).all().result()
            created_nodes += 1

            # Edge: Menu --[1인당가격]--> Cost
            gremlin.submit(
                "g.V().has('Menu','menu_id',menu_id).as('m')"
                ".V().has('Cost','cost_id',cost_id).as('c')"
                ".select('m').coalesce("
                "  outE('1인당가격').where(inV().has('cost_id',cost_id)),"
                "  addE('1인당가격').from('m').to('c').property('amount',amount)"
                ")",
                {"menu_id": menu_id, "cost_id": cost_id, "amount": cost}
            ).all().result()
            created_edges += 1

            logger.info(f"저장 완료: {menu_name} -> {cost}원")

        gremlin.close()
        gremlin = None

        result = {
            "status": "success",
            "created_nodes": created_nodes,
            "created_edges": created_edges,
            "menus_processed": len(menus),
        }
        logger.info(f"Lambda 완료: {result}")
        return {"statusCode": 200, "body": json.dumps(result, ensure_ascii=False)}

    except Exception as e:
        logger.error(f"Lambda 실패: {e}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"status": "error", "message": str(e)})}
    finally:
        if conn:
            conn.close()
        if gremlin:
            gremlin.close()
