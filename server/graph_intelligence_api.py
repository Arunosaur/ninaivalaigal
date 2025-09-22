"""
Graph Intelligence API - SPEC-061 FastAPI Integration

Exposes GraphReasoner methods via REST API endpoints for AI-powered graph reasoning.
"""

from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.auth import get_current_user
from server.graph.age_client import get_age_client
from server.graph.graph_reasoner import GraphReasoner, create_graph_reasoner
from server.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph Intelligence"])


# Request/Response Models
class ExplainContextRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID to explain")
    context_type: str = Field(
        default="retrieval", description="Type of context explanation"
    )
    max_depth: int = Field(
        default=3, ge=1, le=10, description="Maximum graph traversal depth"
    )


class ExplainContextResponse(BaseModel):
    memory_id: str
    retrieval_reason: str
    paths: list[dict[str, Any]]
    relevance_score: float
    confidence: float
    supporting_evidence: list[str]


class InferRelevanceRequest(BaseModel):
    current_memory_id: str = Field(..., description="Current memory context")
    suggestion_count: int = Field(
        default=5, ge=1, le=20, description="Number of suggestions"
    )
    context_memories: Optional[list[str]] = Field(
        default=None, description="Additional context memories"
    )


class InferRelevanceResponse(BaseModel):
    suggested_memories: list[str]
    suggested_agents: list[str]
    reasoning_scores: dict[str, float]
    proximity_metrics: dict[str, float]
    confidence: float


class FeedbackLoopRequest(BaseModel):
    memory_id: str = Field(..., description="Memory being rated")
    feedback_type: str = Field(
        ..., description="Type of feedback (relevance, accuracy, usefulness)"
    )
    feedback_score: float = Field(
        ..., ge=0.0, le=1.0, description="Feedback score (0.0 to 1.0)"
    )
    context_data: Optional[dict[str, Any]] = Field(
        default=None, description="Additional context"
    )


class FeedbackLoopResponse(BaseModel):
    feedback_stored: bool
    weight_updates: dict[str, Any]
    cache_invalidated: bool


class AnalyzeNetworkRequest(BaseModel):
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    time_window: Optional[str] = Field(
        default=None, description="Time window for analysis"
    )


class AnalyzeNetworkResponse(BaseModel):
    structure: dict[str, Any]
    patterns: dict[str, Any]
    insights: list[str]
    recommendations: list[str]


# Dependency to get GraphReasoner instance
async def get_graph_reasoner() -> GraphReasoner:
    """Get GraphReasoner instance with dependencies"""
    age_client = await get_age_client()
    redis_client = await get_redis_client()
    return create_graph_reasoner(age_client, redis_client)


@router.post("/explain-context", response_model=ExplainContextResponse)
async def explain_context(
    request: ExplainContextRequest,
    current_user: dict = Depends(get_current_user),
    graph_reasoner: GraphReasoner = Depends(get_graph_reasoner),
):
    """
    Explain why a memory was retrieved with traceable reasoning paths.

    Shows the graph reasoning behind memory retrieval with confidence scores
    and supporting evidence.
    """
    try:
        user_id = current_user["user_id"]

        logger.info(
            "Explaining memory context",
            memory_id=request.memory_id,
            user_id=user_id,
            context_type=request.context_type,
            max_depth=request.max_depth,
        )

        explanation = await graph_reasoner.explain_context(
            memory_id=request.memory_id,
            user_id=user_id,
            context_type=request.context_type,
            max_depth=request.max_depth,
        )

        return ExplainContextResponse(
            memory_id=explanation.memory_id,
            retrieval_reason=explanation.retrieval_reason,
            paths=[path.__dict__ for path in explanation.paths],
            relevance_score=explanation.relevance_score,
            confidence=explanation.confidence,
            supporting_evidence=explanation.supporting_evidence,
        )

    except Exception as e:
        logger.error(
            "Failed to explain context", error=str(e), memory_id=request.memory_id
        )
        raise HTTPException(
            status_code=500, detail=f"Context explanation failed: {str(e)}"
        ) from e


@router.post("/infer-relevance", response_model=InferRelevanceResponse)
async def infer_relevance(
    request: InferRelevanceRequest,
    current_user: dict = Depends(get_current_user),
    graph_reasoner: GraphReasoner = Depends(get_graph_reasoner),
):
    """
    Suggest relevant memories and agents based on graph proximity.

    Uses graph distance and relevance scoring to recommend related content.
    """
    try:
        user_id = current_user["user_id"]

        logger.info(
            "Inferring memory relevance",
            current_memory_id=request.current_memory_id,
            user_id=user_id,
            suggestion_count=request.suggestion_count,
        )

        inference = await graph_reasoner.infer_relevance(
            current_memory_id=request.current_memory_id,
            user_id=user_id,
            suggestion_count=request.suggestion_count,
            context_memories=request.context_memories,
        )

        return InferRelevanceResponse(
            suggested_memories=inference.suggested_memories,
            suggested_agents=inference.suggested_agents,
            reasoning_scores=inference.reasoning_scores,
            proximity_metrics=inference.proximity_metrics,
            confidence=inference.confidence,
        )

    except Exception as e:
        logger.error(
            "Failed to infer relevance",
            error=str(e),
            memory_id=request.current_memory_id,
        )
        raise HTTPException(
            status_code=500, detail=f"Relevance inference failed: {str(e)}"
        ) from e


