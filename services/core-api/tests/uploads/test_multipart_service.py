#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

# Ensure service library and shared storage packages are importable
LIB_DIR = Path(__file__).parent.parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

STORAGE_DIR = Path(__file__).resolve().parents[4] / "shared" / "storage"
if str(STORAGE_DIR) not in sys.path:
    sys.path.insert(0, str(STORAGE_DIR))

from uploads import InMemoryMultipartUploadStore, MultipartUploadService  # noqa: E402


def _run(coro):
    """Execute an async coroutine synchronously for tests."""

    return asyncio.run(coro)


class FakeMultipartBackend:
    def __init__(self) -> None:
        self.uploads: dict[str, list[dict[str, object]]] = {}
        self.completed: dict[str, list[dict[str, object]]] = {}
        self.aborted: set[str] = set()

    def create_multipart_upload(self, key: str, **_: object) -> dict[str, str]:
        upload_id = f"upload-{len(self.uploads) + 1}"
        self.uploads[upload_id] = []
        return {"upload_id": upload_id, "bucket": "test-bucket", "key": key}

    def generate_part_upload_url(self, key: str, upload_id: str, part_number: int, **_: object) -> str:
        return f"https://example.com/{key}/{upload_id}/{part_number}"

    def upload_part(
        self, key: str, upload_id: str, part_number: int, data: object
    ) -> str:  # pragma: no cover - not used yet
        etag = f"etag-{upload_id}-{part_number}"
        self.uploads.setdefault(upload_id, []).append({"PartNumber": part_number, "ETag": etag})
        return etag

    def complete_multipart_upload(self, key: str, upload_id: str, parts: list[dict[str, object]]) -> dict[str, str]:
        self.completed[upload_id] = list(parts)
        return {
            "bucket": "test-bucket",
            "key": key,
            "location": f"s3://test-bucket/{key}",
            "etag": "final-etag",
        }

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        self.aborted.add(upload_id)
        self.uploads.pop(upload_id, None)

    def list_multipart_parts(self, key: str, upload_id: str) -> list[dict[str, object]]:
        parts = self.uploads.get(upload_id, [])
        return [
            {
                "part_number": item.get("PartNumber"),
                "etag": str(item.get("ETag", "")).strip('"'),
                "size": item.get("Size"),
            }
            for item in parts
        ]


def test_start_session_persists_metadata():
    backend = FakeMultipartBackend()
    store = InMemoryMultipartUploadStore()
    service = MultipartUploadService(backend=backend, store=store, default_part_size=5)

    session = _run(
        service.start_session(
            object_key="uploads/foo.bin",
            filename="foo.bin",
            content_type="application/octet-stream",
            metadata={"origin": "unit-test"},
            total_size=10,
            part_size=5,
            initiated_by="tester",
        )
    )

    assert session.status == "in_progress"
    restored = _run(store.get(session.session_id))
    assert restored is not None
    assert restored.metadata["origin"] == "unit-test"
    assert restored.part_count == 2


def test_complete_session_marks_success():
    backend = FakeMultipartBackend()
    store = InMemoryMultipartUploadStore()
    service = MultipartUploadService(backend=backend, store=store)

    session = _run(service.start_session(object_key="uploads/demo.bin", total_size=12, part_size=6))

    _run(service.register_uploaded_part(session.session_id, part_number=1, etag="etag-1", size=6))
    _run(service.register_uploaded_part(session.session_id, part_number=2, etag="etag-2", size=6))

    result = _run(service.complete_session(session.session_id))

    assert result["etag"] == "final-etag"
    saved = _run(store.get(session.session_id))
    assert saved is not None
    assert saved.status == "completed"
    assert saved.result_etag == "final-etag"


def test_abort_session_records_state():
    backend = FakeMultipartBackend()
    store = InMemoryMultipartUploadStore()
    service = MultipartUploadService(backend=backend, store=store)

    session = _run(service.start_session(object_key="uploads/sample.bin"))
    _run(service.abort_session(session.session_id))

    saved = _run(store.get(session.session_id))
    assert saved is None
    assert session.upload_id in backend.aborted
