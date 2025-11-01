#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
import io

import pytest
from moto import mock_aws
from ninaivalaigal_storage.config import S3Settings, StorageSettings
from ninaivalaigal_storage.exceptions import StorageError
from ninaivalaigal_storage.providers.s3 import S3StorageBackend


def _settings(auto_create_bucket: bool = True) -> StorageSettings:
    return StorageSettings(
        provider="s3",
        bucket="test-storage-bucket",
        prefix="attachments",
        presign_expiry=300,
        default_acl=None,
        s3=S3Settings(
            access_key="testing",
            secret_key="testing",
            session_token=None,
            region="us-east-1",
            endpoint_url=None,
            use_ssl=True,
            verify_ssl=True,
            force_path_style=False,
            profile_name=None,
            signature_version="s3v4",
            auto_create_bucket=auto_create_bucket,
        ),
    )


@mock_aws
def test_upload_download_and_presign_roundtrip():
    backend = S3StorageBackend(_settings())

    key = backend.upload_bytes(b"hello world", "welcome.txt", content_type="text/plain")
    assert key == "attachments/welcome.txt"

    data = backend.download_bytes("welcome.txt")
    assert data == b"hello world"

    url = backend.generate_presigned_url("welcome.txt", expires_in=60)
    assert "X-Amz-Signature" in url
    assert "welcome.txt" in url

    backend.delete_object("welcome.txt")
    with pytest.raises(StorageError):
        backend.download_bytes("welcome.txt")


@mock_aws
def test_upload_fileobj_supports_metadata():
    backend = S3StorageBackend(_settings())

    backend.upload_fileobj(
        io.BytesIO(b"payload"),
        "meta.txt",
        content_type="text/plain",
        metadata={"author": "tester"},
    )

    data = backend.download_bytes("meta.txt")
    assert data == b"payload"


@mock_aws
def test_ensure_bucket_respects_existing_bucket():
    settings = _settings(auto_create_bucket=False)
    backend = S3StorageBackend(settings)

    # Manually create bucket before upload
    backend._client.create_bucket(Bucket=settings.bucket)

    backend.upload_bytes(b"data", "file.bin")
    assert backend.download_bytes("file.bin") == b"data"


@mock_aws
def test_multipart_upload_workflow(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")

    backend = S3StorageBackend(_settings())

    # Start multipart upload
    descriptor = backend.create_multipart_upload(
        "video.mp4",
        content_type="video/mp4",
        metadata={"origin": "unit-test"},
    )

    assert descriptor["bucket"] == backend.bucket_name
    assert descriptor["key"].endswith("video.mp4")

    upload_id = descriptor["upload_id"]

    # Upload two parts (5MB + 1 byte each)
    part_payload = b"a" * (5 * 1024 * 1024 + 1)
    etag_one = backend.upload_part("video.mp4", upload_id, 1, part_payload)
    etag_two = backend.upload_part("video.mp4", upload_id, 2, part_payload)

    assert etag_one and etag_two

    # List parts should show both entries
    parts = backend.list_multipart_parts("video.mp4", upload_id)
    assert len(parts) == 2
    assert {p["part_number"] for p in parts} == {1, 2}

    # Complete upload
    result = backend.complete_multipart_upload(
        "video.mp4",
        upload_id,
        [
            {"part_number": 1, "etag": etag_one},
            {"part_number": 2, "etag": etag_two},
        ],
    )

    assert result["etag"]
    assert result["key"].endswith("video.mp4")

    # Verify combined object size
    combined = backend.download_bytes("video.mp4")
    assert len(combined) == len(part_payload) * 2


@mock_aws
def test_abort_multipart_upload(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

    backend = S3StorageBackend(_settings())

    descriptor = backend.create_multipart_upload("archive.zip")
    upload_id = descriptor["upload_id"]

    # Abort should not raise
    backend.abort_multipart_upload("archive.zip", upload_id)

    # Listing parts after abort should raise multipart error (upload gone)
    with pytest.raises(StorageError):
        backend.list_multipart_parts("archive.zip", upload_id)
