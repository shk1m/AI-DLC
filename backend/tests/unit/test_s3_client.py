"""Tests for app.adapters.s3_client (mock backend)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.adapters.s3_client import (
    LocalMockS3Client,
    S3ClientError,
    S3ObjectNotFoundError,
    build_s3_client,
)
from app.core.config import reset_settings_cache


@pytest.fixture
def mock_client(tmp_path: Path) -> LocalMockS3Client:
    return LocalMockS3Client(bucket="test-bucket", root=tmp_path)


class TestLocalMockS3Client:
    async def test_upload_text_and_download(self, mock_client: LocalMockS3Client) -> None:
        uri = await mock_client.upload_text("foo/bar.txt", "hello world")
        assert uri == "s3://test-bucket/foo/bar.txt"
        content = await mock_client.download("foo/bar.txt")
        assert content == "hello world"

    async def test_upload_json_and_download(self, mock_client: LocalMockS3Client) -> None:
        payload = {"a": 1, "b": "한글", "c": [1, 2, 3]}
        await mock_client.upload_json("data.json", payload)
        text = await mock_client.download("data.json")
        assert json.loads(text) == payload

    async def test_metadata_is_stored(
        self, mock_client: LocalMockS3Client, tmp_path: Path
    ) -> None:
        await mock_client.upload_text(
            "f.txt", "data", metadata={"source": "mafra", "version": "1"}
        )
        meta_file = (
            tmp_path / "test-bucket" / "f.txt.meta.json"
        )
        assert meta_file.exists()
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["metadata"] == {"source": "mafra", "version": "1"}

    async def test_download_missing_raises(self, mock_client: LocalMockS3Client) -> None:
        with pytest.raises(S3ObjectNotFoundError):
            await mock_client.download("missing.txt")

    async def test_list_objects(self, mock_client: LocalMockS3Client) -> None:
        await mock_client.upload_text("news/2026-05-20/a.json", "{}")
        await mock_client.upload_text("news/2026-05-20/b.json", "{}")
        await mock_client.upload_text("other/c.json", "{}")

        all_keys = await mock_client.list_objects()
        assert {
            "news/2026-05-20/a.json",
            "news/2026-05-20/b.json",
            "other/c.json",
        } == set(all_keys)

        news_keys = await mock_client.list_objects(prefix="news/2026-05-20")
        assert len(news_keys) == 2
        assert all(k.startswith("news/2026-05-20") for k in news_keys)

    async def test_exists(self, mock_client: LocalMockS3Client) -> None:
        await mock_client.upload_text("k.txt", "v")
        assert await mock_client.exists("k.txt") is True
        assert await mock_client.exists("nope.txt") is False

    async def test_delete(self, mock_client: LocalMockS3Client) -> None:
        await mock_client.upload_text("k.txt", "v", metadata={"x": "y"})
        await mock_client.delete("k.txt")
        assert await mock_client.exists("k.txt") is False

    async def test_path_traversal_rejected(self, mock_client: LocalMockS3Client) -> None:
        with pytest.raises(S3ClientError):
            await mock_client.upload_text("../escape.txt", "x")

    async def test_meta_files_excluded_from_list(
        self, mock_client: LocalMockS3Client
    ) -> None:
        await mock_client.upload_text("a.txt", "v", metadata={"m": "1"})
        keys = await mock_client.list_objects()
        assert keys == ["a.txt"]
        assert not any(k.endswith(".meta.json") for k in keys)


class TestS3ClientFactory:
    def test_use_mock_returns_local(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USE_MOCK", "true")
        reset_settings_cache()
        client = build_s3_client()
        assert isinstance(client, LocalMockS3Client)

    def test_no_credentials_falls_to_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USE_MOCK", "false")
        monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
        reset_settings_cache()
        client = build_s3_client()
        # 자격증명 없으면 자동 mock
        assert isinstance(client, LocalMockS3Client)
