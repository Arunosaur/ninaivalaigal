"""
SPEC-042: Memory Health & Orphaned Token Report - API Endpoints

RESTful API for memory health monitoring and orphaned token management.
Provides comprehensive health analysis and reporting capabilities.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from auth import get_current_user
from database import User
from memory_health_engine import (
    get_health_engine,
    MemoryHealthEngine,
    MemoryHealthMetrics,
    OrphanedToken,
    SystemHealthReport,
    HealthStatus,
    TokenType
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/health", tags=["memory-health"])


# Request/Response models
class MemoryHealthResponse(BaseModel):
    memory_id: str
    user_id: int
    health_status: str
    quality_score: float
    last_accessed: Optional[datetime]
    access_frequency: int
    feedback_score: Optional[float]
    relevance_score: Optional[float]
    issues: List[str]
    recommendations: List[str]
    created_at: datetime
    updated_at: datetime


class OrphanedTokenResponse(BaseModel):
    token_id: str
    user_id: int
    last_accessed: Optional[datetime]
    created_at: datetime
    orphaned_since: datetime
    orphan_reason: str
    cleanup_recommendation: str
    estimated_impact: str


class SystemHealthReportResponse(BaseModel):
    report_id: str
    generated_at: datetime
    total_memories: int
    healthy_memories: int
    warning_memories: int
    critical_memories: int
    orphaned_tokens: int
    avg_quality_score: float
    system_health_status: str
    top_issues: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]


class HealthSummaryResponse(BaseModel):
    user_id: int
    total_memories: int
    health_distribution: Dict[str, int]
    avg_quality_score: float
    system_health_status: str
    last_analysis: datetime
    needs_attention: int
    orphaned_count: int


class CleanupRecommendationRequest(BaseModel):
    memory_ids: List[str]
    cleanup_type: str = Field(..., description="archive, delete, or review")
    confirm_action: bool = Field(False, description="Confirm the cleanup action")


# Dependency to get health engine
async def get_health_engine_dep() -> MemoryHealthEngine:
    """Dependency to get the health engine"""
    return await get_health_engine()


@router.get("/status")
async def health_system_status():
    """Memory health system status check"""
    try:
        engine = await get_health_engine()
        return {
            "status": "healthy",
            "service": "memory-health-api",
            "engine_initialized": engine is not None,
            "redis_connected": engine.redis_client is not None if engine else False,
            "monitoring_capabilities": [
                "memory_quality_analysis",
                "orphaned_token_detection",
                "health_report_generation",
                "automated_recommendations"
            ]
        }
    except Exception as e:
        logger.error("Memory health system check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "memory-health-api",
            "error": str(e)
        }


@router.get("/memory/{memory_id}", response_model=MemoryHealthResponse)
async def analyze_memory_health(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Analyze health of a specific memory"""
    try:
        health_metrics = await engine.analyze_memory_health(
            current_user.id, memory_id
        )
        
        return MemoryHealthResponse(
            memory_id=health_metrics.memory_id,
            user_id=health_metrics.user_id,
            health_status=health_metrics.health_status.value,
            quality_score=health_metrics.quality_score,
            last_accessed=health_metrics.last_accessed,
            access_frequency=health_metrics.access_frequency,
            feedback_score=health_metrics.feedback_score,
            relevance_score=health_metrics.relevance_score,
            issues=health_metrics.issues,
            recommendations=health_metrics.recommendations,
            created_at=health_metrics.created_at,
            updated_at=health_metrics.updated_at
        )
        
    except Exception as e:
        logger.error(
            "Failed to analyze memory health",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orphaned-tokens", response_model=List[OrphanedTokenResponse])
async def get_orphaned_tokens(
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Get list of orphaned tokens for the current user"""
    try:
        orphaned_tokens = await engine.detect_orphaned_tokens(current_user.id)
        
        return [
            OrphanedTokenResponse(
                token_id=token.token_id,
                user_id=token.user_id,
                last_accessed=token.last_accessed,
                created_at=token.created_at,
                orphaned_since=token.orphaned_since,
                orphan_reason=token.orphan_reason,
                cleanup_recommendation=token.cleanup_recommendation,
                estimated_impact=token.estimated_impact
            )
            for token in orphaned_tokens
        ]
        
    except Exception as e:
        logger.error(
            "Failed to get orphaned tokens",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", response_model=SystemHealthReportResponse)
async def generate_health_report(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Generate comprehensive health report"""
    try:
        health_report = await engine.generate_health_report(current_user.id)
        
        return SystemHealthReportResponse(
            report_id=health_report.report_id,
            generated_at=health_report.generated_at,
            total_memories=health_report.total_memories,
            healthy_memories=health_report.healthy_memories,
            warning_memories=health_report.warning_memories,
            critical_memories=health_report.critical_memories,
            orphaned_tokens=health_report.orphaned_tokens,
            avg_quality_score=health_report.avg_quality_score,
            system_health_status=health_report.system_health_status.value,
            top_issues=health_report.top_issues,
            recommendations=health_report.recommendations,
            metrics=health_report.metrics
        )
        
    except Exception as e:
        logger.error(
            "Failed to generate health report",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=HealthSummaryResponse)
async def get_health_summary(
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Get quick health summary for dashboard"""
    try:
        # Generate quick report
        health_report = await engine.generate_health_report(current_user.id)
        
        needs_attention = (
            health_report.warning_memories + 
            health_report.critical_memories + 
            health_report.orphaned_tokens
        )
        
        return HealthSummaryResponse(
            user_id=current_user.id,
            total_memories=health_report.total_memories,
            health_distribution={
                "healthy": health_report.healthy_memories,
                "warning": health_report.warning_memories,
                "critical": health_report.critical_memories,
                "orphaned": health_report.orphaned_tokens
            },
            avg_quality_score=health_report.avg_quality_score,
            system_health_status=health_report.system_health_status.value,
            last_analysis=health_report.generated_at,
            needs_attention=needs_attention,
            orphaned_count=health_report.orphaned_tokens
        )
        
    except Exception as e:
        logger.error(
            "Failed to get health summary",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues")
async def get_common_issues(
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Get most common health issues across user's memories"""
    try:
        health_report = await engine.generate_health_report(current_user.id)
        
        return {
            "top_issues": health_report.top_issues,
            "issue_count": len(health_report.top_issues),
            "recommendations": health_report.recommendations,
            "system_health": health_report.system_health_status.value,
            "analysis_timestamp": health_report.generated_at
        }
        
    except Exception as e:
        logger.error(
            "Failed to get common issues",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/recommendations")
async def get_cleanup_recommendations(
    request: CleanupRecommendationRequest,
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Get cleanup recommendations for specific memories"""
    try:
        recommendations = []
        
        for memory_id in request.memory_ids:
            try:
                health_metrics = await engine.analyze_memory_health(
                    current_user.id, memory_id
                )
                
                recommendation = {
                    "memory_id": memory_id,
                    "health_status": health_metrics.health_status.value,
                    "quality_score": health_metrics.quality_score,
                    "recommended_action": _determine_cleanup_action(health_metrics),
                    "reasons": health_metrics.issues,
                    "impact_assessment": _assess_cleanup_impact(health_metrics)
                }
                recommendations.append(recommendation)
                
            except Exception as e:
                logger.warning(
                    "Failed to analyze memory for cleanup",
                    memory_id=memory_id,
                    error=str(e)
                )
        
        return {
            "cleanup_type": request.cleanup_type,
            "recommendations": recommendations,
            "total_analyzed": len(recommendations),
            "confirm_required": not request.confirm_action,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(
            "Failed to get cleanup recommendations",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/scan")
async def trigger_maintenance_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Trigger background maintenance scan"""
    try:
        # Add background task for maintenance scan
        background_tasks.add_task(
            _perform_maintenance_scan,
            current_user.id
        )
        
        return {
            "message": "Maintenance scan initiated",
            "user_id": current_user.id,
            "scan_type": "full_health_analysis",
            "estimated_duration": "2-5 minutes",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(
            "Failed to trigger maintenance scan",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_health_metrics(
    current_user: User = Depends(get_current_user),
    engine: MemoryHealthEngine = Depends(get_health_engine_dep),
):
    """Get detailed health metrics for monitoring"""
    try:
        health_report = await engine.generate_health_report(current_user.id)
        
        return {
            "user_id": current_user.id,
            "metrics": health_report.metrics,
            "health_scores": {
                "avg_quality": health_report.avg_quality_score,
                "health_ratio": health_report.healthy_memories / max(1, health_report.total_memories),
                "orphan_ratio": health_report.orphaned_tokens / max(1, health_report.total_memories)
            },
            "trend_indicators": {
                "needs_attention": health_report.warning_memories + health_report.critical_memories,
                "system_health": health_report.system_health_status.value,
                "total_issues": len(health_report.top_issues)
            },
            "generated_at": health_report.generated_at
        }
        
    except Exception as e:
        logger.error(
            "Failed to get health metrics",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


def _determine_cleanup_action(health_metrics: MemoryHealthMetrics) -> str:
    """Determine recommended cleanup action based on health metrics"""
    
    if health_metrics.health_status == HealthStatus.ORPHANED:
        return "delete"
    elif health_metrics.health_status == HealthStatus.CRITICAL:
        if health_metrics.quality_score < 0.1:
            return "delete"
        else:
            return "review"
    elif health_metrics.health_status == HealthStatus.WARNING:
        return "review"
    else:
        return "keep"


def _assess_cleanup_impact(health_metrics: MemoryHealthMetrics) -> str:
    """Assess the impact of cleaning up a memory"""
    
    if health_metrics.access_frequency == 0:
        return "low_impact"
    elif health_metrics.access_frequency < 3:
        return "medium_impact"
    else:
        return "high_impact"


async def _perform_maintenance_scan(user_id: int):
    """Background task for performing maintenance scan"""
    try:
        engine = await get_health_engine()
        
        # Generate comprehensive health report
        health_report = await engine.generate_health_report(user_id)
        
        # Log maintenance scan results
        logger.info(
            "Maintenance scan completed",
            user_id=user_id,
            total_memories=health_report.total_memories,
            system_health=health_report.system_health_status.value,
            orphaned_tokens=health_report.orphaned_tokens
        )
        
        # Could trigger alerts or notifications here
        
    except Exception as e:
        logger.error(
            "Maintenance scan failed",
            user_id=user_id,
            error=str(e)
        )
