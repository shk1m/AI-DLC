"""
공통 pytest fixtures + Hypothesis 프로필 등록.

PBT-09 준수: 환경별 Hypothesis 프로필 (dev: 50회, ci: 200회).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from hypothesis import HealthCheck, Phase, settings


# --- Hypothesis 프로필 등록 (NFR-04 / PBT-09) ---
settings.register_profile(
    "dev",
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "ci",
    max_examples=200,
    deadline=None,
    phases=[Phase.explicit, Phase.generate, Phase.shrink],
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


# --- 공통 fixture ---
@pytest.fixture(scope="session")
def project_root() -> Path:
    """워크스페이스 루트 (테스트가 어디서 실행되든 안정적으로 참조)."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture(autouse=True)
def _force_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    모든 테스트는 기본적으로 USE_MOCK=true 로 실행.
    실제 외부 서비스 호출 방지 (시연 안정성 + CI 격리).
    """
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
