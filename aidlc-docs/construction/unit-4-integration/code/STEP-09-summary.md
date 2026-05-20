# Step 9 Summary — S3 Client (DL-04)

**Phase**: D  
**NFR**: AVAIL-03, MAINT-04

## Created files
- `backend/app/adapters/s3_client.py` — `BaseS3Client` (ABC), `LocalMockS3Client`, `AioBotoS3Client`, factory
- `backend/tests/unit/test_s3_client.py` — 11 tests (mock + factory)

## Highlights
- **Strategy pattern**: ABC로 인터페이스 통일, mock/real 동등 호환
- **Mock 모드 자동 fallback**: `USE_MOCK=true` 또는 자격증명 없으면 자동 LocalMockS3Client
- **Path traversal 방어**: `..` 포함 키 거부 (S3ClientError)
- **메타데이터 보존**: mock에서도 `*.meta.json`으로 별도 저장, list 시 제외
- **aioboto3 lazy import**: 패키지 미설치 시에도 mock 모드 동작
- **`s3://bucket/key` URI 헬퍼**: Bedrock KB 동기화 시 사용
