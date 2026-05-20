# Step 1 Summary — 프로젝트 골격 + 의존성

**Phase**: A — Project Structure Setup  
**Story**: S-1 (데이터 소스 API 키 발급 + 테스트)  
**NFR**: SECURITY-10 (의존성 버전 고정), SECURITY-12 (Secrets management), MAINT-05

## Created files
- `backend/requirements.txt` — 모든 의존성 버전 고정 (FastAPI, LangChain, boto3, structlog, hypothesis, pytest, etc.)
- `backend/pyproject.toml` — Black, Ruff, mypy, pytest, coverage 설정
- `backend/.python-version` — Python 3.11
- `backend/app/__init__.py`, `backend/app/adapters/__init__.py`, `backend/app/core/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/services/__init__.py`
- `backend/scripts/__init__.py`
- `backend/tests/__init__.py`, `backend/tests/unit/__init__.py`, `backend/tests/integration/__init__.py`
- `backend/tests/conftest.py` — Hypothesis 프로필 (dev/ci) 등록 + `USE_MOCK=true` autouse fixture
- `.env.example` — 모든 환경변수 플레이스홀더 (Naver Open API URL 포함)
- `.gitignore` — `.env`, mock 산출물, 로그, 캐시 디렉토리 제외

## Notes
- `.env` 자체는 사용자가 직접 생성 (실제 자격증명 보유)
- `bandit` (S 규칙) 활성화로 secrets/SQL injection 정적 분석 자동화
- pytest-asyncio `mode=auto` → async 함수 자동 인식
- Hypothesis profile은 `HYPOTHESIS_PROFILE=ci`로 CI에서 200회 실행 가능
