#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Environment-driven configuration helpers for storage backends."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .exceptions import StorageConfigError


@dataclass(slots=True)
class S3Settings:
    """Configuration for S3 or MinIO compatible storage."""

    access_key: str | None
    secret_key: str | None
    session_token: str | None
    region: str
    endpoint_url: str | None
    use_ssl: bool
    verify_ssl: bool
    force_path_style: bool
    profile_name: str | None
    signature_version: str
    auto_create_bucket: bool


@dataclass(slots=True)
class StorageSettings:
    """High-level storage configuration used by the factory."""

    provider: str
    bucket: str
    prefix: str | None
    presign_expiry: int
    default_acl: str | None
    s3: S3Settings

    def resolve_key(self, key: str) -> str:
        """Return key with optional prefix applied."""
        normalized = key.lstrip("/")
        if self.prefix:
            return f"{self.prefix.rstrip('/')}/{normalized}"
        return normalized


def _get_env(env: Mapping[str, str], key: str, default: str | None = None) -> str | None:
    value = env.get(key)
    if value is None or value == "":
        return default
    return value


def _get_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _get_int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise StorageConfigError(f"Invalid integer value for {key}: {raw}") from exc


DEFAULT_BUCKET_TEMPLATE = "ninaivalaigal-{env}-attachments"


def load_storage_settings(env: Mapping[str, str] | None = None) -> StorageSettings:
    """Load storage configuration from environment variables."""

    source = env or os.environ

    provider = (_get_env(source, "STORAGE_PROVIDER") or _get_env(source, "STORAGE_BACKEND") or "s3").lower()

    nina_env = _get_env(source, "NINA_ENV", "dev")
    bucket = (
        _get_env(source, "STORAGE_BUCKET")
        or _get_env(source, "STORAGE_S3_BUCKET")
        or DEFAULT_BUCKET_TEMPLATE.format(env=nina_env)
    )

    if not bucket:
        raise StorageConfigError("Storage bucket is required. Set STORAGE_BUCKET or STORAGE_S3_BUCKET.")

    prefix = _get_env(source, "STORAGE_PREFIX")
    presign_expiry = _get_int(source, "STORAGE_PRESIGN_EXPIRY", 900)
    default_acl = _get_env(source, "STORAGE_DEFAULT_OBJECT_ACL")

    if provider not in {"s3", "minio"}:
        raise StorageConfigError(f"Unsupported storage provider '{provider}'. Only 's3' or 'minio' supported.")

    # S3/MinIO specific configuration
    endpoint = _get_env(source, "STORAGE_S3_ENDPOINT") or _get_env(source, "STORAGE_S3_ENDPOINT_URL")
    if endpoint is None and provider == "minio":
        endpoint = "http://localhost:9000"

    region = _get_env(source, "STORAGE_S3_REGION") or _get_env(source, "AWS_REGION") or "us-east-1"
    access_key = _get_env(source, "STORAGE_S3_ACCESS_KEY") or _get_env(source, "AWS_ACCESS_KEY_ID")
    secret_key = _get_env(source, "STORAGE_S3_SECRET_KEY") or _get_env(source, "AWS_SECRET_ACCESS_KEY")
    session_token = _get_env(source, "STORAGE_S3_SESSION_TOKEN") or _get_env(source, "AWS_SESSION_TOKEN")
    profile = _get_env(source, "STORAGE_S3_PROFILE") or _get_env(source, "AWS_PROFILE")

    use_ssl_default = False if provider == "minio" else True
    use_ssl = _get_bool(source, "STORAGE_S3_USE_SSL", use_ssl_default)
    verify_ssl = _get_bool(source, "STORAGE_S3_VERIFY_SSL", use_ssl or provider == "s3")
    force_path_style = _get_bool(source, "STORAGE_S3_FORCE_PATH_STYLE", provider == "minio")
    auto_create_bucket = _get_bool(source, "STORAGE_S3_AUTO_CREATE_BUCKET", provider != "s3")
    signature_version = _get_env(source, "STORAGE_S3_SIGNATURE_VERSION", "s3v4")

    s3_settings = S3Settings(
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        region=region,
        endpoint_url=endpoint,
        use_ssl=use_ssl,
        verify_ssl=verify_ssl,
        force_path_style=force_path_style,
        profile_name=profile,
        signature_version=signature_version,
        auto_create_bucket=auto_create_bucket,
    )

    return StorageSettings(
        provider=provider,
        bucket=bucket,
        prefix=prefix,
        presign_expiry=presign_expiry,
        default_acl=default_acl,
        s3=s3_settings,
    )
