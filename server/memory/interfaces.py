"""
Memory Provider Interfaces

Defines the contract for memory storage providers.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from typing_extensions import TypedDict


class MemoryItem(TypedDict):
    """Memory item data structure"""
    id: str
    text: str
    meta: Mapping[str, Any]
    user_id: int | None
    context_id: str | None
    created_at: str | None  # ISO format timestamp

class MemoryProvider(Protocol):
    """Protocol for memory storage providers"""

    async def remember(
        self,
        *,
        text: str,
        meta: Mapping[str, Any] | None = None,
        user_id: int | None = None,
        context_id: str | None = None
    ) -> MemoryItem:
        """Store a memory item"""
        ...

    async def recall(
        self,
        *,
        query: str,
        k: int = 5,
        user_id: int | None = None,
        context_id: str | None = None
    ) -> Sequence[MemoryItem]:
        """Retrieve memory items by similarity search"""
        ...

    async def delete(
        self,
        *,
        id: str,
        user_id: int | None = None
    ) -> bool:
        """Delete a memory item"""
        ...

    async def list_memories(
        self,
        *,
        user_id: int | None = None,
        context_id: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[MemoryItem]:
        """List memory items with pagination"""
        ...

    async def health_check(self) -> bool:
        """Check if the provider is healthy"""
        ...

class MemoryProviderError(Exception):
    """Base exception for memory provider errors"""
    pass

class MemoryNotFoundError(MemoryProviderError):
    """Raised when a memory item is not found"""
    pass

class MemoryProviderConnectionError(MemoryProviderError):
    """Raised when connection to provider fails"""
    pass
