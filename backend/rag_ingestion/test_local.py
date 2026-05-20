"""
로컬 테스트 - S3 이벤트를 시뮬레이션하여 RAG 적재 테스트

사전 조건:
1. AWS 자격증명 설정
2. S3 Vectors 버킷/인덱스 생성 완료
3. Bedrock Titan Embed 모델 접근 가능
"""
import os
import json

# 환경변수 설정
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("VECTOR_BUCKET_NAME", "ai-dlc-rag-vectors")
os.environ.setdefault("VECTOR_INDEX_NAME", "news-embeddings")
os.environ.setdefault("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

from lambda_handler import handler


def main():
    import boto3

    # 1. 테스트용 기사를 S3에 업로드
    s3 = boto3.client("s3")
    sample_article = {
        "id": "test-001",
        "title": "고등어 가격 급등, 한 달 새 30% 상승",
        "content": "최근 고등어 가격이 급등하고 있다. 기상 악화로 인한 어획량 감소가 주요 원인으로 분석된다. 수산시장 관계자는 당분간 가격 상승세가 이어질 것으로 전망했다.",
        "summary": "기상 악화로 고등어 어획량 감소, 가격 30% 급등",
        "keywords": ["고등어", "수산물", "가격급등", "어획량"],
        "category": "수산물",
        "source": "네이버뉴스",
        "url": "https://news.example.com/article/001",
        "published_at": "2026-05-20T09:00:00Z",
        "related_items": ["고등어", "삼치", "갈치"],
    }

    s3.put_object(
        Bucket="ai-dlc-news-articles",
        Key="test/sample-article.json",
        Body=json.dumps(sample_article, ensure_ascii=False),
        ContentType="application/json",
    )
    print("✅ 테스트 기사 S3 업로드 완료")

    # 2. Lambda 실행 (S3 이벤트 시뮬레이션)
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "ai-dlc-news-articles"},
                    "object": {"key": "test/sample-article.json"},
                }
            }
        ]
    }

    result = handler(event, None)
    print("\n" + "=" * 60)
    print("적재 결과:")
    print("=" * 60)
    print(json.dumps(json.loads(result["body"]), indent=2, ensure_ascii=False))

    # 3. 유사도 검색 테스트
    print("\n" + "=" * 60)
    print("유사도 검색 테스트:")
    print("=" * 60)

    from app.embedding_service import EmbeddingService
    from app.s3vectors_client import S3VectorsClient

    embedding_service = EmbeddingService()
    vectors_client = S3VectorsClient()

    query_embedding = embedding_service.get_embedding("고등어 가격이 왜 올랐나요?")
    results = vectors_client.query_similar(query_embedding, top_k=3)

    for r in results:
        print(f"  - [{r.get('score', 0):.4f}] {r.get('metadata', {}).get('title', 'N/A')}")


if __name__ == "__main__":
    main()
