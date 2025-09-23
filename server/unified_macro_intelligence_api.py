"""
SPEC-059: Unified Macro Intelligence
AI differentiation and competitive advantage through intelligent memory analysis and insights
"""

import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import asyncio
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, text
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import User, Team, Organization
from redis_client import get_redis_client
from relevance_engine import RelevanceEngine

# Initialize router
router = APIRouter(prefix="/macro-intelligence", tags=["macro-intelligence"])

# Pydantic Models
class MacroInsightRequest(BaseModel):
    """Request model for macro intelligence analysis"""
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    org_id: Optional[str] = None
    time_range_days: int = Field(default=30, ge=1, le=365)
    analysis_types: List[str] = Field(default=["patterns", "trends", "insights", "recommendations"])
    include_predictions: bool = Field(default=True)
    context_filter: Optional[str] = None


class MacroInsight(BaseModel):
    """Individual macro insight"""
    id: str
    type: str  # pattern, trend, insight, recommendation, prediction
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    impact_level: str  # low, medium, high, critical
    category: str  # productivity, learning, collaboration, efficiency
    data_points: List[Dict[str, Any]]
    actionable_items: List[str]
    created_at: datetime


class MacroIntelligenceResponse(BaseModel):
    """Response model for macro intelligence analysis"""
    analysis_id: str
    user_id: Optional[str]
    team_id: Optional[str]
    org_id: Optional[str]
    time_range: Dict[str, datetime]
    insights: List[MacroInsight]
    summary: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    generated_at: datetime


class IntelligenceMetrics(BaseModel):
    """Intelligence system metrics"""
    total_insights_generated: int
    avg_confidence_score: float
    insights_by_category: Dict[str, int]
    insights_by_impact: Dict[str, int]
    processing_time_ms: float
    cache_hit_rate: float


# Intelligence Engine Classes
@dataclass
class MemoryPattern:
    """Represents a discovered memory pattern"""
    pattern_type: str
    frequency: int
    contexts: List[str]
    time_distribution: Dict[str, int]
    confidence: float


