"""Tests for app.core.middleware (CorrelationIdMiddleware)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.middleware import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
    _is_valid_correlation_id,
    get_correlation_id,
)


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.add_middleware(CorrelationIdMiddleware)

    @application.get("/echo")
    async def echo(request: Request) -> dict[str, str]:
        return {"correlation_id": get_correlation_id(request)}

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestCorrelationIdValidation:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("", False),
            ("a" * 65, False),  # too long
            ("valid-uuid-1234", True),
            ("abc_123", True),
            ("with space", False),
            ("with;semicolon", False),
            ("a" * 64, True),
        ],
    )
    def test_is_valid_correlation_id(self, value: str, expected: bool) -> None:
        assert _is_valid_correlation_id(value) is expected


class TestCorrelationIdMiddleware:
    def test_generates_id_when_header_missing(self, client: TestClient) -> None:
        response = client.get("/echo")
        assert response.status_code == 200
        cid = response.headers[CORRELATION_ID_HEADER]
        assert len(cid) > 0
        assert response.json()["correlation_id"] == cid

    def test_propagates_valid_incoming_id(self, client: TestClient) -> None:
        response = client.get("/echo", headers={CORRELATION_ID_HEADER: "abc-123-xyz"})
        assert response.headers[CORRELATION_ID_HEADER] == "abc-123-xyz"
        assert response.json()["correlation_id"] == "abc-123-xyz"

    def test_replaces_invalid_id(self, client: TestClient) -> None:
        bad_value = "evil; injection"
        response = client.get("/echo", headers={CORRELATION_ID_HEADER: bad_value})
        cid = response.headers[CORRELATION_ID_HEADER]
        assert cid != bad_value
        assert _is_valid_correlation_id(cid)

    def test_each_request_gets_unique_id(self, client: TestClient) -> None:
        r1 = client.get("/echo")
        r2 = client.get("/echo")
        assert r1.headers[CORRELATION_ID_HEADER] != r2.headers[CORRELATION_ID_HEADER]
