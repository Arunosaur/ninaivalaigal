#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Monitoring Automation System

Provides automated health checks, recovery procedures, and
monitoring infrastructure management.

Features:
- Automated health checks with configurable intervals
- Self-healing procedures for common issues
- Monitoring service lifecycle management
- Health check scheduling and reporting
- Integration with SLO monitoring and alerting
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

from .alerting import Alert, AlertSeverity, AlertStatus, get_alert_manager
from .slo_alerting import get_slo_alerter
from .slo_monitoring import get_slo_status


# Mock health check functions for now - these should be implemented properly
async def check_database():
    """Mock database health check"""
    return {"connected": True, "pool_stats": {"active": 5, "total": 20}}


async def check_redis_memory_cache():
    """Mock Redis health check"""
    return {"status": "healthy", "info": {"used_memory": 1000000, "connected_clients": 5}, "hit_rate": 0.95}


async def check_memory_service():
    """Mock memory service health check"""
    return {"status": "healthy", "available": True}


logger = structlog.get_logger(__name__)


class HealthCheckStatus(Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery action types"""

    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DATABASE = "reconnect_database"
    SCALE_RESOURCES = "scale_resources"
    NOTIFY_OPERATORS = "notify_operators"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    component: str
    status: HealthCheckStatus
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime
    duration_ms: float


@dataclass
class RecoveryActionResult:
    """Result of a recovery action"""

    action: RecoveryAction
    success: bool
    message: str
    timestamp: datetime
    duration_ms: float


class HealthCheck:
    """Base class for health checks"""

    def __init__(self, name: str, check_interval_seconds: int = 60):
        self.name = name
        self.check_interval_seconds = check_interval_seconds
        self.last_check: Optional[datetime] = None
        self.last_result: Optional[HealthCheckResult] = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

    async def execute_check(self) -> HealthCheckResult:
        """Execute the health check"""
        start_time = time.time()

        try:
            result = await self._check()

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            result.timestamp = datetime.utcnow()

            # Update state
            self.last_check = result.timestamp
            self.last_result = result

            # Update consecutive failures
            if result.status in [HealthCheckStatus.UNHEALTHY, HealthCheckStatus.UNKNOWN]:
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 0

            logger.info(
                "health_check_completed",
                component=self.name,
                status=result.status.value,
                duration_ms=duration_ms,
                consecutive_failures=self.consecutive_failures,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            error_result = HealthCheckResult(
                component=self.name,
                status=HealthCheckStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                metrics={},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
            )

            self.last_check = error_result.timestamp
            self.last_result = error_result
            self.consecutive_failures += 1

            logger.error(
                "health_check_error", component=self.name, error=str(e), consecutive_failures=self.consecutive_failures
            )

            return error_result

    async def _check(self) -> HealthCheckResult:
        """Override this method to implement specific health check logic"""
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Database health check"""

    def __init__(self):
        super().__init__("database", check_interval_seconds=30)

    async def _check(self) -> HealthCheckResult:
        """Check database health"""
        try:
            db_status = await check_database()

            if db_status.get("connected", False):
                # Check connection pool
                pool_stats = db_status.get("pool_stats", {})
                active_connections = pool_stats.get("active", 0)
                total_connections = pool_stats.get("total", 0)

                # Determine status based on connection metrics
                if active_connections > total_connections * 0.8:
                    status = HealthCheckStatus.DEGRADED
                    message = f"High connection usage: {active_connections}/{total_connections}"
                else:
                    status = HealthCheckStatus.HEALTHY
                    message = "Database connection healthy"

                return HealthCheckResult(
                    component=self.name,
                    status=status,
                    message=message,
                    metrics={
                        "connected": True,
                        "active_connections": active_connections,
                        "total_connections": total_connections,
                        "response_time_ms": db_status.get("response_time_ms", 0),
                    },
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )
            else:
                return HealthCheckResult(
                    component=self.name,
                    status=HealthCheckStatus.UNHEALTHY,
                    message="Database connection failed",
                    metrics={"connected": False},
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )

        except Exception as e:
            return HealthCheckResult(
                component=self.name,
                status=HealthCheckStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                metrics={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )


class RedisHealthCheck(HealthCheck):
    """Redis health check"""

    def __init__(self):
        super().__init__("redis", check_interval_seconds=30)

    async def _check(self) -> HealthCheckResult:
        """Check Redis health"""
        try:
            redis_status = await check_redis_memory_cache()

            if redis_status.get("status") == "healthy":
                # Extract metrics
                info = redis_status.get("info", {})
                memory_usage = info.get("used_memory", 0)
                connected_clients = info.get("connected_clients", 0)
                hit_rate = redis_status.get("hit_rate", 0)

                # Determine status
                if hit_rate < 0.8:
                    status = HealthCheckStatus.DEGRADED
                    message = f"Low cache hit rate: {hit_rate:.2%}"
                elif connected_clients > 100:
                    status = HealthCheckStatus.DEGRADED
                    message = f"High client connections: {connected_clients}"
                else:
                    status = HealthCheckStatus.HEALTHY
                    message = "Redis cache healthy"

                return HealthCheckResult(
                    component=self.name,
                    status=status,
                    message=message,
                    metrics={
                        "connected": True,
                        "memory_usage_bytes": memory_usage,
                        "connected_clients": connected_clients,
                        "hit_rate": hit_rate,
                    },
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )
            else:
                return HealthCheckResult(
                    component=self.name,
                    status=HealthCheckStatus.UNHEALTHY,
                    message="Redis connection failed",
                    metrics={"connected": False},
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )

        except Exception as e:
            return HealthCheckResult(
                component=self.name,
                status=HealthCheckStatus.UNHEALTHY,
                message=f"Redis health check failed: {str(e)}",
                metrics={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )


class SLOHealthCheck(HealthCheck):
    """SLO compliance health check"""

    def __init__(self):
        super().__init__("slo", check_interval_seconds=60)

    async def _check(self) -> HealthCheckResult:
        """Check SLO compliance"""
        try:
            slo_status = get_slo_status("1h")

            if slo_status.get("overall_status") == "healthy":
                current_metrics = slo_status.get("current", {})

                return HealthCheckResult(
                    component=self.name,
                    status=HealthCheckStatus.HEALTHY,
                    message="All SLOs compliant",
                    metrics=current_metrics,
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )
            else:
                # Determine which SLOs are failing
                compliance = slo_status.get("compliance", {})
                failing_slos = []

                for slo_name, is_compliant in compliance.items():
                    if slo_name != "overall" and not is_compliant:
                        failing_slos.append(slo_name)

                return HealthCheckResult(
                    component=self.name,
                    status=HealthCheckStatus.DEGRADED,
                    message=f"SLO violations: {', '.join(failing_slos)}",
                    metrics={"compliance": compliance, "failing_slos": failing_slos},
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )

        except Exception as e:
            return HealthCheckResult(
                component=self.name,
                status=HealthCheckStatus.UNKNOWN,
                message=f"SLO health check failed: {str(e)}",
                metrics={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )


class RecoveryProcedure:
    """Base class for recovery procedures"""

    def __init__(self, name: str, action: RecoveryAction):
        self.name = name
        self.action = action

    async def execute(self, context: Dict[str, Any]) -> RecoveryActionResult:
        """Execute the recovery procedure"""
        start_time = time.time()

        try:
            result = await self._recover(context)

            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            result.timestamp = datetime.utcnow()

            logger.info(
                "recovery_procedure_completed",
                procedure=self.name,
                action=self.action.value,
                success=result.success,
                duration_ms=duration_ms,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            error_result = RecoveryActionResult(
                action=self.action,
                success=False,
                message=f"Recovery procedure failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
            )

            logger.error("recovery_procedure_error", procedure=self.name, action=self.action.value, error=str(e))

            return error_result

    async def _recover(self, context: Dict[str, Any]) -> RecoveryActionResult:
        """Override this method to implement specific recovery logic"""
        raise NotImplementedError


class RestartServiceRecovery(RecoveryProcedure):
    """Restart service recovery procedure"""

    def __init__(self, service_name: str):
        super().__init__(f"restart-{service_name}", RecoveryAction.RESTART_SERVICE)
        self.service_name = service_name

    async def _recover(self, context: Dict[str, Any]) -> RecoveryActionResult:
        """Restart the specified service"""
        try:
            # Use Docker/Container CLI to restart service
            cmd = ["container", "restart", f"nina-{self.service_name}"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return RecoveryActionResult(
                    action=self.action,
                    success=True,
                    message=f"Successfully restarted {self.service_name}",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )
            else:
                return RecoveryActionResult(
                    action=self.action,
                    success=False,
                    message=f"Failed to restart {self.service_name}: {result.stderr}",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                )

        except subprocess.TimeoutExpired:
            return RecoveryActionResult(
                action=self.action,
                success=False,
                message=f"Restart timeout for {self.service_name}",
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )
        except Exception as e:
            return RecoveryActionResult(
                action=self.action,
                success=False,
                message=f"Restart error for {self.service_name}: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )


class ClearCacheRecovery(RecoveryProcedure):
    """Clear cache recovery procedure"""

    def __init__(self):
        super().__init__("clear-cache", RecoveryAction.CLEAR_CACHE)

    async def _recover(self, context: Dict[str, Any]) -> RecoveryActionResult:
        """Clear Redis cache"""
        try:
            # This would connect to Redis and clear specific caches
            # For now, simulate the action
            await asyncio.sleep(1)  # Simulate cache clearing time

            return RecoveryActionResult(
                action=self.action,
                success=True,
                message="Successfully cleared Redis cache",
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )

        except Exception as e:
            return RecoveryActionResult(
                action=self.action,
                success=False,
                message=f"Failed to clear cache: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=0,
            )


class MonitoringAutomation:
    """Main monitoring automation system"""

    def __init__(self):
        self.health_checks: List[HealthCheck] = []
        self.recovery_procedures: List[RecoveryProcedure] = []
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.health_history: List[HealthCheckResult] = []
        self.recovery_history: List[RecoveryActionResult] = []

        # Initialize health checks
        self._setup_health_checks()

        # Initialize recovery procedures
        self._setup_recovery_procedures()

    def _setup_health_checks(self):
        """Setup health checks"""
        self.health_checks = [DatabaseHealthCheck(), RedisHealthCheck(), SLOHealthCheck()]

    def _setup_recovery_procedures(self):
        """Setup recovery procedures"""
        self.recovery_procedures = [
            RestartServiceRecovery("api"),
            RestartServiceRecovery("redis"),
            ClearCacheRecovery(),
        ]

    async def start_monitoring(self):
        """Start automated monitoring"""
        if self.running:
            logger.warning("monitoring_already_running")
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info(
            "monitoring_automation_started",
            health_checks=len(self.health_checks),
            recovery_procedures=len(self.recovery_procedures),
        )

    async def stop_monitoring(self):
        """Stop automated monitoring"""
        if not self.running:
            return

        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("monitoring_automation_stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._execute_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("monitoring_loop_error", error=str(e))
                await asyncio.sleep(30)

    async def _execute_health_checks(self):
        """Execute all health checks and handle recovery"""
        for health_check in self.health_checks:
            # Check if it's time to run this health check
            if health_check.last_check and datetime.utcnow() - health_check.last_check < timedelta(
                seconds=health_check.check_interval_seconds
            ):
                continue

            # Execute health check
            result = await health_check.execute_check()
            self.health_history.append(result)

            # Keep history manageable
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-500:]

            # Check if recovery is needed
            if (
                result.status in [HealthCheckStatus.UNHEALTHY, HealthCheckStatus.UNKNOWN]
                and health_check.consecutive_failures >= health_check.max_consecutive_failures
            ):

                await self._handle_health_failure(health_check, result)

    async def _handle_health_failure(self, health_check: HealthCheck, result: HealthCheckResult):
        """Handle health check failure with recovery procedures"""
        logger.warning(
            "health_failure_detected",
            component=health_check.name,
            consecutive_failures=health_check.consecutive_failures,
            message=result.message,
        )

        # Send alert
        alert_manager = get_alert_manager()
        if alert_manager:
            alert = Alert(
                id=f"health-{health_check.name}-{int(time.time())}",
                name=f"Health Failure: {health_check.name}",
                severity=AlertSeverity.HIGH,
                status=AlertStatus.FIRING,
                message=f"Component {health_check.name} failed health check: {result.message}",
                source="monitoring-automation",
                timestamp=datetime.utcnow(),
                tags={
                    "component": health_check.name,
                    "consecutive_failures": str(health_check.consecutive_failures),
                    "status": result.status.value,
                },
            )

            await alert_manager.send_alert(alert)

        # Execute recovery procedures
        for procedure in self.recovery_procedures:
            if await self._should_execute_recovery(procedure, health_check, result):
                recovery_result = await procedure.execute(
                    {
                        "component": health_check.name,
                        "health_result": result,
                        "consecutive_failures": health_check.consecutive_failures,
                    }
                )

                self.recovery_history.append(recovery_result)

                # Keep history manageable
                if len(self.recovery_history) > 500:
                    self.recovery_history = self.recovery_history[-250:]

                # If recovery was successful, break
                if recovery_result.success:
                    logger.info("recovery_successful", procedure=procedure.name, component=health_check.name)
                    break

    async def _should_execute_recovery(
        self, procedure: RecoveryProcedure, health_check: HealthCheck, result: HealthCheckResult
    ) -> bool:
        """Determine if recovery procedure should be executed"""
        # Simple logic for now - could be made more sophisticated
        if health_check.name == "database" and procedure.action == RecoveryAction.RESTART_SERVICE:
            return "api" in procedure.name  # Restart API for database issues

        if health_check.name == "redis" and procedure.action == RecoveryAction.CLEAR_CACHE:
            return True

        if health_check.name == "slo" and procedure.action == RecoveryAction.NOTIFY_OPERATORS:
            return True

        return False

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        recent_health = [r for r in self.health_history if r.timestamp > datetime.utcnow() - timedelta(hours=1)]

        recent_recovery = [r for r in self.recovery_history if r.timestamp > datetime.utcnow() - timedelta(hours=1)]

        return {
            "monitoring_active": self.running,
            "health_checks": [
                {
                    "name": hc.name,
                    "last_check": hc.last_check.isoformat() if hc.last_check else None,
                    "last_status": hc.last_result.status.value if hc.last_result else None,
                    "consecutive_failures": hc.consecutive_failures,
                }
                for hc in self.health_checks
            ],
            "recent_health_checks": len(recent_health),
            "recent_recoveries": len(recent_recovery),
            "total_health_checks": len(self.health_history),
            "total_recoveries": len(self.recovery_history),
        }


# Global monitoring automation instance
monitoring_automation: Optional[MonitoringAutomation] = None


async def initialize_monitoring_automation() -> MonitoringAutomation:
    """Initialize monitoring automation system"""
    global monitoring_automation

    monitoring_automation = MonitoringAutomation()

    logger.info("monitoring_automation_initialized")
    return monitoring_automation


async def start_monitoring_automation():
    """Start monitoring automation"""
    if not monitoring_automation:
        await initialize_monitoring_automation()

    await monitoring_automation.start_monitoring()


async def stop_monitoring_automation():
    """Stop monitoring automation"""
    if monitoring_automation:
        await monitoring_automation.stop_monitoring()


def get_monitoring_automation() -> Optional[MonitoringAutomation]:
    """Get the monitoring automation instance"""
    return monitoring_automation
