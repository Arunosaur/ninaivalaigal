#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Integration tests for the Rust memory provider proxy."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from server.memory.factory import RustMemoryProvider
from server.memory.interfaces import MemoryProviderError

pytestmark = pytest.mark.rust_integration


def test_remember_sends_authorization_and_maps_response():
    """Ensure remember forwards the bearer token and normalizes the payload."""

    async def run_test():
        bearer = "Bearer test-token"

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers["authorization"] == bearer
            assert request.url.path == "/memory/remember"

            payload = json.loads(request.content.decode())
            assert payload == {
                "content": "Remember me",
                "metadata": {"topic": "demo"},
                "user_id": "user-1",
                "context_id": None,
            }

            return httpx.Response(
                status_code=200,
                json={
                    "id": "123",
                    "content": "Remember me",
                    "metadata": {"topic": "demo"},
                    "user_id": "user-1",
                    "context_id": None,
                    "created_at": "2025-10-31T12:00:00Z",
                },
            )

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport, base_url="http://memory-service")
        provider = RustMemoryProvider(base_url="http://memory-service", client=client)

        try:
            result = await provider.remember(
                text="Remember me",
                meta={"topic": "demo"},
                user_id="user-1",
                bearer_token=bearer,
            )
        finally:
            await provider.aclose()
            await client.aclose()

        assert result["text"] == "Remember me"
        assert result["meta"] == {"topic": "demo"}
        assert result["user_id"] == "user-1"

    asyncio.run(run_test())


def test_recall_maps_multiple_results():
    """Recall returns normalized memory items."""

    async def run_test():
        bearer = "Bearer recall-token"

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers["authorization"] == bearer
            assert json.loads(request.content.decode()) == {"query": "core", "limit": 3}

            return httpx.Response(
                status_code=200,
                json=[
                    {
                        "id": "1",
                        "content": "core memory",
                        "metadata": {"scope": "personal"},
                        "user_id": "user-1",
                        "context_id": None,
                        "created_at": "2025-10-31T12:00:00Z",
                    },
                    {
                        "id": "2",
                        "content": "core follow-up",
                        "metadata": {},
                        "user_id": "user-1",
                        "context_id": None,
                        "created_at": "2025-10-31T12:05:00Z",
                    },
                ],
            )

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport, base_url="http://memory-service")
        provider = RustMemoryProvider(base_url="http://memory-service", client=client)

        try:
            results = await provider.recall(query="core", k=3, bearer_token=bearer)
        finally:
            await provider.aclose()
            await client.aclose()

        assert len(results) == 2
        assert results[0]["text"] == "core memory"
        assert results[1]["meta"] == {}

    asyncio.run(run_test())


def test_delete_handles_not_found():
    """Delete returns False when the Rust service reports a missing memory."""

    async def run_test():
        bearer = "Bearer delete-token"

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert request.headers["authorization"] == bearer
            assert request.url.path == "/memory/memories/abc"
            return httpx.Response(status_code=404)

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport, base_url="http://memory-service")
        provider = RustMemoryProvider(base_url="http://memory-service", client=client)

        try:
            result = await provider.delete(id="abc", bearer_token=bearer)
        finally:
            await provider.aclose()
            await client.aclose()

        assert result is False

    asyncio.run(run_test())


def test_missing_token_raises_error():
    """Provider requires a bearer token before proxying requests."""

    async def run_test():
        provider = RustMemoryProvider(base_url="http://memory-service")

        with pytest.raises(MemoryProviderError):
            await provider.remember(text="no token", bearer_token=None)

        await provider.aclose()

    asyncio.run(run_test())
