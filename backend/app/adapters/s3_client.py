"""
S3 client adapter — DL-04.

NFR Mapping:
- AVAIL-03: 외부 의존성 격리, mock 모드 지원
- MAINT-04: 명시적 인터페이스
- BR-06-1: URL 중복 방지를 위한 키 일관성

USE_MOCK=true → `./.mock-s3/{bucket}/{key}` 로컬 파일시스템 백엔드 사용 (시연/CI 안전성).

Usage:
    s3 = get_s3_client()
    await s3.upload_json("news/2026-05-20/abc.json", article.model_dump())
    blob = await s3.download("news/2026-05-20/abc.json")
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class S3ClientError(RuntimeError):
    """모든 S3 어댑터 예외의 베이스."""


class S3ObjectNotFoundError(S3ClientError):
    """key 미존재."""


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class BaseS3Client(ABC):
    """S3 어댑터 인터페이스. mock/real 모두 같은 메서드 세트."""

    bucket: str

    @abstractmethod
    async def upload_text(
        self,
        key: str,
        content: str,
        metadata: dict[str, str] | None = None,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str: ...

    @abstractmethod
    async def upload_json(
        self,
        key: str,
        obj: Any,
        metadata: dict[str, str] | None = None,
    ) -> str: ...

    @abstractmethod
    async def download(self, key: str) -> str: ...

    @abstractmethod
    async def list_objects(self, prefix: str = "") -> list[str]: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    def s3_uri(self, key: str) -> str:
        return f"s3://{self.bucket}/{key}"


# ---------------------------------------------------------------------------
# Mock implementation (local filesystem)
# ---------------------------------------------------------------------------
class LocalMockS3Client(BaseS3Client):
    """
    로컬 파일시스템 백엔드. 시연/CI에서 USE_MOCK=true 시 자동 선택.
    실제 boto3 호출 없음. .mock-s3/ 는 .gitignore 처리.
    """

    def __init__(self, bucket: str, root: Path | None = None) -> None:
        self.bucket = bucket
        self._root = (root or Path(".mock-s3")).resolve() / bucket
        self._root.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _path_for(self, key: str) -> Path:
        # 키에 ".." 등 트래버설 방지
        safe_key = key.replace("\\", "/").lstrip("/")
        if ".." in Path(safe_key).parts:
            raise S3ClientError(f"Invalid key (path traversal): {key}")
        return self._root / safe_key

    async def upload_text(
        self,
        key: str,
        content: str,
        metadata: dict[str, str] | None = None,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        path = self._path_for(key)
        async with self._lock:
            await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(path.write_text, content, encoding="utf-8")
            if metadata:
                meta_path = path.with_suffix(path.suffix + ".meta.json")
                await asyncio.to_thread(
                    meta_path.write_text,
                    json.dumps(
                        {"metadata": metadata, "content_type": content_type},
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
        logger.info("s3_upload_mock", bucket=self.bucket, key=key, size=len(content))
        return self.s3_uri(key)

    async def upload_json(
        self,
        key: str,
        obj: Any,
        metadata: dict[str, str] | None = None,
    ) -> str:
        content = json.dumps(obj, ensure_ascii=False, default=str)
        return await self.upload_text(
            key, content, metadata, content_type="application/json"
        )

    async def download(self, key: str) -> str:
        path = self._path_for(key)
        if not path.exists():
            raise S3ObjectNotFoundError(f"Key not found in mock S3: {key}")
        return await asyncio.to_thread(path.read_text, encoding="utf-8")

    async def list_objects(self, prefix: str = "") -> list[str]:
        results: list[str] = []
        prefix_path = self._path_for(prefix) if prefix else self._root
        if not prefix_path.exists():
            return results
        for p in prefix_path.rglob("*"):
            if p.is_file() and not p.name.endswith(".meta.json"):
                rel = p.relative_to(self._root).as_posix()
                results.append(rel)
        return sorted(results)

    async def exists(self, key: str) -> bool:
        return self._path_for(key).exists()

    async def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            await asyncio.to_thread(path.unlink)
        meta = path.with_suffix(path.suffix + ".meta.json")
        if meta.exists():
            await asyncio.to_thread(meta.unlink)
        logger.info("s3_delete_mock", bucket=self.bucket, key=key)


# ---------------------------------------------------------------------------
# Real implementation (aioboto3)
# ---------------------------------------------------------------------------
class AioBotoS3Client(BaseS3Client):
    """
    실제 AWS S3 — aioboto3 기반.
    Production-ready 구현. 본 코드는 import 실패에 대비해 lazy import.
    """

    def __init__(self, bucket: str, region: str) -> None:
        self.bucket = bucket
        self.region = region

    async def _session(self):  # type: ignore[no-untyped-def]
        import aioboto3  # noqa: PLC0415  - lazy import

        return aioboto3.Session(region_name=self.region)

    async def upload_text(
        self,
        key: str,
        content: str,
        metadata: dict[str, str] | None = None,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        session = await self._session()
        async with session.client("s3") as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
                Metadata=metadata or {},
            )
        logger.info("s3_upload", bucket=self.bucket, key=key, size=len(content))
        return self.s3_uri(key)

    async def upload_json(
        self,
        key: str,
        obj: Any,
        metadata: dict[str, str] | None = None,
    ) -> str:
        return await self.upload_text(
            key,
            json.dumps(obj, ensure_ascii=False, default=str),
            metadata,
            content_type="application/json",
        )

    async def download(self, key: str) -> str:
        session = await self._session()
        async with session.client("s3") as s3:
            try:
                resp = await s3.get_object(Bucket=self.bucket, Key=key)
                body = await resp["Body"].read()
                return body.decode("utf-8")
            except s3.exceptions.NoSuchKey as exc:  # type: ignore[attr-defined]
                raise S3ObjectNotFoundError(str(exc)) from exc

    async def list_objects(self, prefix: str = "") -> list[str]:
        session = await self._session()
        async with session.client("s3") as s3:
            paginator = s3.get_paginator("list_objects_v2")
            keys: list[str] = []
            async for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
            return keys

    async def exists(self, key: str) -> bool:
        session = await self._session()
        async with session.client("s3") as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:  # noqa: BLE001
                return False

    async def delete(self, key: str) -> None:
        session = await self._session()
        async with session.client("s3") as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
        logger.info("s3_delete", bucket=self.bucket, key=key)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_default_client: BaseS3Client | None = None


def build_s3_client(settings: Settings | None = None) -> BaseS3Client:
    """
    Settings 기반 S3 클라이언트 생성:
    - USE_MOCK=true 또는 AWS 자격증명 없음 → LocalMockS3Client
    - 그 외 → AioBotoS3Client
    """
    s = settings or get_settings()
    if s.is_mock or not s.has_aws_credentials:
        logger.info("s3_client_mock_mode", bucket=s.s3_bucket)
        return LocalMockS3Client(bucket=s.s3_bucket)
    logger.info("s3_client_aws_mode", bucket=s.s3_bucket, region=s.aws_region)
    return AioBotoS3Client(bucket=s.s3_bucket, region=s.aws_region)


def get_s3_client() -> BaseS3Client:
    """프로세스 전역 S3 클라이언트 싱글톤."""
    global _default_client
    if _default_client is None:
        _default_client = build_s3_client()
    return _default_client


def reset_s3_client() -> None:
    """테스트에서 싱글톤 초기화."""
    global _default_client
    _default_client = None
