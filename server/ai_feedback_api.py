"""
SPEC-040: AI Feedback API Endpoints
REST API for collecting feedback and managing AI learning
"""

from typing import Any, Dict, List, Optional

import structlog
from ai_feedback_system import (
    AIFeedbackSystem,
    ContextImprovement,
    FeedbackType,
    FeedbackValue,
    LearningPattern,
)
from auth import get_current_user
from database.operations import DatabaseOperations, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ai/feedback", tags=["ai_feedback"])


# Request/Response Models
class FeedbackRequest(BaseModel):
    feedback_type: FeedbackType
    feedback_value: FeedbackValue
    context: Dict[str, Any]
    memory_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    confidence_score: Optional[float] = None


class FeedbackResponse(BaseModel):
    event_id: str
    status: str
    message: str


class LearningInsights(BaseModel):
    feedback_statistics: Dict[str, Any]
    improvement_metrics: Dict[str, Any]
    learning_effectiveness: Dict[str, Any]
    active_patterns: int
    pending_improvements: int
    analysis_period_days: int


class ContextOptimizationRequest(BaseModel):
    context: Dict[str, Any]
    apply_learning: bool = True


class ContextOptimizationResponse(BaseModel):
    original_context: Dict[str, Any]
    optimized_context: Dict[str, Any]
    adjustments_applied: List[str]
    confidence_score: float


# Initialize feedback system (will be properly injected in production)
def get_feedback_system(db: DatabaseOperations = Depends(get_db)) -> AIFeedbackSystem:
    """Get AI feedback system instance."""
    # In production, this would include Redis client
    return AIFeedbackSystem(db_manager=db, redis_client=None)