@router.post("/feedback-loop", response_model=FeedbackLoopResponse)
async def feedback_loop(
    request: FeedbackLoopRequest,
    current_user: dict = Depends(get_current_user),
    graph_reasoner: GraphReasoner = Depends(get_graph_reasoner),
):
    """
    Refine graph traversal using user feedback and ranking signals.

    Stores user feedback as weighted edges and updates traversal parameters.
    """
    try:
        user_id = current_user["user_id"]

        logger.info(
            "Processing feedback loop",
            memory_id=request.memory_id,
            user_id=user_id,
            feedback_type=request.feedback_type,
            feedback_score=request.feedback_score,
        )

        result = await graph_reasoner.feedback_loop(
            user_id=user_id,
            memory_id=request.memory_id,
            feedback_type=request.feedback_type,
            feedback_score=request.feedback_score,
            context_data=request.context_data,
        )

        return FeedbackLoopResponse(
            feedback_stored=result["feedback_stored"],
            weight_updates=result["weight_updates"],
            cache_invalidated=result.get("cache_invalidated", False),
        )

    except Exception as e:
        logger.error(
            "Failed to process feedback", error=str(e), memory_id=request.memory_id
        )
        raise HTTPException(
            status_code=500, detail=f"Feedback processing failed: {str(e)}"
        ) from e


@router.post("/analyze-network", response_model=AnalyzeNetworkResponse)
async def analyze_network(
    request: AnalyzeNetworkRequest,
    current_user: dict = Depends(get_current_user),
    graph_reasoner: GraphReasoner = Depends(get_graph_reasoner),
):
    """
    Analyze user's memory network for insights and patterns.

    Provides comprehensive network analysis with structure metrics,
    pattern detection, and actionable insights.
    """
    try:
        user_id = current_user["user_id"]

        logger.info(
            "Analyzing memory network",
            user_id=user_id,
            analysis_type=request.analysis_type,
            time_window=request.time_window,
        )

        analysis = await graph_reasoner.analyze_memory_network(
            user_id=user_id,
            analysis_type=request.analysis_type,
            time_window=request.time_window,
        )

        return AnalyzeNetworkResponse(
            structure=analysis["structure"],
            patterns=analysis["patterns"],
            insights=analysis["insights"],
            recommendations=analysis["recommendations"],
        )

    except Exception as e:
        logger.error(
            "Failed to analyze network", error=str(e), user_id=current_user["user_id"]
        )
        raise HTTPException(
            status_code=500, detail=f"Network analysis failed: {str(e)}"
        ) from e


@router.get("/health")
async def graph_intelligence_health():
    """Health check for graph intelligence services"""
    try:
        # Test GraphReasoner initialization
        graph_reasoner = await get_graph_reasoner()

        return {
            "status": "healthy",
            "service": "graph-intelligence",
            "cache_ttl": graph_reasoner.cache_ttl,
            "components": {
                "graph_reasoner": "operational",
                "apache_age": "connected",
                "redis_cache": "connected",
            },
        }
    except Exception as e:
        logger.error("Graph intelligence health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@router.get("/stats")
async def graph_intelligence_stats(
    current_user: dict = Depends(get_current_user),
    graph_reasoner: GraphReasoner = Depends(get_graph_reasoner),
):
    """Get graph intelligence usage statistics"""
    try:
        user_id = current_user["user_id"]

        # Get basic stats from cache keys
        cache_keys = await graph_reasoner.redis_client.keys(f"graph:*:{user_id}:*")

        return {
            "user_id": user_id,
            "cached_explanations": len([k for k in cache_keys if "explain" in k]),
            "cached_inferences": len([k for k in cache_keys if "infer" in k]),
            "cached_analyses": len([k for k in cache_keys if "analyze" in k]),
            "total_cache_entries": len(cache_keys),
            "cache_ttl_seconds": graph_reasoner.cache_ttl,
        }
    except Exception as e:
        logger.error(
            "Failed to get stats", error=str(e), user_id=current_user["user_id"]
        )
        raise HTTPException(
            status_code=500, detail=f"Stats retrieval failed: {str(e)}"
        ) from e
