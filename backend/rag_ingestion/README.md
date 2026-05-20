# FoodLens - 뉴스 RAG 적재 Lambda (Unit 3)

S3에 뉴스 기사가 업로드되면 Bedrock 임베딩 모델로 벡터화하여 S3 Vectors에 적재하는 Lambda 함수입니다.

## 아키텍처

```
Unit 4 크롤링 → S3 (ai-dlc-news-articles/*.json)
                    ↓ S3 Event Trigger
              Lambda (rag-ingestion)
                    ↓ 임베딩 요청
              Bedrock (Titan Embed Text v2, 1024 dim)
                    ↓ 벡터 저장
              S3 Vectors (ai-dlc-rag-vectors/news-embeddings)
```

## AWS 리소스

| 리소스 | 이름 | 용도 |
|--------|------|------|
| S3 Bucket | `ai-dlc-news-articles` | 뉴스 기사 원본 저장 (트리거) |
| S3 Vector Bucket | `ai-dlc-rag-vectors` | 벡터 저장소 |
| S3 Vector Index | `news-embeddings` | 뉴스 벡터 인덱스 (1024 dim, cosine) |
| Bedrock Model | `amazon.titan-embed-text-v2:0` | 임베딩 모델 |

## S3 기사 JSON 형식

Unit 4가 크롤링 후 S3에 업로드하는 형식:

```json
{
  "id": "unique-article-id",
  "title": "고등어 가격 급등, 한 달 새 30% 상승",
  "content": "기사 본문 전체...",
  "summary": "기사 요약 (선택)",
  "keywords": ["고등어", "수산물", "가격급등"],
  "category": "수산물",
  "source": "네이버뉴스",
  "url": "https://news.example.com/article/001",
  "published_at": "2026-05-20T09:00:00Z",
  "related_items": ["고등어", "삼치"]
}
```

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| AWS_REGION | AWS 리전 | us-east-1 |
| VECTOR_BUCKET_NAME | S3 Vectors 버킷명 | ai-dlc-rag-vectors |
| VECTOR_INDEX_NAME | 벡터 인덱스명 | news-embeddings |
| EMBEDDING_MODEL_ID | Bedrock 임베딩 모델 | amazon.titan-embed-text-v2:0 |
| EMBEDDING_DIMENSION | 벡터 차원 | 1024 |

## 로컬 테스트

```bash
cd rag_ingestion
pip install -r requirements.txt
python test_local.py
```

## 배포

```bash
sam build --template-file template.yaml
sam deploy --guided
```
