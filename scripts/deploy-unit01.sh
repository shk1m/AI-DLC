#!/usr/bin/env bash
# ============================================================================
#  deploy-unit01.sh  —  Unit 1 (Frontend) ECS Fargate 배포 스크립트
#  계정: 777836495456 | 리전: us-east-1
#  사용법: bash scripts/deploy-unit01.sh
# ============================================================================
set -euo pipefail

# ─── 변수 ──────────────────────────────────────────────────────────────────
ACCOUNT_ID="777836495456"
REGION="us-east-1"
PROJECT="dlc"
UNIT="unit01"
APP="frontend"

ECR_REPO="${PROJECT}-${UNIT}-${APP}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}"
IMAGE_TAG="latest"

VPC_NAME="${PROJECT}-vpc"
CLUSTER_NAME="${PROJECT}-cluster"
SERVICE_NAME="${PROJECT}-${UNIT}-${APP}-svc"
TASK_FAMILY="${PROJECT}-${UNIT}-${APP}"
CONTAINER_NAME="${APP}"
LOG_GROUP="/ecs/${PROJECT}/${UNIT}/${APP}"

echo "================================================================"
echo "  DLC Unit01 Frontend — ECS Fargate 배포"
echo "  Account : ${ACCOUNT_ID}"
echo "  Region  : ${REGION}"
echo "  Image   : ${ECR_URI}:${IMAGE_TAG}"
echo "================================================================"

# ─── 1. ECR 리포지토리 생성 ─────────────────────────────────────────────────
echo ""
echo "[1/8] ECR 리포지토리 확인/생성..."
aws ecr describe-repositories \
  --repository-names "${ECR_REPO}" \
  --region "${REGION}" > /dev/null 2>&1 \
  || aws ecr create-repository \
       --repository-name "${ECR_REPO}" \
       --region "${REGION}" \
       --image-scanning-configuration scanOnPush=true \
       --encryption-configuration encryptionType=AES256 \
       --output text --query 'repository.repositoryUri'
echo "  ECR repo: ${ECR_URI}"

# ─── 2. Docker 빌드 + ECR Push ───────────────────────────────────────────────
echo ""
echo "[2/8] ECR 로그인..."
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin \
    "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo ""
echo "[3/8] Docker 빌드 + push (linux/amd64)..."
cd "$(dirname "$0")/../frontend"
docker buildx build \
  --platform linux/amd64 \
  -t "${ECR_URI}:${IMAGE_TAG}" \
  --push \
  .
cd - > /dev/null

# ─── 3. 네트워크 조회 ───────────────────────────────────────────────────────
echo ""
echo "[4/8] 네트워크 리소스 조회..."

# Default VPC 사용 (해커톤 모드 — 빠른 시연)
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" \
  --region "${REGION}" \
  --output text)
echo "  VPC: ${VPC_ID} (Default VPC)"

SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=${VPC_ID}" "Name=map-public-ip-on-launch,Values=true" \
  --query "Subnets[*].SubnetId" \
  --region "${REGION}" \
  --output text | tr '\t' ',')
echo "  Subnets: ${SUBNET_IDS}"

# ─── 4. 보안 그룹 ───────────────────────────────────────────────────────────
echo ""
echo "[5/8] 보안 그룹 설정..."

SG_NAME="${PROJECT}-${UNIT}-${APP}-sg"
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[0].GroupId" \
  --region "${REGION}" \
  --output text 2>/dev/null || echo "None")

if [ "${SG_ID}" = "None" ] || [ -z "${SG_ID}" ]; then
  SG_ID=$(aws ec2 create-security-group \
    --group-name "${SG_NAME}" \
    --description "DLC Unit01 Frontend ECS SG" \
    --vpc-id "${VPC_ID}" \
    --region "${REGION}" \
    --query "GroupId" \
    --output text)
  # 인바운드: 80(HTTP) 허용
  aws ec2 authorize-security-group-ingress \
    --group-id "${SG_ID}" \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region "${REGION}" > /dev/null 2>&1 || true
  # 인바운드: 3000(Next.js) 허용
  aws ec2 authorize-security-group-ingress \
    --group-id "${SG_ID}" \
    --protocol tcp --port 3000 --cidr 0.0.0.0/0 \
    --region "${REGION}" > /dev/null 2>&1 || true
fi
echo "  Security Group: ${SG_ID}"

# ─── 5. ECS Cluster ─────────────────────────────────────────────────────────
echo ""
echo "[6/8] ECS Cluster 확인/생성..."
aws ecs describe-clusters \
  --clusters "${CLUSTER_NAME}" \
  --region "${REGION}" \
  --query "clusters[?status=='ACTIVE'].clusterName" \
  --output text | grep -q "${CLUSTER_NAME}" \
  || aws ecs create-cluster \
       --cluster-name "${CLUSTER_NAME}" \
       --region "${REGION}" \
       --capacity-providers FARGATE FARGATE_SPOT \
       --default-capacity-provider-strategy \
         capacityProvider=FARGATE_SPOT,weight=1 \
       --output text > /dev/null
