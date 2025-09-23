"""
SPEC-036: Memory Injection API Endpoints
REST API for smart memory injection with context rules and AI integration
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user
from database.operations import DatabaseOperations, get_db
from memory_injection import (
    InjectionCandidate,
    InjectionContext,
    InjectionPriority,
    InjectionRule,
    InjectionStrategy,
    InjectionTrigger,
    MemoryInjectionEngine,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory/injection", tags=["memory_injection"])


# Request/Response Models
class InjectionAnalysisRequest(BaseModel):
    session_id: Optional[str] = None
    current_activity: Optional[str] = None
    location_context: Dict[str, Any] = {}
    temporal_context: Dict[str, Any] = {}
    semantic_context: Dict[str, Any] = {}
    user_state: Dict[str, Any] = {}
    environment: Dict[str, Any] = {}
    max_candidates: int = 10


class InjectionExecutionRequest(BaseModel):
    context: InjectionAnalysisRequest
    strategy: InjectionStrategy = InjectionStrategy.CONTEXTUAL
    max_injections: int = 5


class CreateRuleRequest(BaseModel):
    name: str
    description: str
    trigger: InjectionTrigger
    strategy: InjectionStrategy
    priority: InjectionPriority
    conditions: Dict[str, Any]
    actions: Dict[str, Any]


class InjectionAnalysisResponse(BaseModel):
    candidates: List[InjectionCandidate]
    total_candidates: int
    analysis_time_ms: float
    rules_evaluated: int
    context_summary: Dict[str, Any]


class InjectionExecutionResponse(BaseModel):
    injected_memories: List[Dict[str, Any]]
    execution_time_ms: float
    strategy_used: str
    success_count: int
    context_snapshot: Dict[str, Any]


class InjectionAnalyticsResponse(BaseModel):
    total_injections: int
    successful_injections: int
    success_rate: float
    average_relevance_score: float
    rule_performance: List[Dict[str, Any]]
    user_feedback: Dict[str, Any]
    top_triggers: List[Dict[str, Any]]
    analysis_period_days: int


# Initialize injection engine
def get_injection_engine(db: DatabaseOperations = Depends(get_db)) -> MemoryInjectionEngine:
    """Get memory injection engine instance."""
    # In production, this would include Redis, feedback system, and suggestions system
    return MemoryInjectionEngine(db_manager=db, redis_client=None, feedback_system=None, suggestions_system=None)


@router.post("/analyze", response_model=InjectionAnalysisResponse)
async def analyze_injection_opportunities(
    request: InjectionAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> InjectionAnalysisResponse:
    """
    Analyze current context and identify memory injection opportunities.
    """
    try:
        import time
        start_time = time.time()
        
        user_id = current_user["user_id"]
        
        context = InjectionContext(
            user_id=user_id,
            session_id=request.session_id,
            current_activity=request.current_activity,
            location_context=request.location_context,
            temporal_context=request.temporal_context,
            semantic_context=request.semantic_context,
            user_state=request.user_state,
            environment=request.environment
        )
        
        candidates = await injection_engine.analyze_injection_opportunities(
            context=context,
            max_candidates=request.max_candidates
        )
        
        analysis_time = (time.time() - start_time) * 1000
        
        # Get active rules count for response
        active_rules = await injection_engine._get_active_rules(user_id)
        
        return InjectionAnalysisResponse(
            candidates=candidates,
            total_candidates=len(candidates),
            analysis_time_ms=analysis_time,
            rules_evaluated=len(active_rules),
            context_summary={
                "activity": request.current_activity,
                "session_id": request.session_id,
                "context_keys": list(request.semantic_context.keys())
            }
        )
        
    except Exception as e:
        logger.error("Failed to analyze injection opportunities", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to analyze injection opportunities")


@router.post("/execute", response_model=InjectionExecutionResponse)
async def execute_memory_injection(
    request: InjectionExecutionRequest,
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> InjectionExecutionResponse:
    """
    Execute memory injection based on context and strategy.
    """
    try:
        import time
        start_time = time.time()
        
        user_id = current_user["user_id"]
        
        context = InjectionContext(
            user_id=user_id,
            session_id=request.context.session_id,
            current_activity=request.context.current_activity,
            location_context=request.context.location_context,
            temporal_context=request.context.temporal_context,
            semantic_context=request.context.semantic_context,
            user_state=request.context.user_state,
            environment=request.context.environment
        )
        
        injected_memories = await injection_engine.inject_memories(
            context=context,
            strategy=request.strategy,
            max_injections=request.max_injections
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return InjectionExecutionResponse(
            injected_memories=injected_memories,
            execution_time_ms=execution_time,
            strategy_used=request.strategy.value,
            success_count=len(injected_memories),
            context_snapshot=context.dict()
        )
        
    except Exception as e:
        logger.error("Failed to execute memory injection", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to execute memory injection")


@router.post("/rules", response_model=InjectionRule)
async def create_injection_rule(
    request: CreateRuleRequest,
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> InjectionRule:
    """
    Create a new memory injection rule.
    """
    try:
        user_id = current_user["user_id"]
        
        rule_data = {
            "name": request.name,
            "description": request.description,
            "trigger": request.trigger.value,
            "strategy": request.strategy.value,
            "priority": request.priority.value,
            "conditions": request.conditions,
            "actions": request.actions
        }
        
        rule = await injection_engine.create_injection_rule(
            user_id=user_id,
            rule_data=rule_data
        )
        
        return rule
        
    except Exception as e:
        logger.error("Failed to create injection rule", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to create injection rule")


@router.get("/rules")
async def get_injection_rules(
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> List[InjectionRule]:
    """
    Get user's injection rules.
    """
    try:
        user_id = current_user["user_id"]
        
        rules = await injection_engine._get_active_rules(user_id)
        
        return rules
        
    except Exception as e:
        logger.error("Failed to get injection rules", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to retrieve injection rules")


@router.get("/analytics", response_model=InjectionAnalyticsResponse)
async def get_injection_analytics(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> InjectionAnalyticsResponse:
    """
    Get analytics about memory injection performance.
    """
    try:
        user_id = current_user["user_id"]
        
        analytics = await injection_engine.get_injection_analytics(
            user_id=user_id,
            days_back=days_back
        )
        
        return InjectionAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error("Failed to get injection analytics", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to retrieve injection analytics")


@router.post("/context/{context_type}/inject")
async def inject_for_context_type(
    context_type: str,
    context_data: Dict[str, Any],
    max_injections: int = Query(3, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
    injection_engine: MemoryInjectionEngine = Depends(get_injection_engine)
) -> InjectionExecutionResponse:
    """
    Execute context-specific memory injection.
    """
    try:
        import time
        start_time = time.time()
        
        user_id = current_user["user_id"]
        
        # Create context based on type
        context = InjectionContext(
            user_id=user_id,
            current_activity=context_type,
            semantic_context=context_data,
            temporal_context={"injection_time": datetime.utcnow().isoformat()}
        )
        
        # Use contextual strategy for context-specific injection
        injected_memories = await injection_engine.inject_memories(
            context=context,
            strategy=InjectionStrategy.CONTEXTUAL,
            max_injections=max_injections
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return InjectionExecutionResponse(
            injected_memories=injected_memories,
            execution_time_ms=execution_time,
            strategy_used="contextual",
            success_count=len(injected_memories),
            context_snapshot=context.dict()
        )
        
    except Exception as e:
        logger.error("Failed to inject for context type", context_type=context_type, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute context-specific injection")


@router.get("/triggers")
async def get_available_triggers(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about available injection triggers.
    """
    try:
        triggers = {
            InjectionTrigger.CONTEXT_MATCH: {
                "name": "Context Match",
                "description": "Triggers when current context matches specified patterns",
                "use_case": "Contextual memory injection based on user activity"
            },
            InjectionTrigger.KEYWORD_PRESENCE: {
                "name": "Keyword Presence",
                "description": "Triggers when specific keywords are detected",
                "use_case": "Content-based memory injection"
            },
            InjectionTrigger.SEMANTIC_SIMILARITY: {
                "name": "Semantic Similarity",
                "description": "Triggers based on semantic similarity to current content",
                "use_case": "AI-powered contextual suggestions"
            },
            InjectionTrigger.USER_PATTERN: {
                "name": "User Pattern",
                "description": "Triggers based on learned user behavior patterns",
                "use_case": "Personalized memory injection"
            },
            InjectionTrigger.TIME_BASED: {
                "name": "Time Based",
                "description": "Triggers at specific times or intervals",
                "use_case": "Scheduled memory reminders"
            },
            InjectionTrigger.LOCATION_BASED: {
                "name": "Location Based",
                "description": "Triggers based on user location context",
                "use_case": "Location-aware memory suggestions"
            },
            InjectionTrigger.ACTIVITY_BASED: {
                "name": "Activity Based",
                "description": "Triggers based on current user activity",
                "use_case": "Activity-specific memory injection"
            }
        }
        
        strategies = {
            InjectionStrategy.IMMEDIATE: {
                "name": "Immediate",
                "description": "Inject memories immediately when triggered"
            },
            InjectionStrategy.CONTEXTUAL: {
                "name": "Contextual",
                "description": "Inject memories when context is optimal"
            },
            InjectionStrategy.PROACTIVE: {
                "name": "Proactive",
                "description": "Inject memories before user needs them"
            },
            InjectionStrategy.REACTIVE: {
                "name": "Reactive",
                "description": "Inject memories in response to user actions"
            },
            InjectionStrategy.BACKGROUND: {
                "name": "Background",
                "description": "Inject memories in background without interruption"
            }
        }
        
        return {
            "triggers": triggers,
            "strategies": strategies,
            "priorities": [p.value for p in InjectionPriority]
        }
        
    except Exception as e:
        logger.error("Failed to get available triggers", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve trigger information")
