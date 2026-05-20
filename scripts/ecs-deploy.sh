#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT="777836495456"
ECR_URI="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/dlc-unit01-frontend:latest"
CLUSTER="dlc-cluster"
SERVICE="dlc-unit01-frontend-svc"
TASK_FAMILY="dlc-unit01-frontend"
LOG_GROUP="/ecs/dlc/unit01/frontend"

echo "=== Step 1: VPC / Subnet 조회 ==="
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text)
echo "VPC: $VPC_ID"

# 서브넷 전체 조회
SUBNET_LIST=$(aws ec2 describe-subnets --region "$REGION" \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "Subnets[*].SubnetId" --output text)
# 탭을 쉼표로
SUBNETS=$(echo "$SUBNET_LIST" | tr '\t' ',')
FIRST_SUBNET=$(echo "$SUBNET_LIST" | awk '{print $1}')
echo "Subnets: $SUBNETS"
echo "First: $FIRST_SUBNET"

echo ""
echo "=== Step 2: 보안 그룹 ==="
SG_NAME="dlc-unit01-frontend-sg"
SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
  SG_ID=$(aws ec2 create-security-group --region "$REGION" \
    --group-name "$SG_NAME" \
    --description "DLC Unit01 Frontend ECS SG" \
    --vpc-id "$VPC_ID" \
    --query "GroupId" --output text)
  echo "SG 생성: $SG_ID"
  aws ec2 authorize-security-group-ingress --region "$REGION" \
    --group-id "$SG_ID" --protocol tcp --port 3000 --cidr 0.0.0.0/0 > /dev/null 2>&1 || true
  aws ec2 authorize-security-group-ingress --region "$REGION" \
    --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 > /dev/null 2>&1 || true
else
  echo "SG 기존: $SG_ID"
fi

echo ""
echo "=== Step 3: ECS Cluster ==="
EXISTING=$(aws ecs describe-clusters --region "$REGION" \
  --clusters "$CLUSTER" \
  --query "clusters[?status=='ACTIVE'].clusterName" \
  --output text 2>/dev/null || true)
if [ -z "$EXISTING" ]; then
  aws ecs create-cluster --region "$REGION" --cluster-name "$CLUSTER" > /dev/null
  echo "Cluster 생성: $CLUSTER"
else
  echo "Cluster 기존: $CLUSTER"
fi

echo ""
echo "=== Step 4: CloudWatch Log Group ==="
aws logs create-log-group --region "$REGION" \
  --log-group-name "$LOG_GROUP" > /dev/null 2>&1 || true
echo "LogGroup: $LOG_GROUP"

echo ""
echo "=== Step 5: Task Execution Role ==="
EXEC_ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/ecsTaskExecutionRole"
ROLE_EXISTS=$(aws iam get-role --role-name ecsTaskExecutionRole \
  --query "Role.Arn" --output text 2>/dev/null || true)
if [ -z "$ROLE_EXISTS" ]; then
  aws iam create-role --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' > /dev/null
  aws iam attach-role-policy --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy > /dev/null
  echo "Role 생성: ecsTaskExecutionRole"
else
  echo "Role 기존: $EXEC_ROLE_ARN"
fi

echo ""
echo "=== Step 6: Task Definition 등록 ==="
TASK_DEF=$(cat <<JSONEOF
{
  "family": "${TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${EXEC_ROLE_ARN}",
  "containerDefinitions": [{
    "name": "frontend",
    "image": "${ECR_URI}",
    "essential": true,
    "portMappings": [{"containerPort": 3000, "protocol": "tcp"}],
    "environment": [
      {"name": "NEXT_PUBLIC_USE_MOCK", "value": "true"},
      {"name": "NODE_ENV", "value": "production"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${LOG_GROUP}",
        "awslogs-region": "${REGION}",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
JSONEOF
)

TASK_DEF_ARN=$(aws ecs register-task-definition --region "$REGION" \
  --cli-input-json "$TASK_DEF" \
  --query "taskDefinition.taskDefinitionArn" --output text)
echo "TaskDef: $TASK_DEF_ARN"

echo ""
echo "=== Step 7: ECS Service 배포 ==="
SVC_STATUS=$(aws ecs describe-services --region "$REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query "services[?status=='ACTIVE'].serviceName" \
  --output text 2>/dev/null || true)

if [ -z "$SVC_STATUS" ]; then
  aws ecs create-service --region "$REGION" \
    --cluster "$CLUSTER" \
    --service-name "$SERVICE" \
    --task-definition "$TASK_DEF_ARN" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
    > /dev/null
  echo "Service 생성 완료"
else
  aws ecs update-service --region "$REGION" \
    --cluster "$CLUSTER" \
    --service "$SERVICE" \
    --task-definition "$TASK_DEF_ARN" \
    --force-new-deployment > /dev/null
  echo "Service 업데이트 완료"
fi

echo ""
echo "=== 배포 완료 — Task 기동 대기 (40초) ==="
sleep 40

TASK_ARN=$(aws ecs list-tasks --region "$REGION" \
  --cluster "$CLUSTER" --service-name "$SERVICE" \
  --query "taskArns[0]" --output text 2>/dev/null || true)

if [ -n "$TASK_ARN" ] && [ "$TASK_ARN" != "None" ]; then
  ENI=$(aws ecs describe-tasks --region "$REGION" \
    --cluster "$CLUSTER" --tasks "$TASK_ARN" \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
    --output text 2>/dev/null || true)
  if [ -n "$ENI" ] && [ "$ENI" != "None" ]; then
    PUBLIC_IP=$(aws ec2 describe-network-interfaces --region "$REGION" \
      --network-interface-ids "$ENI" \
      --query "NetworkInterfaces[0].Association.PublicIp" \
      --output text 2>/dev/null || true)
    echo ""
    echo "========================================================"
    echo "  ✅ 대시보드 접속: http://${PUBLIC_IP}:3000"
    echo "========================================================"
  fi
fi

echo ""
echo "ECS Console:"
echo "  https://console.aws.amazon.com/ecs/v2/clusters/${CLUSTER}/services/${SERVICE}"
