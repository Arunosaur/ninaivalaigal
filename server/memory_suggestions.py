"""
SPEC-041: Intelligent Related Memory Suggestions
Related memory discovery, intelligent suggestions, and context linking
"""

import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class SuggestionType(str, Enum):
    """Types of memory suggestions"""

    SEMANTIC_SIMILAR = "semantic_similar"
    CONTEXTUAL_RELATED = "contextual_related"
    TEMPORAL_ADJACENT = "temporal_adjacent"
    USER_BEHAVIORAL = "user_behavioral"
    COLLABORATIVE = "collaborative"
    TRENDING = "trending"


class MemorySuggestion(BaseModel):
    """Individual memory suggestion"""

    memory_id: str
    suggestion_type: SuggestionType
    relevance_score: float
    confidence: float
    explanation: str
    metadata: Dict[str, Any]
    suggested_at: datetime


class SuggestionContext(BaseModel):
    """Context for generating suggestions"""

    user_id: str
    current_memory_id: Optional[str] = None
    query_text: Optional[str] = None
    session_context: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}
    temporal_context: Dict[str, Any] = {}


class IntelligentMemorySuggestions:
    """
    Advanced memory suggestion system that uses multiple algorithms
    to discover related memories and provide intelligent recommendations.
    """

    def __init__(self, db_manager, redis_client=None, feedback_system=None):
        self.db = db_manager
        self.redis = redis_client
        self.feedback_system = feedback_system

        # Suggestion algorithm weights (can be learned from feedback)
        self.algorithm_weights = {
            SuggestionType.SEMANTIC_SIMILAR: 0.25,
            SuggestionType.CONTEXTUAL_RELATED: 0.20,
            SuggestionType.TEMPORAL_ADJACENT: 0.15,
            SuggestionType.USER_BEHAVIORAL: 0.20,
            SuggestionType.COLLABORATIVE: 0.10,
            SuggestionType.TRENDING: 0.10,
        }

    async def get_related_memories(
        self,
        context: SuggestionContext,
        max_suggestions: int = 10,
        min_confidence: float = 0.3,
    ) -> List[MemorySuggestion]:
        """
        Get intelligent memory suggestions based on multiple algorithms.
        """
        try:
            # Check cache first
            cache_key = f"suggestions:{context.user_id}:{hash(str(context.dict()))}"
            if self.redis:
                cached = await self._get_cached_suggestions(cache_key)
                if cached:
                    return cached

            suggestions = []

            # Algorithm 1: Semantic similarity using embeddings
            semantic_suggestions = await self._get_semantic_suggestions(context)
            suggestions.extend(semantic_suggestions)

            # Algorithm 2: Contextual relationships
            contextual_suggestions = await self._get_contextual_suggestions(context)
            suggestions.extend(contextual_suggestions)

            # Algorithm 3: Temporal adjacency
            temporal_suggestions = await self._get_temporal_suggestions(context)
            suggestions.extend(temporal_suggestions)

            # Algorithm 4: User behavioral patterns
            behavioral_suggestions = await self._get_behavioral_suggestions(context)
            suggestions.extend(behavioral_suggestions)

            # Algorithm 5: Collaborative filtering
            collaborative_suggestions = await self._get_collaborative_suggestions(
                context
            )
            suggestions.extend(collaborative_suggestions)

            # Algorithm 6: Trending memories
            trending_suggestions = await self._get_trending_suggestions(context)
            suggestions.extend(trending_suggestions)

            # Combine and rank suggestions
            ranked_suggestions = await self._rank_and_deduplicate(
                suggestions, context, max_suggestions, min_confidence
            )

            # Apply user feedback learning
            if self.feedback_system:
                ranked_suggestions = await self._apply_feedback_learning(
                    ranked_suggestions, context
                )

            # Cache results
            if self.redis:
                await self._cache_suggestions(cache_key, ranked_suggestions)

            logger.info(
                "Generated memory suggestions",
                user_id=context.user_id,
                total_suggestions=len(ranked_suggestions),
                algorithms_used=len([s for s in suggestions if s]),
            )

            return ranked_suggestions

        except Exception as e:
            logger.error("Failed to get related memories", error=str(e))
            raise

    async def get_contextual_suggestions(
        self, user_id: str, current_context: Dict[str, Any], max_suggestions: int = 5
    ) -> List[MemorySuggestion]:
        """
        Get suggestions based on current context (e.g., what user is working on).
        """
        try:
            context = SuggestionContext(
                user_id=user_id, session_context=current_context
            )

            suggestions = await self.get_related_memories(
                context=context, max_suggestions=max_suggestions, min_confidence=0.4
            )

            # Filter for contextual suggestions
            contextual_suggestions = [
                s
                for s in suggestions
                if s.suggestion_type
                in [SuggestionType.CONTEXTUAL_RELATED, SuggestionType.SEMANTIC_SIMILAR]
            ]

            return contextual_suggestions[:max_suggestions]

        except Exception as e:
            logger.error("Failed to get contextual suggestions", error=str(e))
            raise

    async def get_discovery_suggestions(
        self, user_id: str, discovery_type: str = "explore", max_suggestions: int = 8
    ) -> List[MemorySuggestion]:
        """
        Get suggestions for memory discovery and exploration.
        """
        try:
            context = SuggestionContext(
                user_id=user_id, user_preferences={"discovery_type": discovery_type}
            )

            if discovery_type == "explore":
                # Focus on diverse, less frequently accessed memories
                suggestions = await self._get_exploration_suggestions(context)
            elif discovery_type == "trending":
                # Focus on popular and recently active memories
                suggestions = await self._get_trending_suggestions(context)
            elif discovery_type == "forgotten":
                # Focus on old memories that might be relevant
                suggestions = await self._get_forgotten_suggestions(context)
            else:
                # Default mixed approach
                suggestions = await self.get_related_memories(context, max_suggestions)

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error("Failed to get discovery suggestions", error=str(e))
            raise

    async def record_suggestion_interaction(
        self,
        user_id: str,
        suggestion: MemorySuggestion,
        interaction_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record user interaction with suggestions for learning.
        """
        try:
            interaction_data = {
                "user_id": user_id,
                "memory_id": suggestion.memory_id,
                "suggestion_type": suggestion.suggestion_type,
                "interaction_type": interaction_type,  # clicked, dismissed, used, etc.
                "relevance_score": suggestion.relevance_score,
                "confidence": suggestion.confidence,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Store interaction for learning
            await self._store_suggestion_interaction(interaction_data)

            # Update algorithm weights based on feedback
            await self._update_algorithm_weights(user_id, suggestion, interaction_type)

            # Provide feedback to the feedback system if available
            if self.feedback_system and interaction_type in ["clicked", "used"]:
                from ai_feedback_system import FeedbackType, FeedbackValue

                feedback_value = (
                    FeedbackValue.POSITIVE
                    if interaction_type == "used"
                    else FeedbackValue.NEUTRAL
                )

                await self.feedback_system.collect_feedback(
                    user_id=user_id,
                    feedback_type=FeedbackType.SUGGESTION_ACCURACY,
                    feedback_value=feedback_value,
                    context={
                        "suggestion_type": suggestion.suggestion_type,
                        "memory_id": suggestion.memory_id,
                        "interaction_type": interaction_type,
                    },
                    memory_ids=[suggestion.memory_id],
                    confidence_score=suggestion.confidence,
                )

            logger.info(
                "Recorded suggestion interaction",
                user_id=user_id,
                memory_id=suggestion.memory_id,
                interaction_type=interaction_type,
            )

        except Exception as e:
            logger.error("Failed to record suggestion interaction", error=str(e))
            raise

    # Private helper methods for different suggestion algorithms

    async def _get_semantic_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on semantic similarity using embeddings."""
        try:
            suggestions = []

            if context.current_memory_id:
                # Find memories similar to current memory
                similar_memories = await self._find_similar_by_embedding(
                    context.current_memory_id, context.user_id, limit=5
                )

                for memory_data in similar_memories:
                    suggestion = MemorySuggestion(
                        memory_id=memory_data["id"],
                        suggestion_type=SuggestionType.SEMANTIC_SIMILAR,
                        relevance_score=memory_data["similarity_score"],
                        confidence=memory_data["similarity_score"] * 0.9,
                        explanation=f"Similar content to your current memory",
                        metadata={"similarity_score": memory_data["similarity_score"]},
                        suggested_at=datetime.utcnow(),
                    )
                    suggestions.append(suggestion)

            elif context.query_text:
                # Find memories similar to query text
                similar_memories = await self._find_similar_by_text(
                    context.query_text, context.user_id, limit=5
                )

                for memory_data in similar_memories:
                    suggestion = MemorySuggestion(
                        memory_id=memory_data["id"],
                        suggestion_type=SuggestionType.SEMANTIC_SIMILAR,
                        relevance_score=memory_data["similarity_score"],
                        confidence=memory_data["similarity_score"] * 0.85,
                        explanation=f"Matches your search: '{context.query_text[:50]}...'",
                        metadata={"query_similarity": memory_data["similarity_score"]},
                        suggested_at=datetime.utcnow(),
                    )
                    suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get semantic suggestions", error=str(e))
            return []

    async def _get_contextual_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on contextual relationships."""
        try:
            suggestions = []

            # Get memories from similar contexts
            if context.session_context:
                contextual_memories = await self._find_by_context(
                    context.session_context, context.user_id, limit=4
                )

                for memory_data in contextual_memories:
                    suggestion = MemorySuggestion(
                        memory_id=memory_data["id"],
                        suggestion_type=SuggestionType.CONTEXTUAL_RELATED,
                        relevance_score=memory_data["context_match_score"],
                        confidence=memory_data["context_match_score"] * 0.8,
                        explanation="Related to your current context",
                        metadata={"context_match": memory_data["context_match_score"]},
                        suggested_at=datetime.utcnow(),
                    )
                    suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get contextual suggestions", error=str(e))
            return []

    async def _get_temporal_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on temporal adjacency."""
        try:
            suggestions = []

            if context.current_memory_id:
                # Get memories created around the same time
                temporal_memories = await self._find_temporal_adjacent(
                    context.current_memory_id, context.user_id, limit=3
                )

                for memory_data in temporal_memories:
                    suggestion = MemorySuggestion(
                        memory_id=memory_data["id"],
                        suggestion_type=SuggestionType.TEMPORAL_ADJACENT,
                        relevance_score=memory_data["temporal_score"],
                        confidence=memory_data["temporal_score"] * 0.7,
                        explanation="Created around the same time",
                        metadata={"time_difference": memory_data["time_diff_hours"]},
                        suggested_at=datetime.utcnow(),
                    )
                    suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get temporal suggestions", error=str(e))
            return []

    async def _get_behavioral_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on user behavioral patterns."""
        try:
            suggestions = []

            # Get user's frequently accessed memories
            frequent_memories = await self._get_user_frequent_memories(
                context.user_id, limit=4
            )

            for memory_data in frequent_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    suggestion_type=SuggestionType.USER_BEHAVIORAL,
                    relevance_score=memory_data["frequency_score"],
                    confidence=memory_data["frequency_score"] * 0.75,
                    explanation="Frequently accessed by you",
                    metadata={"access_count": memory_data["access_count"]},
                    suggested_at=datetime.utcnow(),
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get behavioral suggestions", error=str(e))
            return []

    async def _get_collaborative_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on collaborative filtering."""
        try:
            suggestions = []

            # Get memories popular among similar users
            collaborative_memories = await self._find_collaborative_memories(
                context.user_id, limit=3
            )

            for memory_data in collaborative_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    suggestion_type=SuggestionType.COLLABORATIVE,
                    relevance_score=memory_data["collaborative_score"],
                    confidence=memory_data["collaborative_score"] * 0.6,
                    explanation="Popular among users like you",
                    metadata={"similar_users": memory_data["similar_user_count"]},
                    suggested_at=datetime.utcnow(),
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get collaborative suggestions", error=str(e))
            return []

    async def _get_trending_suggestions(
        self, context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Get suggestions based on trending memories."""
        try:
            suggestions = []

            # Get recently popular memories
            trending_memories = await self._find_trending_memories(
                context.user_id, limit=3
            )

            for memory_data in trending_memories:
                suggestion = MemorySuggestion(
                    memory_id=memory_data["id"],
                    suggestion_type=SuggestionType.TRENDING,
                    relevance_score=memory_data["trending_score"],
                    confidence=memory_data["trending_score"] * 0.65,
                    explanation="Trending recently",
                    metadata={"recent_activity": memory_data["activity_score"]},
                    suggested_at=datetime.utcnow(),
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error("Failed to get trending suggestions", error=str(e))
            return []

    async def _rank_and_deduplicate(
        self,
        suggestions: List[MemorySuggestion],
        context: SuggestionContext,
        max_suggestions: int,
        min_confidence: float,
    ) -> List[MemorySuggestion]:
        """Rank suggestions and remove duplicates."""
        try:
            # Remove duplicates by memory_id
            seen_memory_ids = set()
            unique_suggestions = []

            for suggestion in suggestions:
                if suggestion.memory_id not in seen_memory_ids:
                    seen_memory_ids.add(suggestion.memory_id)
                    unique_suggestions.append(suggestion)

            # Filter by minimum confidence
            filtered_suggestions = [
                s for s in unique_suggestions if s.confidence >= min_confidence
            ]

            # Calculate final scores with algorithm weights
            for suggestion in filtered_suggestions:
                algorithm_weight = self.algorithm_weights.get(
                    suggestion.suggestion_type, 0.1
                )
                suggestion.relevance_score = (
                    suggestion.relevance_score * algorithm_weight
                    + suggestion.confidence * 0.3
                )

            # Sort by relevance score
            ranked_suggestions = sorted(
                filtered_suggestions, key=lambda x: x.relevance_score, reverse=True
            )

            return ranked_suggestions[:max_suggestions]

        except Exception as e:
            logger.error("Failed to rank and deduplicate suggestions", error=str(e))
            return suggestions[:max_suggestions]

    async def _apply_feedback_learning(
        self, suggestions: List[MemorySuggestion], context: SuggestionContext
    ) -> List[MemorySuggestion]:
        """Apply learning from feedback system to improve suggestions."""
        try:
            if not self.feedback_system:
                return suggestions

            # Get user's feedback patterns for suggestions
            user_patterns = await self._get_user_suggestion_patterns(context.user_id)

            # Adjust scores based on learned patterns
            for suggestion in suggestions:
                pattern_key = f"{suggestion.suggestion_type}_{suggestion.memory_id[:8]}"
                if pattern_key in user_patterns:
                    pattern_data = user_patterns[pattern_key]
                    adjustment = pattern_data.get("success_rate", 0.5) - 0.5
                    suggestion.relevance_score += adjustment * 0.2
                    suggestion.confidence = min(
                        1.0, suggestion.confidence + adjustment * 0.1
                    )

            # Re-sort after adjustments
            suggestions.sort(key=lambda x: x.relevance_score, reverse=True)

            return suggestions

        except Exception as e:
            logger.error("Failed to apply feedback learning", error=str(e))
            return suggestions

    # Database query methods (simplified implementations)

    async def _find_similar_by_embedding(
        self, memory_id: str, user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Find memories similar by embedding vectors."""
        # Placeholder - would use pgvector similarity search
        query = """
            SELECT m.id, m.content,
                   (1 - (m.embedding <=> ref.embedding)) as similarity_score
            FROM memories m, memories ref
            WHERE ref.id = $1 AND m.user_id = $2 AND m.id != $1
            ORDER BY m.embedding <=> ref.embedding
            LIMIT $3
        """

        try:
            results = await self.db.fetch_all(query, memory_id, user_id, limit)
            return [dict(row) for row in results] if results else []
        except:
            return []  # Graceful fallback

    async def _find_similar_by_text(
        self, query_text: str, user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Find memories similar to text query."""
        # Placeholder - would use text search
        query = """
            SELECT id, content,
                   ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as similarity_score
            FROM memories
            WHERE user_id = $2 AND to_tsvector('english', content) @@ plainto_tsquery('english', $1)
            ORDER BY similarity_score DESC
            LIMIT $3
        """

        try:
            results = await self.db.fetch_all(query, query_text, user_id, limit)
            return [dict(row) for row in results] if results else []
        except:
            return []
