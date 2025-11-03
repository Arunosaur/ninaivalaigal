#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
SLO Alerting Integration

Monitors SLO compliance and triggers alerts when thresholds are violated.
Integrates with the SLO monitoring system to provide proactive alerting
for service level objective violations.

Features:
- Real-time SLO violation detection
- Automatic alert triggering for SLO breaches
- Alert resolution when SLO compliance is restored
- Configurable alert thresholds and severity levels
- Integration with PagerDuty, Slack, and other notification channels
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import structlog

from .alerting import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertStatus,
    get_alert_manager,
    initialize_alerting,
)
from .slo_monitoring import SLO_TARGETS, get_slo_status, slo_tracker

logger = structlog.get_logger(__name__)


class SLOAlertConfig:
    """Configuration for SLO alerting"""

    def __init__(self):
        # Alert severity mapping for SLO violations
        self.severity_thresholds = {
            "availability": {
                AlertSeverity.CRITICAL: 0.995,  # <99.5% availability
                AlertSeverity.HIGH: 0.998,  # <99.8% availability
                AlertSeverity.MEDIUM: 0.999,  # <99.9% availability (SLO target)
            },
            "response_time_p95": {
                AlertSeverity.CRITICAL: 1.0,  # >1000ms P95
                AlertSeverity.HIGH: 0.5,  # >500ms P95
                AlertSeverity.MEDIUM: 0.2,  # >200ms P95 (SLO target)
            },
            "error_rate": {
                AlertSeverity.CRITICAL: 0.01,  # >1% error rate
                AlertSeverity.HIGH: 0.005,  # >0.5% error rate
                AlertSeverity.MEDIUM: 0.001,  # >0.1% error rate (SLO target)
            },
        }

        # Alert configuration
        self.check_interval_seconds = 60  # Check SLOs every minute
        self.alert_cooldown_minutes = 15  # Wait 15 minutes before re-alerting
        self.consecutive_violations = 2  # Require 2 consecutive violations before alerting

        # Alert templates
        self.alert_templates = {
            "availability": "SLO Violation: Availability {current:.3%} (target: {target:.3%})",
            "response_time_p95": "SLO Violation: P95 Response Time {current:.3f}s (target: {target:.3f}s)",
            "error_rate": "SLO Violation: Error Rate {current:.3%} (target: {target:.3%})",
        }


class SLOViolationState:
    """Tracks state for SLO violations"""

    def __init__(self, metric_name: str, window: str):
        self.metric_name = metric_name
        self.window = window
        self.violation_count = 0
        self.last_alert_time: Optional[datetime] = None
        self.active_alert_ids: Set[str] = set()
        self.last_check_time: Optional[datetime] = None
        self.is_violating = False


