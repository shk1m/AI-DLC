import os


class Settings:
    # Database (Unit 4 크롤링과 동일한 DB)
    db_host = os.environ.get("DB_HOST", "ai-dlc-db.cwzuko60yxak.us-east-1.rds.amazonaws.com")
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_name = os.environ.get("DB_NAME", "aidlc")
    db_user = os.environ.get("DB_USER", "dbadmin")
    db_password = os.environ.get("DB_PASSWORD", "AiDlc2026Pass!")

    # AWS Bedrock
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    bedrock_model_id = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")

    # Menu Generation
    target_servings = int(os.environ.get("TARGET_SERVINGS", "100"))
    budget_per_serving = int(os.environ.get("BUDGET_PER_SERVING", "4500"))
    menu_count = int(os.environ.get("MENU_COUNT", "3"))


settings = Settings()
