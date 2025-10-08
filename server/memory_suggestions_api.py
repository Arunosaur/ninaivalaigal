"""
SPEC-041: Memory Suggestions API Endpoints
REST API for intelligent memory discovery and suggestions
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from auth import get_current_user
from database.operations import DatabaseOperations, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from memory_suggestions import (
    IntelligentMemorySuggestions,
    MemorySuggestion,
    SuggestionContext,
    SuggestionType,
)
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory/suggestions", tags=["memory_suggestions"])


# Request/Response Models
class SuggestionsRequest(BaseModel):
    current_memory_id: Optional[str] = None
    query_text: Optional[str] = None
    session_context: Dict[str, Any] = {}
    max_suggestions: int = 10
    min_confidence: float = 0.3


class ContextualSuggestionsRequest(BaseModel):
    current_context: Dict[str, Any]
    max_suggestions: int = 5


class DiscoverySuggestionsRequest(BaseModel):
    discovery_type: str = "explore"  # explore, trending, forgotten
    max_suggestions: int = 8


class SuggestionInteractionRequest(BaseModel):
    memory_id: str
    suggestion_type: SuggestionType
    relevance_score: float
    confidence: float
    interaction_type: str  # clicked, dismissed, used, bookmarked
    context: Optional[Dict[str, Any]] = None


class SuggestionsResponse(BaseModel):
    suggestions: List[MemorySuggestion]
    total_count: int
    algorithms_used: List[str]
    processing_time_ms: float


class SuggestionStatsResponse(BaseModel):
    total_suggestions_generated: int
    user_interaction_rate: float
    top_performing_algorithms: List[Dict[str, Any]]
    suggestion_accuracy: float
    user_satisfaction_score: float


# Initialize suggestions system
def get_suggestions_system(
    db: DatabaseOperations = Depends(get_db),
) -> IntelligentMemorySuggestions:
    """Get memory suggestions system instance."""
    # In production, this would include Redis and feedback system
    return IntelligentMemorySuggestions(
        db_manager=db, redis_client=None, feedback_system=None
    )


@router.post("/related", response_model=SuggestionsResponse)
async def get_related_memories(
    request: SuggestionsRequest,
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> SuggestionsResponse:
    """
    Get intelligent related memory suggestions.
    """
    try:
        import time

        start_time = time.time()

        user_id = current_user["user_id"]

        context = SuggestionContext(
            user_id=user_id,
            current_memory_id=request.current_memory_id,
            query_text=request.query_text,
            session_context=request.session_context,
        )

        suggestions = await suggestions_system.get_related_memories(
            context=context,
            max_suggestions=request.max_suggestions,
            min_confidence=request.min_confidence,
        )

        processing_time = (time.time() - start_time) * 1000

        # Extract unique algorithms used
        algorithms_used = list(set([s.suggestion_type for s in suggestions]))

        return SuggestionsResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            algorithms_used=algorithms_used,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(
            "Failed to get related memories",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(status_code=500, detail="Failed to get memory suggestions")


@router.post("/contextual", response_model=SuggestionsResponse)
async def get_contextual_suggestions(
    request: ContextualSuggestionsRequest,
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> SuggestionsResponse:
    """
    Get memory suggestions based on current context.
    """
    try:
        import time

        start_time = time.time()

        user_id = current_user["user_id"]

        suggestions = await suggestions_system.get_contextual_suggestions(
            user_id=user_id,
            current_context=request.current_context,
            max_suggestions=request.max_suggestions,
        )

        processing_time = (time.time() - start_time) * 1000

        algorithms_used = list(set([s.suggestion_type for s in suggestions]))

        return SuggestionsResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            algorithms_used=algorithms_used,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(
            "Failed to get contextual suggestions",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(
            status_code=500, detail="Failed to get contextual suggestions"
        )


@router.post("/discover", response_model=SuggestionsResponse)
async def get_discovery_suggestions(
    request: DiscoverySuggestionsRequest,
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> SuggestionsResponse:
    """
    Get memory suggestions for discovery and exploration.
    """
    try:
        import time

        start_time = time.time()

        user_id = current_user["user_id"]

        suggestions = await suggestions_system.get_discovery_suggestions(
            user_id=user_id,
            discovery_type=request.discovery_type,
            max_suggestions=request.max_suggestions,
        )

        processing_time = (time.time() - start_time) * 1000

        algorithms_used = list(set([s.suggestion_type for s in suggestions]))

        return SuggestionsResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            algorithms_used=algorithms_used,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(
            "Failed to get discovery suggestions",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(
            status_code=500, detail="Failed to get discovery suggestions"
        )


@router.post("/interaction")
async def record_suggestion_interaction(
    request: SuggestionInteractionRequest,
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> Dict[str, str]:
    """
    Record user interaction with a suggestion for learning.
    """
    try:
        user_id = current_user["user_id"]

        # Create suggestion object from request
        suggestion = MemorySuggestion(
            memory_id=request.memory_id,
            suggestion_type=request.suggestion_type,
            relevance_score=request.relevance_score,
            confidence=request.confidence,
            explanation="User interaction",
            metadata={},
            suggested_at=datetime.utcnow(),
        )

        await suggestions_system.record_suggestion_interaction(
            user_id=user_id,
            suggestion=suggestion,
            interaction_type=request.interaction_type,
            context=request.context,
        )

        return {"status": "success", "message": "Interaction recorded successfully"}

    except Exception as e:
        logger.error(
            "Failed to record suggestion interaction",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(status_code=500, detail="Failed to record interaction")


@router.get("/memory/{memory_id}/related", response_model=SuggestionsResponse)
async def get_memory_related_suggestions(
    memory_id: str,
    max_suggestions: int = Query(5, ge=1, le=20),
    min_confidence: float = Query(0.3, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> SuggestionsResponse:
    """
    Get suggestions related to a specific memory.
    """
    try:
        import time

        start_time = time.time()

        user_id = current_user["user_id"]

        context = SuggestionContext(user_id=user_id, current_memory_id=memory_id)

        suggestions = await suggestions_system.get_related_memories(
            context=context,
            max_suggestions=max_suggestions,
            min_confidence=min_confidence,
        )

        processing_time = (time.time() - start_time) * 1000

        algorithms_used = list(set([s.suggestion_type for s in suggestions]))

        return SuggestionsResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            algorithms_used=algorithms_used,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(
            "Failed to get memory related suggestions",
            error=str(e),
            memory_id=memory_id,
        )
        raise HTTPException(status_code=500, detail="Failed to get related suggestions")


@router.get("/search/{query}", response_model=SuggestionsResponse)
async def search_related_memories(
    query: str,
    max_suggestions: int = Query(8, ge=1, le=20),
    min_confidence: float = Query(0.2, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_user),
    suggestions_system: IntelligentMemorySuggestions = Depends(get_suggestions_system),
) -> SuggestionsResponse:
    """
    Search for memories related to a text query.
    """
    try:
        import time

        start_time = time.time()

        user_id = current_user["user_id"]

        context = SuggestionContext(user_id=user_id, query_text=query)

        suggestions = await suggestions_system.get_related_memories(
            context=context,
            max_suggestions=max_suggestions,
            min_confidence=min_confidence,
        )

        processing_time = (time.time() - start_time) * 1000

        algorithms_used = list(set([s.suggestion_type for s in suggestions]))

        return SuggestionsResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            algorithms_used=algorithms_used,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error("Failed to search related memories", error=str(e), query=query)
        raise HTTPException(status_code=500, detail="Failed to search related memories")


@router.get("/stats", response_model=SuggestionStatsResponse)
async def get_suggestion_statistics(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> SuggestionStatsResponse:
    """
    Get statistics about suggestion system performance.
    """
    try:
        user_id = current_user["user_id"]

        # Get suggestion interaction statistics
        query = """
            SELECT
                COUNT(*) as total_suggestions,
                COUNT(*) FILTER (WHERE interaction_type IN ('clicked', 'used')) as positive_interactions,
                AVG(CASE WHEN interaction_type = 'used' THEN 1.0 ELSE 0.0 END) as usage_rate,
                suggestion_type,
                COUNT(*) as type_count
            FROM memory_suggestion_interactions
            WHERE user_id = $1
                AND timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY suggestion_type
            ORDER BY type_count DESC
        """

        results = await db.fetch_all(query % days_back, user_id)

        total_suggestions = sum(row[0] for row in results) if results else 0
        positive_interactions = sum(row[1] for row in results) if results else 0

        interaction_rate = (
            (positive_interactions / total_suggestions)
            if total_suggestions > 0
            else 0.0
        )

        # Top performing algorithms
        top_algorithms = []
        if results:
            for row in results:
                algorithm_data = {
                    "algorithm": row[3],  # suggestion_type
                    "usage_count": row[4],  # type_count
                    "success_rate": row[2] if row[2] else 0.0,  # usage_rate
                }
                top_algorithms.append(algorithm_data)

        # Calculate overall metrics
        suggestion_accuracy = interaction_rate * 0.8 + 0.2  # Baseline accuracy
        user_satisfaction = min(1.0, interaction_rate * 1.2)  # Cap at 1.0

        return SuggestionStatsResponse(
            total_suggestions_generated=total_suggestions,
            user_interaction_rate=interaction_rate,
            top_performing_algorithms=top_algorithms,
            suggestion_accuracy=suggestion_accuracy,
            user_satisfaction_score=user_satisfaction,
        )

    except Exception as e:
        logger.error("Failed to get suggestion statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve suggestion statistics"
        )


@router.get("/algorithms")
async def get_available_algorithms(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get information about available suggestion algorithms.
    """
    try:
        algorithms = {
            SuggestionType.SEMANTIC_SIMILAR: {
                "name": "Semantic Similarity",
                "description": "Finds memories with similar content using AI embeddings",
                "strength": "Content relevance",
                "use_case": "Finding related topics and concepts",
            },
            SuggestionType.CONTEXTUAL_RELATED: {
                "name": "Contextual Relationships",
                "description": "Suggests memories based on current context and situation",
                "strength": "Situational relevance",
                "use_case": "Context-aware memory discovery",
            },
            SuggestionType.TEMPORAL_ADJACENT: {
                "name": "Temporal Adjacency",
                "description": "Finds memories created around the same time period",
                "strength": "Time-based connections",
                "use_case": "Discovering related work from same period",
            },
            SuggestionType.USER_BEHAVIORAL: {
                "name": "Behavioral Patterns",
                "description": "Suggests based on your personal usage patterns",
                "strength": "Personalization",
                "use_case": "Frequently accessed and important memories",
            },
            SuggestionType.COLLABORATIVE: {
                "name": "Collaborative Filtering",
                "description": "Finds memories popular among users with similar interests",
                "strength": "Community insights",
                "use_case": "Discovering popular content in your domain",
            },
            SuggestionType.TRENDING: {
                "name": "Trending Content",
                "description": "Highlights recently popular and active memories",
                "strength": "Current relevance",
                "use_case": "Staying updated with recent developments",
            },
        }

        return {
            "algorithms": algorithms,
            "total_count": len(algorithms),
            "default_weights": {
                SuggestionType.SEMANTIC_SIMILAR: 0.25,
                SuggestionType.CONTEXTUAL_RELATED: 0.20,
                SuggestionType.TEMPORAL_ADJACENT: 0.15,
                SuggestionType.USER_BEHAVIORAL: 0.20,
                SuggestionType.COLLABORATIVE: 0.10,
                SuggestionType.TRENDING: 0.10,
            },
        }

    except Exception as e:
        logger.error("Failed to get available algorithms", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve algorithm information"
        )
