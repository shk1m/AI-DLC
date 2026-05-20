import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


class S3VectorsClient:
    """S3 Vectors 벡터 저장/검색 클라이언트"""

    def __init__(self):
        self._client = boto3.client("s3vectors", region_name=settings.aws_region)
        self.bucket_name = settings.vector_bucket_name
        self.index_name = settings.vector_index_name

    def put_vector(self, doc_id: str, embedding: list[float], metadata: dict) -> str:
        """벡터를 S3 Vectors에 저장"""
        try:
            response = self._client.put_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                vectors=[
                    {
                        "key": doc_id,
                        "data": {"float32": embedding},
                        "metadata": metadata,
                    }
                ],
            )
            logger.info(f"벡터 저장 완료: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"벡터 저장 실패: {doc_id} - {e}")
            raise

    def query_similar(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        """벡터 유사도 검색"""
        try:
            response = self._client.query_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                queryVector={"float32": embedding},
                topK=top_k,
                includeMetadata=True,
            )

            results = []
            for item in response.get("vectors", []):
                results.append({
                    "key": item["key"],
                    "score": item.get("distance"),
                    "metadata": item.get("metadata", {}),
                })

            logger.info(f"유사도 검색 완료: {len(results)}건")
            return results
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            raise

    def get_vector(self, doc_id: str) -> dict:
        """특정 벡터 조회"""
        try:
            response = self._client.get_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                keys=[doc_id],
                includeMetadata=True,
            )
            vectors = response.get("vectors", [])
            return vectors[0] if vectors else None
        except Exception as e:
            logger.error(f"벡터 조회 실패: {doc_id} - {e}")
            raise

    def delete_vector(self, doc_id: str):
        """벡터 삭제"""
        try:
            self._client.delete_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                keys=[doc_id],
            )
            logger.info(f"벡터 삭제 완료: {doc_id}")
        except Exception as e:
            logger.error(f"벡터 삭제 실패: {doc_id} - {e}")
            raise
