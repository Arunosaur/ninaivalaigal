"""
Memory Relevance Ranking Engine - SPEC-031 Implementation
Redis-backed contextual relevance scoring for intelligent memory retrieval
"""

import json
import math
from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from redis_client import RedisClient, get_redis_client

logger = structlog.get_logger(__name__)


class RelevanceEngine:
    """Redis-backed memory relevance scoring and ranking system"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.score_ttl = 3600  # 1 hour
        self.top_cache_ttl = 900  # 15 minutes

        # Scoring weights
        self.weights = {
            "time_decay": 1.0,
            "access_frequency": 2.0,
            "user_importance": 5.0,
            "context_match": 3.0,
        }

    def _make_score_key(self, user_id: str, memory_id: str) -> str:
        """Generate Redis key for memory relevance score"""
        return f"relevance:{user_id}:{memory_id}"

    def _make_top_key(self, user_id: str, context_id: str = None) -> str:
        """Generate Redis key for top-N cached results"""
        if context_id:
            return f"relevance:top:{user_id}:{context_id}"
        return f"relevance:top:{user_id}"

    def _make_access_key(self, user_id: str, memory_id: str) -> str:
        """Generate Redis key for access tracking"""
        return f"access:{user_id}:{memory_id}"

    async def calculate_time_decay_score(self, last_access_time: datetime) -> float:
        """Calculate time decay component of relevance score"""
        try:
            now = datetime.utcnow()
            time_diff = (now - last_access_time).total_seconds()

            # Exponential decay: score = e^(-t/tau) where tau = 1 hour
            tau = 3600  # 1 hour in seconds
            decay_score = math.exp(-time_diff / tau)

            return decay_score * self.weights["time_decay"]

        except Exception as e:
            logger.error("Error calculating time decay score", error=str(e))
            return 0.0

    async def calculate_frequency_score(self, user_id: str, memory_id: str) -> float:
        """Calculate access frequency component of relevance score"""
        try:
            if not self.redis.is_connected:
                return 0.0

            access_key = self._make_access_key(user_id, memory_id)

            # Get access count in the last hour
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)

            # Use sorted set to track accesses with timestamps
            access_count = await self.redis.redis.zcount(
                access_key, hour_ago.timestamp(), now.timestamp()
            )

            # Logarithmic scaling for frequency
            frequency_score = (
                math.log(1 + access_count) * self.weights["access_frequency"]
            )

            return frequency_score

        except Exception as e:
            logger.error(
                "Error calculating frequency score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return 0.0

    async def calculate_importance_score(
        self, memory_metadata: dict[str, Any]
    ) -> float:
        """Calculate user importance flag component of relevance score"""
        try:
            is_important = memory_metadata.get("is_important", False)
            is_pinned = memory_metadata.get("is_pinned", False)
            user_rating = memory_metadata.get("user_rating", 0)

            importance_score = 0.0

            if is_important:
                importance_score += self.weights["user_importance"]

            if is_pinned:
                importance_score += self.weights["user_importance"] * 0.5

            # User rating (1-5 scale)
            if user_rating > 0:
                importance_score += (user_rating / 5.0) * self.weights[
                    "user_importance"
                ]

            return importance_score

        except Exception as e:
            logger.error("Error calculating importance score", error=str(e))
            return 0.0

    async def calculate_context_score(
        self, memory_context: str, current_context: str
    ) -> float:
        """Calculate context matching component of relevance score"""
        try:
            if not memory_context or not current_context:
                return 0.0

            # Simple context matching (can be enhanced with embeddings later)
            if memory_context.lower() == current_context.lower():
                return self.weights["context_match"]

            # Partial context matching
            memory_words = set(memory_context.lower().split())
            current_words = set(current_context.lower().split())

            if memory_words and current_words:
                overlap = len(memory_words.intersection(current_words))
                total = len(memory_words.union(current_words))
                similarity = overlap / total if total > 0 else 0.0

                return similarity * self.weights["context_match"]

            return 0.0

        except Exception as e:
            logger.error("Error calculating context score", error=str(e))
            return 0.0

    async def calculate_relevance_score(
        self,
        user_id: str,
        memory_id: str,
        memory_metadata: dict[str, Any],
        current_context: str = None,
    ) -> float:
        """Calculate comprehensive relevance score for a memory"""
        try:
            # Get last access time
            last_access = memory_metadata.get("last_access_time")
            if isinstance(last_access, str):
                last_access = datetime.fromisoformat(last_access.replace("Z", "+00:00"))
            elif not isinstance(last_access, datetime):
                last_access = datetime.utcnow()

            # Calculate component scores
            time_score = await self.calculate_time_decay_score(last_access)
            frequency_score = await self.calculate_frequency_score(user_id, memory_id)
            importance_score = await self.calculate_importance_score(memory_metadata)

            context_score = 0.0
            if current_context:
                memory_context = memory_metadata.get("context", "")
                context_score = await self.calculate_context_score(
                    memory_context, current_context
                )

            # Combine scores
            total_score = (
                time_score + frequency_score + importance_score + context_score
            )

            logger.debug(
                "Relevance score calculated",
                user_id=user_id,
                memory_id=memory_id,
                time_score=time_score,
                frequency_score=frequency_score,
                importance_score=importance_score,
                context_score=context_score,
                total_score=total_score,
            )

            return total_score

        except Exception as e:
            logger.error(
                "Error calculating relevance score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return 0.0

    async def update_memory_score(
        self,
        user_id: str,
        memory_id: str,
        memory_metadata: dict[str, Any],
        current_context: str = None,
    ) -> float:
        """Update relevance score for a memory in Redis"""
        try:
            if not self.redis.is_connected:
                logger.warning("Redis not connected, cannot update memory score")
                return 0.0

            # Calculate new relevance score
            score = await self.calculate_relevance_score(
                user_id, memory_id, memory_metadata, current_context
            )

            # Store score in Redis with TTL
            score_key = self._make_score_key(user_id, memory_id)
            score_data = {
                "score": score,
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": memory_metadata,
                "context": current_context,
            }

            await self.redis.redis.setex(
                score_key, self.score_ttl, json.dumps(score_data)
            )

            # Track access for frequency calculation
            access_key = self._make_access_key(user_id, memory_id)
            now = datetime.utcnow()

            # Add current access to sorted set
            await self.redis.redis.zadd(
                access_key, {str(now.timestamp()): now.timestamp()}
            )

            # Remove old accesses (older than 24 hours)
            day_ago = now - timedelta(days=1)
            await self.redis.redis.zremrangebyscore(access_key, 0, day_ago.timestamp())

            # Set TTL on access key
            await self.redis.redis.expire(access_key, 86400)  # 24 hours

            # Invalidate top-N cache for this user
            await self._invalidate_top_cache(user_id)

            logger.info(
                "Memory relevance score updated",
                user_id=user_id,
                memory_id=memory_id,
                score=score,
            )

            return score

        except Exception as e:
            logger.error(
                "Error updating memory score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return 0.0

    async def get_memory_score(self, user_id: str, memory_id: str) -> Optional[float]:
        """Get cached relevance score for a memory"""
        try:
            if not self.redis.is_connected:
                return None

            score_key = self._make_score_key(user_id, memory_id)
            score_data = await self.redis.redis.get(score_key)

            if score_data:
                data = json.loads(score_data)
                return data.get("score", 0.0)

            return None

        except Exception as e:
            logger.error(
                "Error getting memory score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return None

    async def get_top_memories(
        self, user_id: str, limit: int = 10, context_id: str = None
    ) -> list[tuple[str, float]]:
        """Get top-N most relevant memories for a user"""
        try:
            if not self.redis.is_connected:
                return []

            top_key = self._make_top_key(user_id, context_id)

            # Try to get from cache first
            cached_top = await self.redis.redis.get(top_key)
            if cached_top:
                data = json.loads(cached_top)
                logger.debug(
                    "Top memories cache hit", user_id=user_id, context_id=context_id
                )
                return data[:limit]

            # Cache miss - need to rebuild
            logger.debug("Top memories cache miss, rebuilding", user_id=user_id)

            # Get all relevance scores for this user
            pattern = f"relevance:{user_id}:*"
            score_keys = await self.redis.redis.keys(pattern)

            memory_scores = []
            for key in score_keys:
                try:
                    score_data = await self.redis.redis.get(key)
                    if score_data:
                        data = json.loads(score_data)
                        memory_id = key.split(":")[-1]  # Extract memory_id from key
                        score = data.get("score", 0.0)
                        memory_scores.append((memory_id, score))
                except Exception as e:
                    logger.warning("Error processing score key", key=key, error=str(e))
                    continue

            # Sort by score (descending)
            memory_scores.sort(key=lambda x: x[1], reverse=True)

            # Cache the results
            await self.redis.redis.setex(
                top_key, self.top_cache_ttl, json.dumps(memory_scores)
            )

            logger.info(
                "Top memories rebuilt and cached",
                user_id=user_id,
                context_id=context_id,
                total_memories=len(memory_scores),
            )

            return memory_scores[:limit]

        except Exception as e:
            logger.error("Error getting top memories", user_id=user_id, error=str(e))
            return []

    async def _invalidate_top_cache(self, user_id: str):
        """Invalidate top-N cache for a user"""
        try:
            if not self.redis.is_connected:
                return

            # Delete all top cache keys for this user
            pattern = f"relevance:top:{user_id}*"
            keys = await self.redis.redis.keys(pattern)

            if keys:
                await self.redis.redis.delete(*keys)
                logger.debug(
                    "Top cache invalidated", user_id=user_id, keys_deleted=len(keys)
                )

        except Exception as e:
            logger.error("Error invalidating top cache", user_id=user_id, error=str(e))

    async def get_relevance_stats(self, user_id: str) -> dict[str, Any]:
        """Get relevance engine statistics for a user"""
        try:
            if not self.redis.is_connected:
                return {"error": "Redis not connected"}

            # Count relevance scores
            pattern = f"relevance:{user_id}:*"
            score_keys = await self.redis.redis.keys(pattern)

            # Count access tracking keys
            access_pattern = f"access:{user_id}:*"
            access_keys = await self.redis.redis.keys(access_pattern)

            # Check top cache status
            top_key = self._make_top_key(user_id)
            top_cached = await self.redis.redis.exists(top_key)

            return {
                "user_id": user_id,
                "scored_memories": len(score_keys),
                "tracked_accesses": len(access_keys),
                "top_cache_exists": bool(top_cached),
                "score_ttl": self.score_ttl,
                "top_cache_ttl": self.top_cache_ttl,
                "weights": self.weights,
            }

        except Exception as e:
            logger.error("Error getting relevance stats", user_id=user_id, error=str(e))
            return {"error": str(e)}

    async def update_memory_feedback_score(
        self,
        user_id: int,
        memory_id: str,
        feedback_multiplier: float,
        feedback_data: dict
    ):
        """Update memory relevance score based on feedback (SPEC-040 integration)"""
        try:
            # Get current relevance score
            score_key = f"relevance:{user_id}:{memory_id}"
            current_score = await self.redis_client.get(score_key)
            
            if current_score:
                current_score = float(current_score)
            else:
                # Calculate base relevance score if not cached
                current_score = await self._calculate_base_relevance_score(
                    user_id, memory_id
                )
            
            # Apply feedback multiplier
            adjusted_score = current_score * feedback_multiplier
            
            # Store updated score with feedback metadata
            feedback_key = f"feedback:relevance:{user_id}:{memory_id}"
            feedback_info = {
                "base_score": current_score,
                "feedback_multiplier": feedback_multiplier,
                "adjusted_score": adjusted_score,
                "feedback_data": feedback_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update relevance score with feedback adjustment
            await self.redis_client.setex(
                score_key,
                self.score_ttl,
                str(adjusted_score)
            )
            
            # Store feedback metadata
            await self.redis_client.setex(
                feedback_key,
                self.score_ttl,
                json.dumps(feedback_info)
            )
            
            # Invalidate top-N cache to force recalculation
            top_key = f"relevance:top:{user_id}"
            await self.redis_client.delete(top_key)
            
            logger.info(
                "Memory relevance score updated with feedback",
                user_id=user_id,
                memory_id=memory_id,
                base_score=current_score,
                feedback_multiplier=feedback_multiplier,
                adjusted_score=adjusted_score
            )
            
        except Exception as e:
            logger.error(
                "Error updating memory feedback score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e)
            )
            raise

    async def _calculate_base_relevance_score(
        self, 
        user_id: int, 
        memory_id: str
    ) -> float:
        """Calculate base relevance score for a memory"""
        try:
            # This is a simplified version - in practice, this would use
            # the full relevance calculation logic
            
            # Get access frequency
            access_key = f"access:{user_id}:{memory_id}"
            access_count = await self.redis_client.zcard(access_key)
            
            # Calculate basic score based on access frequency
            frequency_score = min(access_count * 0.1, 1.0)
            
            # Apply time decay (assume recent if no specific timestamp)
            time_score = 0.8  # Default recent score
            
            # Calculate base score
            base_score = (
                frequency_score * self.weights["frequency"] +
                time_score * self.weights["time_decay"]
            )
            
            return base_score
            
        except Exception as e:
            logger.error(
                "Error calculating base relevance score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e)
            )
            return 0.5  # Default neutral score


# Global relevance engine instance
relevance_engine = None


async def get_relevance_engine() -> RelevanceEngine:
    """Dependency injection for relevance engine"""
    global relevance_engine

    if relevance_engine is None:
        redis_client = await get_redis_client()
        relevance_engine = RelevanceEngine(redis_client)

    return relevance_engine


# Convenience functions for common operations
async def update_memory_relevance(
    user_id: str,
    memory_id: str,
    memory_metadata: dict[str, Any],
    current_context: str = None,
) -> float:
    """Update relevance score for a memory"""
    engine = await get_relevance_engine()
    return await engine.update_memory_score(
        user_id, memory_id, memory_metadata, current_context
    )


async def get_relevant_memories(
    user_id: str, limit: int = 10, context_id: str = None
) -> list[tuple[str, float]]:
    """Get top relevant memories for a user"""
    engine = await get_relevance_engine()
    return await engine.get_top_memories(user_id, limit, context_id)
