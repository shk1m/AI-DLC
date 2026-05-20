"""로컬 테스트"""
import os
import json

os.environ.setdefault("DB_HOST", "ai-dlc-db.cwzuko60yxak.us-east-1.rds.amazonaws.com")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "aidlc")
os.environ.setdefault("DB_USER", "dbadmin")
os.environ.setdefault("DB_PASSWORD", "AiDlc2026Pass!")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
os.environ.setdefault("MENU_COUNT", "3")

from lambda_handler import handler

result = handler({}, None)
print(json.dumps(json.loads(result["body"]), indent=2, ensure_ascii=False))
