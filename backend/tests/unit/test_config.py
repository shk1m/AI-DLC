"""Tests for app.core.config Settings."""

from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings, reset_settings_cache


class TestSettings:
    def test_defaults_in_test_env(self) -> None:
        s = Settings()
        # conftest forces USE_MOCK=true
        assert s.use_mock is True
        assert s.app_env == "local"
        assert s.crawler_max_retries == 3
        assert s.cb_failure_threshold == 5

    def test_secret_str_is_masked_on_repr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NAVER_CLIENT_SECRET", "supersecretvalue")
        reset_settings_cache()
        s = Settings()
        # SecretStr ensures the value is not leaked via repr/str
        assert "supersecretvalue" not in repr(s)
        assert s.naver_client_secret is not None
        # actual value still accessible via get_secret_value()
        assert s.naver_client_secret.get_secret_value() == "supersecretvalue"

    def test_naver_auth_headers_requires_credentials(self) -> None:
        s = Settings(naver_client_id=None, naver_client_secret=None)
        assert s.has_naver_credentials is False
        with pytest.raises(ValueError):
            s.naver_auth_headers()

    def test_naver_auth_headers_returns_required_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NAVER_CLIENT_ID", "id123")
        monkeypatch.setenv("NAVER_CLIENT_SECRET", "secret456")
        reset_settings_cache()
        s = Settings()
        headers = s.naver_auth_headers()
        assert headers["X-Naver-Client-Id"] == "id123"
        assert headers["X-Naver-Client-Secret"] == "secret456"
        assert "User-Agent" in headers

    def test_get_settings_is_cached(self) -> None:
        reset_settings_cache()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
