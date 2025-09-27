"""
SPEC-020: Memory Provider Health Monitor
Live status tracking and health registry for memory providers
"""

import asyncio
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Provider health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Individual health metric data point"""

    timestamp: datetime
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthSummary:
    """Aggregated health summary for a provider"""

    provider_name: str
    status: HealthStatus
    last_check: datetime
    uptime_percentage: float
    avg_response_time_ms: float
    error_rate: float
    total_checks: int
    consecutive_failures: int
    last_error: Optional[str] = None
    metrics_window_hours: int = 24


@dataclass
class HealthAlert:
    """Health alert notification"""

    provider_name: str
    alert_level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderHealthMonitor:
    """
    SPEC-020: Provider Health Monitor

    Tracks provider health metrics, generates alerts, and maintains
    live status registry with historical data and trend analysis.
    """

    def __init__(self, metrics_retention_hours: int = 168):  # 7 days default
        self.metrics_retention_hours = metrics_retention_hours
        self.provider_metrics: Dict[str, List[HealthMetric]] = {}
        self.provider_summaries: Dict[str, HealthSummary] = {}
        self.active_alerts: Dict[str, List[HealthAlert]] = {}
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []

        # Health check thresholds
        self.thresholds = {
            "response_time_warning_ms": 1000,
            "response_time_critical_ms": 5000,
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.20,  # 20%
            "consecutive_failures_warning": 3,
            "consecutive_failures_critical": 5,
            "uptime_warning": 0.95,  # 95%
            "uptime_critical": 0.90,  # 90%
        }

        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_active = False

    async def start_monitoring(self) -> None:
        """Start the health monitoring system"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Health monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the health monitoring system"""
        self._monitoring_active = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitoring stopped")

    async def record_health_check(
        self,
        provider_name: str,
        response_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a health check result"""
        try:
            metric = HealthMetric(
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            # Initialize provider metrics if needed
            if provider_name not in self.provider_metrics:
                self.provider_metrics[provider_name] = []
                self.active_alerts[provider_name] = []

            # Add metric
            self.provider_metrics[provider_name].append(metric)

            # Update summary
            await self._update_provider_summary(provider_name)

            # Check for alerts
            await self._check_alerts(provider_name, metric)

        except Exception as e:
            logger.error(f"Failed to record health check for {provider_name}: {e}")

    async def get_provider_health(self, provider_name: str) -> Optional[HealthSummary]:
        """Get current health summary for a provider"""
        return self.provider_summaries.get(provider_name)

    async def get_all_provider_health(self) -> Dict[str, HealthSummary]:
        """Get health summaries for all providers"""
        return self.provider_summaries.copy()

    async def get_provider_metrics(
        self, provider_name: str, hours: int = 24
    ) -> List[HealthMetric]:
        """Get historical metrics for a provider"""
        if provider_name not in self.provider_metrics:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        metrics = self.provider_metrics[provider_name]

        return [m for m in metrics if m.timestamp >= cutoff_time]

    async def get_active_alerts(
        self,
        provider_name: Optional[str] = None,
        alert_level: Optional[AlertLevel] = None,
    ) -> List[HealthAlert]:
        """Get active alerts, optionally filtered by provider and/or level"""
        alerts = []

        if provider_name:
            provider_alerts = self.active_alerts.get(provider_name, [])
            alerts.extend([a for a in provider_alerts if not a.resolved])
        else:
            for provider_alerts in self.active_alerts.values():
                alerts.extend([a for a in provider_alerts if not a.resolved])

        if alert_level:
            alerts = [a for a in alerts if a.alert_level == alert_level]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    async def resolve_alert(self, provider_name: str, alert_message: str) -> bool:
        """Mark an alert as resolved"""
        try:
            if provider_name not in self.active_alerts:
                return False

            for alert in self.active_alerts[provider_name]:
                if alert.message == alert_message and not alert.resolved:
                    alert.resolved = True
                    logger.info(f"Resolved alert for {provider_name}: {alert_message}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

    async def get_health_trends(
        self, provider_name: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get health trends and analysis for a provider"""
        try:
            metrics = await self.get_provider_metrics(provider_name, hours)

            if not metrics:
                return {"error": "No metrics available"}

            # Calculate trends
            response_times = [m.response_time_ms for m in metrics]
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)

            # Time-based analysis
            hourly_buckets = {}
            for metric in metrics:
                hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
                if hour_key not in hourly_buckets:
                    hourly_buckets[hour_key] = []
                hourly_buckets[hour_key].append(metric)

            hourly_stats = {}
            for hour, hour_metrics in hourly_buckets.items():
                hourly_stats[hour.isoformat()] = {
                    "avg_response_time": statistics.mean(
                        [m.response_time_ms for m in hour_metrics]
                    ),
                    "success_rate": sum(1 for m in hour_metrics if m.success)
                    / len(hour_metrics),
                    "total_checks": len(hour_metrics),
                }

            return {
                "provider_name": provider_name,
                "time_window_hours": hours,
                "total_checks": len(metrics),
                "success_rate": success_rate,
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "response_time_std_dev": (
                    statistics.stdev(response_times) if len(response_times) > 1 else 0
                ),
                "hourly_breakdown": hourly_stats,
            }

        except Exception as e:
            logger.error(f"Failed to calculate health trends for {provider_name}: {e}")
            return {"error": str(e)}

    async def export_health_data(
        self, provider_name: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """Export health data for analysis or backup"""
        try:
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "time_window_hours": hours,
                "providers": {},
            }

            providers_to_export = (
                [provider_name] if provider_name else list(self.provider_metrics.keys())
            )

            for prov_name in providers_to_export:
                metrics = await self.get_provider_metrics(prov_name, hours)
                summary = await self.get_provider_health(prov_name)
                alerts = self.active_alerts.get(prov_name, [])

                export_data["providers"][prov_name] = {
                    "summary": {
                        "status": summary.status.value if summary else "unknown",
                        "uptime_percentage": (
                            summary.uptime_percentage if summary else 0
                        ),
                        "avg_response_time_ms": (
                            summary.avg_response_time_ms if summary else 0
                        ),
                        "error_rate": summary.error_rate if summary else 0,
                        "total_checks": summary.total_checks if summary else 0,
                    },
                    "metrics": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "response_time_ms": m.response_time_ms,
                            "success": m.success,
                            "error_message": m.error_message,
                        }
                        for m in metrics
                    ],
                    "alerts": [
                        {
                            "level": a.alert_level.value,
                            "message": a.message,
                            "timestamp": a.timestamp.isoformat(),
                            "resolved": a.resolved,
                        }
                        for a in alerts
                    ],
                }

            return export_data

        except Exception as e:
            logger.error(f"Failed to export health data: {e}")
            return {"error": str(e)}

    def add_alert_callback(self, callback: Callable[[HealthAlert], None]) -> None:
        """Add a callback function to be called when alerts are generated"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[HealthAlert], None]) -> None:
        """Remove an alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    # Private methods
    async def _update_provider_summary(self, provider_name: str) -> None:
        """Update the health summary for a provider"""
        try:
            metrics = self.provider_metrics[provider_name]

            if not metrics:
                return

            # Calculate metrics for the last 24 hours
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]

            if not recent_metrics:
                recent_metrics = metrics[-10:]  # Use last 10 if no recent metrics

            # Calculate summary statistics
            total_checks = len(recent_metrics)
            successful_checks = sum(1 for m in recent_metrics if m.success)
            uptime_percentage = (
                (successful_checks / total_checks) * 100 if total_checks > 0 else 0
            )

            response_times = [m.response_time_ms for m in recent_metrics if m.success]
            avg_response_time = statistics.mean(response_times) if response_times else 0

            error_rate = (
                ((total_checks - successful_checks) / total_checks) * 100
                if total_checks > 0
                else 0
            )

            # Count consecutive failures
            consecutive_failures = 0
            for metric in reversed(recent_metrics):
                if not metric.success:
                    consecutive_failures += 1
                else:
                    break

            # Determine health status
            status = self._calculate_health_status(
                uptime_percentage, avg_response_time, error_rate, consecutive_failures
            )

            # Get last error
            last_error = None
            for metric in reversed(recent_metrics):
                if not metric.success and metric.error_message:
                    last_error = metric.error_message
                    break

            # Update summary
            self.provider_summaries[provider_name] = HealthSummary(
                provider_name=provider_name,
                status=status,
                last_check=recent_metrics[-1].timestamp,
                uptime_percentage=uptime_percentage,
                avg_response_time_ms=avg_response_time,
                error_rate=error_rate,
                total_checks=total_checks,
                consecutive_failures=consecutive_failures,
                last_error=last_error,
            )

        except Exception as e:
            logger.error(f"Failed to update summary for {provider_name}: {e}")

    def _calculate_health_status(
        self,
        uptime_percentage: float,
        avg_response_time_ms: float,
        error_rate: float,
        consecutive_failures: int,
    ) -> HealthStatus:
        """Calculate overall health status based on metrics"""

        # Critical conditions
        if (
            consecutive_failures >= self.thresholds["consecutive_failures_critical"]
            or uptime_percentage < self.thresholds["uptime_critical"] * 100
            or error_rate > self.thresholds["error_rate_critical"] * 100
            or avg_response_time_ms > self.thresholds["response_time_critical_ms"]
        ):
            return HealthStatus.CRITICAL

        # Unhealthy conditions
        if (
            consecutive_failures >= self.thresholds["consecutive_failures_warning"]
            or uptime_percentage < self.thresholds["uptime_warning"] * 100
            or error_rate > self.thresholds["error_rate_warning"] * 100
        ):
            return HealthStatus.UNHEALTHY

        # Degraded conditions
        if avg_response_time_ms > self.thresholds["response_time_warning_ms"]:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def _check_alerts(self, provider_name: str, metric: HealthMetric) -> None:
        """Check if any alerts should be generated based on the latest metric"""
        try:
            summary = self.provider_summaries.get(provider_name)
            if not summary:
                return

            alerts_to_generate = []

            # Check for consecutive failures
            if (
                summary.consecutive_failures
                >= self.thresholds["consecutive_failures_critical"]
            ):
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.CRITICAL,
                        message=f"Provider has {summary.consecutive_failures} consecutive failures",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"consecutive_failures": summary.consecutive_failures},
                    )
                )
            elif (
                summary.consecutive_failures
                >= self.thresholds["consecutive_failures_warning"]
            ):
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.WARNING,
                        message=f"Provider has {summary.consecutive_failures} consecutive failures",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"consecutive_failures": summary.consecutive_failures},
                    )
                )

            # Check response time
            if metric.response_time_ms > self.thresholds["response_time_critical_ms"]:
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.ERROR,
                        message=f"Response time {metric.response_time_ms:.1f}ms exceeds critical threshold",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"response_time_ms": metric.response_time_ms},
                    )
                )
            elif metric.response_time_ms > self.thresholds["response_time_warning_ms"]:
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.WARNING,
                        message=f"Response time {metric.response_time_ms:.1f}ms exceeds warning threshold",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"response_time_ms": metric.response_time_ms},
                    )
                )

            # Check error rate
            if summary.error_rate > self.thresholds["error_rate_critical"] * 100:
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.CRITICAL,
                        message=f"Error rate {summary.error_rate:.1f}% exceeds critical threshold",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"error_rate": summary.error_rate},
                    )
                )
            elif summary.error_rate > self.thresholds["error_rate_warning"] * 100:
                alerts_to_generate.append(
                    HealthAlert(
                        provider_name=provider_name,
                        alert_level=AlertLevel.WARNING,
                        message=f"Error rate {summary.error_rate:.1f}% exceeds warning threshold",
                        timestamp=datetime.now(timezone.utc),
                        metadata={"error_rate": summary.error_rate},
                    )
                )

            # Add new alerts and notify callbacks
            for alert in alerts_to_generate:
                # Check if similar alert already exists
                existing_alerts = self.active_alerts[provider_name]
                similar_alert_exists = any(
                    a.message == alert.message and not a.resolved
                    for a in existing_alerts
                )

                if not similar_alert_exists:
                    self.active_alerts[provider_name].append(alert)

                    # Notify callbacks
                    for callback in self.alert_callbacks:
                        try:
                            callback(alert)
                        except Exception as e:
                            logger.error(f"Alert callback failed: {e}")

        except Exception as e:
            logger.error(f"Failed to check alerts for {provider_name}: {e}")

    async def _cleanup_loop(self) -> None:
        """Background cleanup task to remove old metrics"""
        while self._monitoring_active:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Cleanup every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=self.metrics_retention_hours
            )

            for provider_name in list(self.provider_metrics.keys()):
                metrics = self.provider_metrics[provider_name]

                # Keep only recent metrics
                recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
                self.provider_metrics[provider_name] = recent_metrics

                # Clean up resolved alerts older than 24 hours
                alert_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                alerts = self.active_alerts.get(provider_name, [])
                active_alerts = [
                    a for a in alerts if not a.resolved or a.timestamp >= alert_cutoff
                ]
                self.active_alerts[provider_name] = active_alerts

            logger.debug("Completed metrics cleanup")

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")


# Global health monitor instance
_health_monitor: Optional[ProviderHealthMonitor] = None


async def get_health_monitor() -> ProviderHealthMonitor:
    """Get the global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = ProviderHealthMonitor()
        await _health_monitor.start_monitoring()
    return _health_monitor


async def reset_health_monitor() -> None:
    """Reset the global health monitor (useful for testing)"""
    global _health_monitor
    if _health_monitor:
        await _health_monitor.stop_monitoring()
    _health_monitor = None
