#!/usr/bin/env bash
# 배포된 ECS task의 공인 IP 조회
set -euo pipefail
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
CLUSTER="dlc-cluster"
SERVICE="dlc-unit01-frontend-svc"

TASK_ARN=$(aws ecs list-tasks \
  --cluster "${CLUSTER}" \
  --service-name "${SERVICE}" \
  --region "${REGION}" \
  --query "taskArns[0]" \
  --output text 2>/dev/null)

if [ -z "${TASK_ARN}" ] || [ "${TASK_ARN}" = "None" ]; then
  echo "Task가 아직 기동되지 않았습니다. 잠시 후 다시 시도하세요."; exit 1
fi

ENI_ID=$(aws ecs describe-tasks \
  --cluster "${CLUSTER}" --tasks "${TASK_ARN}" \
  --region "${REGION}" \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "${ENI_ID}" \
  --region "${REGION}" \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text)

echo ""
echo "  ✅ 대시보드: http://${PUBLIC_IP}:3000"
echo ""
