"""
SPEC-063: Agentic Core Execution Framework
Central routing mechanism for intelligent agent execution and orchestration
"""

import asyncio
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import structlog

from .execution_context import ExecutionContext
from .intention_router import IntentionRouter
from .tools.ai_tools import AIToolchain
from .tools.data_ops import DataOperationsTool
from .tools.memory_access import MemoryAccessTool

logger = structlog.get_logger(__name__)


class ExecutionMode(Enum):
    """Available execution modes for the agentic core."""

    INFERENCE = "inference"
    SEARCH = "search"
    SUMMARIZATION = "summarization"
    ANALYTICS = "analytics"
    GENERATION = "generation"
    MEMORY_ANALYSIS = "memory_analysis"
    GRAPH_REASONING = "graph_reasoning"


class ExecutionResult:
    """Result of an agentic execution."""

    def __init__(
        self,
        execution_id: str,
        mode: ExecutionMode,
        success: bool,
        result: Any = None,
        error: Optional[str] = None,
        execution_time: float = 0.0,
        tools_used: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ):
        self.execution_id = execution_id
        self.mode = mode
        self.success = success
        self.result = result
        self.error = error
        self.execution_time = execution_time
        self.tools_used = tools_used or []
        self.context = context or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "mode": self.mode.value,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "tools_used": self.tools_used,
            "context": self.context,
            "timestamp": self.timestamp,
        }


