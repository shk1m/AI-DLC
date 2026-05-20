# Tech Stack Decisions (기술 스택 결정)

---

## 최종 기술 스택

### Frontend
| 기술 | 버전 | 용도 | 선택 근거 |
|------|------|------|-----------|
| Next.js | 14.x | 프레임워크 | SSR/SSG, App Router, 요구사항 명시 |
| React | 18.x | UI 라이브러리 | Next.js 기본 |
| TypeScript | 5.x | 타입 안전성 | 개발 생산성, 버그 방지 |
| Tailwind CSS | 3.x | 스타일링 | Bento-box 레이아웃, 빠른 개발 |
| Recharts | 2.x | 차트 | 요구사항 명시, CustomTooltip 지원 |
| fast-check | 3.x | PBT (프론트) | PBT-09 준수 |

### Backend
| 기술 | 버전 | 용도 | 선택 근거 |
|------|------|------|-----------|
| Python | 3.11+ | 런타임 | AI/ML 생태계, 팀 역량 |
| FastAPI | 0.110+ | 웹 프레임워크 | 비동기, 자동 문서화, Pydantic 통합 |
| Pydantic | 2.x | 데이터 검증 | SECURITY-05 준수, 타입 안전 |
| SQLAlchemy | 2.x | ORM | 비동기 지원, 성숙한 생태계 |
| Alembic | 1.x | DB 마이그레이션 | SQLAlchemy 표준 |
| LangChain | 0.2+ | AI 오케스트레이션 | Agent 기반, 도구 통합 |
| httpx | 0.27+ | HTTP 클라이언트 | 비동기, 타임아웃 관리 |
| structlog | 24.x | 로깅 | 구조화 로그, SECURITY-03 |
| Hypothesis | 6.x | PBT (백엔드) | PBT-09 준수 |
| pytest | 8.x | 테스트 러너 | 표준, Hypothesis 통합 |
| Black | 24.x | 포매터 | 코드 일관성 |
| Ruff | 0.4+ | 린터 | 빠른 속도, 포괄적 규칙 |

### AWS Services
| 서비스 | 용도 | 선택 근거 |
|--------|------|-----------|
| Amazon Bedrock (Claude 3.5 Sonnet) | LLM | 팀 선택, 한국어 성능 우수 |
| Amazon Bedrock Knowledge Bases | RAG | 관리형, 빠른 구축 |
| Amazon Bedrock Guardrails | AI 안전 | 환각 통제, 부적절 응답 필터 |
| Amazon Neptune | 그래프 DB | 온톨로지, 관계 탐색 |
| Amazon RDS (PostgreSQL 15) | 관계형 DB | 시세, 뉴스, 마스터 데이터 |
| Amazon S3 | 객체 저장소 | RAG 소스 문서, 크롤링 원본 |
| AWS Secrets Manager | 비밀 관리 | API 키, DB 자격증명 |

### External APIs
| API | 용도 | 인증 방식 |
|-----|------|-----------|
| KAMIS API | 농산물 시세 | API Key |
| 공공데이터포털 API (6~7개) | 수산물, 축산물, 가공식품 | API Key |
| 네이버 검색 API | 뉴스 검색 | Client ID + Secret |
| 네이버 데이터랩 API | 검색어 트렌드 | Client ID + Secret |

---

## 의존성 관리 (SECURITY-10 준수)

### Python (requirements.txt) - 버전 고정
```
fastapi==0.110.0
uvicorn==0.29.0
pydantic==2.7.0
sqlalchemy==2.0.29
alembic==1.13.1
langchain==0.2.0
langchain-aws==0.1.0
boto3==1.34.0
httpx==0.27.0
structlog==24.1.0
python-dotenv==1.0.1
websockets==12.0
beautifulsoup4==4.12.3
hypothesis==6.100.0
pytest==8.1.0
pytest-asyncio==0.23.0
black==24.3.0
ruff==0.4.0
pip-audit==2.7.0
```

### Node.js (package.json) - 버전 고정
```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "18.3.0",
    "react-dom": "18.3.0",
    "recharts": "2.12.0",
    "tailwindcss": "3.4.0"
  },
  "devDependencies": {
    "typescript": "5.4.0",
    "fast-check": "3.17.0",
    "eslint": "8.57.0",
    "prettier": "3.2.0",
    "@types/react": "18.3.0",
    "@types/node": "20.12.0"
  }
}
```

---

## PBT 프레임워크 설정 (PBT-09 준수)

### Python - Hypothesis 설정
```python
# conftest.py
from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=200, phases=[Phase.explicit, Phase.generate, Phase.shrink])
settings.register_profile("dev", max_examples=50)
settings.load_profile("dev")
```

### TypeScript - fast-check 설정
```typescript
// test.config.ts
import fc from 'fast-check';

fc.configureGlobal({
  numRuns: 100,
  seed: Date.now(), // CI에서 로그로 기록
});
```

---

## 보안 구현 계획 (SECURITY 준수)

### P1 (시연 시 구현)
- [x] SECURITY-03: structlog 구조화 로그
- [x] SECURITY-04: Next.js 보안 헤더 미들웨어
- [x] SECURITY-05: Pydantic 입력 검증
- [x] SECURITY-09: 글로벌 에러 핸들러 (스택 트레이스 미노출)
- [x] SECURITY-10: 의존성 버전 고정
- [x] SECURITY-15: try/except + fail-closed

### P2 (설계 문서로 제시)
- [ ] SECURITY-01: RDS 암호화 (프로덕션 배포 시)
- [ ] SECURITY-06: IAM 최소 권한 (프로덕션 배포 시)
- [ ] SECURITY-07: VPC + Security Group (프로덕션 배포 시)
- [ ] SECURITY-08: Cognito + JWT 인증 (프로덕션 배포 시)
- [ ] SECURITY-12: MFA (프로덕션 배포 시)
