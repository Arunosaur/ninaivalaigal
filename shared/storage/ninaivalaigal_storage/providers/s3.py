#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""S3 and MinIO compatible storage backend."""

from __future__ import annotations

import io
from typing import BinaryIO, Mapping, MutableMapping, Sequence

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from ..base import StorageBackend
from ..config import StorageSettings
from ..exceptions import StorageError, StorageMultipartError

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}


class S3StorageBackend(StorageBackend):
    """Concrete storage backend backed by boto3."""

    def __init__(
        self,
        settings: StorageSettings,
        *,
        client=None,
        session: boto3.session.Session | None = None,
    ) -> None:
        self._settings = settings
        self._bucket = settings.bucket
        self._presign_expiry = settings.presign_expiry
        self._default_acl = settings.default_acl

        if client is not None:
            self._client = client
        else:
            s3 = settings.s3
            session_kwargs: MutableMapping[str, str] = {}
            if s3.access_key:
                session_kwargs["aws_access_key_id"] = s3.access_key
            if s3.secret_key:
                session_kwargs["aws_secret_access_key"] = s3.secret_key
            if s3.session_token:
                session_kwargs["aws_session_token"] = s3.session_token
            if s3.profile_name and "aws_access_key_id" not in session_kwargs:
                session_kwargs["profile_name"] = s3.profile_name

            base_session = session or boto3.session.Session(region_name=s3.region, **session_kwargs)

            config = BotoConfig(
                signature_version=s3.signature_version,
                s3={"addressing_style": "path" if s3.force_path_style else "virtual"},
            )

            self._client = base_session.client(
                "s3",
                endpoint_url=s3.endpoint_url,
                use_ssl=s3.use_ssl,
                verify=s3.verify_ssl,
                config=config,
            )

        if settings.s3.auto_create_bucket:
            self._ensure_bucket()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def bucket_name(self) -> str:
        """Return the configured bucket name."""

        return self._bucket

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        *,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> str:
        object_key = self._settings.resolve_key(key)
        extra_args: dict[str, object] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}
        if self._default_acl:
            extra_args["ACL"] = self._default_acl

        try:
            if extra_args:
                self._client.upload_fileobj(fileobj, self._bucket, object_key, ExtraArgs=extra_args)
            else:
                self._client.upload_fileobj(fileobj, self._bucket, object_key)
        except ClientError as exc:
            raise StorageError("Failed to upload object", key=object_key, code=_error_code(exc)) from exc

        return object_key

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        *,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> str:
        buffer = io.BytesIO(data)
        return self.upload_fileobj(buffer, key, content_type=content_type, metadata=metadata)

    def download_bytes(self, key: str) -> bytes:
        object_key = self._settings.resolve_key(key)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=object_key)
        except ClientError as exc:
            code = _error_code(exc)
            if code in _NOT_FOUND_CODES:
                raise StorageError("Object not found", key=object_key, code=code) from exc
            raise StorageError("Failed to download object", key=object_key, code=code) from exc

        body = response.get("Body")
        if body is None:
            raise StorageError("Empty response body from storage", key=object_key)
        return body.read()

    def delete_object(self, key: str) -> None:
        object_key = self._settings.resolve_key(key)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=object_key)
        except ClientError as exc:
            raise StorageError("Failed to delete object", key=object_key, code=_error_code(exc)) from exc

    def generate_presigned_url(
        self,
        key: str,
        *,
        expires_in: int | None = None,
        method: str = "get_object",
        response_headers: Mapping[str, str] | None = None,
    ) -> str:
        object_key = self._settings.resolve_key(key)
        params: dict[str, str] = {"Bucket": self._bucket, "Key": object_key}
        if response_headers:
            params.update({k: v for k, v in response_headers.items() if v is not None})
        try:
            return self._client.generate_presigned_url(
                method,
                Params=params,
                ExpiresIn=expires_in or self._presign_expiry,
            )
        except ClientError as exc:
            raise StorageError("Failed to create presigned URL", key=object_key, code=_error_code(exc)) from exc

        # ------------------------------------------------------------------
        # Multipart helpers
        # ------------------------------------------------------------------

        def create_multipart_upload(
            self,
            key: str,
            *,
            content_type: str | None = None,
            metadata: Mapping[str, str] | None = None,
            acl: str | None = None,
        ) -> dict[str, str]:
            """Start multipart upload and return identifiers."""

            object_key = self._settings.resolve_key(key)
            extra_args: dict[str, object] = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}
            acl_value = acl or self._default_acl
            if acl_value:
                extra_args["ACL"] = acl_value

            try:
                response = self._client.create_multipart_upload(
                    Bucket=self._bucket,
                    Key=object_key,
                    **extra_args,
                )
            except ClientError as exc:
                raise StorageMultipartError(
                    "Failed to start multipart upload",
                    key=object_key,
                    code=_error_code(exc),
                ) from exc

            return {
                "upload_id": response["UploadId"],
                "bucket": self._bucket,
                "key": object_key,
            }

        def generate_part_upload_url(
            self,
            key: str,
            upload_id: str,
            part_number: int,
            *,
            expires_in: int | None = None,
            extra_params: Mapping[str, str] | None = None,
        ) -> str:
            """Generate presigned URL for uploading a single part."""

            object_key = self._settings.resolve_key(key)
            params: dict[str, object] = {
                "Bucket": self._bucket,
                "Key": object_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            }
            if extra_params:
                params.update({k: v for k, v in extra_params.items() if v is not None})

            try:
                return self._client.generate_presigned_url(
                    "upload_part",
                    Params=params,
                    ExpiresIn=expires_in or self._presign_expiry,
                )
            except ClientError as exc:
                raise StorageMultipartError(
                    "Failed to create multipart presigned URL",
                    key=object_key,
                    code=_error_code(exc),
                ) from exc

        def upload_part(
            self,
            key: str,
            upload_id: str,
            part_number: int,
            data: bytes | BinaryIO,
        ) -> str:
            """Upload part data via server-side transfer and return ETag."""

            object_key = self._settings.resolve_key(key)
            body = data
            try:
                response = self._client.upload_part(
                    Bucket=self._bucket,
                    Key=object_key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=body,
                )
            except ClientError as exc:
                raise StorageMultipartError(
                    "Failed to upload part",
                    key=object_key,
                    code=_error_code(exc),
                ) from exc

            etag = response.get("ETag", "")
            return etag.strip('"')

        def complete_multipart_upload(
            self,
            key: str,
            upload_id: str,
            parts: Sequence[dict[str, object]],
        ) -> dict[str, str | None]:
            """Finalize multipart upload and return object metadata."""

            object_key = self._settings.resolve_key(key)
            formatted_parts = []
            for part in parts:
                part_number = int(part["part_number"] if "part_number" in part else part["PartNumber"])
                etag = str(part["etag"] if "etag" in part else part["ETag"])
                formatted_parts.append(
                    {
                        "PartNumber": part_number,
                        "ETag": etag if etag.startswith('"') else f'"{etag}"',
                    }
                )

            try:
                response = self._client.complete_multipart_upload(
                    Bucket=self._bucket,
                    Key=object_key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": formatted_parts},
                )
            except ClientError as exc:
                raise StorageMultipartError(
                    "Failed to complete multipart upload",
                    key=object_key,
                    code=_error_code(exc),
                ) from exc

            etag = response.get("ETag") or ""
            return {
                "bucket": response.get("Bucket", self._bucket),
                "key": response.get("Key", object_key),
                "location": response.get("Location"),
                "etag": etag.strip('"'),
            }

        def abort_multipart_upload(self, key: str, upload_id: str) -> None:
            """Abort multipart upload session."""

            object_key = self._settings.resolve_key(key)
            try:
                self._client.abort_multipart_upload(
                    Bucket=self._bucket,
                    Key=object_key,
                    UploadId=upload_id,
                )
            except ClientError as exc:
                code = _error_code(exc)
                if code not in _NOT_FOUND_CODES:
                    raise StorageMultipartError(
                        "Failed to abort multipart upload",
                        key=object_key,
                        code=code,
                    ) from exc

        def list_multipart_parts(
            self,
            key: str,
            upload_id: str,
        ) -> list[dict[str, object]]:
            """Return list of uploaded parts for the session."""

            object_key = self._settings.resolve_key(key)
            try:
                paginator = self._client.get_paginator("list_parts")
                parts: list[dict[str, object]] = []
                for page in paginator.paginate(Bucket=self._bucket, Key=object_key, UploadId=upload_id):
                    for item in page.get("Parts", []):
                        parts.append(
                            {
                                "part_number": item.get("PartNumber"),
                                "etag": (item.get("ETag") or "").strip('"'),
                                "size": item.get("Size"),
                                "last_modified": item.get("LastModified"),
                            }
                        )
                return parts
            except ClientError as exc:
                raise StorageMultipartError(
                    "Failed to list multipart parts",
                    key=object_key,
                    code=_error_code(exc),
                ) from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return
        except ClientError as exc:
            code = _error_code(exc)
            if code not in _NOT_FOUND_CODES:
                raise StorageError("Failed to check bucket existence", code=code) from exc

        create_kwargs: dict[str, object] = {"Bucket": self._bucket}
        region = self._settings.s3.region
        if region and region != "us-east-1":
            create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
        try:
            self._client.create_bucket(**create_kwargs)
        except ClientError as exc:  # pragma: no cover - race condition / permissions
            code = _error_code(exc)
            if code in {"BucketAlreadyExists", "BucketAlreadyOwnedByYou"}:
                return
            raise StorageError("Failed to create bucket", code=code) from exc


def _error_code(exc: ClientError) -> str:
    return exc.response.get("Error", {}).get("Code", "unknown")
