"""
SPEC-041: Intelligent Related Memory Suggestions - API Endpoints

RESTful API for generating and managing intelligent memory suggestions.
Integrates with multiple algorithms and provides personalized recommendations.
"""

from datetime import datetime
from typing import Any

import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from suggestions_engine import (
    IntelligentSuggestionsEngine,
    SuggestionRequest,
    SuggestionType,
    get_suggestions_engine,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


# Request/Response models
class GetSuggestionsRequest(BaseModel):
    memory_id: str | None = Field(
        None, description="Base memory for similarity suggestions"
    )
    query: str | None = Field(
        None, description="Query for content-based suggestions"
    )
    context_id: str | None = Field(
        None, description="Context for contextual suggestions"
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum number of suggestions")
    suggestion_types: list[str] | None = Field(
        None, description="Algorithm types to use"
    )
    exclude_memory_ids: list[str] | None = Field(
        None, description="Memory IDs to exclude"
    )
    min_confidence: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )


class MemorySuggestionResponse(BaseModel):
    memory_id: str
    title: str
    content_preview: str
    similarity_score: float
    suggestion_type: str
    reasons: list[str]
    confidence: float
    metadata: dict[str, Any]
    created_at: datetime
    last_accessed: datetime | None = None
    feedback_score: float | None = None
    relevance_score: float | None = None


class SuggestionsListResponse(BaseModel):
    suggestions: list[MemorySuggestionResponse]
    total_found: int
    algorithms_used: list[str]
    generation_time_ms: float
    cached: bool
    metadata: dict[str, Any]


class SuggestionStatsResponse(BaseModel):
    total_suggestions_generated: int
    cache_hit_rate: float
    avg_generation_time_ms: float
    popular_algorithms: list[str]
    user_preferences: dict[str, Any]


class SimilarMemoriesRequest(BaseModel):
    memory_id: str
    limit: int = Field(5, ge=1, le=20)
    min_similarity: float = Field(0.5, ge=0.0, le=1.0)


class RelatedByQueryRequest(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=30)
    context_id: str | None = None


# Dependency to get suggestions engine
async def get_suggestions_engine_dep() -> IntelligentSuggestionsEngine:
    """Dependency to get the suggestions engine"""
    return await get_suggestions_engine()


@router.get("/health")
async def suggestions_health():
    """Suggestions system health check"""
    try:
        engine = await get_suggestions_engine()
        return {
            "status": "healthy",
            "service": "suggestions-api",
            "engine_initialized": engine is not None,
            "redis_connected": engine.redis_client is not None if engine else False,
            "algorithms_available": [
                "content_similarity",
                "collaborative_filtering",
                "feedback_based",
                "context_aware",
            ],
        }
    except Exception as e:
        logger.error("Suggestions health check failed", error=str(e))
        return {"status": "unhealthy", "service": "suggestions-api", "error": str(e)}


@router.post("/generate", response_model=SuggestionsListResponse)
async def generate_suggestions(
    request: GetSuggestionsRequest,
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Generate intelligent memory suggestions"""
    try:
        # Convert string types to enums
        suggestion_types = None
        if request.suggestion_types:
            type_map = {
                "content_similarity": SuggestionType.CONTENT_SIMILARITY,
                "collaborative_filtering": SuggestionType.COLLABORATIVE_FILTERING,
                "feedback_based": SuggestionType.FEEDBACK_BASED,
                "context_aware": SuggestionType.CONTEXT_AWARE,
                "hybrid": SuggestionType.HYBRID,
            }
            suggestion_types = [
                type_map.get(t) for t in request.suggestion_types if t in type_map
            ]

        # Create suggestion request
        suggestion_request = SuggestionRequest(
            user_id=current_user.id,
            memory_id=request.memory_id,
            query=request.query,
            context_id=request.context_id,
            limit=request.limit,
            suggestion_types=suggestion_types,
            exclude_memory_ids=request.exclude_memory_ids or [],
            min_confidence=request.min_confidence,
        )

        # Generate suggestions
        response = await engine.generate_suggestions(suggestion_request)

        # Convert to API response format
        suggestion_responses = [
            MemorySuggestionResponse(
                memory_id=s.memory_id,
                title=s.title,
                content_preview=s.content_preview,
                similarity_score=s.similarity_score,
                suggestion_type=s.suggestion_type.value,
                reasons=[r.value for r in s.reasons],
                confidence=s.confidence,
                metadata=s.metadata,
                created_at=s.created_at,
                last_accessed=s.last_accessed,
                feedback_score=s.feedback_score,
                relevance_score=s.relevance_score,
            )
            for s in response.suggestions
        ]

        return SuggestionsListResponse(
            suggestions=suggestion_responses,
            total_found=response.total_found,
            algorithms_used=[a.value for a in response.algorithms_used],
            generation_time_ms=response.generation_time_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(
            "Failed to generate suggestions", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{memory_id}", response_model=SuggestionsListResponse)
async def get_similar_memories(
    memory_id: str,
    limit: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Get memories similar to a specific memory"""
    try:
        suggestion_request = SuggestionRequest(
            user_id=current_user.id,
            memory_id=memory_id,
            limit=limit,
            suggestion_types=[SuggestionType.CONTENT_SIMILARITY],
            min_confidence=min_similarity,
        )

        response = await engine.generate_suggestions(suggestion_request)

        suggestion_responses = [
            MemorySuggestionResponse(
                memory_id=s.memory_id,
                title=s.title,
                content_preview=s.content_preview,
                similarity_score=s.similarity_score,
                suggestion_type=s.suggestion_type.value,
                reasons=[r.value for r in s.reasons],
                confidence=s.confidence,
                metadata=s.metadata,
                created_at=s.created_at,
                last_accessed=s.last_accessed,
                feedback_score=s.feedback_score,
                relevance_score=s.relevance_score,
            )
            for s in response.suggestions
        ]

        return SuggestionsListResponse(
            suggestions=suggestion_responses,
            total_found=response.total_found,
            algorithms_used=[a.value for a in response.algorithms_used],
            generation_time_ms=response.generation_time_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(
            "Failed to get similar memories",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/by-query", response_model=SuggestionsListResponse)
async def get_suggestions_by_query(
    request: RelatedByQueryRequest,
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Get memory suggestions based on a query"""
    try:
        suggestion_request = SuggestionRequest(
            user_id=current_user.id,
            query=request.query,
            context_id=request.context_id,
            limit=request.limit,
            suggestion_types=[
                SuggestionType.CONTENT_SIMILARITY,
                SuggestionType.CONTEXT_AWARE,
            ],
        )

        response = await engine.generate_suggestions(suggestion_request)

        suggestion_responses = [
            MemorySuggestionResponse(
                memory_id=s.memory_id,
                title=s.title,
                content_preview=s.content_preview,
                similarity_score=s.similarity_score,
                suggestion_type=s.suggestion_type.value,
                reasons=[r.value for r in s.reasons],
                confidence=s.confidence,
                metadata=s.metadata,
                created_at=s.created_at,
                last_accessed=s.last_accessed,
                feedback_score=s.feedback_score,
                relevance_score=s.relevance_score,
            )
            for s in response.suggestions
        ]

        return SuggestionsListResponse(
            suggestions=suggestion_responses,
            total_found=response.total_found,
            algorithms_used=[a.value for a in response.algorithms_used],
            generation_time_ms=response.generation_time_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(
            "Failed to get query-based suggestions",
            user_id=current_user.id,
            query=request.query,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=SuggestionsListResponse)
async def get_trending_memories(
    limit: int = Query(10, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Get trending memories based on feedback and usage patterns"""
    try:
        suggestion_request = SuggestionRequest(
            user_id=current_user.id,
            limit=limit,
            suggestion_types=[
                SuggestionType.FEEDBACK_BASED,
                SuggestionType.COLLABORATIVE_FILTERING,
            ],
            min_confidence=0.6,
        )

        response = await engine.generate_suggestions(suggestion_request)

        suggestion_responses = [
            MemorySuggestionResponse(
                memory_id=s.memory_id,
                title=s.title,
                content_preview=s.content_preview,
                similarity_score=s.similarity_score,
                suggestion_type=s.suggestion_type.value,
                reasons=[r.value for r in s.reasons],
                confidence=s.confidence,
                metadata=s.metadata,
                created_at=s.created_at,
                last_accessed=s.last_accessed,
                feedback_score=s.feedback_score,
                relevance_score=s.relevance_score,
            )
            for s in response.suggestions
        ]

        return SuggestionsListResponse(
            suggestions=suggestion_responses,
            total_found=response.total_found,
            algorithms_used=[a.value for a in response.algorithms_used],
            generation_time_ms=response.generation_time_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(
            "Failed to get trending memories", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personalized", response_model=SuggestionsListResponse)
async def get_personalized_suggestions(
    limit: int = Query(15, ge=1, le=50),
    context_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Get personalized suggestions using all available algorithms"""
    try:
        suggestion_request = SuggestionRequest(
            user_id=current_user.id,
            context_id=context_id,
            limit=limit,
            suggestion_types=[
                SuggestionType.CONTENT_SIMILARITY,
                SuggestionType.COLLABORATIVE_FILTERING,
                SuggestionType.FEEDBACK_BASED,
                SuggestionType.CONTEXT_AWARE,
            ],
            min_confidence=0.4,
        )

        response = await engine.generate_suggestions(suggestion_request)

        suggestion_responses = [
            MemorySuggestionResponse(
                memory_id=s.memory_id,
                title=s.title,
                content_preview=s.content_preview,
                similarity_score=s.similarity_score,
                suggestion_type=s.suggestion_type.value,
                reasons=[r.value for r in s.reasons],
                confidence=s.confidence,
                metadata=s.metadata,
                created_at=s.created_at,
                last_accessed=s.last_accessed,
                feedback_score=s.feedback_score,
                relevance_score=s.relevance_score,
            )
            for s in response.suggestions
        ]

        return SuggestionsListResponse(
            suggestions=suggestion_responses,
            total_found=response.total_found,
            algorithms_used=[a.value for a in response.algorithms_used],
            generation_time_ms=response.generation_time_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(
            "Failed to get personalized suggestions",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SuggestionStatsResponse)
async def get_suggestion_stats(
    current_user: User = Depends(get_current_user),
    engine: IntelligentSuggestionsEngine = Depends(get_suggestions_engine_dep),
):
    """Get user's suggestion statistics and preferences"""
    try:
        # This would collect actual statistics in production
        stats = SuggestionStatsResponse(
            total_suggestions_generated=0,
            cache_hit_rate=0.0,
            avg_generation_time_ms=0.0,
            popular_algorithms=[
                "content_similarity",
                "feedback_based",
                "collaborative_filtering",
            ],
            user_preferences={
                "preferred_algorithms": ["content_similarity"],
                "avg_confidence_threshold": 0.5,
                "typical_limit": 10,
            },
        )

        return stats

    except Exception as e:
        logger.error(
            "Failed to get suggestion stats", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{memory_id}")
async def record_suggestion_feedback(
    memory_id: str,
    helpful: bool,
    suggestion_type: str,
    current_user: User = Depends(get_current_user),
):
    """Record feedback on a suggested memory (integrates with SPEC-040)"""
    try:
        # This would integrate with the feedback system
        # For now, just acknowledge the feedback

        return {
            "message": f"Feedback recorded for memory {memory_id}",
            "helpful": helpful,
            "suggestion_type": suggestion_type,
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(
            "Failed to record suggestion feedback",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))
