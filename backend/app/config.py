import os


class Settings:
    """Lambda 환경변수 기반 설정"""

    # Database (Unit 4 크롤링과 동일한 DB: ai-dlc-db)
    db_host: str = os.environ.get("DB_HOST", "ai-dlc-db.cwzuko60yxak.us-east-1.rds.amazonaws.com")
    db_port: int = int(os.environ.get("DB_PORT", "5432"))
    db_name: str = os.environ.get("DB_NAME", "aidlc")
    db_user: str = os.environ.get("DB_USER", "dbadmin")
    db_password: str = os.environ.get("DB_PASSWORD", "AiDlc2026Pass")

    # AWS Bedrock
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

    # Menu Generation
    target_servings: int = int(os.environ.get("TARGET_SERVINGS", "100"))
    budget_per_serving: int = int(os.environ.get("BUDGET_PER_SERVING", "4500"))

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
