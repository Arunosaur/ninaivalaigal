"""
SPEC-020: Memory Provider Failover Manager
Intelligent failover logic and fallback routing for memory providers
"""

import asyncio
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .health_monitor import AlertLevel, HealthStatus, ProviderHealthMonitor
from .interfaces import MemoryNotFoundError, MemoryProvider, MemoryProviderError
from .provider_registry import MemoryProviderRegistry, ProviderStatus

logger = logging.getLogger(__name__)


class FailoverStrategy(Enum):
    """Failover strategy options"""

    PRIORITY_BASED = "priority_based"  # Use provider priority order
    HEALTH_BASED = "health_based"  # Use healthiest provider first
    ROUND_ROBIN = "round_robin"  # Distribute load evenly
    PERFORMANCE_BASED = "performance_based"  # Use fastest provider
    HYBRID = "hybrid"  # Combine multiple strategies


class OperationType(Enum):
    """Memory operation types for routing decisions"""

    REMEMBER = "remember"
    RECALL = "recall"
    DELETE = "delete"
    LIST = "list"
    HEALTH_CHECK = "health_check"


@dataclass
class FailoverRule:
    """Failover rule configuration"""

    operation_type: OperationType
    strategy: FailoverStrategy
    max_retries: int = 3
    retry_delay_ms: int = 100
    timeout_ms: int = 5000
    fallback_providers: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Result of a memory operation with metadata"""

    success: bool
    result: Any = None
    provider_name: Optional[str] = None
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    attempts: int = 1
    fallback_used: bool = False


@dataclass
class ProviderMetrics:
    """Performance metrics for a provider"""

    provider_name: str
    avg_response_time_ms: float
    success_rate: float
    last_used: datetime
    total_operations: int
    recent_errors: int
    weight: float = 1.0


class MemoryProviderFailoverManager:
    """
    SPEC-020: Memory Provider Failover Manager

    Manages intelligent failover and routing decisions for memory operations
    with support for multiple strategies, health-based routing, and performance optimization.
    """

    def __init__(
        self, registry: MemoryProviderRegistry, health_monitor: ProviderHealthMonitor
    ):
        self.registry = registry
        self.health_monitor = health_monitor

        # Failover configuration
        self.failover_rules: Dict[OperationType, FailoverRule] = {}
        self.provider_metrics: Dict[str, ProviderMetrics] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Round-robin state
        self._round_robin_index = 0
        self._last_provider_selection = {}

        # Performance tracking
        self._operation_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000

        # Initialize default rules
        self._initialize_default_rules()

    async def execute_operation(
        self, operation_type: OperationType, operation_func: Callable, *args, **kwargs
    ) -> OperationResult:
        """
        Execute a memory operation with intelligent failover

        Args:
            operation_type: Type of operation being performed
            operation_func: Function to call on the provider
            *args, **kwargs: Arguments to pass to the operation function

        Returns:
            OperationResult with success status and metadata
        """
        start_time = datetime.now(timezone.utc)
        rule = self.failover_rules.get(operation_type, self._get_default_rule())

        # Get ordered list of providers to try
        providers_to_try = await self._get_provider_order(operation_type, rule)

        if not providers_to_try:
            return OperationResult(
                success=False,
                error_message="No available providers for operation",
                attempts=0,
            )

        last_error = None
        total_attempts = 0

        for attempt, provider_name in enumerate(providers_to_try):
            if attempt >= rule.max_retries:
                break

            # Check circuit breaker
            if self._is_circuit_breaker_open(provider_name, operation_type):
                logger.debug(f"Circuit breaker open for {provider_name}, skipping")
                continue

            try:
                provider = await self.registry.get_provider(provider_name)
                if not provider:
                    continue

                # Execute operation with timeout
                operation_start = datetime.now(timezone.utc)

                try:
                    result = await asyncio.wait_for(
                        operation_func(provider, *args, **kwargs),
                        timeout=rule.timeout_ms / 1000.0,
                    )

                    response_time = (
                        datetime.now(timezone.utc) - operation_start
                    ).total_seconds() * 1000
                    total_attempts += 1

                    # Record successful operation
                    await self._record_operation_success(
                        provider_name, operation_type, response_time
                    )

                    # Update circuit breaker
                    self._record_circuit_breaker_success(provider_name, operation_type)

                    # Record in history
                    self._add_to_history(
                        {
                            "timestamp": start_time.isoformat(),
                            "operation_type": operation_type.value,
                            "provider_name": provider_name,
                            "success": True,
                            "response_time_ms": response_time,
                            "attempts": total_attempts,
                            "fallback_used": attempt > 0,
                        }
                    )

                    return OperationResult(
                        success=True,
                        result=result,
                        provider_name=provider_name,
                        response_time_ms=response_time,
                        attempts=total_attempts,
                        fallback_used=attempt > 0,
                    )

                except asyncio.TimeoutError:
                    error_msg = f"Operation timeout after {rule.timeout_ms}ms"
                    last_error = error_msg
                    await self._record_operation_failure(
                        provider_name, operation_type, error_msg
                    )
                    self._record_circuit_breaker_failure(provider_name, operation_type)

                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    await self._record_operation_failure(
                        provider_name, operation_type, error_msg
                    )
                    self._record_circuit_breaker_failure(provider_name, operation_type)

                    # Don't retry on certain errors
                    if isinstance(e, MemoryNotFoundError):
                        break

                total_attempts += 1

                # Wait before retry
                if attempt < len(providers_to_try) - 1:
                    await asyncio.sleep(rule.retry_delay_ms / 1000.0)

            except Exception as e:
                logger.error(f"Unexpected error with provider {provider_name}: {e}")
                last_error = str(e)
                continue

        # All providers failed
        total_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Record failure in history
        self._add_to_history(
            {
                "timestamp": start_time.isoformat(),
                "operation_type": operation_type.value,
                "provider_name": None,
                "success": False,
                "response_time_ms": total_time,
                "attempts": total_attempts,
                "error_message": last_error,
            }
        )

        return OperationResult(
            success=False,
            error_message=f"All providers failed. Last error: {last_error}",
            attempts=total_attempts,
        )

    async def configure_failover_rule(
        self, operation_type: OperationType, rule: FailoverRule
    ) -> None:
        """Configure failover rule for an operation type"""
        self.failover_rules[operation_type] = rule
        logger.info(
            f"Configured failover rule for {operation_type.value}: {rule.strategy.value}"
        )

    async def get_provider_recommendations(
        self, operation_type: OperationType, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recommended providers for an operation type"""
        try:
            rule = self.failover_rules.get(operation_type, self._get_default_rule())
            providers = await self._get_provider_order(operation_type, rule)

            recommendations = []
            for provider_name in providers[:limit]:
                provider_info = await self.registry.list_providers()
                provider_data = next(
                    (p for p in provider_info if p["name"] == provider_name), None
                )

                if provider_data:
                    health = await self.health_monitor.get_provider_health(
                        provider_name
                    )
                    metrics = self.provider_metrics.get(provider_name)

                    recommendation = {
                        "provider_name": provider_name,
                        "status": provider_data["status"],
                        "health_status": health.status.value if health else "unknown",
                        "avg_response_time_ms": (
                            metrics.avg_response_time_ms if metrics else 0
                        ),
                        "success_rate": metrics.success_rate if metrics else 0,
                        "recommendation_score": self._calculate_recommendation_score(
                            provider_name, operation_type
                        ),
                    }
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get provider recommendations: {e}")
            return []

    async def get_failover_statistics(self) -> Dict[str, Any]:
        """Get failover and routing statistics"""
        try:
            # Calculate overall statistics
            total_operations = len(self._operation_history)
            successful_operations = sum(
                1 for op in self._operation_history if op["success"]
            )

            success_rate = (
                (successful_operations / total_operations * 100)
                if total_operations > 0
                else 0
            )

            # Calculate average response times by operation type
            operation_stats = {}
            for op_type in OperationType:
                type_ops = [
                    op
                    for op in self._operation_history
                    if op["operation_type"] == op_type.value
                ]
                if type_ops:
                    successful_type_ops = [op for op in type_ops if op["success"]]
                    operation_stats[op_type.value] = {
                        "total_operations": len(type_ops),
                        "successful_operations": len(successful_type_ops),
                        "success_rate": len(successful_type_ops) / len(type_ops) * 100,
                        "avg_response_time_ms": (
                            statistics.mean(
                                [op["response_time_ms"] for op in successful_type_ops]
                            )
                            if successful_type_ops
                            else 0
                        ),
                        "fallback_usage_rate": sum(
                            1 for op in type_ops if op.get("fallback_used", False)
                        )
                        / len(type_ops)
                        * 100,
                    }

            # Provider usage statistics
            provider_usage = {}
            for provider_name, metrics in self.provider_metrics.items():
                provider_usage[provider_name] = {
                    "total_operations": metrics.total_operations,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "success_rate": metrics.success_rate,
                    "recent_errors": metrics.recent_errors,
                    "last_used": (
                        metrics.last_used.isoformat() if metrics.last_used else None
                    ),
                }

            # Circuit breaker status
            circuit_breaker_status = {}
            for provider_name, breakers in self.circuit_breakers.items():
                circuit_breaker_status[provider_name] = {
                    operation_type.value: {
                        "state": (
                            "open"
                            if breaker.get("failures", 0) >= breaker.get("threshold", 5)
                            else "closed"
                        ),
                        "failures": breaker.get("failures", 0),
                        "last_failure": breaker.get("last_failure"),
                    }
                    for operation_type, breaker in breakers.items()
                }

            return {
                "overall_statistics": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "success_rate": success_rate,
                    "avg_response_time_ms": (
                        statistics.mean(
                            [
                                op["response_time_ms"]
                                for op in self._operation_history
                                if op["success"]
                            ]
                        )
                        if successful_operations > 0
                        else 0
                    ),
                },
                "operation_statistics": operation_stats,
                "provider_usage": provider_usage,
                "circuit_breaker_status": circuit_breaker_status,
                "failover_rules": {
                    op_type.value: {
                        "strategy": rule.strategy.value,
                        "max_retries": rule.max_retries,
                        "timeout_ms": rule.timeout_ms,
                    }
                    for op_type, rule in self.failover_rules.items()
                },
            }

        except Exception as e:
            logger.error(f"Failed to get failover statistics: {e}")
            return {"error": str(e)}

    async def reset_circuit_breakers(self, provider_name: Optional[str] = None) -> None:
        """Reset circuit breakers for a provider or all providers"""
        try:
            if provider_name:
                if provider_name in self.circuit_breakers:
                    self.circuit_breakers[provider_name] = {}
                    logger.info(f"Reset circuit breakers for provider: {provider_name}")
            else:
                self.circuit_breakers = {}
                logger.info("Reset all circuit breakers")

        except Exception as e:
            logger.error(f"Failed to reset circuit breakers: {e}")

    # Private methods
    async def _get_provider_order(
        self, operation_type: OperationType, rule: FailoverRule
    ) -> List[str]:
        """Get ordered list of providers based on failover strategy"""
        try:
            available_providers = await self.registry.list_providers(
                ProviderStatus.ACTIVE
            )

            if not available_providers:
                return []

            provider_names = [p["name"] for p in available_providers]

            if rule.strategy == FailoverStrategy.PRIORITY_BASED:
                # Sort by priority (lower number = higher priority)
                return sorted(
                    provider_names,
                    key=lambda name: next(
                        (
                            p["priority"]
                            for p in available_providers
                            if p["name"] == name
                        ),
                        999,
                    ),
                )

            elif rule.strategy == FailoverStrategy.HEALTH_BASED:
                # Sort by health status and metrics
                provider_scores = []
                for name in provider_names:
                    score = await self._calculate_health_score(name)
                    provider_scores.append((name, score))

                provider_scores.sort(key=lambda x: x[1], reverse=True)
                return [name for name, _ in provider_scores]

            elif rule.strategy == FailoverStrategy.ROUND_ROBIN:
                # Rotate through providers
                if provider_names:
                    self._round_robin_index = (self._round_robin_index + 1) % len(
                        provider_names
                    )
                    return (
                        provider_names[self._round_robin_index :]
                        + provider_names[: self._round_robin_index]
                    )
                return provider_names

            elif rule.strategy == FailoverStrategy.PERFORMANCE_BASED:
                # Sort by performance metrics
                provider_scores = []
                for name in provider_names:
                    score = await self._calculate_performance_score(
                        name, operation_type
                    )
                    provider_scores.append((name, score))

                provider_scores.sort(key=lambda x: x[1], reverse=True)
                return [name for name, _ in provider_scores]

            elif rule.strategy == FailoverStrategy.HYBRID:
                # Combine health, performance, and priority
                provider_scores = []
                for name in provider_names:
                    health_score = await self._calculate_health_score(name)
                    perf_score = await self._calculate_performance_score(
                        name, operation_type
                    )
                    priority = next(
                        (
                            p["priority"]
                            for p in available_providers
                            if p["name"] == name
                        ),
                        999,
                    )
                    priority_score = 1.0 / (
                        priority + 1
                    )  # Lower priority number = higher score

                    # Weighted combination
                    combined_score = (
                        health_score * 0.4 + perf_score * 0.4 + priority_score * 0.2
                    )
                    provider_scores.append((name, combined_score))

                provider_scores.sort(key=lambda x: x[1], reverse=True)
                return [name for name, _ in provider_scores]

            else:
                # Default to priority-based
                return sorted(
                    provider_names,
                    key=lambda name: next(
                        (
                            p["priority"]
                            for p in available_providers
                            if p["name"] == name
                        ),
                        999,
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to get provider order: {e}")
            return []

    async def _calculate_health_score(self, provider_name: str) -> float:
        """Calculate health score for a provider (0.0 to 1.0)"""
        try:
            health = await self.health_monitor.get_provider_health(provider_name)

            if not health:
                return 0.0

            # Base score from health status
            status_scores = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.7,
                HealthStatus.UNHEALTHY: 0.3,
                HealthStatus.CRITICAL: 0.1,
                HealthStatus.UNKNOWN: 0.0,
            }

            base_score = status_scores.get(health.status, 0.0)

            # Adjust based on metrics
            uptime_factor = health.uptime_percentage / 100.0
            error_factor = max(0.0, 1.0 - (health.error_rate / 100.0))

            # Response time factor (penalize slow responses)
            response_factor = 1.0
            if health.avg_response_time_ms > 1000:  # > 1 second
                response_factor = max(
                    0.1, 1.0 - (health.avg_response_time_ms - 1000) / 10000
                )

            return base_score * uptime_factor * error_factor * response_factor

        except Exception as e:
            logger.error(f"Failed to calculate health score for {provider_name}: {e}")
            return 0.0

    async def _calculate_performance_score(
        self, provider_name: str, operation_type: OperationType
    ) -> float:
        """Calculate performance score for a provider and operation type"""
        try:
            metrics = self.provider_metrics.get(provider_name)

            if not metrics:
                return 0.5  # Neutral score for unknown providers

            # Base score from success rate
            success_score = metrics.success_rate / 100.0

            # Response time score (faster = better)
            response_score = 1.0
            if metrics.avg_response_time_ms > 100:  # > 100ms
                response_score = max(
                    0.1, 1.0 - (metrics.avg_response_time_ms - 100) / 1000
                )

            # Recent usage factor (prefer recently used providers)
            if metrics.last_used:
                time_since_use = (
                    datetime.now(timezone.utc) - metrics.last_used
                ).total_seconds()
                recency_score = max(
                    0.1, 1.0 - (time_since_use / 3600)
                )  # Decay over 1 hour
            else:
                recency_score = 0.1

            # Error penalty
            error_penalty = max(0.0, 1.0 - (metrics.recent_errors / 10.0))

            return success_score * response_score * recency_score * error_penalty

        except Exception as e:
            logger.error(
                f"Failed to calculate performance score for {provider_name}: {e}"
            )
            return 0.0

    def _calculate_recommendation_score(
        self, provider_name: str, operation_type: OperationType
    ) -> float:
        """Calculate overall recommendation score for a provider"""
        try:
            # This is a simplified version - in practice you'd combine multiple factors
            metrics = self.provider_metrics.get(provider_name)
            if not metrics:
                return 0.0

            return (metrics.success_rate / 100.0) * (
                1.0 / (metrics.avg_response_time_ms / 100.0 + 1)
            )

        except Exception:
            return 0.0

    def _is_circuit_breaker_open(
        self, provider_name: str, operation_type: OperationType
    ) -> bool:
        """Check if circuit breaker is open for a provider and operation"""
        try:
            if provider_name not in self.circuit_breakers:
                return False

            breaker = self.circuit_breakers[provider_name].get(operation_type.value, {})
            failures = breaker.get("failures", 0)
            threshold = breaker.get("threshold", 5)
            last_failure = breaker.get("last_failure")

            if failures >= threshold:
                # Check if enough time has passed to try again (circuit breaker timeout)
                if last_failure:
                    time_since_failure = (
                        datetime.now(timezone.utc) - last_failure
                    ).total_seconds()
                    if time_since_failure > 300:  # 5 minutes
                        # Reset circuit breaker
                        breaker["failures"] = 0
                        return False
                return True

            return False

        except Exception:
            return False

    def _record_circuit_breaker_success(
        self, provider_name: str, operation_type: OperationType
    ) -> None:
        """Record successful operation for circuit breaker"""
        try:
            if provider_name not in self.circuit_breakers:
                self.circuit_breakers[provider_name] = {}

            if operation_type.value not in self.circuit_breakers[provider_name]:
                self.circuit_breakers[provider_name][operation_type.value] = {
                    "failures": 0,
                    "threshold": 5,
                    "last_failure": None,
                }

            # Reset failure count on success
            self.circuit_breakers[provider_name][operation_type.value]["failures"] = 0

        except Exception as e:
            logger.error(f"Failed to record circuit breaker success: {e}")

    def _record_circuit_breaker_failure(
        self, provider_name: str, operation_type: OperationType
    ) -> None:
        """Record failed operation for circuit breaker"""
        try:
            if provider_name not in self.circuit_breakers:
                self.circuit_breakers[provider_name] = {}

            if operation_type.value not in self.circuit_breakers[provider_name]:
                self.circuit_breakers[provider_name][operation_type.value] = {
                    "failures": 0,
                    "threshold": 5,
                    "last_failure": None,
                }

            breaker = self.circuit_breakers[provider_name][operation_type.value]
            breaker["failures"] += 1
            breaker["last_failure"] = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to record circuit breaker failure: {e}")

    async def _record_operation_success(
        self, provider_name: str, operation_type: OperationType, response_time_ms: float
    ) -> None:
        """Record successful operation metrics"""
        try:
            if provider_name not in self.provider_metrics:
                self.provider_metrics[provider_name] = ProviderMetrics(
                    provider_name=provider_name,
                    avg_response_time_ms=response_time_ms,
                    success_rate=100.0,
                    last_used=datetime.now(timezone.utc),
                    total_operations=1,
                    recent_errors=0,
                )
            else:
                metrics = self.provider_metrics[provider_name]

                # Update moving averages
                total_ops = metrics.total_operations + 1
                metrics.avg_response_time_ms = (
                    metrics.avg_response_time_ms * metrics.total_operations
                    + response_time_ms
                ) / total_ops

                # Update success rate (simple moving average over last 100 operations)
                success_count = int(
                    metrics.success_rate * min(metrics.total_operations, 100) / 100
                )
                success_count += 1
                window_size = min(total_ops, 100)
                metrics.success_rate = (success_count / window_size) * 100

                metrics.total_operations = total_ops
                metrics.last_used = datetime.now(timezone.utc)
                metrics.recent_errors = max(
                    0, metrics.recent_errors - 1
                )  # Decay errors

            # Record in health monitor
            await self.health_monitor.record_health_check(
                provider_name, response_time_ms, True
            )

        except Exception as e:
            logger.error(f"Failed to record operation success: {e}")

    async def _record_operation_failure(
        self, provider_name: str, operation_type: OperationType, error_message: str
    ) -> None:
        """Record failed operation metrics"""
        try:
            if provider_name not in self.provider_metrics:
                self.provider_metrics[provider_name] = ProviderMetrics(
                    provider_name=provider_name,
                    avg_response_time_ms=0.0,
                    success_rate=0.0,
                    last_used=datetime.now(timezone.utc),
                    total_operations=1,
                    recent_errors=1,
                )
            else:
                metrics = self.provider_metrics[provider_name]

                # Update success rate
                total_ops = metrics.total_operations + 1
                success_count = int(
                    metrics.success_rate * min(metrics.total_operations, 100) / 100
                )
                window_size = min(total_ops, 100)
                metrics.success_rate = (success_count / window_size) * 100

                metrics.total_operations = total_ops
                metrics.last_used = datetime.now(timezone.utc)
                metrics.recent_errors += 1

            # Record in health monitor
            await self.health_monitor.record_health_check(
                provider_name, 0.0, False, error_message
            )

        except Exception as e:
            logger.error(f"Failed to record operation failure: {e}")

    def _add_to_history(self, operation_data: Dict[str, Any]) -> None:
        """Add operation to history with size limit"""
        try:
            self._operation_history.append(operation_data)

            # Maintain history size limit
            if len(self._operation_history) > self._max_history_size:
                self._operation_history = self._operation_history[
                    -self._max_history_size :
                ]

        except Exception as e:
            logger.error(f"Failed to add to history: {e}")

    def _initialize_default_rules(self) -> None:
        """Initialize default failover rules"""
        try:
            # Default rules for different operation types
            default_rules = {
                OperationType.REMEMBER: FailoverRule(
                    operation_type=OperationType.REMEMBER,
                    strategy=FailoverStrategy.HYBRID,
                    max_retries=3,
                    retry_delay_ms=100,
                    timeout_ms=5000,
                ),
                OperationType.RECALL: FailoverRule(
                    operation_type=OperationType.RECALL,
                    strategy=FailoverStrategy.PERFORMANCE_BASED,
                    max_retries=2,
                    retry_delay_ms=50,
                    timeout_ms=3000,
                ),
                OperationType.DELETE: FailoverRule(
                    operation_type=OperationType.DELETE,
                    strategy=FailoverStrategy.PRIORITY_BASED,
                    max_retries=3,
                    retry_delay_ms=100,
                    timeout_ms=2000,
                ),
                OperationType.LIST: FailoverRule(
                    operation_type=OperationType.LIST,
                    strategy=FailoverStrategy.HEALTH_BASED,
                    max_retries=2,
                    retry_delay_ms=50,
                    timeout_ms=3000,
                ),
                OperationType.HEALTH_CHECK: FailoverRule(
                    operation_type=OperationType.HEALTH_CHECK,
                    strategy=FailoverStrategy.ROUND_ROBIN,
                    max_retries=1,
                    retry_delay_ms=0,
                    timeout_ms=1000,
                ),
            }

            self.failover_rules.update(default_rules)

        except Exception as e:
            logger.error(f"Failed to initialize default rules: {e}")

    def _get_default_rule(self) -> FailoverRule:
        """Get default failover rule"""
        return FailoverRule(
            operation_type=OperationType.RECALL,
            strategy=FailoverStrategy.HYBRID,
            max_retries=3,
            retry_delay_ms=100,
            timeout_ms=5000,
        )


# Global failover manager instance
_failover_manager: Optional[MemoryProviderFailoverManager] = None


async def get_failover_manager() -> MemoryProviderFailoverManager:
    """Get the global failover manager instance"""
    global _failover_manager
    if _failover_manager is None:
        from .health_monitor import get_health_monitor
        from .provider_registry import get_provider_registry

        registry = await get_provider_registry()
        health_monitor = await get_health_monitor()
        _failover_manager = MemoryProviderFailoverManager(registry, health_monitor)

    return _failover_manager


async def reset_failover_manager() -> None:
    """Reset the global failover manager (useful for testing)"""
    global _failover_manager
    _failover_manager = None
