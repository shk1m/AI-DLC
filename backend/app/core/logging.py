"""
Structured logging via structlog.

NFR Mapping:
- OBS-01: JSON 구조화 로그
- SECURITY-03: 민감정보 마스킹 (api_key/password/secret/token)
- OBS-02: correlation_id 자동 포함 (contextvars)
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars
from structlog.types import EventDict

from app.core.config import get_settings

# 마스킹 대상 키 (정확 일치 + suffix 매칭)
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|password|passwd|secret|token|authorization|client[_-]?secret)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?:Bearer\s+)?[A-Za-z0-9_\-]{32,}",  # 토큰 패턴 휴리스틱
)
_MASK = "***REDACTED***"


def _mask_sensitive(_logger: Any, _name: str, event_dict: EventDict) -> EventDict:
    """SECURITY-03: 민감 키/값을 마스킹."""
    masked: EventDict = {}
    for key, value in event_dict.items():
        if _SENSITIVE_KEY_PATTERN.search(key):
            masked[key] = _MASK
            continue
        if isinstance(value, str) and len(value) >= 32 and _SENSITIVE_VALUE_PATTERN.fullmatch(
            value
        ):
            masked[key] = _MASK
            continue
        if isinstance(value, dict):
            masked[key] = _mask_dict(value)
        else:
            masked[key] = value
    return masked


def _mask_dict(d: dict[str, Any]) -> dict[str, Any]:
    """중첩 dict 재귀 마스킹."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if _SENSITIVE_KEY_PATTERN.search(str(k)):
            out[k] = _MASK
        elif isinstance(v, dict):
            out[k] = _mask_dict(v)
        else:
            out[k] = v
    return out


def configure_logging() -> None:
    """
    애플리케이션 시작 시 1회 호출.
    structlog + stdlib logging 통합 설정.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # stdlib logging 기본 설정
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors: list[Any] = [
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _mask_sensitive,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.enable_structured_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """모듈에서 사용할 logger 인스턴스."""
    return structlog.get_logger(name)


# Alias for backward compatibility with main.py (Unit 2)
def setup_logging(debug: bool = False, **kwargs):
    """Wrapper for configure_logging that accepts debug parameter."""
    configure_logging()

