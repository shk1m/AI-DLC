# Story Generation Plan

## 개요
이 문서는 유저 스토리 생성을 위한 계획과 질문을 포함합니다.
아래 질문에 답변 후 승인해 주시면 스토리를 생성합니다.

---

## Story Generation Steps

- [x] Step 1: 페르소나 정의 (영양사, MD, 바이어 상세 프로필)
- [x] Step 2: 에픽(Epic) 구조화 (기능 요구사항 기반)
- [x] Step 3: 유저 스토리 작성 (INVEST 기준, 수용 기준 포함)
- [x] Step 4: 스토리 우선순위 매핑 (해커톤 시간 제약 반영)
- [x] Step 5: 페르소나-스토리 매핑 검증

---

## 질문 (Story Planning Questions)

아래 질문에 [Answer]: 태그 뒤에 선택지를 입력해 주세요.

---

### Question 1
유저 스토리 분류(Breakdown) 방식은 어떤 것을 선호하시나요?

A) 페르소나 기반 - 영양사/MD/바이어별로 스토리 그룹화
B) 기능 기반 - 대시보드/챗봇/시뮬레이션 등 기능별 그룹화
C) 유저 저니 기반 - 사용자 워크플로우 흐름 순서로 구성
D) 에픽 기반 - 대주제(Epic) 아래 세부 스토리 계층 구조
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 2
각 페르소나의 전문성 수준과 기술 친숙도를 어떻게 설정할까요?

A) 모두 IT에 익숙한 전문가 (복잡한 UI/기능 허용)
B) 기본적인 웹 사용 가능, 전문 도구 경험 있음 (중간 복잡도)
C) IT에 익숙하지 않은 현장 실무자 (최대한 단순한 UX 필요)
D) 페르소나별 차등 설정 (영양사: 중간, MD: 높음, 바이어: 높음)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 3
수용 기준(Acceptance Criteria) 작성 수준은?

A) 간결한 Given-When-Then 형식 (핵심 시나리오만)
B) 상세한 Given-When-Then + 엣지 케이스 포함
C) 체크리스트 형식 (구현 확인 항목 나열)
D) BDD 스타일 (Gherkin 문법, 자동화 테스트 연계 가능)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 4
해커톤 시연을 고려할 때, 스토리 우선순위 기준은?

A) 시각적 임팩트 우선 (심사위원에게 보여줄 수 있는 것 먼저)
B) 기술 복잡도 우선 (AI/데이터 파이프라인 등 기술 점수 높은 것 먼저)
C) 엔드투엔드 완성도 우선 (하나의 시나리오를 완전히 동작하게)
D) 균형 배분 (모든 기능을 최소 수준으로 구현 후 점진적 개선)
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 5
챗봇 사용자 시나리오에서 AI 응답의 톤앤매너는?

A) 전문적/격식체 (보고서 스타일, "~입니다", "~됩니다")
B) 친근한 존댓말 (대화형, "~해요", "~드릴게요")
C) 간결한 데이터 중심 (수치와 팩트 위주, 최소한의 설명)
D) 컨설턴트 스타일 (분석 + 추천 + 근거를 구조화하여 제시)
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

### Question 6
원문에서 제시된 4개 유저 케이스 외에 추가로 강조하고 싶은 시나리오가 있나요?

A) 현재 제시된 US-01~US-07으로 충분
B) 가격 알림/모니터링 시나리오 추가 (특정 품목 가격이 임계치 초과 시 알림)
C) 주간/월간 리포트 자동 생성 시나리오 추가
D) 공급업체 비교/추천 시나리오 추가
E) 시즌별 메뉴 자동 계획 시나리오 추가
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 7
스토리 규모(크기)는 어느 정도로 분할할까요?

A) 대형 스토리 (에픽 수준, 5~10개) - 해커톤 시간 고려 큰 단위로
B) 중형 스토리 (15~20개) - 기능 단위로 적절히 분할
C) 소형 스토리 (25~30개) - 세밀하게 분할하여 진행 추적 용이
D) 해커톤 환경에 맞게 AI가 적절히 판단
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---
