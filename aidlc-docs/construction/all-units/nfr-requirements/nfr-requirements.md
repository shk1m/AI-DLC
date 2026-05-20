# NFR Requirements (비기능 요구사항 상세)

---

## 1. 성능 요구사항 (Performance)

| ID | 요구사항 | 목표값 | 측정 방법 |
|----|----------|--------|-----------|
| PERF-01 | 대시보드 초기 로딩 | ≤ 3초 | First Contentful Paint |
| PERF-02 | 차트 데이터 렌더링 | ≤ 1초 | API 응답 + 렌더링 완료 |
| PERF-03 | 챗봇 첫 토큰 응답 | ≤ 2초 | WebSocket 첫 토큰 수신 |
| PERF-04 | 챗봇 전체 응답 | ≤ 5초 | 스트리밍 완료 |
| PERF-05 | 시세 API 응답 | ≤ 500ms | 캐시 히트 시 |
| PERF-06 | 시세 API 응답 (캐시 미스) | ≤ 3초 | 외부 API 호출 포함 |
| PERF-07 | 대체 식자재 추천 | ≤ 2초 | Neptune 쿼리 + 계산 |
| PERF-08 | 원가 시뮬레이션 | ≤ 3초 | AI 추천 포함 |

### 성능 최적화 전략
- **캐싱**: Redis 또는 인메모리 캐시 (시세 1시간, 온톨로지 24시간)
- **비동기 처리**: FastAPI async/await 전면 활용
- **병렬 호출**: 독립적인 외부 API 호출은 asyncio.gather로 병렬화
- **프론트엔드**: Next.js SSG/ISR로 정적 콘텐츠 최적화, 코드 스플리팅

---

## 2. 가용성 요구사항 (Availability)

| ID | 요구사항 | 목표값 | 비고 |
|----|----------|--------|------|
| AVAIL-01 | 시연 환경 가용성 | 99% (시연 시간 내) | localhost 기반 |
| AVAIL-02 | 프로덕션 설계 가용성 | 99.9% | 문서화만 (구현 X) |
| AVAIL-03 | 외부 API 장애 대응 | Fallback 자동 전환 | 캐시 데이터 사용 |
| AVAIL-04 | Bedrock 장애 대응 | 사전 정의된 응답 | "서비스 일시 중단" 안내 |

### Fallback 전략
```
외부 API 호출 실패 시:
1. 캐시된 데이터 반환 (stale-while-revalidate)
2. 캐시도 없으면 "데이터 조회 불가" 메시지
3. 3회 재시도 후 최종 실패 처리
```

---

## 3. 보안 요구사항 (Security) - SECURITY-01~15 적용

| SECURITY Rule | 적용 방법 | 우선순위 |
|---------------|-----------|----------|
| SECURITY-01 | RDS 암호화 at rest (AES-256), TLS 1.2+ 강제 | P1 |
| SECURITY-03 | Python logging + 구조화 로그 (JSON) | P1 |
| SECURITY-04 | Next.js middleware에서 보안 헤더 설정 | P1 |
| SECURITY-05 | Pydantic 스키마 검증 (모든 엔드포인트) | P1 |
| SECURITY-06 | IAM 최소 권한 정책 (Bedrock, Neptune, RDS) | P1 |
| SECURITY-08 | API 인증 미들웨어 (시연: 간소화, 설계: JWT) | P2 |
| SECURITY-09 | 에러 응답에 스택 트레이스 미노출 | P1 |
| SECURITY-10 | requirements.txt 버전 고정, pip-audit | P1 |
| SECURITY-11 | 보안 로직 전용 모듈 분리 | P2 |
| SECURITY-12 | 시연: 간소화 인증, 설계: Cognito + MFA | P2 |
| SECURITY-15 | 글로벌 에러 핸들러, fail-closed 패턴 | P1 |

### 시연 환경 vs 프로덕션 설계
| 항목 | 시연 (localhost) | 프로덕션 (설계) |
|------|-----------------|-----------------|
| 인증 | API Key 또는 없음 | Cognito + JWT + MFA |
| HTTPS | HTTP (localhost) | CloudFront + ACM |
| WAF | 없음 | AWS WAF |
| 네트워크 | 로컬 | VPC + Private Subnet |

---

## 4. 테스팅 요구사항 (PBT-01~10 적용)

### PBT 프레임워크 선택 (PBT-09)
| 언어 | 프레임워크 | 용도 |
|------|-----------|------|
| Python | Hypothesis | 백엔드 비즈니스 로직 PBT |
| TypeScript | fast-check | 프론트엔드 유틸리티 PBT |

### PBT 대상 식별 (PBT-01)
| 컴포넌트 | 속성 카테고리 | 테스트 대상 |
|----------|--------------|-------------|
| PriceService | Invariant | 도매가 ≤ 소매가, 가격 > 0 |
| PriceService | Round-trip | 시세 직렬화/역직렬화 |
| SpikeDetector | Invariant | Spike 수 ≤ 전체 데이터 포인트 수 |
| CostSimulator | Invariant | 총 원가 = Σ(재료별 원가) |
| CostSimulator | Commutativity | 재료 순서 무관하게 동일 결과 |
| SubstituteService | Invariant | 유사도 점수 0~1 범위 |
| OntologyService | Round-trip | 노드 생성/조회 일관성 |
| API Schemas | Round-trip | Pydantic 직렬화/역직렬화 |

### 테스트 커버리지 목표
| 유형 | 목표 | 비고 |
|------|------|------|
| 단위 테스트 | 70%+ | 핵심 비즈니스 로직 |
| PBT | 핵심 로직 100% | 위 테이블 대상 전체 |
| 통합 테스트 | 주요 API 경로 | E2E 시나리오 |

---

## 5. 확장성 요구사항 (Scalability)

| ID | 요구사항 | 설계 방향 |
|----|----------|-----------|
| SCALE-01 | 데이터 소스 추가 용이 | Adapter 패턴 (인터페이스 통일) |
| SCALE-02 | 식자재 카테고리 확장 | DB 기반 동적 카테고리 (하드코딩 X) |
| SCALE-03 | 동시 사용자 확장 | 프로덕션: ECS Auto Scaling |
| SCALE-04 | 온톨로지 노드 확장 | Neptune 자동 스케일링 |
| SCALE-05 | RAG 문서 확장 | S3 + Bedrock KB 자동 동기화 |

---

## 6. 관찰성 요구사항 (Observability)

| ID | 요구사항 | 구현 |
|----|----------|------|
| OBS-01 | 구조화 로그 | Python structlog (JSON 포맷) |
| OBS-02 | 요청 추적 | correlation_id 미들웨어 |
| OBS-03 | API 응답 시간 측정 | FastAPI middleware + 메트릭 |
| OBS-04 | 외부 API 호출 모니터링 | httpx 이벤트 훅 |
| OBS-05 | 에러 알림 | 프로덕션: CloudWatch Alarms |

---

## 7. 유지보수성 요구사항 (Maintainability)

| ID | 요구사항 | 구현 |
|----|----------|------|
| MAINT-01 | 코드 포매팅 | Black (Python), Prettier (TS) |
| MAINT-02 | 린팅 | Ruff (Python), ESLint (TS) |
| MAINT-03 | 타입 안전성 | Pydantic (Python), TypeScript strict |
| MAINT-04 | API 문서 자동 생성 | FastAPI OpenAPI (Swagger UI) |
| MAINT-05 | 의존성 관리 | requirements.txt 버전 고정 |
