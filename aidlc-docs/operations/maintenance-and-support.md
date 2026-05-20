# Maintenance & Support - 식견(FoodLens)

## Routine Maintenance

### Daily
- [ ] 크롤링 파이프라인 성공률 확인
- [ ] 시세 데이터 신선도 확인 (마지막 수집 시간)
- [ ] 에러 로그 리뷰

### Weekly
- [ ] 의존성 취약점 스캔 (`pip-audit`)
- [ ] 캐시 효율성 리뷰
- [ ] 사용자 피드백 분석

### Monthly
- [ ] 보안 패치 적용 (OS, Python, Node.js)
- [ ] 비용 최적화 리뷰
- [ ] 용량 계획 검토
- [ ] DR 드릴 (분기별)

---

## Incident Response

### Severity Classification
| Severity | 정의 | 대응 시간 | 해결 목표 |
|----------|------|-----------|-----------|
| SEV-1 | 서비스 완전 중단 | 5분 | 30분 |
| SEV-2 | 주요 기능 장애 | 15분 | 2시간 |
| SEV-3 | 부분 기능 영향 | 1시간 | 8시간 |
| SEV-4 | 경미한 이슈 | 다음 영업일 | 5영업일 |

### Common Scenarios

#### 외부 API 장애 (KAMIS/네이버)
1. Circuit Breaker가 자동으로 OPEN 전환
2. 캐시된 데이터로 Fallback 응답
3. API 복구 시 자동으로 HALF_OPEN → CLOSED
4. 장기 장애 시: Mock 모드 전환 (`USE_MOCK=true`)

#### Bedrock 응답 지연/실패
1. 타임아웃 설정 (30초)
2. 실패 시 "서비스 일시 중단" 메시지 표시
3. Guardrails 위반 시 안전한 기본 응답

#### DB 연결 고갈
1. Connection Pool 모니터링
2. 유휴 연결 정리
3. Pool 크기 조정 (pool_size, max_overflow)

---

## Capacity Planning

### Current (시연 환경)
| 리소스 | 현재 | 한계 |
|--------|------|------|
| CPU | 1 core | 8 cores (로컬) |
| Memory | 2GB | 16GB (로컬) |
| PostgreSQL | 100MB | 10GB (Docker) |
| 동시 사용자 | 1~5명 | 10명 (로컬) |

### Production (설계)
| 리소스 | 초기 | 6개월 | 12개월 |
|--------|------|-------|--------|
| ECS Tasks | 2 | 4 | 8 |
| RDS | db.r6g.large | db.r6g.xlarge | db.r6g.2xlarge |
| Neptune | db.r5.large | db.r5.xlarge | db.r5.2xlarge |
| 동시 사용자 | 100 | 500 | 2000 |
| 월 비용 | ~$735 | ~$1,200 | ~$2,500 |

### Scaling Triggers
- CPU > 70% (5분 지속) → ECS Auto Scaling
- Memory > 80% → 인스턴스 업그레이드
- DB 연결 > 80% → Pool 확장 또는 Read Replica
- 응답 시간 p95 > 3초 → 캐시 전략 강화

---

## Disaster Recovery

### Strategy
- **RPO**: 24시간 (일별 스냅샷)
- **RTO**: 30분 (스냅샷 복원 + 서비스 재시작)

### Backup Schedule
| 리소스 | 방법 | 주기 | 보존 |
|--------|------|------|------|
| RDS | 자동 스냅샷 | 일별 | 35일 |
| Neptune | 자동 스냅샷 | 일별 | 35일 |
| S3 | 버전 관리 | 실시간 | 영구 |
| 코드 | Git | 커밋마다 | 영구 |

### Recovery Steps
1. 최신 스냅샷에서 DB 복원
2. ECS 서비스 재배포
3. Health check 확인
4. 데이터 무결성 검증
5. 사용자 알림
