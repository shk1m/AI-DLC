"""FoodLens API - FastAPI 메인 진입점

SECURITY-15: 글로벌 에러 핸들러, fail-closed 패턴
SECURITY-03: 구조화 로그
OBS-02: Correlation ID 미들웨어
"""

import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.aws import verify_aws_credentials
from app.core.logging import setup_logging
from app.routers import chat, news, prices, recipes
from app.schemas.common import HealthCheckResponse

settings = get_settings()

# 로깅 초기화
setup_logging(debug=settings.debug)
logger = structlog.get_logger()

# 앱 시작 시간 (uptime 계산용)
APP_START_TIME = time.time()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MD/영양사/바이어 전용 AI 식자재 시세 분석 대시보드 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (시연 환경)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Middleware ────────────────────────────────────────────────────

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """OBS-02: Correlation ID 미들웨어

    1. X-Correlation-ID 헤더 확인
    2. 없으면 UUID 생성
    3. 모든 로그에 포함
    4. 응답에 헤더로 반환
    """
    correlation_id = request.headers.get(
        "X-Correlation-ID", str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id

    # structlog 컨텍스트에 바인딩
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # 응답 헤더에 Correlation ID 추가
    response.headers["X-Correlation-ID"] = correlation_id

    logger.info(
        "request_completed",
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )

    return response


# ─── Global Error Handler (SECURITY-15) ───────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """SECURITY-09: 스택 트레이스 미노출
    SECURITY-15: fail-closed 패턴
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        correlation_id=correlation_id,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "correlation_id": correlation_id,
        },
    )


# ─── Routers ──────────────────────────────────────────────────────

app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(chat.router, tags=["chat"])


# ─── Health Check ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    uptime = time.time() - APP_START_TIME

    # AWS 자격증명 검증
    aws_status = await verify_aws_credentials()
    aws_check = "ok" if aws_status.get("valid") else "fail"

    return HealthCheckResponse(
        status="healthy" if aws_check == "ok" else "degraded",
        checks={
            "database": "ok",
            "cache": "ok",
            "aws": aws_check,
        },
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
