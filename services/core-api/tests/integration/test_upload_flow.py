#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Integration coverage for the multipart upload HTTP API."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import jwt
import pytest

try:
    from api.upload_api import router as upload_router
    from auth_utils import JWT_ALGORITHM, JWT_SECRET
    from dependencies import get_rate_limiter, get_upload_service
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from security.audit import SecurityEventType, security_alert_manager
    from uploads import InMemoryMultipartUploadStore, MultipartUploadService
except ModuleNotFoundError:  # pragma: no cover - environment without FastAPI
    FASTAPI_AVAILABLE = False
else:
    FASTAPI_AVAILABLE = True

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")


if FASTAPI_AVAILABLE:

    class FakeMultipartBackend:
        """Minimal storage backend stub used for integration testing."""

        def __init__(self) -> None:
            self.uploads: dict[str, list[dict[str, Any]]] = {}
            self.completed: dict[str, list[dict[str, Any]]] = {}
            self.aborted: set[str] = set()
            self.fail_on_complete: bool = False

        def create_multipart_upload(self, key: str, **_: Any) -> dict[str, str]:
            upload_id = f"upload-{len(self.uploads) + 1}"
            self.uploads[upload_id] = []
            return {"upload_id": upload_id, "bucket": "test-bucket", "key": key}

        def generate_part_upload_url(self, key: str, upload_id: str, part_number: int, **_: Any) -> str:
            return f"https://example.com/{key}/{upload_id}/{part_number}"

        def upload_part(self, key: str, upload_id: str, part_number: int, data: Any) -> str:  # pragma: no cover
            etag = f"etag-{upload_id}-{part_number}"
            self.uploads.setdefault(upload_id, []).append(
                {
                    "PartNumber": part_number,
                    "ETag": etag,
                    "Size": len(data) if hasattr(data, "__len__") else None,
                }
            )
            return etag

        def complete_multipart_upload(self, key: str, upload_id: str, parts: list[dict[str, Any]]) -> dict[str, str]:
            if self.fail_on_complete:
                raise Exception("simulated backend failure")
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

        def list_multipart_parts(self, key: str, upload_id: str) -> list[dict[str, Any]]:
            parts = self.uploads.get(upload_id, [])
            return [
                {
                    "part_number": item.get("PartNumber"),
                    "etag": str(item.get("ETag", "")).strip('"'),
                    "size": item.get("Size"),
                }
                for item in parts
            ]

    class FakeRateLimiter:
        """Simple in-memory rate limiter for integration testing."""

        def __init__(self) -> None:
            self._requests: dict[tuple[str, str], list[float]] = {}

        async def is_allowed(self, user_id: str, endpoint: str, limit: int = 100, window: int = 60):
            key = (user_id, endpoint)
            now = time.monotonic()
            window_seconds = float(window)

            calls = [ts for ts in self._requests.get(key, []) if now - ts < window_seconds]
            if len(calls) >= limit:
                self._requests[key] = calls
                return False, {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_at": None,
                }

            calls.append(now)
            self._requests[key] = calls
            remaining = max(limit - len(calls), 0)
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": remaining,
                "reset_at": None,
            }

    def _auth_headers(user_id: str = "user-1", role: str = "user") -> dict[str, str]:
        payload = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "account_type": "organization",
            "role": role,
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture(name="test_context")
    def fixture_test_context():
        """Provide an isolated app and service for each test."""

        backend = FakeMultipartBackend()
        store = InMemoryMultipartUploadStore()
        rate_limiter = FakeRateLimiter()
        service = MultipartUploadService(backend=backend, store=store)

        app = FastAPI()
        app.include_router(upload_router)
        app.dependency_overrides[get_upload_service] = lambda: service
        app.dependency_overrides[get_rate_limiter] = lambda: rate_limiter

        original_recent_events = list(security_alert_manager.recent_events)
        original_active_alerts = list(security_alert_manager.active_alerts)

        try:
            yield app, service, backend, store, rate_limiter
        finally:
            app.dependency_overrides.clear()
            security_alert_manager.recent_events = original_recent_events
            security_alert_manager.active_alerts = original_active_alerts


def _run(action):
    return asyncio.run(action)


