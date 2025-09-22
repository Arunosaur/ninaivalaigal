"""
Execution Context for SPEC-063 Agentic Core
Captures contextual data for agent execution with auditability and replay capability
"""

import time
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class ExecutionContext:
    """
    Serializable execution context for agentic operations.

    Captures all contextual data needed for agent execution including:
    - User information and permissions
    - Memory context and history
    - Environment and configuration
    - Execution state and tool usage
    - Audit trail for tracing and replay
    """

    def __init__(
        self,
        execution_id: str,
        user_id: str,
        user_prompt: str,
        context_data: Optional[Dict] = None,
        redis_client=None,
    ):
        # Core identification
        self.execution_id = execution_id
        self.user_id = user_id
        self.user_prompt = user_prompt

        # Context data
        self.context_data = context_data or {}
        self.redis_client = redis_client

        # Execution state
        self.start_time = time.time()
        self.tools_used: List[str] = []
        self.memory_context: Dict[str, Any] = {}
        self.permissions: Dict[str, bool] = {}
        self.environment: Dict[str, Any] = {}

        # Audit trail
        self.audit_trail: List[Dict[str, Any]] = []
        self.execution_steps: List[Dict[str, Any]] = []

        # Performance tracking
        self.performance_metrics = {
            "memory_retrievals": 0,
            "ai_calls": 0,
            "database_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Safety and resource tracking
        self.resource_usage = {
            "memory_mb": 0,
            "cpu_time": 0.0,
            "network_calls": 0,
        }

        self.initialized = False

    async def initialize(self):
        """Initialize the execution context with user data and permissions."""
        if self.initialized:
            return

        try:
            # Load user permissions
            await self._load_user_permissions()

            # Load memory context
            await self._load_memory_context()

            # Set up environment
            await self._setup_environment()

            # Record initialization
            self.add_audit_entry(
                "context_initialized",
                {
                    "user_id": self.user_id,
                    "prompt_length": len(self.user_prompt),
                    "context_keys": list(self.context_data.keys()),
                },
            )

            self.initialized = True

            logger.info(
                "Execution context initialized",
                execution_id=self.execution_id,
                user_id=self.user_id,
                permissions_loaded=len(self.permissions),
                memory_context_loaded=len(self.memory_context),
            )

        except Exception as e:
            logger.error("Failed to initialize execution context", error=str(e))
            raise

    async def _load_user_permissions(self):
        """Load user permissions and access controls."""
        # In a real implementation, this would query the RBAC system
        # For now, we'll set default permissions

        self.permissions = {
            "can_access_memories": True,
            "can_use_ai": True,
            "can_perform_analytics": True,
            "can_generate_content": True,
            "can_access_graph": True,
            "can_modify_data": False,  # Default to read-only
        }

        # Check for admin or elevated permissions
        if self.context_data.get("admin_mode", False):
            self.permissions["can_modify_data"] = True
            self.permissions["can_access_system"] = True

        self.add_audit_entry(
            "permissions_loaded",
            {
                "permissions": list(self.permissions.keys()),
                "admin_mode": self.context_data.get("admin_mode", False),
            },
        )

    async def _load_memory_context(self):
        """Load relevant memory context for the execution."""
        if not self.redis_client:
            logger.warning("No Redis client available for memory context")
            return

        try:
            # Load recent memory context
            recent_memories_key = f"recent_memories:{self.user_id}"
            recent_memories = await self.redis_client.lrange(recent_memories_key, 0, 10)

            # Load user preferences
            preferences_key = f"user_preferences:{self.user_id}"
            preferences = await self.redis_client.hgetall(preferences_key)

            # Load session context if available
            session_key = f"session_context:{self.user_id}"
            session_context = await self.redis_client.hgetall(session_key)

            self.memory_context = {
                "recent_memories": recent_memories or [],
                "user_preferences": preferences or {},
                "session_context": session_context or {},
                "context_loaded_at": time.time(),
            }

            self.performance_metrics["memory_retrievals"] += 3  # 3 Redis calls

            self.add_audit_entry(
                "memory_context_loaded",
                {
                    "recent_memories_count": len(recent_memories or []),
                    "preferences_count": len(preferences or {}),
                    "session_context_keys": list((session_context or {}).keys()),
                },
            )

        except Exception as e:
            logger.warning("Failed to load memory context", error=str(e))
            self.memory_context = {}

    async def _setup_environment(self):
        """Set up the execution environment."""
        self.environment = {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "timestamp": self.start_time,
            "redis_available": self.redis_client is not None,
            "context_data_keys": list(self.context_data.keys()),
            "permissions_count": len(self.permissions),
        }

        # Add environment-specific settings
        if self.context_data.get("debug_mode", False):
            self.environment["debug_mode"] = True
            self.environment["verbose_logging"] = True

        if self.context_data.get("test_mode", False):
            self.environment["test_mode"] = True
            self.environment["mock_external_calls"] = True

    def add_tool_usage(self, tool_name: str):
        """Record tool usage for tracking and metrics."""
        self.tools_used.append(tool_name)

        self.add_audit_entry(
            "tool_used",
            {
                "tool_name": tool_name,
                "usage_count": self.tools_used.count(tool_name),
                "total_tools_used": len(self.tools_used),
            },
        )

        logger.debug(
            "Tool usage recorded",
            execution_id=self.execution_id,
            tool_name=tool_name,
            total_tools=len(self.tools_used),
        )

    def add_audit_entry(self, action: str, details: Dict[str, Any]):
        """Add an entry to the audit trail."""
        audit_entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details,
            "execution_id": self.execution_id,
            "user_id": self.user_id,
        }

        self.audit_trail.append(audit_entry)

        # Keep audit trail manageable (last 100 entries)
        if len(self.audit_trail) > 100:
            self.audit_trail.pop(0)

    def add_execution_step(
        self,
        step_name: str,
        step_data: Dict[str, Any],
        duration: Optional[float] = None,
    ):
        """Record an execution step for replay capability."""
        step = {
            "timestamp": time.time(),
            "step_name": step_name,
            "step_data": step_data,
            "duration": duration,
            "tools_used_count": len(self.tools_used),
        }

        self.execution_steps.append(step)

        self.add_audit_entry(
            "execution_step",
            {
                "step_name": step_name,
                "step_number": len(self.execution_steps),
                "duration": duration,
            },
        )

    def update_performance_metric(self, metric_name: str, increment: int = 1):
        """Update a performance metric."""
        if metric_name in self.performance_metrics:
            self.performance_metrics[metric_name] += increment
        else:
            self.performance_metrics[metric_name] = increment

        logger.debug(
            "Performance metric updated",
            execution_id=self.execution_id,
            metric=metric_name,
            value=self.performance_metrics[metric_name],
        )

    def update_resource_usage(self, resource: str, value: float):
        """Update resource usage tracking."""
        if resource in self.resource_usage:
            self.resource_usage[resource] += value
        else:
            self.resource_usage[resource] = value

    def check_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        has_permission = self.permissions.get(permission, False)

        self.add_audit_entry(
            "permission_check",
            {
                "permission": permission,
                "granted": has_permission,
            },
        )

        return has_permission

    def get_memory_context(self, key: str, default=None):
        """Get a value from the memory context."""
        return self.memory_context.get(key, default)

    def get_user_preference(self, preference: str, default=None):
        """Get a user preference from the memory context."""
        preferences = self.memory_context.get("user_preferences", {})
        return preferences.get(preference, default)

    def get_session_context(self, key: str, default=None):
        """Get a value from the session context."""
        session_context = self.memory_context.get("session_context", {})
        return session_context.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the execution context to a dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "user_prompt": self.user_prompt,
            "context_data": self.context_data,
            "start_time": self.start_time,
            "tools_used": self.tools_used,
            "memory_context": self.memory_context,
            "permissions": self.permissions,
            "environment": self.environment,
            "audit_trail": self.audit_trail[-10:],  # Last 10 entries
            "execution_steps": self.execution_steps,
            "performance_metrics": self.performance_metrics,
            "resource_usage": self.resource_usage,
            "initialized": self.initialized,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], redis_client=None) -> "ExecutionContext":
        """Create an ExecutionContext from a dictionary (for replay)."""
        context = cls(
            execution_id=data["execution_id"],
            user_id=data["user_id"],
            user_prompt=data["user_prompt"],
            context_data=data.get("context_data", {}),
            redis_client=redis_client,
        )

        # Restore state
        context.start_time = data.get("start_time", time.time())
        context.tools_used = data.get("tools_used", [])
        context.memory_context = data.get("memory_context", {})
        context.permissions = data.get("permissions", {})
        context.environment = data.get("environment", {})
        context.audit_trail = data.get("audit_trail", [])
        context.execution_steps = data.get("execution_steps", [])
        context.performance_metrics = data.get("performance_metrics", {})
        context.resource_usage = data.get("resource_usage", {})
        context.initialized = data.get("initialized", False)

        return context

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution context."""
        execution_time = time.time() - self.start_time

        return {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "execution_time": execution_time,
            "tools_used_count": len(self.tools_used),
            "unique_tools": len(set(self.tools_used)),
            "audit_entries": len(self.audit_trail),
            "execution_steps": len(self.execution_steps),
            "performance_metrics": self.performance_metrics,
            "resource_usage": self.resource_usage,
            "permissions_granted": sum(
                1 for granted in self.permissions.values() if granted
            ),
            "memory_context_loaded": bool(self.memory_context),
        }
