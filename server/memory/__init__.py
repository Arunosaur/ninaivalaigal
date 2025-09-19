"""
Memory Substrate Module

Provides pluggable memory providers for different storage backends:
- Native PostgreSQL with pgvector
- HTTP-based mem0 sidecar
- Future: Redis, Elasticsearch, etc.
"""

from .interfaces import MemoryProvider, MemoryItem
from .factory import get_memory_provider

__all__ = [
    'MemoryProvider',
    'MemoryItem', 
    'get_memory_provider'
]
