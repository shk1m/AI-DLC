import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Bedrock 임베딩 모델 호출 서비스"""

    def __init__(self):
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.model_id = settings.embedding_model_id

    def get_embedding(self, text: str) -> list[float]:
        """텍스트를 벡터 임베딩으로 변환 (Titan Embed Text v2)"""
        # 텍스트 길이 제한 (Titan v2 최대 8192 토큰)
        if len(text) > 20000:
            text = text[:20000]

        try:
            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "inputText": text,
                    "dimensions": settings.embedding_dimension,
                    "normalize": True,
                }),
            )

            result = json.loads(response["body"].read())
            embedding = result["embedding"]
            logger.info(f"임베딩 생성 완료: dim={len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
