"""
Memory Provider Factory

Creates memory providers based on configuration.
"""

import os

from .interfaces import MemoryProvider
from .providers.mem0_http import Mem0HttpMemoryProvider
from .providers.postgres import PostgresMemoryProvider


def get_memory_provider(provider_type: str | None = None, **kwargs) -> MemoryProvider:
    """
    Get a memory provider instance based on configuration.

    Args:
        provider_type: Override provider type ('native', 'http')
        **kwargs: Additional configuration for the provider

    Returns:
        MemoryProvider instance
    """
    if provider_type is None:
        provider_type = os.getenv("MEMORY_PROVIDER", "native")

    if provider_type == "http":
        return Mem0HttpMemoryProvider(
            base_url=kwargs.get("base_url")
            or os.getenv("MEM0_URL", "http://127.0.0.1:7070"),
            auth_secret=kwargs.get("auth_secret")
            or os.getenv("MEMORY_SHARED_SECRET", ""),
            **kwargs,
        )
    elif provider_type == "native":
        return PostgresMemoryProvider(
            database_url=kwargs.get("database_url")
            or os.getenv("NINAIVALAIGAL_DATABASE_URL")
            or os.getenv("DATABASE_URL"),
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown memory provider type: {provider_type}")


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
