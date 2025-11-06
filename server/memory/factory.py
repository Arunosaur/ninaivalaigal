#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Memory provider factory with Rust integration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import httpx

from server.config import DEFAULT_RUST_DATABASE_URL_SESSION

from .interfaces import MemoryItem, MemoryProvider, MemoryProviderError
from .providers.postgres import PostgresMemoryProvider


class RustMemoryProvider:
    """HTTP provider that proxies to the Rust Memory Service."""

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
        if self._owns_client:
            await self.client.aclose()

    @staticmethod
    def _build_headers(bearer_token: str | None, required: bool = True) -> dict[str, str]:
        """Build headers for Rust service requests.

        Args:
            bearer_token: Authorization token (optional for health_check)
            required: Whether bearer_token is required (default True)

        Returns:
            Headers dict with Authorization if token provided or required

        Raises:
            MemoryProviderError: If bearer_token is required but not provided
        """
        if required and not bearer_token:
            raise MemoryProviderError("Authorization token required for Rust memory provider requests")
        if bearer_token:
            return {"Authorization": bearer_token}
        return {}

    @staticmethod
    def _map_memory(data: dict[str, Any]) -> MemoryItem:
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
        meta: Mapping[str, Any] | None = None,
        user_id: str | None = None,
        context_id: str | None = None,
        bearer_token: str | None = None,
    ) -> MemoryItem:
        try:
            response = await self.client.post(
                "/memory/remember",
                json={
                    "content": text,
                    "metadata": dict(meta) if meta is not None else {},
                    "user_id": user_id,
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
        k: int = 5,
        user_id: str | None = None,
        context_id: str | None = None,
        bearer_token: str | None = None,
    ) -> list[MemoryItem]:
        payload: dict[str, Any] = {"query": query, "limit": k}
        if user_id is not None:
            payload["user_id"] = user_id
        if context_id is not None:
            payload["context_id"] = context_id
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
        context_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        bearer_token: str | None = None,
    ) -> list[MemoryItem]:
        try:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if user_id is not None:
                params["user_id"] = user_id
            if context_id is not None:
                params["context_id"] = context_id
            response = await self.client.get(
                "/memory/memories",
                params=params,
                headers=self._build_headers(bearer_token),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._error("list", exc) from exc

        data = response.json()
        return [self._map_memory(item) for item in data]

    async def delete(
        self,
        *,
        id: str,
        user_id: str | None = None,
        bearer_token: str | None = None,
    ) -> bool:
        """Delete a memory item by ID.

        Args:
            id: Memory item ID to delete
            user_id: Optional user ID (for multi-tenancy)
            bearer_token: Authorization token

        Returns:
            True if deleted, False if not found
        """
        response = await self.client.delete(
            f"/memory/memories/{id}",
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

    async def health_check(self) -> bool:
        """Check if the Rust memory service is healthy.

        Health check doesn't require authentication, so we don't use bearer_token.
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False


def _flag_enabled(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_memory_provider(provider_type: str | None = None, **kwargs: Any) -> MemoryProvider:
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
    if provider_choice in {"mem0", "http"}:
        raise RuntimeError("Legacy mem0 providers are no longer supported. Use MEMORY_PROVIDER=rust or postgres.")

    raise ValueError(f"Unknown memory provider type: {provider_choice}. Use 'rust' or 'postgres'.")


_provider_instance: MemoryProvider | None = None


def get_default_memory_provider() -> MemoryProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_memory_provider()
    return _provider_instance


def reset_memory_provider() -> None:
    global _provider_instance
    _provider_instance = None
