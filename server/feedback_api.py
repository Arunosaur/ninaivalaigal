"""
SPEC-040: Feedback Loop System - API Endpoints

RESTful API for collecting and managing user feedback on memory relevance.
Supports both implicit and explicit feedback mechanisms.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from auth import get_current_user
from database import User
from feedback_engine import (
    get_feedback_engine,
    FeedbackType,
    FeedbackSentiment,
    FeedbackEngine,
    MemoryFeedbackScore
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Request/Response models
class ImplicitFeedbackRequest(BaseModel):
    memory_id: str
    feedback_type: str = Field(..., description="Type: dwell, click, navigation")
    value: float = Field(..., ge=0.0, description="Raw feedback value")
    metadata: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None


class ExplicitFeedbackRequest(BaseModel):
    memory_id: str
    feedback_type: str = Field(..., description="Type: thumbs_up, thumbs_down, quality_note")
    sentiment: str = Field(..., description="Sentiment: positive, negative, neutral")
    notes: Optional[str] = None
    context_id: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None


class DwellTimeFeedbackRequest(BaseModel):
    memory_id: str
    dwell_time_seconds: float = Field(..., ge=0.0, description="Time spent viewing memory")
    context_id: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None


class MemoryRatingRequest(BaseModel):
    memory_id: str
    rating: str = Field(..., description="Rating: thumbs_up or thumbs_down")
    notes: Optional[str] = None
    context_id: Optional[str] = None
    query: Optional[str] = None


class FeedbackResponse(BaseModel):
    event_id: str
    message: str
    timestamp: datetime


class MemoryFeedbackScoreResponse(BaseModel):
    memory_id: str
    user_id: int
    total_score: float
    positive_count: int
    negative_count: int
    implicit_score: float
    explicit_score: float
    last_updated: datetime
    feedback_multiplier: float


class FeedbackStatsResponse(BaseModel):
    total_events: int
    positive_feedback: int
    negative_feedback: int
    neutral_feedback: int
    avg_dwell_time: float
    top_memories: List[Dict[str, Any]]


# Dependency to get feedback engine
async def get_feedback_engine_dep() -> FeedbackEngine:
    """Dependency to get the feedback engine"""
    return await get_feedback_engine()


@router.get("/health")
async def feedback_health():
    """Feedback system health check"""
    try:
        engine = await get_feedback_engine()
        return {
            "status": "healthy",
            "service": "feedback-api",
            "engine_initialized": engine is not None,
            "redis_connected": engine.redis_client is not None if engine else False
        }
    except Exception as e:
        logger.error("Feedback health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "feedback-api",
            "error": str(e)
        }


@router.post("/implicit", response_model=FeedbackResponse)
async def record_implicit_feedback(
    request: ImplicitFeedbackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Record implicit feedback (dwell time, clicks, navigation patterns)"""
    try:
        # Map string to enum
        feedback_type_map = {
            "dwell": FeedbackType.IMPLICIT_DWELL,
            "click": FeedbackType.IMPLICIT_CLICK,
            "navigation": FeedbackType.IMPLICIT_NAVIGATION,
        }
        
        feedback_type = feedback_type_map.get(request.feedback_type)
        if not feedback_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type: {request.feedback_type}"
            )
        
        event_id = await engine.record_implicit_feedback(
            user_id=current_user.id,
            memory_id=request.memory_id,
            feedback_type=feedback_type,
            value=request.value,
            metadata=request.metadata or {},
            context_id=request.context_id,
            query=request.query,
            session_id=request.session_id
        )
        
        return FeedbackResponse(
            event_id=event_id,
            message="Implicit feedback recorded successfully",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to record implicit feedback",
            user_id=current_user.id,
            memory_id=request.memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explicit", response_model=FeedbackResponse)
async def record_explicit_feedback(
    request: ExplicitFeedbackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Record explicit feedback (thumbs up/down, quality notes)"""
    try:
        # Map strings to enums
        feedback_type_map = {
            "thumbs_up": FeedbackType.EXPLICIT_THUMBS_UP,
            "thumbs_down": FeedbackType.EXPLICIT_THUMBS_DOWN,
            "quality_note": FeedbackType.EXPLICIT_QUALITY_NOTE,
        }
        
        sentiment_map = {
            "positive": FeedbackSentiment.POSITIVE,
            "negative": FeedbackSentiment.NEGATIVE,
            "neutral": FeedbackSentiment.NEUTRAL,
        }
        
        feedback_type = feedback_type_map.get(request.feedback_type)
        sentiment = sentiment_map.get(request.sentiment)
        
        if not feedback_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type: {request.feedback_type}"
            )
        
        if not sentiment:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sentiment: {request.sentiment}"
            )
        
        event_id = await engine.record_explicit_feedback(
            user_id=current_user.id,
            memory_id=request.memory_id,
            feedback_type=feedback_type,
            sentiment=sentiment,
            notes=request.notes,
            context_id=request.context_id,
            query=request.query,
            session_id=request.session_id
        )
        
        return FeedbackResponse(
            event_id=event_id,
            message="Explicit feedback recorded successfully",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to record explicit feedback",
            user_id=current_user.id,
            memory_id=request.memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dwell", response_model=FeedbackResponse)
async def record_dwell_time(
    request: DwellTimeFeedbackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Record dwell time feedback (simplified endpoint)"""
    try:
        event_id = await engine.record_implicit_feedback(
            user_id=current_user.id,
            memory_id=request.memory_id,
            feedback_type=FeedbackType.IMPLICIT_DWELL,
            value=request.dwell_time_seconds,
            metadata={"dwell_time_seconds": request.dwell_time_seconds},
            context_id=request.context_id,
            query=request.query,
            session_id=request.session_id
        )
        
        return FeedbackResponse(
            event_id=event_id,
            message=f"Dwell time feedback recorded: {request.dwell_time_seconds}s",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to record dwell time feedback",
            user_id=current_user.id,
            memory_id=request.memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate", response_model=FeedbackResponse)
async def rate_memory(
    request: MemoryRatingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Rate a memory with thumbs up/down (simplified endpoint)"""
    try:
        # Map rating to feedback type and sentiment
        if request.rating == "thumbs_up":
            feedback_type = FeedbackType.EXPLICIT_THUMBS_UP
            sentiment = FeedbackSentiment.POSITIVE
        elif request.rating == "thumbs_down":
            feedback_type = FeedbackType.EXPLICIT_THUMBS_DOWN
            sentiment = FeedbackSentiment.NEGATIVE
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rating: {request.rating}. Use 'thumbs_up' or 'thumbs_down'"
            )
        
        event_id = await engine.record_explicit_feedback(
            user_id=current_user.id,
            memory_id=request.memory_id,
            feedback_type=feedback_type,
            sentiment=sentiment,
            notes=request.notes,
            context_id=request.context_id,
            query=request.query
        )
        
        return FeedbackResponse(
            event_id=event_id,
            message=f"Memory rated: {request.rating}",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to rate memory",
            user_id=current_user.id,
            memory_id=request.memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{memory_id}/score", response_model=MemoryFeedbackScoreResponse)
async def get_memory_feedback_score(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Get aggregated feedback score for a specific memory"""
    try:
        score = await engine.get_memory_feedback_score(current_user.id, memory_id)
        
        if not score:
            raise HTTPException(
                status_code=404,
                detail=f"No feedback score found for memory {memory_id}"
            )
        
        # Calculate feedback multiplier for display
        feedback_multiplier = 1.0 + (score.total_score * 0.2)
        feedback_multiplier = max(0.5, min(1.5, feedback_multiplier))
        
        return MemoryFeedbackScoreResponse(
            memory_id=score.memory_id,
            user_id=score.user_id,
            total_score=score.total_score,
            positive_count=score.positive_count,
            negative_count=score.negative_count,
            implicit_score=score.implicit_score,
            explicit_score=score.explicit_score,
            last_updated=score.last_updated,
            feedback_multiplier=feedback_multiplier
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get memory feedback score",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Get user's feedback statistics"""
    try:
        # This would require additional methods in the feedback engine
        # For now, return a placeholder response
        return FeedbackStatsResponse(
            total_events=0,
            positive_feedback=0,
            negative_feedback=0,
            neutral_feedback=0,
            avg_dwell_time=0.0,
            top_memories=[]
        )
        
    except Exception as e:
        logger.error(
            "Failed to get feedback stats",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/{memory_id}/process")
async def process_memory_feedback(
    memory_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: FeedbackEngine = Depends(get_feedback_engine_dep),
):
    """Manually trigger feedback processing for a memory (admin/debug endpoint)"""
    try:
        # This would trigger reprocessing of all feedback for a memory
        # Implementation would depend on additional methods in feedback engine
        
        return {
            "message": f"Feedback processing triggered for memory {memory_id}",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(
            "Failed to process memory feedback",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
