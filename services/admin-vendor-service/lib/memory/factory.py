#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Memory Provider Factory

Creates memory providers based on configuration.
"""

import os

from config import DEFAULT_RUST_DATABASE_URL_SESSION

from .interfaces import MemoryProvider
from .providers.postgres import PostgresMemoryProvider


def get_memory_provider(provider_type: str | None = None, **kwargs) -> MemoryProvider:
    """
    Get a memory provider instance based on configuration.

    Args:
    provider_type: Override provider type ('native', 'postgres', 'rust')
        **kwargs: Additional configuration for the provider

    Returns:
        MemoryProvider instance
    """
    if provider_type is None:
        provider_type = os.getenv("MEMORY_PROVIDER", "postgres")

    provider_choice = provider_type.strip().lower()

    if provider_choice in {"native", "postgres", "rust"}:
        return PostgresMemoryProvider(
            database_url=kwargs.get("database_url")
            or os.getenv("DATABASE_URL_SESSION")
            or os.getenv("NINAIVALAIGAL_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or DEFAULT_RUST_DATABASE_URL_SESSION,
            **kwargs,
        )
    if provider_choice in {"mem0", "http"}:
        raise RuntimeError("Legacy mem0 providers are no longer supported. Use MEMORY_PROVIDER=postgres.")
    raise ValueError(f"Unknown memory provider type: {provider_choice}. Use 'postgres' or 'rust'.")


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
