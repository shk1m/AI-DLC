"""AWS 클라이언트 팩토리

- STS 임시 자격증명 지원 (워크샵 환경)
- Bedrock, S3, Neptune 클라이언트 제공
- IAM 최소 권한 원칙 (SECURITY-06)
"""

import boto3
import structlog
from botocore.config import Config

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# 재시도 + 타임아웃 설정 (NFR: Retry with Exponential Backoff)
_BOTO_CONFIG = Config(
    region_name=settings.aws_region,
    retries={"max_attempts": 3, "mode": "adaptive"},
    connect_timeout=5,
    read_timeout=30,
)


def _get_credentials_kwargs() -> dict:
    """환경 변수 기반 자격증명 인자 구성"""
    kwargs: dict = {}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token
    return kwargs


def get_bedrock_runtime_client():
    """Bedrock Runtime 클라이언트 (LLM 호출용)"""
    return boto3.client(
        "bedrock-runtime",
        config=_BOTO_CONFIG,
        **_get_credentials_kwargs(),
    )


def get_bedrock_agent_runtime_client():
    """Bedrock Agent Runtime 클라이언트 (Knowledge Base RAG)"""
    return boto3.client(
        "bedrock-agent-runtime",
        config=_BOTO_CONFIG,
        **_get_credentials_kwargs(),
    )


def get_s3_client():
    """S3 클라이언트 (RAG 소스 문서)"""
    return boto3.client(
        "s3",
        config=_BOTO_CONFIG,
        **_get_credentials_kwargs(),
    )


async def verify_aws_credentials() -> dict:
    """AWS 자격증명 유효성 검증 (앱 시작 시 호출)

    Returns:
        dict with 'valid', 'account', 'arn' or 'error'
    """
    try:
        sts = boto3.client(
            "sts",
            config=_BOTO_CONFIG,
            **_get_credentials_kwargs(),
        )
        identity = sts.get_caller_identity()
        logger.info(
            "aws_credentials_valid",
            account=identity.get("Account"),
            arn=identity.get("Arn"),
        )
        return {
            "valid": True,
            "account": identity.get("Account"),
            "arn": identity.get("Arn"),
        }
    except Exception as e:
        logger.error("aws_credentials_invalid", error=str(e))
        return {"valid": False, "error": str(e)}
