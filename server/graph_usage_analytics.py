"""
Graph Usage Analytics System
SPEC-040/041 Optimization: Track usage_count, last_accessed, relevance_score per node
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth import get_current_user, get_db
from redis_client import get_redis_client

# Initialize router
router = APIRouter(prefix="/graph-analytics", tags=["graph-usage-analytics"])

@dataclass
class NodeUsageMetrics:
    """Usage metrics for a graph node"""
    node_id: str
    node_type: str
    usage_count: int
    last_accessed: datetime
    relevance_score: float
    access_frequency: float  # accesses per day
    user_interactions: int
    ai_suggestions: int
    feedback_score: float

@dataclass
class GraphUsageInsight:
    """Insight derived from usage analytics"""
    insight_type: str
    title: str
    description: str
    affected_nodes: List[str]
    confidence: float
    recommendation: str

class GraphUsageAnalytics:
    """Core analytics engine for graph usage tracking"""
    
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
        self.analytics_ttl = 86400  # 24 hours
    
    async def track_node_access(self, node_id: str, node_type: str, user_id: str, 
                               access_type: str = "view") -> None:
        """Track when a node is accessed"""
        
        # Update usage count
        usage_key = f"graph:usage:{node_id}"
        await self.redis.hincrby(usage_key, "usage_count", 1)
        await self.redis.hset(usage_key, "last_accessed", datetime.utcnow().isoformat())
        await self.redis.hset(usage_key, "node_type", node_type)
        await self.redis.expire(usage_key, self.analytics_ttl)
        
        # Track user-specific access
        user_access_key = f"graph:user_access:{user_id}:{node_id}"
        await self.redis.hincrby(user_access_key, "count", 1)
        await self.redis.hset(user_access_key, "last_access", datetime.utcnow().isoformat())
        await self.redis.hset(user_access_key, "access_type", access_type)
        await self.redis.expire(user_access_key, self.analytics_ttl)
        
        # Track access patterns by hour
        hour_key = f"graph:hourly:{datetime.utcnow().strftime('%Y%m%d_%H')}"
        await self.redis.hincrby(hour_key, node_id, 1)
        await self.redis.expire(hour_key, 86400 * 7)  # Keep for 7 days
    
    async def track_ai_suggestion(self, node_id: str, suggestion_type: str, 
                                 confidence: float, user_id: str) -> None:
        """Track when a node is suggested by AI"""
        
        # Update AI suggestion count
        ai_key = f"graph:ai_suggestions:{node_id}"
        await self.redis.hincrby(ai_key, "suggestion_count", 1)
        await self.redis.hset(ai_key, "last_suggested", datetime.utcnow().isoformat())
        await self.redis.hset(ai_key, "suggestion_type", suggestion_type)
        await self.redis.expire(ai_key, self.analytics_ttl)
        
        # Track suggestion confidence
        confidence_key = f"graph:confidence:{node_id}"
        current_confidence = await self.redis.hget(confidence_key, "avg_confidence")
        current_count = await self.redis.hget(confidence_key, "count")
        
        if current_confidence and current_count:
            # Calculate running average
            current_avg = float(current_confidence)
            count = int(current_count)
            new_avg = ((current_avg * count) + confidence) / (count + 1)
            await self.redis.hset(confidence_key, "avg_confidence", new_avg)
            await self.redis.hincrby(confidence_key, "count", 1)
        else:
            # First confidence score
            await self.redis.hset(confidence_key, "avg_confidence", confidence)
            await self.redis.hset(confidence_key, "count", 1)
        
        await self.redis.expire(confidence_key, self.analytics_ttl)
    
    async def track_user_feedback(self, node_id: str, user_id: str, 
                                 feedback_score: float, feedback_type: str) -> None:
        """Track user feedback on nodes"""
        
        # Update feedback metrics
        feedback_key = f"graph:feedback:{node_id}"
        current_score = await self.redis.hget(feedback_key, "avg_feedback")
        current_count = await self.redis.hget(feedback_key, "feedback_count")
        
        if current_score and current_count:
            # Calculate running average
            current_avg = float(current_score)
            count = int(current_count)
            new_avg = ((current_avg * count) + feedback_score) / (count + 1)
            await self.redis.hset(feedback_key, "avg_feedback", new_avg)
            await self.redis.hincrby(feedback_key, "feedback_count", 1)
        else:
            # First feedback
            await self.redis.hset(feedback_key, "avg_feedback", feedback_score)
            await self.redis.hset(feedback_key, "feedback_count", 1)
        
        await self.redis.hset(feedback_key, "last_feedback", datetime.utcnow().isoformat())
        await self.redis.expire(feedback_key, self.analytics_ttl)
        
        # Track user-specific feedback
        user_feedback_key = f"graph:user_feedback:{user_id}:{node_id}"
        await self.redis.hset(user_feedback_key, "score", feedback_score)
        await self.redis.hset(user_feedback_key, "type", feedback_type)
        await self.redis.hset(user_feedback_key, "timestamp", datetime.utcnow().isoformat())
        await self.redis.expire(user_feedback_key, self.analytics_ttl)
    
    async def calculate_relevance_score(self, node_id: str) -> float:
        """Calculate dynamic relevance score based on usage patterns"""
        
        # Get usage metrics
        usage_key = f"graph:usage:{node_id}"
        usage_data = await self.redis.hgetall(usage_key)
        
        if not usage_data:
            return 0.0
        
        usage_count = int(usage_data.get("usage_count", 0))
        last_accessed = usage_data.get("last_accessed")
        
        # Get AI suggestion metrics
        ai_key = f"graph:ai_suggestions:{node_id}"
        ai_data = await self.redis.hgetall(ai_key)
        suggestion_count = int(ai_data.get("suggestion_count", 0))
        
        # Get confidence metrics
        confidence_key = f"graph:confidence:{node_id}"
        confidence_data = await self.redis.hgetall(confidence_key)
        avg_confidence = float(confidence_data.get("avg_confidence", 0.0))
        
        # Get feedback metrics
        feedback_key = f"graph:feedback:{node_id}"
        feedback_data = await self.redis.hgetall(feedback_key)
        avg_feedback = float(feedback_data.get("avg_feedback", 0.5))  # Default neutral
        
        # Calculate recency factor
        recency_factor = 1.0
        if last_accessed:
            last_access_time = datetime.fromisoformat(last_accessed)
            days_since_access = (datetime.utcnow() - last_access_time).days
            recency_factor = max(0.1, 1.0 - (days_since_access * 0.1))  # Decay over time
        
        # Calculate composite relevance score
        usage_score = min(usage_count / 100.0, 1.0)  # Normalize to 0-1
        suggestion_score = min(suggestion_count / 50.0, 1.0)  # Normalize to 0-1
        
        relevance_score = (
            usage_score * 0.3 +           # 30% usage frequency
            suggestion_score * 0.2 +      # 20% AI suggestions
            avg_confidence * 0.2 +        # 20% AI confidence
            avg_feedback * 0.2 +          # 20% user feedback
            recency_factor * 0.1          # 10% recency
        )
        
        return min(relevance_score, 1.0)
    
    async def get_node_metrics(self, node_id: str) -> Optional[NodeUsageMetrics]:
        """Get comprehensive metrics for a node"""
        
        # Get all metric data
        usage_key = f"graph:usage:{node_id}"
        usage_data = await self.redis.hgetall(usage_key)
        
        if not usage_data:
            return None
        
        ai_key = f"graph:ai_suggestions:{node_id}"
        ai_data = await self.redis.hgetall(ai_key)
        
        feedback_key = f"graph:feedback:{node_id}"
        feedback_data = await self.redis.hgetall(feedback_key)
        
        # Calculate access frequency (accesses per day)
        usage_count = int(usage_data.get("usage_count", 0))
        last_accessed_str = usage_data.get("last_accessed")
        
        access_frequency = 0.0
        if last_accessed_str and usage_count > 0:
            last_accessed = datetime.fromisoformat(last_accessed_str)
            days_active = max((datetime.utcnow() - last_accessed).days, 1)
            access_frequency = usage_count / days_active
        
        # Calculate relevance score
        relevance_score = await self.calculate_relevance_score(node_id)
        
        return NodeUsageMetrics(
            node_id=node_id,
            node_type=usage_data.get("node_type", "Unknown"),
            usage_count=usage_count,
            last_accessed=datetime.fromisoformat(last_accessed_str) if last_accessed_str else datetime.utcnow(),
            relevance_score=relevance_score,
            access_frequency=access_frequency,
            user_interactions=usage_count,  # Simplified for now
            ai_suggestions=int(ai_data.get("suggestion_count", 0)),
            feedback_score=float(feedback_data.get("avg_feedback", 0.5))
        )
    
    async def analyze_usage_patterns(self, user_id: Optional[str] = None) -> List[GraphUsageInsight]:
        """Analyze usage patterns and generate insights"""
        
        insights = []
        
        # Get all nodes with usage data
        usage_keys = await self.redis.keys("graph:usage:*")
        node_metrics = []
        
        for key in usage_keys[:50]:  # Limit to 50 nodes for performance
            node_id = key.split(":")[-1]
            metrics = await self.get_node_metrics(node_id)
            if metrics:
                node_metrics.append(metrics)
        
        if not node_metrics:
            return insights
        
        # Sort by relevance score
        node_metrics.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Insight 1: Highly relevant nodes
        top_nodes = [m for m in node_metrics[:5] if m.relevance_score > 0.8]
        if top_nodes:
            insights.append(GraphUsageInsight(
                insight_type="high_relevance",
                title="Highly Relevant Nodes Identified",
                description=f"Found {len(top_nodes)} nodes with high relevance scores (>0.8)",
                affected_nodes=[n.node_id for n in top_nodes],
                confidence=0.9,
                recommendation="Consider promoting these nodes in recommendations"
            ))
        
        # Insight 2: Underutilized nodes
        underutilized = [m for m in node_metrics if m.usage_count > 0 and m.relevance_score < 0.3]
        if underutilized:
            insights.append(GraphUsageInsight(
                insight_type="underutilized",
                title="Underutilized Nodes Detected",
                description=f"Found {len(underutilized)} nodes with low relevance despite usage",
                affected_nodes=[n.node_id for n in underutilized[:10]],
                confidence=0.7,
                recommendation="Review content quality or improve discoverability"
            ))
        
        # Insight 3: High AI confidence but low user feedback
        ai_mismatch = [m for m in node_metrics if m.ai_suggestions > 5 and m.feedback_score < 0.4]
        if ai_mismatch:
            insights.append(GraphUsageInsight(
                insight_type="ai_user_mismatch",
                title="AI-User Preference Mismatch",
                description=f"Found {len(ai_mismatch)} nodes frequently suggested by AI but poorly rated by users",
                affected_nodes=[n.node_id for n in ai_mismatch[:10]],
                confidence=0.8,
                recommendation="Adjust AI recommendation algorithms or improve content"
            ))
        
        # Insight 4: Trending nodes (high recent activity)
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        trending = [m for m in node_metrics if m.last_accessed > recent_threshold and m.access_frequency > 2.0]
        if trending:
            insights.append(GraphUsageInsight(
                insight_type="trending",
                title="Trending Nodes Identified",
                description=f"Found {len(trending)} nodes with high recent activity",
                affected_nodes=[n.node_id for n in trending],
                confidence=0.85,
                recommendation="Consider featuring these nodes or analyzing what makes them popular"
            ))
        
        return insights
    
    async def get_usage_summary(self, time_window: str = "24h") -> Dict[str, Any]:
        """Get usage summary statistics"""
        
        # Calculate time window
        if time_window == "24h":
            start_time = datetime.utcnow() - timedelta(hours=24)
        elif time_window == "7d":
            start_time = datetime.utcnow() - timedelta(days=7)
        elif time_window == "30d":
            start_time = datetime.utcnow() - timedelta(days=30)
        else:
            start_time = datetime.utcnow() - timedelta(hours=24)
        
        # Get all usage keys
        usage_keys = await self.redis.keys("graph:usage:*")
        
        total_nodes = len(usage_keys)
        total_accesses = 0
        active_nodes = 0
        avg_relevance = 0.0
        
        relevance_scores = []
        
        for key in usage_keys:
            node_id = key.split(":")[-1]
            usage_data = await self.redis.hgetall(key)
            
            if usage_data:
                usage_count = int(usage_data.get("usage_count", 0))
                total_accesses += usage_count
                
                last_accessed_str = usage_data.get("last_accessed")
                if last_accessed_str:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                    if last_accessed > start_time:
                        active_nodes += 1
                
                # Calculate relevance for this node
                relevance = await self.calculate_relevance_score(node_id)
                relevance_scores.append(relevance)
        
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        return {
            "time_window": time_window,
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "total_accesses": total_accesses,
            "avg_accesses_per_node": total_accesses / max(total_nodes, 1),
            "avg_relevance_score": avg_relevance,
            "activity_rate": active_nodes / max(total_nodes, 1),
            "timestamp": datetime.utcnow().isoformat()
        }


# Pydantic Models
class NodeAccessRequest(BaseModel):
    """Request to track node access"""
    node_id: str
    node_type: str
    access_type: str = Field(default="view")

class AIFeedbackRequest(BaseModel):
    """Request to track AI suggestion feedback"""
    node_id: str
    suggestion_type: str
    confidence: float = Field(ge=0.0, le=1.0)

class UserFeedbackRequest(BaseModel):
    """Request to track user feedback"""
    node_id: str
    feedback_score: float = Field(ge=0.0, le=1.0)
    feedback_type: str = Field(default="relevance")

class UsageAnalyticsResponse(BaseModel):
    """Response with usage analytics"""
    summary: Dict[str, Any]
    insights: List[Dict[str, Any]]
    top_nodes: List[Dict[str, Any]]
    timestamp: str

# Global analytics engine
analytics_engine = None

async def get_analytics_engine(db: Session = Depends(get_db)):
    """Get or create analytics engine instance"""
    global analytics_engine
    if analytics_engine is None:
        redis_client = await get_redis_client()
        analytics_engine = GraphUsageAnalytics(redis_client, db)
    return analytics_engine

# API Endpoints

@router.post("/track-access")
async def track_node_access(
    request: NodeAccessRequest,
    current_user = Depends(get_current_user),
    analytics: GraphUsageAnalytics = Depends(get_analytics_engine)
):
    """Track node access for analytics"""
    
    user_id = current_user.get("user_id", "unknown")
    
    await analytics.track_node_access(
        node_id=request.node_id,
        node_type=request.node_type,
        user_id=user_id,
        access_type=request.access_type
    )
    
    return {"status": "tracked", "node_id": request.node_id, "timestamp": datetime.utcnow().isoformat()}

@router.post("/track-ai-suggestion")
async def track_ai_suggestion(
    request: AIFeedbackRequest,
    current_user = Depends(get_current_user),
    analytics: GraphUsageAnalytics = Depends(get_analytics_engine)
):
    """Track AI suggestion for analytics"""
    
    user_id = current_user.get("user_id", "unknown")
    
    await analytics.track_ai_suggestion(
        node_id=request.node_id,
        suggestion_type=request.suggestion_type,
        confidence=request.confidence,
        user_id=user_id
    )
    
    return {"status": "tracked", "node_id": request.node_id, "timestamp": datetime.utcnow().isoformat()}

@router.post("/track-feedback")
async def track_user_feedback(
    request: UserFeedbackRequest,
    current_user = Depends(get_current_user),
    analytics: GraphUsageAnalytics = Depends(get_analytics_engine)
):
    """Track user feedback for analytics"""
    
    user_id = current_user.get("user_id", "unknown")
    
    await analytics.track_user_feedback(
        node_id=request.node_id,
        user_id=user_id,
        feedback_score=request.feedback_score,
        feedback_type=request.feedback_type
    )
    
    return {"status": "tracked", "node_id": request.node_id, "timestamp": datetime.utcnow().isoformat()}

@router.get("/analytics", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    time_window: str = "24h",
    current_user = Depends(get_current_user),
    analytics: GraphUsageAnalytics = Depends(get_analytics_engine)
):
    """Get comprehensive usage analytics"""
    
    try:
        # Get usage summary
        summary = await analytics.get_usage_summary(time_window)
        
        # Get insights
        insights = await analytics.analyze_usage_patterns()
        
        # Get top nodes by relevance
        usage_keys = await analytics.redis.keys("graph:usage:*")
        top_nodes = []
        
        for key in usage_keys[:10]:  # Top 10 nodes
            node_id = key.split(":")[-1]
            metrics = await analytics.get_node_metrics(node_id)
            if metrics:
                top_nodes.append({
                    "node_id": metrics.node_id,
                    "node_type": metrics.node_type,
                    "relevance_score": metrics.relevance_score,
                    "usage_count": metrics.usage_count,
                    "last_accessed": metrics.last_accessed.isoformat()
                })
        
        # Sort by relevance score
        top_nodes.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return UsageAnalyticsResponse(
            summary=summary,
            insights=[insight.__dict__ for insight in insights],
            top_nodes=top_nodes[:5],  # Top 5
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.get("/node/{node_id}/metrics")
async def get_node_metrics(
    node_id: str,
    current_user = Depends(get_current_user),
    analytics: GraphUsageAnalytics = Depends(get_analytics_engine)
):
    """Get detailed metrics for a specific node"""
    
    metrics = await analytics.get_node_metrics(node_id)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Node metrics not found")
    
    return {
        "node_id": metrics.node_id,
        "node_type": metrics.node_type,
        "usage_count": metrics.usage_count,
        "last_accessed": metrics.last_accessed.isoformat(),
        "relevance_score": metrics.relevance_score,
        "access_frequency": metrics.access_frequency,
        "ai_suggestions": metrics.ai_suggestions,
        "feedback_score": metrics.feedback_score,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def analytics_health():
    """Health check for analytics system"""
    return {
        "status": "healthy",
        "service": "graph-usage-analytics",
        "tracking_features": ["node_access", "ai_suggestions", "user_feedback", "relevance_scoring"],
        "timestamp": datetime.utcnow().isoformat()
    }