class AgentCore:
    """
    Central agentic execution engine for dynamic memory-driven reasoning.

    Features:
    - Intent-based routing to specialized execution modes
    - Context-aware tool selection and orchestration
    - Memory injection and AI alignment
    - Execution tracing and observability
    - Resource sandboxing and safety controls
    """

    def __init__(
        self,
        redis_client=None,
        graph_intelligence=None,
        performance_manager=None,
    ):
        self.redis_client = redis_client
        self.graph_intelligence = graph_intelligence
        self.performance_manager = performance_manager

        # Core components
        self.intention_router = IntentionRouter()
        self.ai_toolchain = AIToolchain()
        self.memory_tool = MemoryAccessTool(redis_client)
        self.data_ops_tool = DataOperationsTool()

        # Execution state
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionResult] = []

        # Performance metrics
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "mode_usage": {mode.value: 0 for mode in ExecutionMode},
            "tool_usage": {},
        }

        # Safety controls
        self.max_concurrent_executions = 10
        self.max_execution_time = 300  # 5 minutes
        self.resource_limits = {
            "memory_mb": 512,
            "cpu_percent": 50,
        }

    async def execute(
        self,
        user_prompt: str,
        user_id: str,
        context: Optional[Dict] = None,
        execution_mode: Optional[ExecutionMode] = None,
    ) -> ExecutionResult:
        """
        Execute an intelligent operation based on user prompt and context.

        Args:
            user_prompt: The user's request or query
            user_id: User identifier for context and permissions
            context: Additional context data
            execution_mode: Override automatic intent detection

        Returns:
            ExecutionResult with the outcome of the execution
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        # Check resource limits
        if len(self.active_executions) >= self.max_concurrent_executions:
            return ExecutionResult(
                execution_id=execution_id,
                mode=ExecutionMode.INFERENCE,
                success=False,
                error="Maximum concurrent executions reached",
                execution_time=0.0,
            )

        try:
            # Create execution context
            exec_context = ExecutionContext(
                execution_id=execution_id,
                user_id=user_id,
                user_prompt=user_prompt,
                context_data=context or {},
                redis_client=self.redis_client,
            )

            # Initialize context with memory and permissions
            await exec_context.initialize()

            # Track active execution
            self.active_executions[execution_id] = exec_context

            # Determine execution mode
            if execution_mode is None:
                execution_mode = await self.intention_router.route_intent(
                    user_prompt, exec_context
                )

            logger.info(
                "Starting agentic execution",
                execution_id=execution_id,
                user_id=user_id,
                mode=execution_mode.value,
                prompt_length=len(user_prompt),
            )

            # Execute based on mode
            result = await self._execute_mode(execution_mode, exec_context)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Create successful result
            execution_result = ExecutionResult(
                execution_id=execution_id,
                mode=execution_mode,
                success=True,
                result=result,
                execution_time=execution_time,
                tools_used=exec_context.tools_used,
                context=exec_context.to_dict(),
            )

            # Update metrics
            self._update_metrics(execution_result)

            logger.info(
                "Agentic execution completed",
                execution_id=execution_id,
                mode=execution_mode.value,
                execution_time=execution_time,
                tools_used=len(exec_context.tools_used),
            )

            return execution_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            execution_result = ExecutionResult(
                execution_id=execution_id,
                mode=execution_mode or ExecutionMode.INFERENCE,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

            self._update_metrics(execution_result)

            logger.error(
                "Agentic execution failed",
                execution_id=execution_id,
                error=error_msg,
                execution_time=execution_time,
            )

            return execution_result

        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    async def _execute_mode(
        self,
        mode: ExecutionMode,
        context: ExecutionContext,
    ) -> Any:
        """Execute the specific mode with appropriate tools and logic."""

        if mode == ExecutionMode.INFERENCE:
            return await self._execute_inference(context)

        elif mode == ExecutionMode.SEARCH:
            return await self._execute_search(context)

        elif mode == ExecutionMode.SUMMARIZATION:
            return await self._execute_summarization(context)

        elif mode == ExecutionMode.ANALYTICS:
            return await self._execute_analytics(context)

        elif mode == ExecutionMode.GENERATION:
            return await self._execute_generation(context)

        elif mode == ExecutionMode.MEMORY_ANALYSIS:
            return await self._execute_memory_analysis(context)

        elif mode == ExecutionMode.GRAPH_REASONING:
            return await self._execute_graph_reasoning(context)

        else:
            raise ValueError(f"Unsupported execution mode: {mode}")

    async def _execute_inference(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute AI inference with memory injection."""
        # Retrieve relevant memories
        memories = await self.memory_tool.get_relevant_memories(
            user_id=context.user_id,
            query=context.user_prompt,
            limit=10,
        )

        # Inject memories into AI context
        enhanced_prompt = await self.ai_toolchain.inject_memory_context(
            prompt=context.user_prompt,
            memories=memories,
            user_context=context.context_data,
        )

        # Generate AI response
        response = await self.ai_toolchain.generate_response(
            prompt=enhanced_prompt,
            user_id=context.user_id,
            context=context,
        )

        context.add_tool_usage("memory_retrieval")
        context.add_tool_usage("ai_inference")

        return {
            "response": response,
            "memories_used": len(memories),
            "enhanced_prompt_length": len(enhanced_prompt),
        }

    async def _execute_search(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute intelligent search across memories and data."""
        # Use memory tool for semantic search
        search_results = await self.memory_tool.semantic_search(
            user_id=context.user_id,
            query=context.user_prompt,
            limit=20,
        )

        # Enhance with data operations if needed
        if context.context_data.get("include_analytics", False):
            analytics = await self.data_ops_tool.analyze_search_results(search_results)
            context.add_tool_usage("data_analytics")
        else:
            analytics = None

        context.add_tool_usage("semantic_search")

        return {
            "search_results": search_results,
            "result_count": len(search_results),
            "analytics": analytics,
        }

    async def _execute_summarization(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute intelligent summarization of memories or data."""
        # Get memories to summarize
        memories = await self.memory_tool.get_memories_for_summarization(
            user_id=context.user_id,
            context_filter=context.context_data.get("context_filter"),
            limit=50,
        )

        # Generate summary using AI
        summary = await self.ai_toolchain.generate_summary(
            memories=memories,
            user_prompt=context.user_prompt,
            context=context,
        )

        context.add_tool_usage("memory_retrieval")
        context.add_tool_usage("ai_summarization")

        return {
            "summary": summary,
            "memories_summarized": len(memories),
            "summary_length": len(summary) if summary else 0,
        }

    async def _execute_analytics(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute data analytics and insights generation."""
        # Get data for analysis
        data = await self.memory_tool.get_analytics_data(
            user_id=context.user_id,
            context_filter=context.context_data.get("context_filter"),
        )

        # Perform analytics
        analytics_result = await self.data_ops_tool.perform_analytics(
            data=data,
            analysis_type=context.context_data.get("analysis_type", "general"),
            user_prompt=context.user_prompt,
        )

        context.add_tool_usage("data_analytics")
        context.add_tool_usage("memory_retrieval")

        return analytics_result

    async def _execute_generation(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute content generation with memory context."""
        # Get relevant memories for context
        context_memories = await self.memory_tool.get_relevant_memories(
            user_id=context.user_id,
            query=context.user_prompt,
            limit=15,
        )

        # Generate content
        generated_content = await self.ai_toolchain.generate_content(
            prompt=context.user_prompt,
            context_memories=context_memories,
            generation_type=context.context_data.get("generation_type", "text"),
            context=context,
        )

        context.add_tool_usage("memory_retrieval")
        context.add_tool_usage("ai_generation")

        return {
            "generated_content": generated_content,
            "context_memories_used": len(context_memories),
            "generation_type": context.context_data.get("generation_type", "text"),
        }

    async def _execute_memory_analysis(
        self, context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute memory network analysis and insights."""
        # Perform memory network analysis
        network_analysis = await self.memory_tool.analyze_memory_network(
            user_id=context.user_id,
            context_filter=context.context_data.get("context_filter"),
        )

        # Generate insights using AI
        insights = await self.ai_toolchain.generate_memory_insights(
            network_analysis=network_analysis,
            user_prompt=context.user_prompt,
            context=context,
        )

        context.add_tool_usage("memory_network_analysis")
        context.add_tool_usage("ai_insights")

        return {
            "network_analysis": network_analysis,
            "insights": insights,
            "total_memories": network_analysis.get("total_memories", 0),
        }

    async def _execute_graph_reasoning(
        self, context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute graph-based reasoning using SPEC-061 integration."""
        if not self.graph_intelligence:
            raise RuntimeError("Graph intelligence not available")

        # Use graph intelligence for reasoning
        reasoning_result = await self.graph_intelligence.optimized_explain_context(
            user_id=context.user_id,
            memory_id=context.context_data.get("memory_id"),
            context_id=context.context_data.get("context_id"),
        )

        # Enhance with relevance inference if requested
        if context.context_data.get("include_relevance", True):
            relevance_result = await self.graph_intelligence.optimized_infer_relevance(
                user_id=context.user_id,
                current_memory_id=context.context_data.get("memory_id"),
                candidate_memory_ids=context.context_data.get("candidate_memories", []),
            )
        else:
            relevance_result = None

        context.add_tool_usage("graph_reasoning")
        context.add_tool_usage("relevance_inference")

        return {
            "reasoning_result": reasoning_result,
            "relevance_result": relevance_result,
            "graph_intelligence_used": True,
        }

    def _update_metrics(self, result: ExecutionResult):
        """Update execution metrics."""
        self.metrics["total_executions"] += 1

        if result.success:
            self.metrics["successful_executions"] += 1
        else:
            self.metrics["failed_executions"] += 1

        # Update average execution time
        total_time = (
            self.metrics["avg_execution_time"] * (self.metrics["total_executions"] - 1)
            + result.execution_time
        )
        self.metrics["avg_execution_time"] = (
            total_time / self.metrics["total_executions"]
        )

        # Update mode usage
        self.metrics["mode_usage"][result.mode.value] += 1

        # Update tool usage
        for tool in result.tools_used:
            self.metrics["tool_usage"][tool] = (
                self.metrics["tool_usage"].get(tool, 0) + 1
            )

        # Store in history (keep last 1000)
        self.execution_history.append(result)
        if len(self.execution_history) > 1000:
            self.execution_history.pop(0)

    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get comprehensive execution metrics."""
        return {
            "metrics": self.metrics,
            "active_executions": len(self.active_executions),
            "recent_executions": [
                result.to_dict() for result in self.execution_history[-10:]
            ],
            "resource_limits": self.resource_limits,
            "available_modes": [mode.value for mode in ExecutionMode],
        }

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific execution."""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            return {
                "status": "active",
                "execution_id": execution_id,
                "user_id": context.user_id,
                "start_time": context.start_time,
                "tools_used": context.tools_used,
            }

        # Check history
        for result in reversed(self.execution_history):
            if result.execution_id == execution_id:
                return result.to_dict()

        return None

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        if execution_id in self.active_executions:
            # In a real implementation, this would cancel the async task
            del self.active_executions[execution_id]
            logger.info("Execution cancelled", execution_id=execution_id)
            return True

        return False


# Global agent core instance
_agent_core: Optional[AgentCore] = None


def get_agent_core(
    redis_client=None,
    graph_intelligence=None,
    performance_manager=None,
) -> AgentCore:
    """Get the global agent core instance."""
    global _agent_core

    if _agent_core is None:
        _agent_core = AgentCore(
            redis_client=redis_client,
            graph_intelligence=graph_intelligence,
            performance_manager=performance_manager,
        )

    return _agent_core