if FASTAPI_AVAILABLE:

    def test_complete_upload_flow(test_context):
        app, _, _, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                start_response = await client.post(
                    "/upload/multipart/start",
                    json={
                        "object_key": "test/file.bin",
                        "filename": "file.bin",
                        "content_type": "application/octet-stream",
                        "total_size": 15_728_640,
                        "part_size": 5_242_880,
                        "metadata": {"origin": "integration"},
                    },
                    headers=headers,
                )
                assert start_response.status_code == 201
                session_data = start_response.json()
                session_id = session_data["session_id"]

                for part_number in range(1, 4):
                    url_response = await client.post(
                        f"/upload/multipart/{session_id}/part-url",
                        json={"part_number": part_number},
                        headers=headers,
                    )
                    assert url_response.status_code == 200
                    body = url_response.json()
                    assert body["part_number"] == part_number
                    assert body["upload_url"].startswith("https://example.com/")

                    register_response = await client.post(
                        f"/upload/multipart/{session_id}/parts",
                        json={
                            "part_number": part_number,
                            "etag": f"etag-{part_number}",
                            "size": 5_242_880,
                        },
                        headers=headers,
                    )
                    assert register_response.status_code == 200

                status_response = await client.get(
                    f"/upload/multipart/{session_id}/status",
                    headers=headers,
                )
                assert status_response.status_code == 200
                status_payload = status_response.json()
                assert status_payload["parts_uploaded"] == 3
                assert status_payload["status"] == "in_progress"
                assert status_payload["progress"]["uploaded_bytes"] == 3 * 5_242_880

                complete_response = await client.post(
                    f"/upload/multipart/{session_id}/complete",
                    headers=headers,
                )
                assert complete_response.status_code == 200
                completed = complete_response.json()
                assert completed["success"] is True
                assert completed["etag"] == "final-etag"

        _run(_flow())

    def test_abort_upload_flow(test_context):
        app, _, backend, _, _ = test_context

        async def _flow():
            headers = _auth_headers("abort-user")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                start_response = await client.post(
                    "/upload/multipart/start",
                    json={"object_key": "test/abort.bin"},
                    headers=headers,
                )
                assert start_response.status_code == 201
                session_id = start_response.json()["session_id"]

                event_count_before = len(security_alert_manager.recent_events)
                abort_response = await client.delete(
                    f"/upload/multipart/{session_id}",
                    headers=headers,
                )
                assert abort_response.status_code == 200

                status_response = await client.get(
                    f"/upload/multipart/{session_id}/status",
                    headers=headers,
                )
                assert status_response.status_code == 404

                assert len(security_alert_manager.recent_events) == event_count_before + 1
                audit_event = security_alert_manager.recent_events[-1]
                assert audit_event["event_type"] == SecurityEventType.ADMIN_ACTION
                assert audit_event["metadata"]["action"] == "multipart_upload_abort"
                assert audit_event["metadata"]["session_id"] == session_id

        _run(_flow())

    def test_register_part_for_missing_session_returns_404(test_context):
        app, _, _, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post(
                    "/upload/multipart/missing-session/parts",
                    json={"part_number": 1, "etag": "nope", "size": 10},
                    headers=headers,
                )
                assert response.status_code == 404

        _run(_flow())

    def test_complete_without_parts_returns_conflict(test_context):
        app, _, _, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                start_response = await client.post(
                    "/upload/multipart/start",
                    json={"object_key": "test/conflict.bin"},
                    headers=headers,
                )
                assert start_response.status_code == 201
                session_id = start_response.json()["session_id"]

                complete_response = await client.post(
                    f"/upload/multipart/{session_id}/complete",
                    headers=headers,
                )
                assert complete_response.status_code == 409
                assert "without uploaded parts" in complete_response.json()["detail"]

        _run(_flow())

    def test_get_part_url_after_completion_returns_conflict(test_context):
        app, _, backend, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                start_response = await client.post(
                    "/upload/multipart/start",
                    json={"object_key": "test/completed.bin"},
                    headers=headers,
                )
                assert start_response.status_code == 201
                session_id = start_response.json()["session_id"]

                register_response = await client.post(
                    f"/upload/multipart/{session_id}/parts",
                    json={"part_number": 1, "etag": "etag-1", "size": 1024},
                    headers=headers,
                )
                assert register_response.status_code == 200

                complete_response = await client.post(
                    f"/upload/multipart/{session_id}/complete",
                    headers=headers,
                )
                assert complete_response.status_code == 200

                url_response = await client.post(
                    f"/upload/multipart/{session_id}/part-url",
                    json={"part_number": 2},
                    headers=headers,
                )
                assert url_response.status_code == 409
                assert "state" in url_response.json()["detail"]

        _run(_flow())

    def test_abort_missing_session_returns_404(test_context):
        app, _, _, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.delete(
                    "/upload/multipart/not-a-session",
                    headers=headers,
                )
                assert response.status_code == 404

        _run(_flow())

    def test_complete_backend_failure_returns_500(test_context):
        app, _, backend, _, _ = test_context

        async def _flow():
            headers = _auth_headers()
            backend.fail_on_complete = True
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                start_response = await client.post(
                    "/upload/multipart/start",
                    json={"object_key": "test/backend-error.bin"},
                    headers=headers,
                )
                session_id = start_response.json()["session_id"]

                register_response = await client.post(
                    f"/upload/multipart/{session_id}/parts",
                    json={"part_number": 1, "etag": "etag-err", "size": 2048},
                    headers=headers,
                )
                assert register_response.status_code == 200

                complete_response = await client.post(
                    f"/upload/multipart/{session_id}/complete",
                    headers=headers,
                )
                assert complete_response.status_code == 500
                assert "simulated backend failure" in complete_response.json()["detail"]

        _run(_flow())

    def test_rate_limit_exceeded_returns_429(test_context):
        app, _, _, _, _ = test_context

        async def _flow():
            headers = _auth_headers("rate-user")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                for _ in range(5):
                    response = await client.post(
                        "/upload/multipart/start",
                        json={"object_key": "rate/limited.bin"},
                        headers=headers,
                    )
                    assert response.status_code == 201

                blocked = await client.post(
                    "/upload/multipart/start",
                    json={"object_key": "rate/limited.bin"},
                    headers=headers,
                )
                assert blocked.status_code == 429
                assert blocked.json()["detail"] == "Rate limit exceeded"

        _run(_flow())


if not FASTAPI_AVAILABLE:  # pragma: no cover - sanity placeholder

    def test_fastapi_dependency_missing():
        pytest.skip("FastAPI not installed")
