"""
Demo data seeding script (Unit 4 - Step 15).

사용법:
    python -m backend.scripts.seed_demo_data [--dry-run] [--reset]

기능:
    1. data/ontology/food_nodes.json → 시연용 food_items 캐시
    2. data/news/samples/*.json → S3(mock) 업로드
    3. data/sample/*.json 존재 확인
    4. 캐시 워밍 (1주일치 가상 시세 데이터)

실제 DB 연결(PostgreSQL)은 Unit 2(alembic migrate 후)와 합의 시 추가.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.adapters.s3_client import build_s3_client
from app.core.cache_manager import TTL_NEWS, TTL_ONTOLOGY, TTL_PRICES, get_cache_manager, reset_cache_manager
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("seed_demo_data")


# ---------------------------------------------------------------------------
# 1. Load ontology nodes into cache
# ---------------------------------------------------------------------------
async def seed_ontology_cache(dry_run: bool = False) -> int:
    nodes_path = ROOT / "data" / "ontology" / "food_nodes.json"
    if not nodes_path.exists():
        logger.error("seed_missing_file", path=str(nodes_path))
        return 0

    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    if dry_run:
        logger.info("seed_dry_run", stage="ontology", count=len(nodes))
        return len(nodes)

    cache = get_cache_manager()
    for node in nodes:
        await cache.set(f"ontology:node:{node['id']}", node, ttl=TTL_ONTOLOGY)
        await cache.set(f"ontology:name:{node['name']}", node["id"], ttl=TTL_ONTOLOGY)

    # 전체 노드 목록도 캐싱
    await cache.set("ontology:all_nodes", nodes, ttl=TTL_ONTOLOGY)
    logger.info("seed_ontology_cache_done", count=len(nodes))
    return len(nodes)


# ---------------------------------------------------------------------------
# 2. Seed price sample data (1-week mock prices)
# ---------------------------------------------------------------------------
async def seed_price_cache(dry_run: bool = False) -> int:
    nodes_path = ROOT / "data" / "ontology" / "food_nodes.json"
    if not nodes_path.exists():
        return 0

    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    price_data: list[dict] = []

    base_prices: dict[str, tuple[float, float]] = {
        "고등어": (8500, 12000), "갈치": (15000, 20000), "삼치": (7000, 10000),
        "배추": (3500, 5000), "무": (1500, 2500), "상추": (2000, 4000),
        "마늘": (8000, 12000), "양파": (1500, 3000), "대파": (2000, 3500),
        "한우": (85000, 95000), "삼겹살": (25000, 32000), "닭고기": (6000, 8500),
        "사과": (5000, 7000), "딸기": (12000, 18000), "계란": (7000, 9000),
    }

    today = datetime.now(tz=timezone.utc).date()
    count = 0
    for node in nodes[:25]:  # 처음 25개만
        name = node["name"]
        low, high = base_prices.get(name, (3000, 8000))
        week_data = []
        for offset in range(7):
            day = today - timedelta(days=6 - offset)
            wholesale = round(low + (high - low) * (0.4 + 0.2 * (offset / 6)), 0)
            retail = round(wholesale * 1.3, 0)
            week_data.append({
                "date": str(day),
                "item_id": node["id"],
                "item_name": name,
                "wholesale_price": wholesale,
                "retail_price": retail,
                "price_gap": round((retail - wholesale) / wholesale * 100, 1),
                "source": "KAMIS",
            })
            price_data.append(week_data[-1])
            count += 1

        if not dry_run:
            cache = get_cache_manager()
            await cache.set(f"prices:{node['id']}:week", week_data, ttl=TTL_PRICES)

    logger.info("seed_price_cache_done", records=count)
    return count


# ---------------------------------------------------------------------------
# 3. Upload news samples to S3 (mock)
# ---------------------------------------------------------------------------
async def seed_news_s3(dry_run: bool = False) -> int:
    samples_dir = ROOT / "data" / "news" / "samples"
    if not samples_dir.exists():
        return 0

    s3 = build_s3_client()
    total = 0
    for json_file in samples_dir.glob("*.json"):
        articles = json.loads(json_file.read_text(encoding="utf-8"))
        if dry_run:
            logger.info("seed_dry_run", stage="news_s3", file=json_file.name, count=len(articles))
            total += len(articles)
            continue
        for article in articles:
            key = f"news/samples/{json_file.stem}/{uuid4()}.json"
            try:
                await s3.upload_json(key, article)
                total += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("seed_news_upload_error", key=key, error_type=type(exc).__name__)

    logger.info("seed_news_s3_done", total=total)
    return total


# ---------------------------------------------------------------------------
# 4. Warm category cache
# ---------------------------------------------------------------------------
async def seed_category_cache(dry_run: bool = False) -> int:
    nodes_path = ROOT / "data" / "ontology" / "food_nodes.json"
    if not nodes_path.exists():
        return 0
    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))

    # 카테고리별 분류
    by_category: dict[str, list] = {}
    for n in nodes:
        cat = n.get("category", "OTHER")
        by_category.setdefault(cat, []).append(n)

    if not dry_run:
        cache = get_cache_manager()
        from app.core.cache_manager import TTL_CATEGORIES
        for cat, items in by_category.items():
            await cache.set(f"categories:{cat}", items, ttl=TTL_CATEGORIES)
        await cache.set("categories:all", list(by_category.keys()), ttl=TTL_CATEGORIES)

    logger.info("seed_category_cache_done", categories=list(by_category.keys()))
    return len(by_category)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main(dry_run: bool = False, reset: bool = False) -> None:
    settings = get_settings()
    logger.info("seed_start", mock=settings.is_mock, dry_run=dry_run, reset=reset)

    if reset:
        reset_cache_manager()
        logger.info("seed_cache_reset")

    n_nodes = await seed_ontology_cache(dry_run)
    n_prices = await seed_price_cache(dry_run)
    n_news = await seed_news_s3(dry_run)
    n_cats = await seed_category_cache(dry_run)

    logger.info(
        "seed_complete",
        nodes=n_nodes, prices=n_prices, news=n_news, categories=n_cats
    )
    print(f"\n✅ Seed complete: {n_nodes} nodes | {n_prices} price records | {n_news} news | {n_cats} categories")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FoodLens demo data seeder")
    parser.add_argument("--dry-run", action="store_true", help="Count without writing")
    parser.add_argument("--reset", action="store_true", help="Clear cache before seeding")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, reset=args.reset))
