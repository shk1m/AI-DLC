# Unit of Work Plan

## 개요
7개 Epic을 4명 팀원이 병렬 개발 가능한 단위(Unit of Work)로 분해합니다.
모놀리식 FastAPI 구조이므로 Unit = 논리적 모듈(팀원 담당 영역)입니다.

---

## Plan Steps

- [x] Step 1: 팀원 역할 기반 Unit 분해
- [x] Step 2: Unit별 책임 범위 정의
- [x] Step 3: Unit 간 의존성 매핑
- [x] Step 4: Story-Unit 매핑
- [x] Step 5: 코드 조직 전략 정의

---

## 질문 (Unit Decomposition Questions)

---

### Question 1
Unit 분해 기준은 팀원 역할(프론트/백엔드/AI/풀스택) 기반으로 할까요, 아니면 기능 도메인(시세/챗봇/레시피) 기반으로 할까요?

A) 팀원 역할 기반 (프론트엔드 Unit, 백엔드 Unit, AI Unit, 통합 Unit)
B) 기능 도메인 기반 (시세 Unit, 챗봇 Unit, 레시피 Unit, 인프라 Unit)
C) 혼합 (프론트엔드는 1 Unit, 백엔드는 도메인별 분리)
D) AI가 최적으로 판단
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2
프론트엔드와 백엔드 간 API 계약(Contract)은 어떻게 관리할까요?

A) API 스펙을 먼저 정의하고 각자 독립 개발 (Contract-First)
B) 백엔드가 먼저 구현하고 프론트가 맞춤 (Backend-First)
C) Mock API로 프론트 먼저 개발, 이후 실제 API 연결 (Frontend-First)
D) 동시 개발하면서 수시로 싱크 (Iterative)
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---
