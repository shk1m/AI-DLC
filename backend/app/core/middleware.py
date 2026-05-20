"""
Correlation ID middleware for FastAPI/Starlette.

NFR Mapping:
- OBS-02: Request tracing via correlation_id
- SECURITY-15: 미처리 예외 시에도 correlation_id 보장 (에러 핸들러에서 활용)
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_ID_HEADER = "X-Correlation-ID"


def _is_valid_correlation_id(value: str) -> bool:
    """
    수신한 헤더 값이 안전한 ID 형식인지 검증.
    악의적 헤더 주입 방지: UUID 또는 영숫자/하이픈 ≤ 64자 허용.
    """
    if not value or len(value) > 64:
        return False
    return all(c.isalnum() or c in "-_" for c in value)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    요청별 correlation_id 부여 및 전파.

    동작:
    1. 요청 헤더 X-Correlation-ID 확인
    2. 없거나 유효하지 않으면 UUID4 생성
    3. request.state 및 structlog contextvars에 바인딩
    4. 응답 헤더에 동일 값 포함
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(CORRELATION_ID_HEADER, "")
        if _is_valid_correlation_id(incoming):
            correlation_id = incoming
        else:
            correlation_id = str(uuid.uuid4())

        # request.state에 저장 (다른 미들웨어/라우터에서 접근 가능)
        request.state.correlation_id = correlation_id

        # structlog 컨텍스트에 바인딩 (모든 로그에 자동 포함)
        clear_contextvars()
        bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
        finally:
            # 컨텍스트 정리 (다음 요청에 누수 방지)
            structlog.contextvars.unbind_contextvars("method", "path")

        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


def get_correlation_id(request: Request) -> str:
    """라우터/서비스에서 현재 요청의 correlation_id를 가져오는 헬퍼."""
    return getattr(request.state, "correlation_id", "unknown")
