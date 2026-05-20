"""Tests for app.core.logging."""

from __future__ import annotations

import json
import logging

import pytest
import structlog

from app.core.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_structlog() -> None:
    """각 테스트마다 structlog 설정 초기화."""
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


class TestStructuredLogging:
    def test_configure_logging_does_not_raise(self) -> None:
        configure_logging()
        log = get_logger("test")
        # 호출이 예외 없이 동작하는지만 검증
        log.info("hello", extra="value")

    def test_get_logger_returns_bound_logger(self) -> None:
        configure_logging()
        log = get_logger("foo")
        assert hasattr(log, "info")
        assert hasattr(log, "bind")

    def test_sensitive_keys_are_masked(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ENABLE_STRUCTURED_LOGS", "true")
        from app.core.config import reset_settings_cache

        reset_settings_cache()
        configure_logging()
        log = get_logger("test")

        log.info(
            "request",
            api_key="real-secret-value-please-redact",
            password="hunter2",
            client_secret="0Y8nQxuyrR-fake",
            normal_field="visible",
        )
        captured = capsys.readouterr().out
        assert "real-secret-value-please-redact" not in captured
        assert "hunter2" not in captured
        assert "0Y8nQxuyrR-fake" not in captured
        assert "***REDACTED***" in captured
        assert "visible" in captured

    def test_nested_dict_masking(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ENABLE_STRUCTURED_LOGS", "true")
        from app.core.config import reset_settings_cache

        reset_settings_cache()
        configure_logging()
        log = get_logger("test")
        log.info(
            "outer",
            payload={"username": "alice", "password": "should-be-hidden"},
        )
        captured = capsys.readouterr().out
        assert "should-be-hidden" not in captured
        assert "alice" in captured

    def test_long_token_value_is_masked(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ENABLE_STRUCTURED_LOGS", "true")
        from app.core.config import reset_settings_cache

        reset_settings_cache()
        configure_logging()
        log = get_logger("test")
        token = "abcdefghijklmnopqrstuvwxyz0123456789"  # 36 chars
        log.info("auth", header_value=token)
        captured = capsys.readouterr().out
        assert token not in captured

    def test_json_output_is_parseable(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ENABLE_STRUCTURED_LOGS", "true")
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        from app.core.config import reset_settings_cache

        reset_settings_cache()
        configure_logging()
        log = get_logger("test")
        log.info("event", foo="bar", count=3)
        captured = capsys.readouterr().out.strip()
        # 마지막 줄이 JSON
        line = captured.splitlines()[-1]
        parsed = json.loads(line)
        assert parsed["event"] == "event"
        assert parsed["foo"] == "bar"
        assert parsed["count"] == 3
        assert "timestamp" in parsed
        assert parsed["level"] == "info"