class MacroIntelligenceEngine:
    """Core engine for macro intelligence analysis"""
    
    def __init__(self, redis_client, relevance_engine: RelevanceEngine):
        self.redis = redis_client
        self.relevance_engine = relevance_engine
        self.cache_ttl = 3600  # 1 hour cache
    
    async def analyze_memory_patterns(self, user_id: str, days: int = 30) -> List[MemoryPattern]:
        """Analyze memory usage patterns for insights"""
        cache_key = f"macro:patterns:{user_id}:{days}"
        
        # Check cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return [MemoryPattern(**p) for p in json.loads(cached)]
        
        # Mock pattern analysis (in production, query actual memory data)
        patterns = [
            MemoryPattern(
                pattern_type="daily_peak",
                frequency=85,
                contexts=["work", "research"],
                time_distribution={"morning": 40, "afternoon": 45, "evening": 15},
                confidence=0.87
            ),
            MemoryPattern(
                pattern_type="context_clustering",
                frequency=72,
                contexts=["project_alpha", "meetings"],
                time_distribution={"weekday": 80, "weekend": 20},
                confidence=0.74
            ),
            MemoryPattern(
                pattern_type="knowledge_gaps",
                frequency=23,
                contexts=["learning", "documentation"],
                time_distribution={"consistent": 100},
                confidence=0.91
            )
        ]
        
        # Cache results
        await self.redis.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps([p.__dict__ for p in patterns])
        )
        
        return patterns
    
    async def generate_insights(self, patterns: List[MemoryPattern], user_id: str) -> List[MacroInsight]:
        """Generate actionable insights from patterns"""
        insights = []
        
        for pattern in patterns:
            if pattern.pattern_type == "daily_peak" and pattern.confidence > 0.8:
                insights.append(MacroInsight(
                    id=str(uuid4()),
                    type="insight",
                    title="Peak Productivity Hours Identified",
                    description=f"Your memory activity peaks during afternoon hours ({pattern.time_distribution['afternoon']}% of activity). Consider scheduling important tasks during this time.",
                    confidence_score=pattern.confidence,
                    impact_level="high",
                    category="productivity",
                    data_points=[{
                        "metric": "time_distribution",
                        "values": pattern.time_distribution,
                        "contexts": pattern.contexts
                    }],
                    actionable_items=[
                        "Schedule important meetings in the afternoon",
                        "Block afternoon time for deep work",
                        "Use morning for routine tasks"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            elif pattern.pattern_type == "context_clustering" and pattern.confidence > 0.7:
                insights.append(MacroInsight(
                    id=str(uuid4()),
                    type="pattern",
                    title="Context Clustering Detected",
                    description=f"Strong correlation between {', '.join(pattern.contexts)} contexts suggests workflow optimization opportunities.",
                    confidence_score=pattern.confidence,
                    impact_level="medium",
                    category="efficiency",
                    data_points=[{
                        "metric": "context_correlation",
                        "contexts": pattern.contexts,
                        "frequency": pattern.frequency
                    }],
                    actionable_items=[
                        "Create templates for recurring context combinations",
                        "Set up automated workflows",
                        "Consider context-specific memory organization"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            elif pattern.pattern_type == "knowledge_gaps" and pattern.confidence > 0.85:
                insights.append(MacroInsight(
                    id=str(uuid4()),
                    type="recommendation",
                    title="Learning Opportunities Identified",
                    description="Consistent gaps in documentation and learning contexts suggest structured learning could improve productivity.",
                    confidence_score=pattern.confidence,
                    impact_level="high",
                    category="learning",
                    data_points=[{
                        "metric": "gap_frequency",
                        "value": pattern.frequency,
                        "contexts": pattern.contexts
                    }],
                    actionable_items=[
                        "Schedule regular learning sessions",
                        "Create knowledge base templates",
                        "Set up documentation workflows"
                    ],
                    created_at=datetime.utcnow()
                ))
        
        return insights
    
    async def generate_predictions(self, patterns: List[MemoryPattern], user_id: str) -> List[MacroInsight]:
        """Generate predictive insights"""
        predictions = []
        
        # Predict future memory needs based on patterns
        if any(p.pattern_type == "daily_peak" for p in patterns):
            predictions.append(MacroInsight(
                id=str(uuid4()),
                type="prediction",
                title="Memory Usage Forecast",
                description="Based on current patterns, expect 25% increase in memory activity next week during project deadlines.",
                confidence_score=0.78,
                impact_level="medium",
                category="productivity",
                data_points=[{
                    "metric": "predicted_increase",
                    "value": 25,
                    "timeframe": "next_week"
                }],
                actionable_items=[
                    "Prepare additional memory capacity",
                    "Schedule memory organization time",
                    "Set up automated backups"
                ],
                created_at=datetime.utcnow()
            ))
        
        return predictions
    
    async def calculate_summary_metrics(self, insights: List[MacroInsight]) -> Dict[str, Any]:
        """Calculate summary metrics for the analysis"""
        if not insights:
            return {"total_insights": 0, "avg_confidence": 0.0}
        
        total_insights = len(insights)
        avg_confidence = sum(i.confidence_score for i in insights) / total_insights
        
        category_counts = {}
        impact_counts = {}
        
        for insight in insights:
            category_counts[insight.category] = category_counts.get(insight.category, 0) + 1
            impact_counts[insight.impact_level] = impact_counts.get(insight.impact_level, 0) + 1
        
        return {
            "total_insights": total_insights,
            "avg_confidence": round(avg_confidence, 3),
            "insights_by_category": category_counts,
            "insights_by_impact": impact_counts,
            "high_impact_insights": len([i for i in insights if i.impact_level == "high"]),
            "actionable_recommendations": sum(len(i.actionable_items) for i in insights)
        }


# Global intelligence engine instance
intelligence_engine = None

async def get_intelligence_engine():
    """Get or create intelligence engine instance"""
    global intelligence_engine
    if intelligence_engine is None:
        redis_client = await get_redis_client()
        relevance_engine = RelevanceEngine(redis_client)
        intelligence_engine = MacroIntelligenceEngine(redis_client, relevance_engine)
    return intelligence_engine


# API Endpoints

@router.post("/analyze", response_model=MacroIntelligenceResponse)
async def analyze_macro_intelligence(
    request: MacroIntelligenceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate macro intelligence analysis"""
    
    start_time = datetime.utcnow()
    analysis_id = str(uuid4())
    
    # Determine analysis scope
    target_user_id = request.user_id or str(current_user.id)
    
    # Validate access permissions
    if request.user_id and request.user_id != str(current_user.id):
        # Check if current user has permission to analyze other users
        # In production, implement proper RBAC checks
        pass
    
    try:
        engine = await get_intelligence_engine()
        
        # Analyze memory patterns
        patterns = await engine.analyze_memory_patterns(target_user_id, request.time_range_days)
        
        # Generate insights
        insights = []
        if "patterns" in request.analysis_types or "insights" in request.analysis_types:
            pattern_insights = await engine.generate_insights(patterns, target_user_id)
            insights.extend(pattern_insights)
        
        # Generate predictions
        if request.include_predictions and "predictions" in request.analysis_types:
            predictions = await engine.generate_predictions(patterns, target_user_id)
            insights.extend(predictions)
        
        # Calculate summary metrics
        summary = await engine.calculate_summary_metrics(insights)
        
        # Generate recommendations
        recommendations = []
        for insight in insights:
            if insight.type == "recommendation" and insight.confidence_score > 0.7:
                recommendations.extend(insight.actionable_items[:2])  # Top 2 items
        
        # Calculate overall confidence
        overall_confidence = summary.get("avg_confidence", 0.0)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        response = MacroIntelligenceResponse(
            analysis_id=analysis_id,
            user_id=target_user_id,
            team_id=request.team_id,
            org_id=request.org_id,
            time_range={
                "start": datetime.utcnow() - timedelta(days=request.time_range_days),
                "end": datetime.utcnow()
            },
            insights=insights,
            summary=summary,
            recommendations=recommendations[:5],  # Top 5 recommendations
            confidence_score=overall_confidence,
            generated_at=datetime.utcnow()
        )
        
        # Store analysis results in background
        background_tasks.add_task(store_analysis_results, analysis_id, response, processing_time)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/insights/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve stored analysis results"""
    
    engine = await get_intelligence_engine()
    cache_key = f"macro:analysis:{analysis_id}"
    
    cached_result = await engine.redis.get(cache_key)
    if not cached_result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return json.loads(cached_result)


@router.get("/metrics", response_model=IntelligenceMetrics)
async def get_intelligence_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get intelligence system metrics"""
    
    engine = await get_intelligence_engine()
    
    # Mock metrics (in production, calculate from actual data)
    metrics = IntelligenceMetrics(
        total_insights_generated=1247,
        avg_confidence_score=0.82,
        insights_by_category={
            "productivity": 456,
            "learning": 321,
            "collaboration": 289,
            "efficiency": 181
        },
        insights_by_impact={
            "high": 387,
            "medium": 623,
            "low": 237
        },
        processing_time_ms=1250.0,
        cache_hit_rate=0.73
    )
    
    return metrics


@router.post("/insights/{insight_id}/feedback")
async def provide_insight_feedback(
    insight_id: str,
    feedback: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Provide feedback on insight quality"""
    
    engine = await get_intelligence_engine()
    
    # Store feedback for model improvement
    feedback_key = f"macro:feedback:{insight_id}"
    feedback_data = {
        "user_id": str(current_user.id),
        "insight_id": insight_id,
        "feedback": feedback,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await engine.redis.setex(feedback_key, 86400 * 30, json.dumps(feedback_data))  # 30 days
    
    return {"message": "Feedback recorded successfully", "insight_id": insight_id}


@router.get("/trends")
async def get_intelligence_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get intelligence trends over time"""
    
    # Mock trend data (in production, calculate from historical analyses)
    trends = {
        "insight_generation_trend": [
            {"date": "2024-09-01", "count": 23},
            {"date": "2024-09-02", "count": 31},
            {"date": "2024-09-03", "count": 28},
            # ... more data points
        ],
        "confidence_trend": [
            {"date": "2024-09-01", "avg_confidence": 0.78},
            {"date": "2024-09-02", "avg_confidence": 0.82},
            {"date": "2024-09-03", "avg_confidence": 0.85},
            # ... more data points
        ],
        "category_trends": {
            "productivity": {"growth_rate": 0.15, "trend": "increasing"},
            "learning": {"growth_rate": 0.08, "trend": "stable"},
            "collaboration": {"growth_rate": 0.22, "trend": "increasing"},
            "efficiency": {"growth_rate": -0.05, "trend": "decreasing"}
        }
    }
    
    return trends


# Background Tasks

async def store_analysis_results(analysis_id: str, response: MacroIntelligenceResponse, processing_time: float):
    """Store analysis results for future retrieval"""
    
    engine = await get_intelligence_engine()
    cache_key = f"macro:analysis:{analysis_id}"
    
    # Store full results
    result_data = response.dict()
    result_data["processing_time_ms"] = processing_time
    
    await engine.redis.setex(cache_key, 86400 * 7, json.dumps(result_data, default=str))  # 7 days
    
    # Update metrics
    metrics_key = f"macro:metrics:{datetime.utcnow().date()}"
    await engine.redis.hincrby(metrics_key, "total_analyses", 1)
    await engine.redis.hincrbyfloat(metrics_key, "total_processing_time", processing_time)
    await engine.redis.expire(metrics_key, 86400 * 30)  # 30 days
