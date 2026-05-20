import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """Amazon Bedrock Claude 호출 클라이언트"""

    def __init__(self):
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.model_id = settings.bedrock_model_id

    def invoke(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        """Bedrock Claude Converse API 호출"""
        try:
            response = self._client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                },
            )
            result = response["output"]["message"]["content"][0]["text"]
            logger.info(f"Bedrock 호출 성공: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Bedrock 호출 실패: {e}")
            raise


bedrock_client = BedrockClient()
