"""
로컬 테스트 스크립트 - Lambda 핸들러를 로컬에서 실행
사용법: python test_local.py

사전 조건:
1. PostgreSQL 실행 중 (Unit 4 크롤링 DB)
2. 환경변수 설정 또는 .env 파일
3. AWS 자격증명 설정 (Bedrock 호출용)
"""
import os
import json

# 환경변수 설정 (로컬 테스트용)
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "ai-dlc")
os.environ.setdefault("DB_USER", "admin")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

from lambda_handler import handler


def main():
    # EventBridge에서 오는 것과 유사한 이벤트
    event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        # 특정 날짜 테스트 시 아래 주석 해제
        # "target_date": "2026-05-20"
    }

    context = None  # Lambda context (로컬에서는 불필요)

    result = handler(event, context)
    print("\n" + "=" * 60)
    print("실행 결과:")
    print("=" * 60)
    print(json.dumps(json.loads(result["body"]), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
