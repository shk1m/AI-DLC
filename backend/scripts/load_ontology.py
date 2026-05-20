"""
Ontology loader — Neptune Gremlin (Step 16).

USE_MOCK=true → 로컬 검증 + JSON 덤프만 수행 (Neptune 연결 없음).
실 Neptune 연결 시: NEPTUNE_ENDPOINT 환경변수 필요.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("load_ontology")

DATA_DIR = ROOT / "data" / "ontology"


async def load_mock(nodes_path: Path, edges_path: Path) -> dict:
    """mock 모드: 데이터 유효성 검증 후 통계 반환."""
    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    edges = json.loads(edges_path.read_text(encoding="utf-8"))

    node_ids = {n["id"] for n in nodes}
    valid_edges = [e for e in edges if e["from"] in node_ids and e["to"] in node_ids]
    invalid = len(edges) - len(valid_edges)

    logger.info(
        "ontology_mock_validated",
        nodes=len(nodes), edges=len(edges),
        valid_edges=len(valid_edges), invalid_edges=invalid,
    )

    # 요약 JSON 출력
    output_path = ROOT / "data" / "ontology" / "load_summary.json"
    summary = {
        "node_count": len(nodes),
        "edge_count": len(valid_edges),
        "invalid_edges": invalid,
        "categories": list({n["category"] for n in nodes}),
        "relations": list({e["relation"] for e in edges}),
    }
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("ontology_summary_written", path=str(output_path))
    return summary


async def load_neptune(nodes: list, edges: list) -> dict:
    """실제 Neptune 적재 (gremlin-python)."""
    try:
        from gremlin_python.driver import client as gremlin_client  # noqa: PLC0415
    except ImportError:
        logger.error("gremlin_not_installed", hint="pip install gremlinpython")
        return {}

    settings = get_settings()
    endpoint = settings.neptune_endpoint
    if not endpoint:
        raise ValueError("NEPTUNE_ENDPOINT not configured")

    gc = gremlin_client.Client(endpoint, "g")
    n_nodes = 0
    n_edges = 0
    try:
        for node in nodes:
            q = (
                f"g.addV('FoodItem')"
                f".property('item_id', '{node['id']}')"
                f".property('name', '{node['name']}')"
                f".property('category', '{node['category']}')"
                f".property('unit', '{node.get('unit', '')}')"
            )
            gc.submit(q).all().result()
            n_nodes += 1

        for edge in edges:
            q = (
                f"g.V().has('item_id', '{edge['from']}')"
                f".addE('{edge['relation']}')"
                f".to(g.V().has('item_id', '{edge['to']}'))"
                f".property('similarity', {edge.get('similarity', 0.5)})"
            )
            gc.submit(q).all().result()
            n_edges += 1
    finally:
        gc.close()

    logger.info("neptune_load_done", nodes=n_nodes, edges=n_edges)
    return {"nodes": n_nodes, "edges": n_edges}


async def main() -> None:
    nodes_path = DATA_DIR / "food_nodes.json"
    edges_path = DATA_DIR / "food_edges.json"

    if not nodes_path.exists() or not edges_path.exists():
        logger.error("ontology_data_missing", dir=str(DATA_DIR))
        return

    settings = get_settings()
    if settings.is_mock or not settings.neptune_endpoint:
        logger.info("ontology_mock_mode")
        result = await load_mock(nodes_path, edges_path)
    else:
        nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
        edges = json.loads(edges_path.read_text(encoding="utf-8"))
        result = await load_neptune(nodes, edges)

    print(f"\n✅ Ontology load result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
