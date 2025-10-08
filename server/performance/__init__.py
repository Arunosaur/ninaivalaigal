"""
Performance optimization package for ninaivalaigal.

Provides caching, query optimization, and performance monitoring utilities.
"""

from .async_optimizer import AsyncOperationOptimizer, get_async_optimizer
from .connection_pool import OptimizedDatabaseManager, get_optimized_db_manager
from .integration import (
    PerformanceManager,
    get_performance_manager,
    initialize_performance_optimizations,
)
from .query_cache import QueryCache, QueryCacheDecorator

__all__ = [
    "QueryCache",
    "QueryCacheDecorator",
    "AsyncOperationOptimizer",
    "get_async_optimizer",
    "OptimizedDatabaseManager",
    "get_optimized_db_manager",
    "PerformanceManager",
    "get_performance_manager",
    "initialize_performance_optimizations",
]
