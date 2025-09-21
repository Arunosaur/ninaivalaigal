"""
mem0 HTTP Memory Provider

HTTP-based implementation that forwards requests to mem0 sidecar service.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import httpx

from ..interfaces import (
    MemoryItem,
    MemoryNotFoundError,
    MemoryProviderConnectionError,
    MemoryProviderError,
)


class Mem0HttpMemoryProvider:
    """HTTP-based memory provider that forwards to mem0 sidecar"""

    def __init__(self, base_url: str, auth_secret: str = "", **kwargs):
        self.base_url = base_url.rstrip("/")
        self.auth_secret = auth_secret
        self.timeout = kwargs.get("timeout", 30.0)

        # Create HTTP client
        headers = {}
        if auth_secret:
            headers["Authorization"] = f"Bearer {auth_secret}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=self.timeout
        )

    async def remember(
        self,
        *,
        text: str,
        meta: Mapping[str, Any] | None = None,
        user_id: int | None = None,
        context_id: str | None = None,
    ) -> MemoryItem:
        """Store a memory item via mem0 HTTP API"""
        try:
            payload = {
                "text": text,
                "metadata": meta or {},
                "user_id": str(user_id) if user_id else None,
                "context_id": context_id,
            }

            response = await self.client.post("/add", json=payload)
            response.raise_for_status()

            result = response.json()

            # Transform mem0 response to our MemoryItem format
            return MemoryItem(
                id=result.get("id", ""),
                text=text,
                meta=meta or {},
                user_id=user_id,
                context_id=context_id,
                created_at=datetime.utcnow().isoformat(),
            )

        except httpx.HTTPError as e:
            raise MemoryProviderConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            raise MemoryProviderError(f"Failed to store memory: {e}")

    async def recall(
        self,
        *,
        query: str,
        k: int = 5,
        user_id: int | None = None,
        context_id: str | None = None,
    ) -> Sequence[MemoryItem]:
        """Retrieve memory items via mem0 HTTP API"""
        try:
            payload = {
                "query": query,
                "limit": k,
                "user_id": str(user_id) if user_id else None,
                "context_id": context_id,
            }

            response = await self.client.post("/search", json=payload)
            response.raise_for_status()

            result = response.json()
            memories = []

            # Transform mem0 response to our MemoryItem format
            for item in result.get("results", []):
                memories.append(
                    MemoryItem(
                        id=item.get("id", ""),
                        text=item.get("text", ""),
                        meta=item.get("metadata", {}),
                        user_id=user_id,
                        context_id=context_id,
                        created_at=item.get("created_at"),
                    )
                )

            return memories

        except httpx.HTTPError as e:
            raise MemoryProviderConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            raise MemoryProviderError(f"Failed to recall memories: {e}")

    async def delete(self, *, id: str, user_id: int | None = None) -> bool:
        """Delete a memory item via mem0 HTTP API"""
        try:
            payload = {"memory_id": id, "user_id": str(user_id) if user_id else None}

            response = await self.client.post("/delete", json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("deleted", False)

        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 404:
                raise MemoryNotFoundError(f"Memory not found: {id}")
            raise MemoryProviderConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            raise MemoryProviderError(f"Failed to delete memory: {e}")

    async def list_memories(
        self,
        *,
        user_id: int | None = None,
        context_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MemoryItem]:
        """List memory items via mem0 HTTP API"""
        try:
            params = {"limit": limit, "offset": offset}

            if user_id is not None:
                params["user_id"] = str(user_id)

            if context_id is not None:
                params["context_id"] = context_id

            response = await self.client.get("/memories", params=params)
            response.raise_for_status()

            result = response.json()
            memories = []

            for item in result.get("memories", []):
                memories.append(
                    MemoryItem(
                        id=item.get("id", ""),
                        text=item.get("text", ""),
                        meta=item.get("metadata", {}),
                        user_id=user_id,
                        context_id=context_id,
                        created_at=item.get("created_at"),
                    )
                )

            return memories

        except httpx.HTTPError as e:
            raise MemoryProviderConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            raise MemoryProviderError(f"Failed to list memories: {e}")

    async def health_check(self) -> bool:
        """Check if mem0 HTTP service is healthy"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except:
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
