"""
S3 Vectors RAG 검색 + Bedrock Claude 응답 생성 서비스

사용법:
    from app.rag_query_service import RAGQueryService
    
    rag = RAGQueryService()
    answer = rag.query("고등어 가격이 왜 올랐나요?")
    print(answer["answer"])
    print(answer["sources"])
"""
import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


class RAGQueryService:
    """S3 Vectors RAG + Bedrock Claude 질의응답 서비스"""

    def __init__(self):
        self._bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self._s3vectors = boto3.client("s3vectors", region_name=settings.aws_region)
        self.embedding_model_id = settings.embedding_model_id
        self.llm_model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    def query(self, question: str, top_k: int = 5) -> dict:
        """
        RAG 파이프라인 실행
        1. 질문 임베딩
        2. S3 Vectors에서 유사 문서 검색
        3. 검색 결과를 컨텍스트로 Claude에 전달
        4. 답변 반환
        """
        # Step 1: 질문을 벡터로 변환
        query_embedding = self._get_embedding(question)

        # Step 2: S3 Vectors에서 유사 문서 검색
        search_results = self._search_similar(query_embedding, top_k=top_k)

        if not search_results:
            return {
                "answer": "관련 정보를 찾을 수 없습니다.",
                "sources": [],
                "confidence": 0.0,
            }

        # Step 3: 검색 결과를 컨텍스트로 구성
        context = self._build_context(search_results)

        # Step 4: Claude에 질문 + 컨텍스트 전달하여 답변 생성
        answer = self._generate_answer(question, context)

        return {
            "answer": answer,
            "sources": [
                {
                    "title": r.get("metadata", {}).get("title", ""),
                    "url": r.get("metadata", {}).get("url", ""),
                    "source": r.get("metadata", {}).get("source", ""),
                    "published_at": r.get("metadata", {}).get("published_at", ""),
                    "score": r.get("score"),
                }
                for r in search_results
            ],
            "confidence": search_results[0].get("score", 0) if search_results else 0,
        }

    def _get_embedding(self, text: str) -> list[float]:
        """텍스트를 벡터 임베딩으로 변환"""
        response = self._bedrock.invoke_model(
            modelId=self.embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": text,
                "dimensions": settings.embedding_dimension,
                "normalize": True,
            }),
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def _search_similar(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        """S3 Vectors에서 유사 벡터 검색"""
        response = self._s3vectors.query_vectors(
            vectorBucketName=settings.vector_bucket_name,
            indexName=settings.vector_index_name,
            queryVector={"float32": embedding},
            topK=top_k,
            returnMetadata=True,
        )

        results = []
        for item in response.get("vectors", []):
            results.append({
                "key": item["key"],
                "score": item.get("distance"),
                "metadata": item.get("metadata", {}),
            })

        logger.info(f"유사 문서 검색: {len(results)}건")
        return results

    def _build_context(self, search_results: list[dict]) -> str:
        """검색 결과를 LLM 컨텍스트 문자열로 변환"""
        context_parts = []

        for i, result in enumerate(search_results, 1):
            meta = result.get("metadata", {})
            part = f"[문서 {i}]\n"
            part += f"제목: {meta.get('title', 'N/A')}\n"
            if meta.get("summary"):
                part += f"요약: {meta['summary']}\n"
            if meta.get("content"):
                part += f"본문: {meta['content']}\n"
            if meta.get("published_at"):
                part += f"발행일: {meta['published_at']}\n"
            if meta.get("source"):
                part += f"출처: {meta['source']}\n"
            if meta.get("keywords"):
                part += f"키워드: {meta['keywords']}\n"
            context_parts.append(part)

        return "\n---\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """Claude에 RAG 컨텍스트와 질문을 전달하여 답변 생성"""
        system_prompt = """당신은 농수산물 시장 전문 AI 어시스턴트입니다.
아래 제공된 뉴스 기사 정보를 기반으로 사용자의 질문에 답변합니다.

규칙:
1. 제공된 문서 정보에 기반하여 답변합니다.
2. 문서에 없는 내용은 추측하지 않고 "해당 정보가 없습니다"라고 답합니다.
3. 답변 형식: [분석] → [추천] → [근거] 구조로 응답합니다.
4. 출처를 명시합니다.
5. 한국어로 답변합니다."""

        user_prompt = f"""아래 참고 문서를 기반으로 질문에 답변해주세요.

## 참고 문서
{context}

## 질문
{question}

위 문서 정보를 기반으로 답변해주세요."""

        response = self._bedrock.converse(
            modelId=self.llm_model_id,
            system=[{"text": system_prompt}],
            messages=[
                {"role": "user", "content": [{"text": user_prompt}]}
            ],
            inferenceConfig={"maxTokens": 2048, "temperature": 0.3},
        )

        return response["output"]["message"]["content"][0]["text"]
