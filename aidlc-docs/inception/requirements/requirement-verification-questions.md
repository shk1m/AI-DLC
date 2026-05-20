# 요구사항 명확화 질문

아래 질문에 답변해 주세요. 각 질문의 [Answer]: 태그 뒤에 선택지 문자를 입력해 주세요.
선택지 중 맞는 것이 없으면 X를 선택하고 설명을 추가해 주세요.

---

## Question 1
팀원 4명의 기술 스택 역량은 어떻게 구성되어 있나요?

A) 프론트엔드 2명 + 백엔드 1명 + AI/데이터 1명
B) 프론트엔드 1명 + 백엔드 2명 + AI/데이터 1명
C) 프론트엔드 1명 + 백엔드 1명 + AI/데이터 1명 + 풀스택 1명
D) 모두 풀스택 개발자 (역할 유동적 배분 가능)
E) 프론트엔드 1명 + 백엔드 1명 + AI/데이터 2명
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 2
AWS 계정 및 서비스 사용 범위는 어떻게 되나요?

A) AWS 프리티어 계정만 사용 가능 (비용 제한 있음)
B) 사내 AWS 계정 사용 가능 (합리적 범위 내 비용 허용)
C) AWS 서비스 제한 없이 사용 가능 (해커톤 전용 계정 제공)
D) AWS 사용 불가 - 로컬 또는 다른 클라우드만 가능
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 3
AI/LLM 서비스로 어떤 것을 사용할 수 있나요?

A) Amazon Bedrock (Claude, Titan 등) 사용 가능
B) OpenAI API (GPT-4) 사용 가능
C) Google Gemini API 사용 가능
D) 여러 LLM 혼합 사용 가능 (Bedrock + OpenAI 등)
E) 사내 자체 LLM 또는 특정 모델만 사용 가능
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
데이터 소스 접근 방식에 대해 어떤 전략을 선호하시나요?

A) 실제 공공 API (KAMIS 농산물유통정보, 공공데이터포털 등)를 최대한 활용하고, 불가능한 부분만 Mock 데이터
B) 시연 안정성을 위해 전체 Mock/샘플 데이터로 구성하되, 실제 API 연동 가능한 구조로 설계
C) 핵심 데이터(가격 시세)는 실제 API, 부가 데이터(뉴스, 레시피)는 Mock 데이터
D) 크롤링 중심으로 실시간 데이터 수집 (뉴스, 시세 사이트)
X) Other (please describe after [Answer]: tag below)

[Answer]: A, D

---

## Question 5
해커톤 시연 시 가장 중요하게 보여주고 싶은 핵심 기능 우선순위는? (1순위 선택)

A) 실시간 시세 대시보드 + 가격 이상치(Spike) 뉴스 매핑 (시각적 임팩트)
B) AI 챗봇의 대체 식자재 추천 및 레시피 제안 (AI 활용도)
C) 식수별 원가 시뮬레이션 및 비용 절감 전략 (비즈니스 가치)
D) 전체 기능을 고르게 구현 (완성도 중시)
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 6
프론트엔드 배포 및 시연 환경은 어떻게 하실 건가요?

A) Vercel/Netlify 등 무료 호스팅에 배포하여 URL로 시연
B) AWS Amplify 또는 S3+CloudFront로 배포
C) 로컬 개발 서버(localhost)에서 직접 시연
D) EC2 인스턴스에 전체 스택 배포
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 7
뉴스 크롤링 대상을 어디로 한정할까요?

A) 네이버 뉴스 검색 API (안정적, API 키 필요)
B) 농림축산식품부/해양수산부 공식 보도자료
C) 주요 경제지 RSS 피드 (한경, 매경 등)
D) 여러 소스 혼합 (네이버 API + 공식 보도자료)
E) Mock 뉴스 데이터로 시연하고 구조만 실제 연동 가능하게
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 8
RAG(Retrieval-Augmented Generation) 구현 수준은 어느 정도를 목표로 하시나요?

A) 완전한 벡터 DB 기반 RAG (Pinecone, OpenSearch 등 활용)
B) 간이 RAG (임베딩 + 인메모리 벡터 검색, FAISS 등)
C) 프롬프트 엔지니어링 기반 컨텍스트 주입 (RAG 유사 효과, 구현 간소화)
D) Knowledge Base 서비스 활용 (Amazon Bedrock Knowledge Bases 등)
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 9
온톨로지/지식 그래프 구현 수준은?

A) 완전한 그래프 DB (Neptune, Neo4j) 기반 온톨로지
B) JSON-LD 또는 RDF 기반 경량 온톨로지 + 관계형 DB
C) 계층적 분류 체계(Taxonomy)만 구현하고 온톨로지는 설계 문서로 제시
D) 시연용 하드코딩된 관계 데이터 + 향후 그래프 DB 마이그레이션 계획
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10
백엔드 기술 스택 선호도는?

A) Node.js (Express/Fastify) - 프론트엔드와 언어 통일
B) Python (FastAPI) - AI/ML 라이브러리 활용 용이
C) 서버리스 (AWS Lambda + API Gateway) - 인프라 관리 최소화
D) Next.js API Routes로 백엔드 통합 - 별도 서버 없이 구현
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 11: Security Extensions
이 프로젝트에 보안 확장 규칙을 적용할까요?

A) Yes — 모든 보안 규칙을 블로킹 제약으로 적용 (프로덕션 수준 애플리케이션에 권장)
B) No — 보안 규칙 생략 (PoC, 프로토타입, 실험적 프로젝트에 적합)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 12: Property-Based Testing Extension
이 프로젝트에 속성 기반 테스팅(PBT) 규칙을 적용할까요?

A) Yes — 모든 PBT 규칙을 블로킹 제약으로 적용
B) Partial — 순수 함수와 직렬화 라운드트립에만 PBT 규칙 적용
C) No — PBT 규칙 생략 (단순 CRUD, UI 전용 프로젝트에 적합)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 13
서비스 이름 방향성에 대한 선호가 있으신가요?

A) 한국어 이름 (예: 식탁지기, 장보기AI 등 친근한 느낌)
B) 영어 이름 (예: FoodPulse, MenuMind 등 글로벌/테크 느낌)
C) 한영 혼합 (예: 식재AI, Smart식단 등)
D) 창의적/조어 (예: 밥심, 식견 등 언어유희 포함)
E) AI가 자유롭게 제안해 주세요
X) Other (please describe after [Answer]: tag below)

[Answer]: E

---
