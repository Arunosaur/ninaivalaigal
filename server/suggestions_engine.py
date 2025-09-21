"""
SPEC-041: Intelligent Related Memory Suggestions Engine

Provides intelligent memory suggestions based on:
- Content similarity (embeddings-based)
- User behavior patterns (collaborative filtering)
- Feedback data integration (SPEC-040)
- Relevance scores (SPEC-031)
- Access patterns and context

Key Features:
- Multi-algorithm suggestion generation
- Redis-cached performance optimization
- Feedback-aware ranking
- Context-sensitive recommendations
- Real-time and batch suggestion modes
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from feedback_engine import get_feedback_engine
from redis_client import get_redis_client
from relevance_engine import get_relevance_engine

logger = structlog.get_logger(__name__)


class SuggestionType(Enum):
    """Types of suggestion algorithms"""

    CONTENT_SIMILARITY = "content_similarity"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    FEEDBACK_BASED = "feedback_based"
    CONTEXT_AWARE = "context_aware"
    HYBRID = "hybrid"


class SuggestionReason(Enum):
    """Reasons for suggesting a memory"""

    SIMILAR_CONTENT = "similar_content"
    SIMILAR_USERS = "similar_users"
    HIGH_FEEDBACK = "high_feedback"
    RECENT_ACCESS = "recent_access"
    CONTEXTUAL_MATCH = "contextual_match"
    TRENDING = "trending"


@dataclass
class MemorySuggestion:
    """Individual memory suggestion with metadata"""

    memory_id: str
    title: str
    content_preview: str
    similarity_score: float
    suggestion_type: SuggestionType
    reasons: list[SuggestionReason]
    confidence: float
    metadata: dict[str, Any]
    created_at: datetime
    last_accessed: datetime | None = None
    feedback_score: float | None = None
    relevance_score: float | None = None


@dataclass
class SuggestionRequest:
    """Request parameters for generating suggestions"""

    user_id: int
    memory_id: str | None = None  # Base memory for similarity
    query: str | None = None  # Query-based suggestions
    context_id: str | None = None
    limit: int = 10
    suggestion_types: list[SuggestionType] = None
    exclude_memory_ids: list[str] = None
    min_confidence: float = 0.3


@dataclass
class SuggestionResponse:
    """Response containing suggested memories"""

    suggestions: list[MemorySuggestion]
    total_found: int
    algorithms_used: list[SuggestionType]
    generation_time_ms: float
    cached: bool
    metadata: dict[str, Any]


class IntelligentSuggestionsEngine:
    """Core engine for generating intelligent memory suggestions"""

    def __init__(self):
        self.redis_client = None
        self.relevance_engine = None
        self.feedback_engine = None
        self.cache_ttl = 900  # 15 minutes cache TTL

        # Algorithm weights for hybrid suggestions
        self.algorithm_weights = {
            SuggestionType.CONTENT_SIMILARITY: 0.4,
            SuggestionType.COLLABORATIVE_FILTERING: 0.3,
            SuggestionType.FEEDBACK_BASED: 0.2,
            SuggestionType.CONTEXT_AWARE: 0.1,
        }

        # Confidence thresholds
        self.confidence_thresholds = {
            SuggestionType.CONTENT_SIMILARITY: 0.7,
            SuggestionType.COLLABORATIVE_FILTERING: 0.6,
            SuggestionType.FEEDBACK_BASED: 0.8,
            SuggestionType.CONTEXT_AWARE: 0.5,
        }

    async def initialize(self):
        """Initialize Redis connections and dependencies"""
        try:
            self.redis_client = await get_redis_client()
            self.relevance_engine = await get_relevance_engine()
            self.feedback_engine = await get_feedback_engine()
            logger.info("Suggestions engine initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize suggestions engine", error=str(e))
            raise

    async def generate_suggestions(
        self, request: SuggestionRequest
    ) -> SuggestionResponse:
        """Generate intelligent memory suggestions"""

        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_response = await self._get_cached_suggestions(cache_key)

            if cached_response:
                logger.info(
                    "Suggestions served from cache",
                    user_id=request.user_id,
                    cache_key=cache_key,
                )
                return cached_response

            # Generate suggestions using multiple algorithms
            all_suggestions = []
            algorithms_used = []

            # Determine which algorithms to use
            suggestion_types = request.suggestion_types or [
                SuggestionType.CONTENT_SIMILARITY,
                SuggestionType.COLLABORATIVE_FILTERING,
                SuggestionType.FEEDBACK_BASED,
            ]

            # Generate suggestions from each algorithm
            for suggestion_type in suggestion_types:
                try:
                    suggestions = await self._generate_by_algorithm(
                        request, suggestion_type
                    )
                    all_suggestions.extend(suggestions)
                    algorithms_used.append(suggestion_type)
                except Exception as e:
                    logger.warning(
                        "Algorithm failed, continuing with others",
                        algorithm=suggestion_type.value,
                        error=str(e),
                    )

            # Rank and deduplicate suggestions
            final_suggestions = await self._rank_and_filter_suggestions(
                all_suggestions, request
            )

            # Create response
            generation_time = (time.time() - start_time) * 1000
            response = SuggestionResponse(
                suggestions=final_suggestions[: request.limit],
                total_found=len(all_suggestions),
                algorithms_used=algorithms_used,
                generation_time_ms=generation_time,
                cached=False,
                metadata={
                    "request_id": f"sugg_{int(time.time() * 1000)}",
                    "user_id": request.user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Cache the response
            await self._cache_suggestions(cache_key, response)

            logger.info(
                "Suggestions generated successfully",
                user_id=request.user_id,
                total_found=len(all_suggestions),
                final_count=len(final_suggestions),
                generation_time_ms=generation_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Failed to generate suggestions", user_id=request.user_id, error=str(e)
            )
            raise

    async def _generate_by_algorithm(
        self, request: SuggestionRequest, algorithm: SuggestionType
    ) -> list[MemorySuggestion]:
        """Generate suggestions using a specific algorithm"""

        if algorithm == SuggestionType.CONTENT_SIMILARITY:
            return await self._content_similarity_suggestions(request)
        elif algorithm == SuggestionType.COLLABORATIVE_FILTERING:
            return await self._collaborative_filtering_suggestions(request)
        elif algorithm == SuggestionType.FEEDBACK_BASED:
            return await self._feedback_based_suggestions(request)
        elif algorithm == SuggestionType.CONTEXT_AWARE:
            return await self._context_aware_suggestions(request)
        else:
            return []

    async def _content_similarity_suggestions(
        self, request: SuggestionRequest
    ) -> list[MemorySuggestion]:
        """Generate suggestions based on content similarity"""

        suggestions = []

        try:
            # This would use actual embeddings in production
            # For now, simulate content similarity based on stored data

            if request.memory_id:
                # Find memories similar to a specific memory
                similar_memories = await self._find_similar_memories_by_content(
                    request.user_id, request.memory_id
                )
            elif request.query:
                # Find memories similar to a query
                similar_memories = await self._find_similar_memories_by_query(
                    request.user_id, request.query
                )
            else:
                # Find generally popular/relevant memories
                similar_memories = await self._find_popular_memories(request.user_id)

            for memory_data in similar_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    title=memory_data.get("title", "Untitled Memory"),
                    content_preview=memory_data.get("content", "")[:200] + "...",
                    similarity_score=memory_data.get("similarity", 0.8),
                    suggestion_type=SuggestionType.CONTENT_SIMILARITY,
                    reasons=[SuggestionReason.SIMILAR_CONTENT],
                    confidence=memory_data.get("similarity", 0.8),
                    metadata={"algorithm": "content_similarity"},
                    created_at=datetime.utcnow(),
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(
                "Content similarity suggestions failed",
                user_id=request.user_id,
                error=str(e),
            )

        return suggestions

    async def _collaborative_filtering_suggestions(
        self, request: SuggestionRequest
    ) -> list[MemorySuggestion]:
        """Generate suggestions based on similar user behavior"""

        suggestions = []

        try:
            # Find users with similar access patterns
            similar_users = await self._find_similar_users(request.user_id)

            # Get memories accessed by similar users
            for user_id in similar_users:
                user_memories = await self._get_user_popular_memories(user_id)

                for memory_data in user_memories:
                    # Skip if user already has this memory
                    if await self._user_has_memory(request.user_id, memory_data["id"]):
                        continue

                    suggestion = MemorySuggestion(
                        memory_id=memory_data["id"],
                        title=memory_data.get("title", "Untitled Memory"),
                        content_preview=memory_data.get("content", "")[:200] + "...",
                        similarity_score=memory_data.get("popularity", 0.7),
                        suggestion_type=SuggestionType.COLLABORATIVE_FILTERING,
                        reasons=[SuggestionReason.SIMILAR_USERS],
                        confidence=0.6,
                        metadata={
                            "algorithm": "collaborative_filtering",
                            "similar_user_id": user_id,
                        },
                        created_at=datetime.utcnow(),
                    )
                    suggestions.append(suggestion)

        except Exception as e:
            logger.error(
                "Collaborative filtering suggestions failed",
                user_id=request.user_id,
                error=str(e),
            )

        return suggestions

    async def _feedback_based_suggestions(
        self, request: SuggestionRequest
    ) -> list[MemorySuggestion]:
        """Generate suggestions based on high-feedback memories"""

        suggestions = []

        try:
            # Get memories with high positive feedback
            high_feedback_memories = await self._get_high_feedback_memories(
                request.user_id
            )

            for memory_data in high_feedback_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    title=memory_data.get("title", "Untitled Memory"),
                    content_preview=memory_data.get("content", "")[:200] + "...",
                    similarity_score=memory_data.get("feedback_score", 0.8),
                    suggestion_type=SuggestionType.FEEDBACK_BASED,
                    reasons=[SuggestionReason.HIGH_FEEDBACK],
                    confidence=0.8,
                    metadata={
                        "algorithm": "feedback_based",
                        "feedback_score": memory_data.get("feedback_score"),
                    },
                    created_at=datetime.utcnow(),
                    feedback_score=memory_data.get("feedback_score"),
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(
                "Feedback-based suggestions failed",
                user_id=request.user_id,
                error=str(e),
            )

        return suggestions

    async def _context_aware_suggestions(
        self, request: SuggestionRequest
    ) -> list[MemorySuggestion]:
        """Generate suggestions based on current context"""

        suggestions = []

        try:
            if not request.context_id:
                return suggestions

            # Find memories accessed in similar contexts
            context_memories = await self._get_context_memories(
                request.user_id, request.context_id
            )

            for memory_data in context_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    title=memory_data.get("title", "Untitled Memory"),
                    content_preview=memory_data.get("content", "")[:200] + "...",
                    similarity_score=memory_data.get("context_relevance", 0.6),
                    suggestion_type=SuggestionType.CONTEXT_AWARE,
                    reasons=[SuggestionReason.CONTEXTUAL_MATCH],
                    confidence=0.5,
                    metadata={
                        "algorithm": "context_aware",
                        "context_id": request.context_id,
                    },
                    created_at=datetime.utcnow(),
                )
                suggestions.append(suggestion)

        except Exception as e:
            logger.error(
                "Context-aware suggestions failed",
                user_id=request.user_id,
                error=str(e),
            )

        return suggestions

    async def _rank_and_filter_suggestions(
        self, suggestions: list[MemorySuggestion], request: SuggestionRequest
    ) -> list[MemorySuggestion]:
        """Rank and filter suggestions by confidence and relevance"""

        # Remove duplicates
        seen_memory_ids = set()
        unique_suggestions = []

        for suggestion in suggestions:
            if suggestion.memory_id not in seen_memory_ids:
                seen_memory_ids.add(suggestion.memory_id)
                unique_suggestions.append(suggestion)

        # Filter by minimum confidence
        filtered_suggestions = [
            s for s in unique_suggestions if s.confidence >= request.min_confidence
        ]

        # Filter out excluded memories
        if request.exclude_memory_ids:
            filtered_suggestions = [
                s
                for s in filtered_suggestions
                if s.memory_id not in request.exclude_memory_ids
            ]

        # Enhance with relevance scores
        for suggestion in filtered_suggestions:
            try:
                # Get relevance score from SPEC-031
                relevance_score = await self._get_memory_relevance_score(
                    request.user_id, suggestion.memory_id
                )
                suggestion.relevance_score = relevance_score

                # Get feedback score from SPEC-040
                feedback_score_obj = (
                    await self.feedback_engine.get_memory_feedback_score(
                        request.user_id, suggestion.memory_id
                    )
                )
                if feedback_score_obj:
                    suggestion.feedback_score = feedback_score_obj.total_score

            except Exception as e:
                logger.warning(
                    "Failed to enhance suggestion with scores",
                    memory_id=suggestion.memory_id,
                    error=str(e),
                )

        # Sort by combined score (similarity + relevance + feedback)
        def calculate_combined_score(suggestion: MemorySuggestion) -> float:
            base_score = suggestion.similarity_score * 0.4
            relevance_bonus = (suggestion.relevance_score or 0) * 0.3
            feedback_bonus = (suggestion.feedback_score or 0) * 0.3
            return base_score + relevance_bonus + feedback_bonus

        filtered_suggestions.sort(key=calculate_combined_score, reverse=True)

        return filtered_suggestions

    async def _find_similar_memories_by_content(
        self, user_id: int, memory_id: str
    ) -> list[dict[str, Any]]:
        """Find memories similar to a given memory by content"""

        # This would use actual embeddings and similarity search in production
        # For now, return simulated similar memories
        return [
            {
                "id": f"similar_memory_{i}",
                "title": f"Similar Memory {i}",
                "content": f"Content similar to memory {memory_id}",
                "similarity": 0.8 - (i * 0.1),
            }
            for i in range(1, 4)
        ]

    async def _find_similar_memories_by_query(
        self, user_id: int, query: str
    ) -> list[dict[str, Any]]:
        """Find memories similar to a query"""

        # This would use semantic search in production
        return [
            {
                "id": f"query_memory_{i}",
                "title": f"Memory matching '{query}' {i}",
                "content": f"Content related to query: {query}",
                "similarity": 0.9 - (i * 0.15),
            }
            for i in range(1, 3)
        ]

    async def _find_popular_memories(self, user_id: int) -> list[dict[str, Any]]:
        """Find generally popular memories"""

        return [
            {
                "id": f"popular_memory_{i}",
                "title": f"Popular Memory {i}",
                "content": f"Popular content {i}",
                "similarity": 0.7,
            }
            for i in range(1, 3)
        ]

    async def _find_similar_users(self, user_id: int) -> list[int]:
        """Find users with similar behavior patterns"""

        # This would analyze actual user behavior in production
        return [user_id + 1, user_id + 2]  # Simulated similar users

    async def _get_user_popular_memories(self, user_id: int) -> list[dict[str, Any]]:
        """Get popular memories for a specific user"""

        return [
            {
                "id": f"user_{user_id}_memory_{i}",
                "title": f"User {user_id} Memory {i}",
                "content": f"Content from user {user_id}",
                "popularity": 0.8,
            }
            for i in range(1, 3)
        ]

    async def _user_has_memory(self, user_id: int, memory_id: str) -> bool:
        """Check if user already has access to a memory"""

        # This would check actual user memories in production
        return False  # Simplified for now

    async def _get_high_feedback_memories(self, user_id: int) -> list[dict[str, Any]]:
        """Get memories with high positive feedback"""

        try:
            # This would query actual feedback data in production
            return [
                {
                    "id": f"high_feedback_memory_{i}",
                    "title": f"Highly Rated Memory {i}",
                    "content": f"Content with high feedback {i}",
                    "feedback_score": 0.9 - (i * 0.1),
                }
                for i in range(1, 3)
            ]
        except Exception:
            return []

    async def _get_context_memories(
        self, user_id: int, context_id: str
    ) -> list[dict[str, Any]]:
        """Get memories accessed in similar contexts"""

        return [
            {
                "id": f"context_memory_{i}",
                "title": f"Context Memory {i}",
                "content": f"Content from context {context_id}",
                "context_relevance": 0.6,
            }
            for i in range(1, 2)
        ]

    async def _get_memory_relevance_score(self, user_id: int, memory_id: str) -> float:
        """Get relevance score from SPEC-031 engine"""

        try:
            # This would get actual relevance score in production
            return 0.7  # Simulated score
        except Exception:
            return 0.5

    def _generate_cache_key(self, request: SuggestionRequest) -> str:
        """Generate cache key for suggestion request"""

        key_parts = [
            f"suggestions:{request.user_id}",
            f"memory:{request.memory_id or 'none'}",
            f"query:{hash(request.query) if request.query else 'none'}",
            f"context:{request.context_id or 'none'}",
            f"limit:{request.limit}",
            f"types:{':'.join([t.value for t in (request.suggestion_types or [])])}",
        ]
        return ":".join(key_parts)

    async def _get_cached_suggestions(
        self, cache_key: str
    ) -> SuggestionResponse | None:
        """Get cached suggestions if available"""

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Reconstruct response object
                suggestions = [MemorySuggestion(**s) for s in data["suggestions"]]
                response = SuggestionResponse(
                    suggestions=suggestions,
                    total_found=data["total_found"],
                    algorithms_used=[
                        SuggestionType(a) for a in data["algorithms_used"]
                    ],
                    generation_time_ms=data["generation_time_ms"],
                    cached=True,
                    metadata=data["metadata"],
                )
                return response
        except Exception as e:
            logger.warning("Failed to get cached suggestions", error=str(e))

        return None

    async def _cache_suggestions(self, cache_key: str, response: SuggestionResponse):
        """Cache suggestions response"""

        try:
            # Convert to serializable format
            data = {
                "suggestions": [asdict(s) for s in response.suggestions],
                "total_found": response.total_found,
                "algorithms_used": [a.value for a in response.algorithms_used],
                "generation_time_ms": response.generation_time_ms,
                "cached": False,
                "metadata": response.metadata,
            }

            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(data, default=str)
            )

        except Exception as e:
            logger.warning("Failed to cache suggestions", error=str(e))


# Global suggestions engine instance
_suggestions_engine: IntelligentSuggestionsEngine | None = None


async def get_suggestions_engine() -> IntelligentSuggestionsEngine:
    """Get the global suggestions engine instance"""
    global _suggestions_engine
    if _suggestions_engine is None:
        _suggestions_engine = IntelligentSuggestionsEngine()
        await _suggestions_engine.initialize()
    return _suggestions_engine


def reset_suggestions_engine():
    """Reset the global suggestions engine instance (useful for testing)"""
    global _suggestions_engine
    _suggestions_engine = None
