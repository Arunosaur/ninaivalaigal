#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
from ninaivalaigal_storage.config import StorageConfigError, load_storage_settings


def test_load_storage_settings_minio_defaults():
    env = {
        "STORAGE_PROVIDER": "minio",
        "STORAGE_S3_ACCESS_KEY": "minio",
        "STORAGE_S3_SECRET_KEY": "minio123",
        "NINA_ENV": "dev",
    }

    settings = load_storage_settings(env)

    assert settings.provider == "minio"
    assert settings.bucket == "ninaivalaigal-dev-attachments"
    assert settings.s3.endpoint_url == "http://localhost:9000"
    assert settings.s3.use_ssl is False
    assert settings.s3.force_path_style is True
    assert settings.presign_expiry == 900


def test_load_storage_settings_custom_bucket_and_prefix():
    env = {
        "STORAGE_PROVIDER": "s3",
        "STORAGE_BUCKET": "acme-prod-artifacts",
        "STORAGE_PREFIX": "attachments",
        "STORAGE_PRESIGN_EXPIRY": "600",
        "STORAGE_S3_REGION": "us-west-2",
        "STORAGE_S3_USE_SSL": "true",
    }

    settings = load_storage_settings(env)

    assert settings.bucket == "acme-prod-artifacts"
    assert settings.prefix == "attachments"
    assert settings.presign_expiry == 600
    assert settings.s3.region == "us-west-2"
    assert settings.s3.use_ssl is True


def test_load_storage_settings_invalid_provider():
    env = {
        "STORAGE_PROVIDER": "gcs",
        "STORAGE_BUCKET": "bucket",
    }

    try:
        load_storage_settings(env)
    except StorageConfigError as exc:
        assert "Unsupported storage provider" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected StorageConfigError to be raised")
