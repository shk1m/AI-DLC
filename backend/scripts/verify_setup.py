"""
Deployment verification script (Step 22) — 시연 사전 점검.

사용법: python -m backend.scripts.verify_setup
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("verify_setup")

OK = "✅"
WARN = "⚠️ "
ERR = "❌"


def check(label: str, result: bool, warn_only: bool = False) -> bool:
    icon = OK if result else (WARN if warn_only else ERR)
    print(f"  {icon} {label}")
    return result


async def main() -> int:
    s = get_settings()
    failures = 0
    print("\n🔍 FoodLens Setup Verification\n")

    # --- Core env ---
    print("[1] Core environment")
    check("USE_MOCK flag", s.use_mock or not s.use_mock)  # always pass, just show
    check("APP_ENV set", bool(s.app_env))

    # --- Data files ---
    print("\n[2] Demo data files")
    for rel in [
        "data/ontology/food_nodes.json",
        "data/ontology/food_edges.json",
        "data/news/samples/naver_news.json",
        "data/news/samples/mafra_news.json",
        "data/news/samples/mof_news.json",
    ]:
        ok = (ROOT / rel).exists()
        if not ok:
            failures += 1
        check(rel, ok)

    # --- API credentials ---
    print("\n[3] API credentials (warn only in mock mode)")
    warn = s.is_mock
    if not check("Naver Client ID", s.has_naver_credentials, warn_only=warn) and not warn:
        failures += 1
    if not check("AWS credentials", s.has_aws_credentials, warn_only=True):
        pass  # 시연에서는 warn only

    # --- Imports ---
    print("\n[4] Required packages")
    for pkg_name, pkg in [
        ("fastapi", "fastapi"),
        ("pydantic", "pydantic"),
        ("structlog", "structlog"),
        ("httpx", "httpx"),
        ("bs4", "bs4"),
        ("hypothesis", "hypothesis"),
    ]:
        try:
            __import__(pkg)
            check(pkg_name, True)
        except ImportError:
            check(pkg_name, False)
            failures += 1

    # --- Mock S3 ---
    print("\n[5] S3 (mock)")
    try:
        from app.adapters.s3_client import build_s3_client
        client = build_s3_client()
        test_key = "__verify__/test.txt"
        await client.upload_text(test_key, "ok")
        content = await client.download(test_key)
        await client.delete(test_key)
        check("S3 mock read/write", content == "ok")
    except Exception as exc:
        check(f"S3 mock ({type(exc).__name__})", False)
        failures += 1

    print(f"\n{'✅ All checks passed' if failures == 0 else f'⚠️  {failures} check(s) failed'}\n")
    return failures


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
