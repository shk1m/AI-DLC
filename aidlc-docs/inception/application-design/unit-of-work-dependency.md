# Unit of Work 의존성 (Dependencies)

---

## 의존성 매트릭스

| From \ To | Unit 1 (Frontend) | Unit 2 (Backend) | Unit 3 (AI/Data) | Unit 4 (Integration) |
|-----------|:-----------------:|:----------------:|:----------------:|:--------------------:|
| **Unit 1 (Frontend)** | - | REST/WS 호출 | - | - |
| **Unit 2 (Backend)** | - | - | 서비스 호출 | 어댑터 공유 |
| **Unit 3 (AI/Data)** | - | 서비스 등록 | - | 데이터 의존 |
| **Unit 4 (Integration)** | 연동 지원 | 연동 지원 | 데이터 적재 | - |

---

## 의존성 상세

### Unit 1 (Frontend) → Unit 2 (Backend)
- **유형**: API 소비자
- **인터페이스**: REST API + WebSocket
- **결합도**: 낮음 (API 계약 기반)
- **싱크 방식**: 동시 개발 + 수시 싱크

### Unit 2 (Backend) → Unit 3 (AI/Data)
- **유형**: 서비스 호출
- **인터페이스**: Python 함수 호출 (같은 프로세스 내)
- **결합도**: 중간 (서비스 인터페이스 공유)
- **싱크 방식**: 인터페이스 먼저 합의, 구현은 독립

### Unit 3 (AI/Data) → Unit 4 (Integration)
- **유형**: 데이터 의존
- **인터페이스**: S3 버킷, Neptune 데이터
- **결합도**: 낮음 (데이터 포맷 합의만 필요)
- **싱크 방식**: 데이터 스키마 먼저 합의

### Unit 4 (Integration) → Unit 1, 2
- **유형**: 지원/연동
- **인터페이스**: 통합 테스트, 연동 디버깅
- **결합도**: 낮음 (지원 역할)
- **싱크 방식**: 필요 시 즉시 지원

---

## 개발 순서 (Critical Path)

```
시간 →
─────────────────────────────────────────────────────────

Unit 2 (Backend):  [API 구조 셋업] → [시세 API] → [레시피 API] → [WS 챗봇]
                         ↓
Unit 3 (AI/Data):  [Neptune 스키마] → [Bedrock KB] → [LangChain Agent] → [튜닝]
                         ↓
Unit 4 (Integration): [크롤러] → [데이터 적재] → [프론트-백 연동] → [시연 준비]
                         
Unit 1 (Frontend): [레이아웃] → [차트+테이블] → [챗봇 UI] → [시뮬레이터] → [폴리싱]
                                      ↑ (Mock 데이터로 독립 개발 가능)
```

### 블로킹 의존성
1. **Unit 3 → Unit 4**: Neptune 스키마가 정의되어야 온톨로지 데이터 적재 가능
2. **Unit 2 → Unit 3**: ChatService가 LangChainAgent를 호출하므로 Agent 인터페이스 합의 필요
3. **Unit 1 → Unit 2**: API 응답 형식 합의 필요 (하지만 Mock으로 독립 개발 가능)

### 비블로킹 (병렬 가능)
- Unit 1은 Mock 데이터로 독립 개발 가능
- Unit 2의 시세 API와 Unit 3의 Neptune 구축은 병렬 가능
- Unit 4의 크롤러는 독립 개발 가능

---

## 싱크 포인트 (Sync Points)

| 시간 | 싱크 내용 | 참여 Unit |
|------|-----------|-----------|
| 11:30 | API 응답 형식 합의 (TypeScript 타입 공유) | 1, 2 |
| 12:00 | Neptune 스키마 + Agent 인터페이스 합의 | 2, 3 |
| 13:30 | 첫 번째 통합 테스트 (시세 API 연동) | 1, 2, 4 |
| 15:00 | 챗봇 WebSocket 연동 테스트 | 1, 2, 3 |
| 16:30 | 전체 통합 테스트 | 1, 2, 3, 4 |