class SLOAlerter:
    """SLO alerting system"""

    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.config = SLOAlertConfig()
        self.violation_states: Dict[str, SLOViolationState] = {}
        self.running = False
        self.task: Optional[asyncio.Task] = None

    def _get_state_key(self, metric_name: str, window: str) -> str:
        """Get state key for metric/window combination"""
        return f"{metric_name}:{window}"

    def _get_violation_severity(self, metric_name: str, current_value: float) -> Optional[AlertSeverity]:
        """Determine alert severity based on current value"""
        thresholds = self.config.severity_thresholds.get(metric_name, {})

        for severity, threshold in thresholds.items():
            if metric_name == "availability":
                if current_value < threshold:
                    return severity
            else:  # response_time_p95, error_rate
                if current_value > threshold:
                    return severity

        return None

    def _should_alert(self, state: SLOViolationState, severity: AlertSeverity) -> bool:
        """Check if we should send an alert"""
        # Check consecutive violations
        if state.violation_count < self.config.consecutive_violations:
            return False

        # Check cooldown
        if state.last_alert_time:
            time_since_last = datetime.utcnow() - state.last_alert_time
            if time_since_last.total_seconds() < self.config.alert_cooldown_minutes * 60:
                return False

        return True

    async def _create_slo_alert(
        self, metric_name: str, window: str, current_value: float, target_value: float, severity: AlertSeverity
    ) -> Alert:
        """Create an SLO violation alert"""
        alert_id = f"slo-{metric_name}-{window}-{int(time.time())}"

        template = self.config.alert_templates.get(metric_name, "SLO Violation: {metric_name}")
        message = template.format(current=current_value, target=target_value, metric_name=metric_name)

        alert = Alert(
            id=alert_id,
            name=f"SLO Violation: {metric_name.replace('_', ' ').title()}",
            severity=severity,
            status=AlertStatus.FIRING,
            message=message,
            source="slo-monitoring",
            metric_name=metric_name,
            threshold=target_value,
            current_value=current_value,
            timestamp=datetime.utcnow(),
            tags={"window": window, "slo_type": metric_name, "severity": severity.value, "service": "ninaivalaigal"},
        )

        return alert

    async def _check_slo_compliance(self):
        """Check SLO compliance and trigger alerts if needed"""
        try:
            # Check all configured windows
            for window in ["1h", "24h"]:
                slo_status = get_slo_status(window)

                if slo_status.get("overall_status") == "error":
                    logger.warning("slo_status_error", window=window, error=slo_status.get("error"))
                    continue

                current_metrics = slo_status.get("current", {})

                for metric_name, target_value in SLO_TARGETS.items():
                    current_value = current_metrics.get(metric_name)

                    if current_value is None:
                        continue

                    state_key = self._get_state_key(metric_name, window)

                    # Initialize state if needed
                    if state_key not in self.violation_states:
                        self.violation_states[state_key] = SLOViolationState(metric_name, window)

                    state = self.violation_states[state_key]
                    state.last_check_time = datetime.utcnow()

                    # Check if this is a violation
                    is_violating = False
                    if metric_name == "availability":
                        is_violating = current_value < target_value
                    else:  # response_time_p95, error_rate
                        is_violating = current_value > target_value

                    if is_violating:
                        # This is a violation
                        state.violation_count += 1
                        state.is_violating = True

                        # Determine severity
                        severity = self._get_violation_severity(metric_name, current_value)

                        if severity and self._should_alert(state, severity):
                            # Create and send alert
                            alert = await self._create_slo_alert(
                                metric_name, window, current_value, target_value, severity
                            )

                            success = await self.alert_manager.send_alert(alert)
                            if success:
                                state.last_alert_time = datetime.utcnow()
                                state.active_alert_ids.add(alert.id)

                                logger.warning(
                                    "slo_alert_triggered",
                                    metric=metric_name,
                                    window=window,
                                    current=current_value,
                                    target=target_value,
                                    severity=severity.value,
                                    alert_id=alert.id,
                                )

                    else:
                        # This is not a violation - check if we need to resolve alerts
                        if state.is_violating:
                            state.is_violating = False
                            state.violation_count = 0

                            # Resolve any active alerts
                            for alert_id in list(state.active_alert_ids):
                                await self.alert_manager.resolve_alert(alert_id, "slo-recovered")
                                state.active_alert_ids.discard(alert_id)

                            logger.info(
                                "slo_violation_resolved",
                                metric=metric_name,
                                window=window,
                                current=current_value,
                                target=target_value,
                            )

        except Exception as e:
            logger.error("slo_check_failed", error=str(e))

    async def start_monitoring(self):
        """Start SLO monitoring loop"""
        if self.running:
            logger.warning("slo_monitoring_already_running")
            return

        self.running = True
        self.task = asyncio.create_task(self._monitoring_loop())

        logger.info("slo_monitoring_started", check_interval=self.config.check_interval_seconds)

    async def stop_monitoring(self):
        """Stop SLO monitoring loop"""
        if not self.running:
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("slo_monitoring_stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_slo_compliance()
                await asyncio.sleep(self.config.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("slo_monitoring_loop_error", error=str(e))
                await asyncio.sleep(self.config.check_interval_seconds)

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        active_violations = []
        for state_key, state in self.violation_states.items():
            if state.is_violating:
                active_violations.append(
                    {
                        "metric": state.metric_name,
                        "window": state.window,
                        "violation_count": state.violation_count,
                        "active_alerts": len(state.active_alert_ids),
                        "last_check": state.last_check_time.isoformat() if state.last_check_time else None,
                    }
                )

        return {
            "monitoring_active": self.running,
            "check_interval_seconds": self.config.check_interval_seconds,
            "active_violations": active_violations,
            "total_violation_states": len(self.violation_states),
            "last_check": datetime.utcnow().isoformat(),
        }


# Global SLO alerter instance
slo_alerter: Optional[SLOAlerter] = None


async def initialize_slo_alerting() -> SLOAlerter:
    """Initialize SLO alerting system"""
    global slo_alerter

    # Initialize alert manager if needed
    alert_manager = get_alert_manager()
    if not alert_manager:
        alert_manager = await initialize_alerting()

    slo_alerter = SLOAlerter(alert_manager)

    logger.info("slo_alerting_initialized")
    return slo_alerter


async def start_slo_monitoring():
    """Start SLO monitoring"""
    if not slo_alerter:
        await initialize_slo_alerting()

    await slo_alerter.start_monitoring()


async def stop_slo_monitoring():
    """Stop SLO monitoring"""
    if slo_alerter:
        await slo_alerter.stop_monitoring()


def get_slo_alerter() -> Optional[SLOAlerter]:
    """Get the SLO alerter instance"""
    return slo_alerter


# Manual alert triggering for testing and special cases
async def trigger_manual_slo_alert(metric_name: str, window: str, current_value: float, severity: AlertSeverity):
    """Manually trigger an SLO alert (for testing or special cases)"""
    alert_manager = get_alert_manager()
    if not alert_manager:
        raise Exception("Alert manager not initialized")

    target_value = SLO_TARGETS.get(metric_name)
    if target_value is None:
        raise ValueError(f"Unknown SLO metric: {metric_name}")

    alert = await SLOAlerter(alert_manager)._create_slo_alert(
        metric_name, window, current_value, target_value, severity
    )

    success = await alert_manager.send_alert(alert)

    logger.info(
        "manual_slo_alert_triggered",
        metric=metric_name,
        window=window,
        current=current_value,
        severity=severity.value,
        success=success,
    )

    return success if success else False
