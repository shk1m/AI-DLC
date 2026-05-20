#!/bin/bash
# FoodLens Menu Generation Lambda 배포 스크립트
set -e

STACK_NAME="foodlens-menu-generation"
S3_BUCKET="${DEPLOY_BUCKET:-foodlens-lambda-deploy}"
REGION="${AWS_REGION:-us-east-1}"

echo "📦 의존성 설치..."
pip install -r requirements.txt -t ./package --quiet

echo "📁 배포 패키지 생성..."
cd package
zip -r9 ../deployment.zip . -x "*.pyc" "__pycache__/*"
cd ..
zip -g deployment.zip lambda_handler.py
zip -gr deployment.zip app/

echo "🚀 SAM 빌드 & 배포..."
sam build --template-file template.yaml

sam deploy \
  --stack-name $STACK_NAME \
  --region $REGION \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    DbHost=$DB_HOST \
    DbPort=${DB_PORT:-5432} \
    DbName=${DB_NAME:-foodlens} \
    DbUser=$DB_USER \
    DbPassword=$DB_PASSWORD \
    BedrockModelId=${BEDROCK_MODEL_ID:-anthropic.claude-3-5-sonnet-20241022-v2:0} \
  --no-confirm-changeset

echo "✅ 배포 완료!"
echo "Lambda 함수: foodlens-menu-generation"
echo "스케줄: 매일 06:00 UTC"

# 정리
rm -rf package deployment.zip
