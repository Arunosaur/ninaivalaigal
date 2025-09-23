"""
Agentic API for SPEC-063 Agentic Core Execution Framework
Provides REST endpoints for intelligent agent execution and graph intelligence
"""

import time
from typing import Any, Dict, List, Optional

import structlog
from agent import AgentCore, ExecutionMode, get_agent_core
from fastapi import APIRouter, HTTPException, Request
from graph.intelligence_deployment import (
    GraphIntelligenceDeployment as graph_intelligence,
)
from graph.intelligence_deployment import get_graph_intelligence_deployment
from performance import get_performance_manager
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/agentic", tags=["agentic_intelligence"])


# Request/Response Models
class AgentExecutionRequest(BaseModel):
    user_prompt: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    execution_mode: Optional[str] = None
    temperature: Optional[float] = 0.7


class AgentExecutionResponse(BaseModel):
    execution_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    mode: str
    tools_used: List[str]
    context_summary: Dict[str, Any]


class GraphIntelligenceDeployRequest(BaseModel):
    redis_config: Optional[Dict[str, Any]] = None
    graph_db_config: Optional[Dict[str, Any]] = None
    force_redeploy: bool = False


class GraphIntelligenceResponse(BaseModel):
    status: str
    deployment_time: Optional[float] = None
    components: List[str]
    capabilities: List[str]
    health_status: str


class IntentAnalysisRequest(BaseModel):
    user_prompt: str
    context: Optional[Dict[str, Any]] = None


class IntentAnalysisResponse(BaseModel):
    detected_intent: str
    confidence: float
    explanation: Dict[str, Any]
    alternative_modes: List[str]


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(request: AgentExecutionRequest) -> AgentExecutionResponse:
    """
    Execute an intelligent agent operation based on user prompt and context.

    This is the main entry point for agentic execution, providing:
    - Intent-based routing to specialized execution modes
    - Context-aware tool selection and orchestration
    - Memory injection and AI alignment
    - Execution tracing and observability
    """
    try:
        # Get agent core instance
        performance_manager = get_performance_manager()
        redis_client = (
            performance_manager.redis_client
            if performance_manager.initialized
            else None
        )
        graph_intelligence = (
            performance_manager.graph_intelligence
            if performance_manager.initialized
            else None
        )

        agent_core = get_agent_core(
            redis_client=redis_client,
            graph_intelligence=graph_intelligence,
            performance_manager=performance_manager,
        )

        # Parse execution mode if provided
        execution_mode = None
        if request.execution_mode:
            try:
                execution_mode = ExecutionMode(request.execution_mode.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid execution mode: {request.execution_mode}. "
                    f"Valid modes: {[mode.value for mode in ExecutionMode]}",
                )

        # Execute the agent
        result = await agent_core.execute(
            user_prompt=request.user_prompt,
            user_id=request.user_id,
            context=request.context,
            execution_mode=execution_mode,
        )

        # Convert to response model
        return AgentExecutionResponse(
            execution_id=result.execution_id,
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            mode=result.mode.value,
            tools_used=result.tools_used,
            context_summary=result.context,
        )

    except Exception as e:
        logger.error("Agent execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/analyze-intent", response_model=IntentAnalysisResponse)