echo "  Cluster: ${CLUSTER_NAME}"

# ─── 6. CloudWatch Log Group ─────────────────────────────────────────────────
aws logs create-log-group \
  --log-group-name "${LOG_GROUP}" \
  --region "${REGION}" > /dev/null 2>&1 || true

# ─── 7. ECS Task Definition ─────────────────────────────────────────────────
echo ""
echo "[7/8] Task Definition 등록..."

# Task Execution Role ARN
EXEC_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole"
# 없으면 생성
aws iam get-role --role-name ecsTaskExecutionRole > /dev/null 2>&1 || \
  aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"ecs-tasks.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }' > /dev/null 2>&1 && \
  aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    > /dev/null 2>&1 || true

TASK_DEF_JSON=$(cat <<EOF
{
  "family": "${TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${EXEC_ROLE_ARN}",
  "containerDefinitions": [
    {
      "name": "${CONTAINER_NAME}",
      "image": "${ECR_URI}:${IMAGE_TAG}",
      "essential": true,
      "portMappings": [
        { "containerPort": 3000, "protocol": "tcp" }
      ],
      "environment": [
        { "name": "NEXT_PUBLIC_USE_MOCK", "value": "true" },
        { "name": "NEXT_PUBLIC_API_BASE_URL", "value": "http://localhost:8000" },
        { "name": "NODE_ENV", "value": "production" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${LOG_GROUP}",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "wget -qO- http://localhost:3000/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 15
      }
    }
  ]
}
EOF
)

TASK_DEF_ARN=$(aws ecs register-task-definition \
  --cli-input-json "${TASK_DEF_JSON}" \
  --region "${REGION}" \
  --query "taskDefinition.taskDefinitionArn" \
  --output text)
echo "  Task Def: ${TASK_DEF_ARN}"

# ─── 8. ECS Service 생성/업데이트 ────────────────────────────────────────────
echo ""
echo "[8/8] ECS Service 배포..."

FIRST_SUBNET=$(echo "${SUBNET_IDS}" | cut -d',' -f1)

SERVICE_EXISTS=$(aws ecs describe-services \
  --cluster "${CLUSTER_NAME}" \
  --services "${SERVICE_NAME}" \
  --region "${REGION}" \
  --query "services[?status=='ACTIVE'].serviceName" \
  --output text 2>/dev/null || echo "")

if [ -z "${SERVICE_EXISTS}" ]; then
  aws ecs create-service \
    --cluster "${CLUSTER_NAME}" \
    --service-name "${SERVICE_NAME}" \
    --task-definition "${TASK_DEF_ARN}" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
      subnets=[${SUBNET_IDS}],
      securityGroups=[${SG_ID}],
      assignPublicIp=ENABLED
    }" \
    --region "${REGION}" \
    --output text > /dev/null
  echo "  Service 생성 완료: ${SERVICE_NAME}"
else
  aws ecs update-service \
    --cluster "${CLUSTER_NAME}" \
    --service "${SERVICE_NAME}" \
    --task-definition "${TASK_DEF_ARN}" \
    --force-new-deployment \
    --region "${REGION}" \
    --output text > /dev/null
  echo "  Service 업데이트 완료: ${SERVICE_NAME}"
fi

echo ""
echo "================================================================"
echo "  배포 완료! Task 기동 대기 중 (~30초)..."
echo "================================================================"
sleep 35

# 공인 IP 조회
TASK_ARN=$(aws ecs list-tasks \
  --cluster "${CLUSTER_NAME}" \
  --service-name "${SERVICE_NAME}" \
  --region "${REGION}" \
  --query "taskArns[0]" \
  --output text 2>/dev/null || echo "")

if [ -n "${TASK_ARN}" ] && [ "${TASK_ARN}" != "None" ]; then
  ENI_ID=$(aws ecs describe-tasks \
    --cluster "${CLUSTER_NAME}" \
    --tasks "${TASK_ARN}" \
    --region "${REGION}" \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
    --output text 2>/dev/null || echo "")

  if [ -n "${ENI_ID}" ] && [ "${ENI_ID}" != "None" ]; then
    PUBLIC_IP=$(aws ec2 describe-network-interfaces \
      --network-interface-ids "${ENI_ID}" \
      --region "${REGION}" \
      --query "NetworkInterfaces[0].Association.PublicIp" \
      --output text 2>/dev/null || echo "pending")
    echo ""
    echo "  ✅ 대시보드 접속 URL: http://${PUBLIC_IP}:3000"
    echo ""
  fi
fi

echo "  ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/${CLUSTER_NAME}/services/${SERVICE_NAME}"
echo ""
echo "  ⚠️  Task가 아직 starting 상태라면 2~3분 후 다시 IP를 조회하세요:"
echo "  bash scripts/get-url.sh"
