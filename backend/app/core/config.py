"""
Application settings (Pydantic Settings).

환경변수에서 설정을 로드하며, .env 파일도 자동 인식합니다.
SECURITY-12 준수: 비밀값은 코드에 하드코딩하지 않으며, 로그에 출력 시 마스킹 대상입니다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """전역 애플리케이션 설정."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_env: Literal["local", "dev", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    use_mock: bool = Field(
        default=True,
        description="True면 외부 서비스 호출 차단 (테스트/시연 안전성).",
    )
    enable_structured_logs: bool = True

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://admin:postgres@localhost:5432/foodlens"
    db_password: SecretStr | None = None

    # ---- Cache / Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- AWS ----
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: SecretStr | None = None
    aws_secret_access_key: SecretStr | None = None
    s3_bucket: str = "foodlens-rag-docs"
    bedrock_kb_id: str | None = None
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    neptune_endpoint: str | None = None

    # ---- KAMIS API ----
    kamis_api_key: SecretStr | None = None
    kamis_api_id: str | None = None
    kamis_base_url: str = "https://www.kamis.or.kr/service/price/xml.do"

    # ---- 공공데이터포털 ----
    public_data_api_key: SecretStr | None = None

    # ---- Naver Open API ----
    naver_client_id: SecretStr | None = None
    naver_client_secret: SecretStr | None = None
    naver_news_api_url: str = "https://openapi.naver.com/v1/search/news.json"
    naver_datalab_api_url: str = "https://openapi.naver.com/v1/datalab/search"

    # ---- Government press crawler ----
    mafra_base_url: str = "https://www.mafra.go.kr"
    mof_base_url: str = "https://www.mof.go.kr"
    crawler_user_agent: str = "FoodLens-Crawler/0.1 (+contact@foodlens.local)"
    crawler_timeout_seconds: float = 15.0
    crawler_max_retries: int = 3

    # ---- Resilience (NFR Design 1.1 / 1.2) ----
    cb_failure_threshold: int = 5
    cb_recovery_timeout: float = 30.0

    # --- helpers ---
    @property
    def is_mock(self) -> bool:
        """USE_MOCK=true 또는 자격증명 누락 시 True (시연/CI 안전성)."""
        return self.use_mock

    @property
    def has_aws_credentials(self) -> bool:
        return self.aws_access_key_id is not None and self.aws_secret_access_key is not None

    @property
    def has_naver_credentials(self) -> bool:
        return self.naver_client_id is not None and self.naver_client_secret is not None

    def naver_auth_headers(self) -> dict[str, str]:
        """
        Naver Open API 인증 헤더.
        호출 측에서 has_naver_credentials 체크 후 사용해야 함.
        """
        if not self.has_naver_credentials:
            raise ValueError("Naver credentials are not configured")
        return {
            "X-Naver-Client-Id": self.naver_client_id.get_secret_value(),  # type: ignore[union-attr]
            "X-Naver-Client-Secret": self.naver_client_secret.get_secret_value(),  # type: ignore[union-attr]
            "User-Agent": self.crawler_user_agent,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """싱글톤 Settings 인스턴스 (FastAPI Depends 호환)."""
    return Settings()


def reset_settings_cache() -> None:
    """테스트에서 환경변수 변경 후 캐시를 비우기 위한 헬퍼."""
    get_settings.cache_clear()
