"""애플리케이션 환경 설정 (SECURITY-12: 비밀 관리)"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """환경 변수 기반 설정. .env 파일에서 로드."""

    # 앱 설정
    app_name: str = "FoodLens API"
    app_version: str = "1.0.0"
    debug: bool = False

    # DB 설정 (DB명: ai-dlc)
    database_url: str = "postgresql+asyncpg://admin:password@localhost:5432/ai-dlc"

    # Redis 설정
    redis_url: str = "redis://localhost:6379"

    # 외부 API 키
    kamis_api_key: str = ""
    kamis_cert_id: str = ""
    public_data_api_key: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # AWS 설정 (워크샵 환경: us-east-1)
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    # Bedrock 모델: Inference Profile ID (us-east-1, on-demand 호출 가능)
    # Claude Sonnet 4.5 (성능 우수, 한국어 우수)
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    # Claude 3.5 Haiku (빠른 응답, 비용 절감)
    bedrock_model_id_fast: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    neptune_endpoint: str = ""
    s3_bucket_name: str = "foodlens-rag-docs"

    # 캐시 TTL (초)
    cache_ttl_prices: int = 3600  # 1시간
    cache_ttl_news: int = 1800  # 30분
    cache_ttl_ontology: int = 86400  # 24시간
    cache_ttl_categories: int = 86400  # 24시간
    cache_ttl_trends: int = 21600  # 6시간

    # Circuit Breaker 설정
    cb_failure_threshold: int = 5
    cb_recovery_timeout: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
