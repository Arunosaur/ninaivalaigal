"""
SPEC-063: Agentic Core Execution Framework Package
Dynamic intent routing and intelligent agent orchestration
"""

from .agent_core import AgentCore, ExecutionMode, ExecutionResult, get_agent_core
from .execution_context import ExecutionContext
from .intention_router import IntentionRouter

__all__ = [
    "AgentCore",
    "ExecutionMode",
    "ExecutionResult",
    "ExecutionContext",
    "IntentionRouter",
    "get_agent_core",
]
