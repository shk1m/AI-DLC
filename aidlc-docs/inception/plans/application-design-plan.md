# Application Design Plan

## 개요
요구사항과 유저 스토리를 기반으로 애플리케이션 컴포넌트를 식별하고 서비스 레이어를 설계합니다.

---

## Design Steps

- [x] Step 1: 프론트엔드 컴포넌트 식별 (Next.js 14)
- [x] Step 2: 백엔드 서비스 컴포넌트 식별 (FastAPI + LangChain)
- [x] Step 3: 데이터 레이어 컴포넌트 식별 (Neptune, RDS, Bedrock KB)
- [x] Step 4: 외부 연동 컴포넌트 식별 (API, 크롤러)
- [x] Step 5: 서비스 오케스트레이션 설계
- [x] Step 6: 컴포넌트 의존성 매핑
- [x] Step 7: 통합 설계 문서 생성

---

## 질문 (Application Design Questions)

아래 질문에 [Answer]: 태그 뒤에 선택지를 입력해 주세요.

---

### Question 1
프론트엔드와 백엔드 간 통신 패턴은?

A) REST API 단일 통신 (모든 요청이 REST)
B) REST + WebSocket 혼합 (챗봇은 WebSocket 스트리밍, 나머지는 REST)
C) REST + SSE(Server-Sent Events) 혼합 (챗봇은 SSE 스트리밍)
D) GraphQL 기반 (유연한 쿼리)
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 2
백엔드 서비스 구조는 어떤 패턴을 선호하시나요?

A) 모놀리식 FastAPI (단일 서버에 모든 엔드포인트)
B) 도메인별 라우터 분리 (단일 서버, 내부 모듈화)
C) 마이크로서비스 (시세 서비스, 챗봇 서비스, 크롤링 서비스 분리)
D) 서버리스 + FastAPI 혼합 (크롤링은 Lambda, 나머지는 FastAPI)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 3
데이터 접근 패턴은?

A) Repository 패턴 (각 데이터 소스별 Repository 클래스)
B) ORM 직접 사용 (SQLAlchemy 등으로 직접 쿼리)
C) 서비스 레이어에서 직접 데이터 접근 (별도 추상화 없음)
D) CQRS 패턴 (읽기/쓰기 분리)
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 4
LangChain 체인 구성 방식은?

A) 단일 체인 (하나의 범용 체인으로 모든 질문 처리)
B) 멀티 체인 + 라우터 (질문 유형별 전문 체인 분기)
C) Agent 기반 (LangChain Agent가 도구를 선택하여 처리)
D) RAG 체인 + 도구 체인 분리 (지식 검색과 계산/분석 분리)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---
