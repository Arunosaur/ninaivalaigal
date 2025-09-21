"""
Memory Token Preloading Engine - SPEC-038 Implementation
Intelligent cache warming for optimal memory retrieval performance
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any

import structlog
from redis_client import RedisClient, get_redis_client
from relevance_engine import RelevanceEngine, get_relevance_engine

logger = structlog.get_logger(__name__)


class PreloadingConfig:
    """Configuration for memory preloading strategies"""

    def __init__(self):
        self.enabled = os.getenv("PRELOAD_ENABLED", "true").lower() == "true"
        self.startup_preload = os.getenv("PRELOAD_STARTUP", "true").lower() == "true"
        self.background_refresh = (
            os.getenv("PRELOAD_BACKGROUND", "true").lower() == "true"
        )
        self.max_memories_per_user = int(os.getenv("PRELOAD_MAX_MEMORIES", "100"))
        self.refresh_interval_minutes = int(os.getenv("PRELOAD_REFRESH_INTERVAL", "30"))

        # Preloading strategy weights
        self.strategy_weights = {
            "recent_memories": 0.4,  # 40% recent memories
            "frequent_memories": 0.3,  # 30% high-frequency memories
            "important_memories": 0.2,  # 20% user-flagged important
            "context_relevant": 0.1,  # 10% context-relevant
        }

        # TTL settings for different preload types
        self.ttl_settings = {
            "recent": 7200,  # 2 hours
            "frequent": 14400,  # 4 hours
            "important": 21600,  # 6 hours
            "trending": 3600,  # 1 hour
        }


class MemoryPreloadingEngine:
    """Redis-backed memory preloading system for performance optimization"""

    def __init__(self, redis_client: RedisClient, relevance_engine: RelevanceEngine):
        self.redis = redis_client
        self.relevance = relevance_engine
        self.config = PreloadingConfig()
        self.preload_prefix = "preload:"

    def _make_preload_key(self, user_id: str, strategy: str) -> str:
        """Generate Redis key for preloaded memories"""
        return f"{self.preload_prefix}{user_id}:{strategy}"

    def _make_status_key(self, user_id: str) -> str:
        """Generate Redis key for preloading status"""
        return f"{self.preload_prefix}status:{user_id}"

    async def get_recent_memories(
        self, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recently accessed memories for preloading"""
        try:
            # In a real implementation, this would query the database
            # For now, return sample data structure
            recent_memories = []

            # Simulate recent memories with metadata
            for i in range(min(limit, 20)):  # Simulate 20 recent memories
                memory = {
                    "memory_id": f"recent_mem_{user_id}_{i}",
                    "content": f"Recent memory {i} for user {user_id}",
                    "last_access_time": (
                        datetime.utcnow() - timedelta(hours=i)
                    ).isoformat(),
                    "access_count": 10 - i,  # More recent = more accesses
                    "is_important": i < 5,  # First 5 are important
                    "context": "recent_work",
                    "relevance_score": 0.9 - (i * 0.04),  # Decreasing relevance
                }
                recent_memories.append(memory)

            logger.debug(
                "Retrieved recent memories for preloading",
                user_id=user_id,
                count=len(recent_memories),
            )

            return recent_memories

        except Exception as e:
            logger.error("Error getting recent memories", user_id=user_id, error=str(e))
            return []

    async def get_frequent_memories(
        self, user_id: str, limit: int = 30
    ) -> list[dict[str, Any]]:
        """Get high-frequency memories for preloading"""
        try:
            # Simulate frequent memories based on access patterns
            frequent_memories = []

            for i in range(min(limit, 15)):  # Simulate 15 frequent memories
                memory = {
                    "memory_id": f"freq_mem_{user_id}_{i}",
                    "content": f"Frequently accessed memory {i} for user {user_id}",
                    "last_access_time": (
                        datetime.utcnow() - timedelta(days=i + 1)
                    ).isoformat(),
                    "access_count": 50 - (i * 2),  # High access counts
                    "is_important": True,
                    "context": "frequent_tasks",
                    "relevance_score": 0.95 - (i * 0.03),  # High relevance
                }
                frequent_memories.append(memory)

            logger.debug(
                "Retrieved frequent memories for preloading",
                user_id=user_id,
                count=len(frequent_memories),
            )

            return frequent_memories

        except Exception as e:
            logger.error(
                "Error getting frequent memories", user_id=user_id, error=str(e)
            )
            return []

    async def get_important_memories(
        self, user_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get user-flagged important memories for preloading"""
        try:
            # Simulate important/pinned memories
            important_memories = []

            for i in range(min(limit, 10)):  # Simulate 10 important memories
                memory = {
                    "memory_id": f"imp_mem_{user_id}_{i}",
                    "content": f"Important memory {i} for user {user_id}",
                    "last_access_time": (
                        datetime.utcnow() - timedelta(days=i * 2)
                    ).isoformat(),
                    "access_count": 25 + i,
                    "is_important": True,
                    "is_pinned": True,
                    "user_rating": 5,  # Highest rating
                    "context": "important_projects",
                    "relevance_score": 1.0,  # Maximum relevance
                }
                important_memories.append(memory)

            logger.debug(
                "Retrieved important memories for preloading",
                user_id=user_id,
                count=len(important_memories),
            )

            return important_memories

        except Exception as e:
            logger.error(
                "Error getting important memories", user_id=user_id, error=str(e)
            )
            return []

    async def select_memories_for_preloading(
        self, user_id: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Select memories for preloading based on configured strategies"""
        try:
            if not self.config.enabled:
                return {}

            max_memories = self.config.max_memories_per_user
            strategies = self.config.strategy_weights

            # Calculate memory allocation per strategy
            recent_limit = int(max_memories * strategies["recent_memories"])
            frequent_limit = int(max_memories * strategies["frequent_memories"])
            important_limit = int(max_memories * strategies["important_memories"])

            # Get memories for each strategy
            recent_memories = await self.get_recent_memories(user_id, recent_limit)
            frequent_memories = await self.get_frequent_memories(
                user_id, frequent_limit
            )
            important_memories = await self.get_important_memories(
                user_id, important_limit
            )

            selected_memories = {
                "recent": recent_memories,
                "frequent": frequent_memories,
                "important": important_memories,
            }

            total_selected = sum(
                len(memories) for memories in selected_memories.values()
            )

            logger.info(
                "Selected memories for preloading",
                user_id=user_id,
                total_memories=total_selected,
                recent=len(recent_memories),
                frequent=len(frequent_memories),
                important=len(important_memories),
            )

            return selected_memories

        except Exception as e:
            logger.error(
                "Error selecting memories for preloading", user_id=user_id, error=str(e)
            )
            return {}

    async def preload_memories_to_cache(
        self, user_id: str, memories_by_strategy: dict[str, list[dict[str, Any]]]
    ) -> dict[str, int]:
        """Preload selected memories into Redis cache"""
        try:
            if not self.redis.is_connected:
                logger.warning(
                    "Redis not connected, skipping preloading", user_id=user_id
                )
                return {}

            preload_stats = {}

            for strategy, memories in memories_by_strategy.items():
                if not memories:
                    continue

                preload_key = self._make_preload_key(user_id, strategy)
                ttl = self.config.ttl_settings.get(strategy, 3600)

                # Store memories in Redis as a JSON list
                memories_data = {
                    "memories": memories,
                    "preloaded_at": datetime.utcnow().isoformat(),
                    "strategy": strategy,
                    "ttl": ttl,
                    "user_id": user_id,
                }

                await self.redis.redis.setex(
                    preload_key, ttl, json.dumps(memories_data)
                )

                # Also cache individual memories for fast lookup
                for memory in memories:
                    memory_key = f"memory:{user_id}:{memory['memory_id']}"
                    await self.redis.redis.setex(memory_key, ttl, json.dumps(memory))

                preload_stats[strategy] = len(memories)

                logger.debug(
                    "Preloaded memories to cache",
                    user_id=user_id,
                    strategy=strategy,
                    count=len(memories),
                    ttl=ttl,
                )

            # Update preloading status
            await self._update_preload_status(user_id, preload_stats)

            total_preloaded = sum(preload_stats.values())
            logger.info(
                "Memory preloading completed",
                user_id=user_id,
                total_preloaded=total_preloaded,
                strategies=preload_stats,
            )

            return preload_stats

        except Exception as e:
            logger.error(
                "Error preloading memories to cache", user_id=user_id, error=str(e)
            )
            return {}

    async def _update_preload_status(self, user_id: str, preload_stats: dict[str, int]):
        """Update preloading status in Redis"""
        try:
            status_key = self._make_status_key(user_id)
            status_data = {
                "user_id": user_id,
                "last_preload": datetime.utcnow().isoformat(),
                "preload_stats": preload_stats,
                "total_memories": sum(preload_stats.values()),
                "config": {
                    "max_memories": self.config.max_memories_per_user,
                    "strategies": self.config.strategy_weights,
                },
            }

            # Status expires after 24 hours
            await self.redis.redis.setex(status_key, 86400, json.dumps(status_data))

        except Exception as e:
            logger.error("Error updating preload status", user_id=user_id, error=str(e))

    async def get_preloaded_memory(
        self, user_id: str, memory_id: str
    ) -> dict[str, Any] | None:
        """Get a preloaded memory from cache"""
        try:
            if not self.redis.is_connected:
                return None

            memory_key = f"memory:{user_id}:{memory_id}"
            cached_memory = await self.redis.redis.get(memory_key)

            if cached_memory:
                logger.debug(
                    "Preloaded memory cache hit", user_id=user_id, memory_id=memory_id
                )
                return json.loads(cached_memory)

            return None

        except Exception as e:
            logger.error(
                "Error getting preloaded memory",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return None

    async def get_preload_status(self, user_id: str) -> dict[str, Any]:
        """Get preloading status for a user"""
        try:
            if not self.redis.is_connected:
                return {"error": "Redis not connected"}

            status_key = self._make_status_key(user_id)
            status_data = await self.redis.redis.get(status_key)

            if status_data:
                return json.loads(status_data)

            return {
                "user_id": user_id,
                "status": "not_preloaded",
                "message": "No preloading data found",
            }

        except Exception as e:
            logger.error("Error getting preload status", user_id=user_id, error=str(e))
            return {"error": str(e)}

    async def trigger_preloading(self, user_id: str) -> dict[str, Any]:
        """Manually trigger memory preloading for a user"""
        try:
            logger.info("Triggering memory preloading", user_id=user_id)

            # Select memories for preloading
            selected_memories = await self.select_memories_for_preloading(user_id)

            if not selected_memories:
                return {
                    "user_id": user_id,
                    "status": "skipped",
                    "message": "No memories selected for preloading",
                }

            # Preload memories to cache
            preload_stats = await self.preload_memories_to_cache(
                user_id, selected_memories
            )

            return {
                "user_id": user_id,
                "status": "completed",
                "preload_stats": preload_stats,
                "total_memories": sum(preload_stats.values()),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error triggering preloading", user_id=user_id, error=str(e))
            return {"user_id": user_id, "status": "failed", "error": str(e)}

    async def background_cache_warming(self, user_ids: list[str] = None):
        """Background task to warm cache for active users"""
        try:
            if not self.config.background_refresh:
                logger.debug("Background cache warming disabled")
                return

            logger.info(
                "Starting background cache warming",
                user_count=len(user_ids) if user_ids else "all",
            )

            # If no specific users provided, this would query active users from database
            if not user_ids:
                # Simulate active users for demo
                user_ids = ["user_1", "user_2", "user_3"]

            warming_results = []

            for user_id in user_ids:
                try:
                    result = await self.trigger_preloading(user_id)
                    warming_results.append(result)

                    # Small delay between users to avoid overwhelming Redis
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(
                        "Error warming cache for user", user_id=user_id, error=str(e)
                    )
                    warming_results.append(
                        {"user_id": user_id, "status": "failed", "error": str(e)}
                    )

            successful_warmings = sum(
                1 for r in warming_results if r.get("status") == "completed"
            )

            logger.info(
                "Background cache warming completed",
                total_users=len(user_ids),
                successful=successful_warmings,
                failed=len(user_ids) - successful_warmings,
            )

            return warming_results

        except Exception as e:
            logger.error("Error in background cache warming", error=str(e))
            return []


# Global preloading engine instance
preloading_engine = None


async def get_preloading_engine() -> MemoryPreloadingEngine:
    """Dependency injection for preloading engine"""
    global preloading_engine

    if preloading_engine is None:
        redis_client = await get_redis_client()
        relevance_engine = await get_relevance_engine()
        preloading_engine = MemoryPreloadingEngine(redis_client, relevance_engine)

    return preloading_engine


# Convenience functions for common operations
async def trigger_user_preloading(user_id: str) -> dict[str, Any]:
    """Trigger preloading for a specific user"""
    engine = await get_preloading_engine()
    return await engine.trigger_preloading(user_id)


async def get_user_preload_status(user_id: str) -> dict[str, Any]:
    """Get preloading status for a user"""
    engine = await get_preloading_engine()
    return await engine.get_preload_status(user_id)


async def get_preloaded_memory(user_id: str, memory_id: str) -> dict[str, Any] | None:
    """Get a preloaded memory from cache"""
    engine = await get_preloading_engine()
    return await engine.get_preloaded_memory(user_id, memory_id)
