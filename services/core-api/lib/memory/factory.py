#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Memory provider factory with Rust gating support."""

import os
from typing import Any

import httpx

from config import DEFAULT_RUST_DATABASE_URL_SESSION

from .interfaces import MemoryProvider, MemoryProviderError
from .providers.postgres import PostgresMemoryProvider


class RustMemoryProvider:
    """HTTP provider that proxies to Rust Memory Service"""

    def __init__(self, base_url: str, **kwargs: Any):
        self.base_url = base_url.rstrip("/")
        self.timeout = kwargs.get("timeout", 30.0)
        client: httpx.AsyncClient | None = kwargs.get("client")
        if client is not None:
            self.client = client
            self._owns_client = False
        else:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
            self._owns_client = True

    async def aclose(self) -> None:
        """Close the underlying HTTP client when we created it."""
        if self._owns_client:
            await self.client.aclose()

    @staticmethod
    def _build_headers(bearer_token: str | None) -> dict[str, str]:
        if not bearer_token:
            raise MemoryProviderError("Authorization token required for Rust memory provider requests")
        return {"Authorization": bearer_token}

    @staticmethod
    def _map_memory(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data.get("id"),
            "text": data.get("content"),
            "meta": data.get("metadata") or {},
            "user_id": data.get("user_id"),
            "context_id": data.get("context_id"),
            "created_at": data.get("created_at"),
        }

    @staticmethod
    def _error(operation: str, exc: httpx.HTTPStatusError) -> MemoryProviderError:
        status = exc.response.status_code
        detail = exc.response.text
        return MemoryProviderError(f"Rust memory service {operation} failed with status {status}: {detail}")

    async def remember(
        self,
        *,
        text: str,
        meta: dict | None = None,
        user_id: str | None = None,
        context_id: str | None = None,
        bearer_token: str | None = None,
    ):
        """Store memory via Rust service"""
        try:
            response = await self.client.post(
                "/memory/remember",
                json={
                    "content": text,
                    "metadata": meta or {},
                    "context_id": context_id,
                },
                headers=self._build_headers(bearer_token),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._error("remember", exc) from exc

        return self._map_memory(response.json())

    async def recall(
        self,
        *,
        query: str,
        k: int = 10,
        user_id: str | None = None,
        context_id: str | None = None,
        bearer_token: str | None = None,
    ):
        """Recall memories via Rust service"""
        payload = {"query": query, "limit": k}
        try:
            response = await self.client.post(
                "/memory/recall",
                json=payload,
                headers=self._build_headers(bearer_token),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._error("recall", exc) from exc

        data = response.json()
        return [self._map_memory(item) for item in data]

    async def list_memories(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        bearer_token: str | None = None,
    ):
        """List memories via Rust service"""
        try:
            response = await self.client.get(
                "/memory/memories",
                headers=self._build_headers(bearer_token),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._error("list", exc) from exc

        data = response.json()
        # Limit/offset implemented client-side until server exposes pagination
        sliced = data[offset : offset + limit]
        return [self._map_memory(item) for item in sliced]

    async def delete(
        self,
        *,
        memory_id: str,
        user_id: str | None = None,
        bearer_token: str | None = None,
    ):
        """Delete memory via Rust service"""
        response = await self.client.delete(
            f"/memory/memories/{memory_id}",
            headers=self._build_headers(bearer_token),
        )

        if response.status_code == 204:
            return True
        if response.status_code == 404:
            return False

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._error("delete", exc) from exc

        return False

    async def health_check(self):
        """Check Rust service health"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except:
            return False


def _flag_enabled(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_memory_provider(provider_type: str | None = None, **kwargs) -> MemoryProvider:
    """Create memory provider honoring feature flag gating for Rust."""

    resolved_provider = provider_type or os.getenv("MEMORY_PROVIDER")
    if resolved_provider:
        provider_choice = resolved_provider.strip().lower()
    else:
        provider_choice = "rust" if _flag_enabled(os.getenv("USE_RUST_MEMORY"), default=False) else "postgres"

    if provider_choice == "rust":
        rust_url = kwargs.get("base_url") or os.getenv("MEMORY_SERVICE_URL", "http://localhost:13393")
        return RustMemoryProvider(base_url=rust_url, **kwargs)
    if provider_choice == "postgres":
        return PostgresMemoryProvider(
            database_url=kwargs.get("database_url")
            or os.getenv("DATABASE_URL_SESSION")
            or os.getenv("NINAIVALAIGAL_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or DEFAULT_RUST_DATABASE_URL_SESSION,
            **kwargs,
        )

    raise ValueError(f"Unknown memory provider type: {provider_choice}. Use 'rust' or 'postgres'.")


# Global provider instance (lazy-loaded)
_provider_instance: MemoryProvider | None = None


def get_default_memory_provider() -> MemoryProvider:
    """Get the default memory provider instance (singleton)"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_memory_provider()
    return _provider_instance


def reset_memory_provider():
    """Reset the global provider instance (useful for testing)"""
    global _provider_instance
    _provider_instance = None
