"""
AWS Lambda 핸들러 - 뉴스 기사 RAG 적재 (S3 Vectors)
S3에 뉴스 기사가 업로드되면 트리거되어 Bedrock 임베딩 후 S3 Vectors에 저장

트리거: S3 PutObject (ai-dlc-news-articles 버킷)
입력: S3에 업로드된 뉴스 기사 (JSON 형식)
출력: S3 Vectors (ai-dlc-rag-vectors/news-embeddings)에 벡터 적재
"""
import json
import logging
import urllib.parse

import boto3

from app.config import settings
from app.embedding_service import EmbeddingService
from app.s3vectors_client import S3VectorsClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handler(event, context):
    """Lambda 엔트리포인트 - S3 이벤트 트리거"""
    logger.info(f"Lambda 실행 시작: {json.dumps(event, default=str)}")

    embedding_service = EmbeddingService()
    vectors_client = S3VectorsClient()
    results = []

    for record in event.get("Records", []):
        try:
            # S3 이벤트에서 버킷/키 추출
            bucket = record["s3"]["bucket"]["name"]
            key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

            logger.info(f"처리 대상: s3://{bucket}/{key}")

            # S3에서 기사 파일 읽기
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            article = json.loads(content)

            # 임베딩할 텍스트 구성
            text_to_embed = _build_embedding_text(article)

            # Bedrock으로 임베딩 생성
            embedding = embedding_service.get_embedding(text_to_embed)

            # 메타데이터 구성 (S3 Vectors에 저장)
            metadata = _build_metadata(article)

            # S3 Vectors에 저장
            doc_id = article.get("id", key.replace("/", "_"))
            vectors_client.put_vector(
                doc_id=doc_id,
                embedding=embedding,
                metadata=metadata,
            )

            results.append({
                "key": key,
                "status": "success",
                "doc_id": doc_id,
            })
            logger.info(f"적재 완료: {key} -> doc_id={doc_id}")

        except Exception as e:
            logger.error(f"처리 실패: {key} - {e}", exc_info=True)
            results.append({
                "key": key,
                "status": "error",
                "error": str(e),
            })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": len(results),
            "results": results,
        }, ensure_ascii=False),
    }


def _build_embedding_text(article: dict) -> str:
    """기사 데이터에서 임베딩할 텍스트 구성"""
    parts = []

    if article.get("title"):
        parts.append(f"제목: {article['title']}")
    if article.get("summary"):
        parts.append(f"요약: {article['summary']}")
    if article.get("content"):
        parts.append(f"본문: {article['content']}")
    if article.get("keywords"):
        parts.append(f"키워드: {', '.join(article['keywords'])}")
    if article.get("category"):
        parts.append(f"카테고리: {article['category']}")

    return "\n".join(parts)


def _build_metadata(article: dict) -> dict:
    """S3 Vectors에 저장할 메타데이터 구성"""
    metadata = {}

    if article.get("title"):
        metadata["title"] = article["title"]
    if article.get("summary"):
        metadata["summary"] = article["summary"]
    if article.get("content"):
        # content는 길 수 있으므로 앞부분만 저장
        metadata["content"] = article["content"][:2000]
    if article.get("keywords"):
        metadata["keywords"] = json.dumps(article["keywords"], ensure_ascii=False)
    if article.get("category"):
        metadata["category"] = article["category"]
    if article.get("source"):
        metadata["source"] = article["source"]
    if article.get("url"):
        metadata["url"] = article["url"]
    if article.get("published_at"):
        metadata["published_at"] = article["published_at"]
    if article.get("related_items"):
        metadata["related_items"] = json.dumps(article["related_items"], ensure_ascii=False)

    return metadata