@router.post("/collect", response_model=FeedbackResponse)
async def collect_feedback(
    feedback_request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> FeedbackResponse:
    """
    Collect user feedback for AI learning.
    """
    try:
        user_id = current_user["user_id"]

        event_id = await feedback_system.collect_feedback(
            user_id=user_id,
            feedback_type=feedback_request.feedback_type,
            feedback_value=feedback_request.feedback_value,
            context=feedback_request.context,
            memory_ids=feedback_request.memory_ids,
            session_id=feedback_request.session_id,
            confidence_score=feedback_request.confidence_score,
        )

        return FeedbackResponse(
            event_id=event_id,
            status="success",
            message="Feedback collected successfully",
        )

    except Exception as e:
        logger.error(
            "Failed to collect feedback",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(status_code=500, detail="Failed to collect feedback")


@router.get("/patterns", response_model=List[LearningPattern])
async def get_learning_patterns(
    feedback_type: Optional[FeedbackType] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> List[LearningPattern]:
    """
    Get learned patterns from user feedback.
    """
    try:
        user_id = current_user["user_id"]

        patterns = await feedback_system.analyze_feedback_patterns(
            user_id=user_id, feedback_type=feedback_type, days_back=days_back
        )

        return patterns

    except Exception as e:
        logger.error(
            "Failed to get learning patterns",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve learning patterns"
        )


@router.get("/improvements", response_model=List[ContextImprovement])
async def get_context_improvements(
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> List[ContextImprovement]:
    """
    Get suggested context improvements based on learning.
    """
    try:
        user_id = current_user["user_id"]

        # Get recent patterns
        patterns = await feedback_system.analyze_feedback_patterns(
            user_id=user_id, days_back=30
        )

        # Generate improvements
        improvements = await feedback_system.generate_context_improvements(patterns)

        return improvements

    except Exception as e:
        logger.error(
            "Failed to get context improvements",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve context improvements"
        )


@router.post("/optimize-context", response_model=ContextOptimizationResponse)
async def optimize_context(
    optimization_request: ContextOptimizationRequest,
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> ContextOptimizationResponse:
    """
    Optimize context using learned patterns.
    """
    try:
        user_id = current_user["user_id"]
        original_context = optimization_request.context.copy()

        if optimization_request.apply_learning:
            optimized_context = await feedback_system.apply_learning_adjustments(
                user_id=user_id, context=optimization_request.context
            )
        else:
            optimized_context = original_context

        # Calculate adjustments made
        adjustments_applied = []
        if optimized_context != original_context:
            for key in optimized_context:
                if (
                    key not in original_context
                    or optimized_context[key] != original_context[key]
                ):
                    adjustments_applied.append(f"Modified {key}")

        # Calculate confidence score based on available patterns
        confidence_score = 0.8 if adjustments_applied else 1.0

        return ContextOptimizationResponse(
            original_context=original_context,
            optimized_context=optimized_context,
            adjustments_applied=adjustments_applied,
            confidence_score=confidence_score,
        )

    except Exception as e:
        logger.error(
            "Failed to optimize context",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(status_code=500, detail="Failed to optimize context")


@router.get("/insights", response_model=LearningInsights)
async def get_learning_insights(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> LearningInsights:
    """
    Get insights from AI learning system.
    """
    try:
        user_id = current_user["user_id"]

        insights = await feedback_system.get_feedback_insights(
            user_id=user_id, days_back=days_back
        )

        return LearningInsights(**insights)

    except Exception as e:
        logger.error(
            "Failed to get learning insights",
            error=str(e),
            user_id=current_user.get("user_id"),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve learning insights"
        )


@router.post("/memory/{memory_id}/relevance")
async def rate_memory_relevance(
    memory_id: str,
    relevance_score: float = Query(..., ge=0.0, le=1.0),
    context: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> FeedbackResponse:
    """
    Rate the relevance of a specific memory.
    """
    try:
        user_id = current_user["user_id"]

        # Convert score to feedback value
        if relevance_score >= 0.7:
            feedback_value = FeedbackValue.POSITIVE
        elif relevance_score <= 0.3:
            feedback_value = FeedbackValue.NEGATIVE
        else:
            feedback_value = FeedbackValue.NEUTRAL

        feedback_context = context or {}
        feedback_context.update(
            {
                "memory_id": memory_id,
                "relevance_score": relevance_score,
                "feedback_source": "explicit_rating",
            }
        )

        event_id = await feedback_system.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.MEMORY_RELEVANCE,
            feedback_value=feedback_value,
            context=feedback_context,
            memory_ids=[memory_id],
            confidence_score=relevance_score,
        )

        return FeedbackResponse(
            event_id=event_id,
            status="success",
            message=f"Memory relevance rated: {relevance_score}",
        )

    except Exception as e:
        logger.error(
            "Failed to rate memory relevance", error=str(e), memory_id=memory_id
        )
        raise HTTPException(status_code=500, detail="Failed to rate memory relevance")


@router.post("/context/quality")
async def rate_context_quality(
    quality_score: float = Query(..., ge=0.0, le=1.0),
    context_details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    feedback_system: AIFeedbackSystem = Depends(get_feedback_system),
) -> FeedbackResponse:
    """
    Rate the quality of provided context.
    """
    try:
        user_id = current_user["user_id"]

        # Convert score to feedback value
        if quality_score >= 0.7:
            feedback_value = FeedbackValue.POSITIVE
        elif quality_score <= 0.3:
            feedback_value = FeedbackValue.NEGATIVE
        else:
            feedback_value = FeedbackValue.NEUTRAL

        feedback_context = context_details or {}
        feedback_context.update(
            {
                "quality_score": quality_score,
                "feedback_source": "context_quality_rating",
            }
        )

        event_id = await feedback_system.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.CONTEXT_QUALITY,
            feedback_value=feedback_value,
            context=feedback_context,
            session_id=session_id,
            confidence_score=quality_score,
        )

        return FeedbackResponse(
            event_id=event_id,
            status="success",
            message=f"Context quality rated: {quality_score}",
        )

    except Exception as e:
        logger.error("Failed to rate context quality", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to rate context quality")


@router.get("/statistics")
async def get_feedback_statistics(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get feedback statistics for the user.
    """
    try:
        user_id = current_user["user_id"]

        # Get feedback counts by type
        query = """
            SELECT
                feedback_type,
                feedback_value,
                COUNT(*) as count
            FROM ai_feedback_events
            WHERE user_id = $1
                AND timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY feedback_type, feedback_value
            ORDER BY feedback_type, feedback_value
        """

        results = await db.fetch_all(query % days_back, user_id)

        statistics = {
            "total_feedback": 0,
            "by_type": {},
            "by_value": {"positive": 0, "negative": 0, "neutral": 0},
            "period_days": days_back,
        }

        for row in results:
            feedback_type = row[0]
            feedback_value = row[1]
            count = row[2]

            statistics["total_feedback"] += count
            statistics["by_value"][feedback_value] += count

            if feedback_type not in statistics["by_type"]:
                statistics["by_type"][feedback_type] = {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                }

            statistics["by_type"][feedback_type][feedback_value] = count

        return statistics

    except Exception as e:
        logger.error("Failed to get feedback statistics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve feedback statistics"
        )
