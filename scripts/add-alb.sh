#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT="777836495456"
CLUSTER="dlc-cluster"
SERVICE="dlc-unit01-frontend-svc"
VPC_ID="vpc-0cd044b14fe0b8ab5"
ALB_NAME="dlc-frontend-alb"
TG_NAME="dlc-unit01-frontend-tg"

echo "=== Step 1: 서브넷 조회 (최소 2개 AZ 필요) ==="
SUBNET_LIST=$(aws ec2 describe-subnets --region "$REGION" \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "Subnets[*].SubnetId" --output text)
echo "Subnets: $SUBNET_LIST"

# 최소 2개 서브넷 (다른 AZ)
SUB1=$(echo "$SUBNET_LIST" | awk '{print $1}')
SUB2=$(echo "$SUBNET_LIST" | awk '{print $2}')
echo "Using: $SUB1, $SUB2"

echo ""
echo "=== Step 2: ALB 보안 그룹 (80 인바운드) ==="
ALB_SG_NAME="dlc-alb-sg"
ALB_SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=${ALB_SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)

if [ -z "$ALB_SG_ID" ] || [ "$ALB_SG_ID" = "None" ]; then
  ALB_SG_ID=$(aws ec2 create-security-group --region "$REGION" \
    --group-name "$ALB_SG_NAME" \
    --description "DLC ALB - HTTP 80 from anywhere" \
    --vpc-id "$VPC_ID" \
    --query "GroupId" --output text)
  aws ec2 authorize-security-group-ingress --region "$REGION" \
    --group-id "$ALB_SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 > /dev/null
  echo "ALB SG 생성: $ALB_SG_ID"
else
  echo "ALB SG 기존: $ALB_SG_ID"
fi

echo ""
echo "=== Step 3: ECS Task SG에 ALB SG로부터 3000 인바운드 허용 ==="
ECS_SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=dlc-unit01-frontend-sg" "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[0].GroupId" --output text)
echo "ECS SG: $ECS_SG_ID"

# ALB SG → ECS SG:3000 허용 (이미 있으면 무시)
aws ec2 authorize-security-group-ingress --region "$REGION" \
  --group-id "$ECS_SG_ID" \
  --protocol tcp --port 3000 \
  --source-group "$ALB_SG_ID" > /dev/null 2>&1 || true
echo "  ALB→ECS:3000 인바운드 추가됨"

echo ""
echo "=== Step 4: Target Group 생성 (IP 타입, 포트 3000) ==="
TG_ARN=$(aws elbv2 describe-target-groups --region "$REGION" \
  --names "$TG_NAME" \
  --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || true)

if [ -z "$TG_ARN" ] || [ "$TG_ARN" = "None" ]; then
  TG_ARN=$(aws elbv2 create-target-group --region "$REGION" \
    --name "$TG_NAME" \
    --protocol HTTP --port 3000 \
    --vpc-id "$VPC_ID" \
    --target-type ip \
    --health-check-path "/" \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --query "TargetGroups[0].TargetGroupArn" --output text)
  echo "TG 생성: $TG_ARN"
else
  echo "TG 기존: $TG_ARN"
fi

echo ""
echo "=== Step 5: ALB 생성 ==="
ALB_ARN=$(aws elbv2 describe-load-balancers --region "$REGION" \
  --names "$ALB_NAME" \
  --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || true)

if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
  ALB_ARN=$(aws elbv2 create-load-balancer --region "$REGION" \
    --name "$ALB_NAME" \
    --subnets "$SUB1" "$SUB2" \
    --security-groups "$ALB_SG_ID" \
    --scheme internet-facing \
    --type application \
    --query "LoadBalancers[0].LoadBalancerArn" --output text)
  echo "ALB 생성: $ALB_ARN"
  echo "  프로비저닝 대기 (30초)..."
  sleep 30
else
  echo "ALB 기존: $ALB_ARN"
fi

ALB_DNS=$(aws elbv2 describe-load-balancers --region "$REGION" \
  --load-balancer-arns "$ALB_ARN" \
  --query "LoadBalancers[0].DNSName" --output text)
echo "ALB DNS: $ALB_DNS"

echo ""
echo "=== Step 6: Listener (HTTP:80 → TG:3000) ==="
LISTENER_ARN=$(aws elbv2 describe-listeners --region "$REGION" \
  --load-balancer-arn "$ALB_ARN" \
  --query "Listeners[0].ListenerArn" --output text 2>/dev/null || true)

if [ -z "$LISTENER_ARN" ] || [ "$LISTENER_ARN" = "None" ]; then
  LISTENER_ARN=$(aws elbv2 create-listener --region "$REGION" \
    --load-balancer-arn "$ALB_ARN" \
    --protocol HTTP --port 80 \
    --default-actions "Type=forward,TargetGroupArn=${TG_ARN}" \
    --query "Listeners[0].ListenerArn" --output text)
  echo "Listener 생성: $LISTENER_ARN"
else
  echo "Listener 기존: $LISTENER_ARN"
fi

echo ""
echo "=== Step 7: ECS Service에 ALB Target Group 연결 ==="
# ECS Service를 삭제 후 재생성 (기존 서비스에 LB 추가는 불가)
echo "  기존 서비스 삭제 중..."
aws ecs update-service --region "$REGION" \
  --cluster "$CLUSTER" --service "$SERVICE" \
  --desired-count 0 > /dev/null 2>&1 || true
sleep 5
aws ecs delete-service --region "$REGION" \
  --cluster "$CLUSTER" --service "$SERVICE" \
  --force > /dev/null 2>&1 || true
sleep 5

SUBNETS_CSV=$(echo "$SUBNET_LIST" | tr '\t' ',')
TASK_DEF_ARN=$(aws ecs describe-task-definition --region "$REGION" \
  --task-definition "dlc-unit01-frontend" \
  --query "taskDefinition.taskDefinitionArn" --output text)

echo "  서비스 재생성 (ALB 연결)..."
aws ecs create-service --region "$REGION" \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --task-definition "$TASK_DEF_ARN" \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS_CSV}],securityGroups=[${ECS_SG_ID}],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TG_ARN},containerName=frontend,containerPort=3000" \
  > /dev/null
echo "  Service 재생성 완료 (ALB 연결됨)"

echo ""
echo "=== 배포 완료 — Task 기동 대기 (60초) ==="
sleep 60

echo ""
echo "========================================================"
echo "  ✅ 대시보드 접속 URL:"
echo ""
echo "     http://${ALB_DNS}"
echo ""
echo "========================================================"
echo ""
echo "  (ALB 프로비저닝 완료까지 1~2분 추가 소요될 수 있음)"
echo "  ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/${CLUSTER}/services/${SERVICE}"
