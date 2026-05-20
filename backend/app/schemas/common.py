"""Pydantic 스키마: 공통 응답"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """에러 응답 (SECURITY-09: 스택 트레이스 미노출)"""

    error: str
    correlation_id: str | None = None
    detail: str | None = None


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""

    status: str
    checks: dict[str, str]
    version: str
    uptime_seconds: float