async def analyze_intent(request: IntentAnalysisRequest) -> IntentAnalysisResponse:
    """
    Analyze user intent and provide routing recommendations.

    Useful for understanding how the system would route a request
    without actually executing it.
    """
    try:
        # Get agent core for intention router
        agent_core = get_agent_core()

        # Create mock execution context for analysis
        import uuid

        from .agent.execution_context import ExecutionContext

        mock_context = ExecutionContext(
            execution_id=str(uuid.uuid4()),
            user_id=(
                request.context.get("user_id", "analysis_user")
                if request.context
                else "analysis_user"
            ),
            user_prompt=request.user_prompt,
            context_data=request.context or {},
        )

        # Analyze intent
        detected_mode = await agent_core.intention_router.route_intent(
            request.user_prompt, mock_context
        )

        # Get detailed explanation
        explanation = agent_core.intention_router.get_routing_explanation(
            request.user_prompt, detected_mode, mock_context
        )

        # Calculate confidence based on score distribution
        mode_scores = explanation.get("mode_scores", {})
        if mode_scores:
            max_score = max(mode_scores.values())
            total_score = sum(mode_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.0
        else:
            confidence = 0.5

        # Get alternative modes (top 3 excluding selected)
        sorted_modes = sorted(mode_scores.items(), key=lambda x: x[1], reverse=True)
        alternative_modes = [
            mode for mode, score in sorted_modes[1:4] if mode != detected_mode.value
        ]

        return IntentAnalysisResponse(
            detected_intent=detected_mode.value,
            confidence=confidence,
            explanation=explanation,
            alternative_modes=alternative_modes,
        )

    except Exception as e:
        logger.error("Intent analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")


@router.post("/deploy-graph-intelligence", response_model=GraphIntelligenceResponse)
async def deploy_graph_intelligence_endpoint(
    request: GraphIntelligenceDeployRequest,
) -> GraphIntelligenceResponse:
    """
    Deploy the complete graph intelligence stack (SPEC-060/061 integration).

    This endpoint deploys:
    - SPEC-061: Property Graph Intelligence Framework
    - SPEC-062: GraphOps Stack Integration
    - Performance optimization wrappers
    - Real-time monitoring integration
    """
    try:
        # Get Redis client from performance manager
        performance_manager = get_performance_manager()
        redis_client = (
            performance_manager.redis_client
            if performance_manager.initialized
            else None
        )

        # Check if already deployed and not forcing redeploy
        deployment = get_graph_intelligence_deployment()
        if deployment.deployed and not request.force_redeploy:
            status = await deployment.get_deployment_status()
            capabilities = await deployment.get_intelligence_capabilities()

            return GraphIntelligenceResponse(
                status="already_deployed",
                components=status["deployment_metrics"]["components_deployed"],
                capabilities=capabilities,
                health_status="operational",
            )

        # Deploy the graph intelligence stack
        deployment_result = await deploy_graph_intelligence(
            redis_client=redis_client,
            graph_db_config=request.graph_db_config,
        )

        # Get capabilities
        capabilities = await deployment.get_intelligence_capabilities()

        return GraphIntelligenceResponse(
            status=deployment_result["status"],
            deployment_time=deployment_result.get("deployment_time"),
            components=deployment_result["components"],
            capabilities=capabilities,
            health_status=deployment_result["health_status"],
        )

    except Exception as e:
        logger.error("Graph intelligence deployment failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Graph intelligence deployment failed: {str(e)}"
        )


@router.get("/graph-intelligence/status")
async def get_graph_intelligence_status():
    """Get the current status of graph intelligence deployment."""
    try:
        deployment = get_graph_intelligence_deployment()
        status = await deployment.get_deployment_status()
        capabilities = await deployment.get_intelligence_capabilities()

        return {
            "status": "success",
            "data": {
                "deployment_status": status,
                "capabilities": capabilities,
                "deployed": deployment.deployed,
            },
        }

    except Exception as e:
        logger.error("Failed to get graph intelligence status", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph intelligence status: {str(e)}"
        )


@router.get("/execution/metrics")
async def get_execution_metrics():
    """Get comprehensive execution metrics from the agent core."""
    try:
        agent_core = get_agent_core()
        metrics = await agent_core.get_execution_metrics()

        return {
            "status": "success",
            "data": metrics,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error("Failed to get execution metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get execution metrics: {str(e)}"
        )


@router.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get the status of a specific execution."""
    try:
        agent_core = get_agent_core()
        status = await agent_core.get_execution_status(execution_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Execution not found")

        return {
            "status": "success",
            "data": status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get execution status", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get execution status: {str(e)}"
        )


@router.post("/execution/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel an active execution."""
    try:
        agent_core = get_agent_core()
        cancelled = await agent_core.cancel_execution(execution_id)

        if not cancelled:
            raise HTTPException(
                status_code=404, detail="Execution not found or already completed"
            )

        return {
            "status": "success",
            "message": "Execution cancelled successfully",
            "execution_id": execution_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel execution", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel execution: {str(e)}"
        )


@router.get("/modes")
async def get_available_modes():
    """Get all available execution modes and their descriptions."""
    mode_descriptions = {
        ExecutionMode.INFERENCE: "AI inference with memory context injection",
        ExecutionMode.SEARCH: "Intelligent search across memories and data",
        ExecutionMode.SUMMARIZATION: "Intelligent summarization of memories or data",
        ExecutionMode.ANALYTICS: "Data analytics and insights generation",
        ExecutionMode.GENERATION: "Content generation with memory context",
        ExecutionMode.MEMORY_ANALYSIS: "Memory network analysis and insights",
        ExecutionMode.GRAPH_REASONING: "Graph-based reasoning using SPEC-061 integration",
    }

    return {
        "status": "success",
        "data": {
            "available_modes": [
                {
                    "mode": mode.value,
                    "description": mode_descriptions[mode],
                }
                for mode in ExecutionMode
            ],
            "default_mode": "inference",
            "total_modes": len(ExecutionMode),
        },
    }


@router.get("/health")
async def agentic_health_check():
    """Comprehensive health check for agentic systems."""
    try:
        health_status = {
            "agentic_core": "unknown",
            "graph_intelligence": "unknown",
            "performance_integration": "unknown",
            "redis_connection": "unknown",
        }

        issues = []

        # Check agent core
        try:
            agent_core = get_agent_core()
            health_status["agentic_core"] = "healthy"
        except Exception as e:
            health_status["agentic_core"] = "unhealthy"
            issues.append(f"Agent core: {str(e)}")

        # Check graph intelligence deployment
        try:
            deployment = get_graph_intelligence_deployment()
            if deployment.deployed:
                health_status["graph_intelligence"] = "healthy"
            else:
                health_status["graph_intelligence"] = "not_deployed"
        except Exception as e:
            health_status["graph_intelligence"] = "unhealthy"
            issues.append(f"Graph intelligence: {str(e)}")

        # Check performance integration
        try:
            performance_manager = get_performance_manager()
            if performance_manager.initialized:
                health_status["performance_integration"] = "healthy"

                # Check Redis connection
                if performance_manager.redis_client:
                    await performance_manager.redis_client.redis.ping()
                    health_status["redis_connection"] = "healthy"
                else:
                    health_status["redis_connection"] = "not_configured"
            else:
                health_status["performance_integration"] = "not_initialized"
        except Exception as e:
            health_status["performance_integration"] = "unhealthy"
            issues.append(f"Performance integration: {str(e)}")

        # Determine overall status
        if not issues:
            overall_status = "healthy"
        elif len(issues) <= 1:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "components": health_status,
            "issues": issues,
            "timestamp": time.time(),
            "capabilities": {
                "agent_execution": health_status["agentic_core"] == "healthy",
                "graph_reasoning": health_status["graph_intelligence"] == "healthy",
                "performance_optimization": health_status["performance_integration"]
                == "healthy",
                "redis_caching": health_status["redis_connection"] == "healthy",
            },
        }

    except Exception as e:
        logger.error("Agentic health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }
