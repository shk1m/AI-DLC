import os


class Settings:
    """Lambda 환경변수 기반 설정"""

    # AWS
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")

    # Bedrock Embedding
    embedding_model_id: str = os.environ.get(
        "EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
    )

    # S3 Vectors
    vector_bucket_name: str = os.environ.get("VECTOR_BUCKET_NAME", "ai-dlc-rag-vectors")
    vector_index_name: str = os.environ.get("VECTOR_INDEX_NAME", "news-embeddings")

    # Embedding dimension (Titan Embed Text v2 = 1024)
    embedding_dimension: int = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))


settings = Settings()
