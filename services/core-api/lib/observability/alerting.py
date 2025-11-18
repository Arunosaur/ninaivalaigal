#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Alerting and Notification System

Provides comprehensive alerting infrastructure for SLO violations,
system health issues, and operational incidents.

Integrates with:
- PagerDuty for critical incident routing
- Slack for team notifications
- Email for stakeholder communications
- Webhook systems for custom integrations
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None  # type: ignore

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"  # Service down, SLO violation
    HIGH = "high"  # Performance degradation, health issues
    MEDIUM = "medium"  # Warning thresholds exceeded
    LOW = "low"  # Informational alerts


class AlertStatus(Enum):
    """Alert lifecycle status"""

    FIRING = "firing"  # Active alert
    RESOLVED = "resolved"  # Alert condition cleared
    ACKNOWLEDGED = "acknowledged"  # Alert acknowledged by operator


class NotificationChannel(Enum):
    """Available notification channels"""

    PAGERDUTY = "pagerduty"
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


class Alert(BaseModel):
    """Alert data model"""

    id: str = Field(description="Unique alert identifier")
    name: str = Field(description="Alert name/title")
    severity: AlertSeverity = Field(description="Alert severity level")
    status: AlertStatus = Field(description="Alert status")
    message: str = Field(description="Alert message/description")
    source: str = Field(description="Alert source (service, component)")
    metric_name: Optional[str] = Field(description="Related metric name")
    threshold: Optional[float] = Field(description="Threshold that was violated")
    current_value: Optional[float] = Field(description="Current metric value")
    timestamp: datetime = Field(description="Alert creation timestamp")
    resolved_at: Optional[datetime] = Field(description="Alert resolution timestamp")
    acknowledged_by: Optional[str] = Field(description="Who acknowledged the alert")
    tags: Dict[str, str] = Field(default_factory=dict, description="Alert tags/metadata")


class PagerDutyConfig(BaseModel):
    """PagerDuty integration configuration"""

    integration_key: str = Field(description="PagerDuty integration key")
    api_key: Optional[str] = Field(description="PagerDuty API key for management")
    service_id: Optional[str] = Field(description="PagerDuty service ID")
    escalation_policy: Optional[str] = Field(description="Escalation policy ID")


class SlackConfig(BaseModel):
    """Slack integration configuration"""

    webhook_url: str = Field(description="Slack webhook URL")
    channel: str = Field(default="#alerts", description="Slack channel")
    mention_users: List[str] = Field(default_factory=list, description="Users to mention")
    mention_channels: List[str] = Field(default_factory=list, description="Channels to mention")


class EmailConfig(BaseModel):
    """Email notification configuration"""

    smtp_host: str = Field(description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    username: str = Field(description="SMTP username")
    password: str = Field(description="SMTP password")
    from_address: str = Field(description="From email address")
    to_addresses: List[str] = Field(description="Recipient email addresses")


class WebhookConfig(BaseModel):
    """Custom webhook configuration"""

    url: str = Field(description="Webhook URL")
    method: str = Field(default="POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class AlertingConfig(BaseModel):
    """Complete alerting configuration"""

    pagerduty: Optional[PagerDutyConfig] = None
    slack: Optional[SlackConfig] = None
    email: Optional[EmailConfig] = None
    webhook: Optional[WebhookConfig] = None
    enabled_channels: List[NotificationChannel] = Field(default_factory=list)
    rate_limit_minutes: int = Field(default=5, description="Rate limit for similar alerts")
    deduplication_window: int = Field(default=300, description="Deduplication window in seconds")


class AlertManager:
    """Main alerting system manager"""

    def __init__(self, config: AlertingConfig):
        self.config = config
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_notifications: Dict[str, datetime] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _should_throttle(self, alert: Alert) -> bool:
        """Check if alert should be throttled due to rate limiting"""
        alert_key = f"{alert.name}:{alert.source}:{alert.severity.value}"

        if alert_key in self.last_notifications:
            time_since_last = datetime.utcnow() - self.last_notifications[alert_key]
            if time_since_last.total_seconds() < self.config.rate_limit_minutes * 60:
                return True

        return False

    def _find_duplicate_alert(self, alert: Alert) -> Optional[Alert]:
        """Find existing duplicate alert"""
        for existing_alert in self.active_alerts.values():
            if (
                existing_alert.name == alert.name
                and existing_alert.source == alert.source
                and existing_alert.severity == alert.severity
                and existing_alert.status == AlertStatus.FIRING
            ):

                # Check if within deduplication window
                time_diff = (alert.timestamp - existing_alert.timestamp).total_seconds()
                if time_diff < self.config.deduplication_window:
                    return existing_alert

        return None

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through configured channels"""
        try:
            # Check for throttling
            if self._should_throttle(alert):
                logger.info("alert_throttled", alert_id=alert.id, alert_name=alert.name)
                return False

            # Check for duplicates
            duplicate = self._find_duplicate_alert(alert)
            if duplicate:
                logger.info("alert_deduplicated", new_alert_id=alert.id, existing_alert_id=duplicate.id)
                return False

            # Store alert
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # Send notifications
            success = True
            for channel in self.config.enabled_channels:
                try:
                    if channel == NotificationChannel.PAGERDUTY and self.config.pagerduty:
                        await self._send_pagerduty_alert(alert)
                    elif channel == NotificationChannel.SLACK and self.config.slack:
                        await self._send_slack_alert(alert)
                    elif channel == NotificationChannel.EMAIL and self.config.email:
                        await self._send_email_alert(alert)
                    elif channel == NotificationChannel.WEBHOOK and self.config.webhook:
                        await self._send_webhook_alert(alert)

                    # Update rate limit tracking
                    alert_key = f"{alert.name}:{alert.source}:{alert.severity.value}"
                    self.last_notifications[alert_key] = datetime.utcnow()

                except Exception as e:
                    logger.error("alert_channel_failed", channel=channel.value, alert_id=alert.id, error=str(e))
                    success = False

            logger.info(
                "alert_sent",
                alert_id=alert.id,
                alert_name=alert.name,
                severity=alert.severity.value,
                channels_sent=len(self.config.enabled_channels),
            )

            return success

        except Exception as e:
            logger.error("alert_send_failed", alert_id=alert.id, error=str(e))
            return False

    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            logger.warning("alert_not_found", alert_id=alert_id)
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()

        # Send resolution notifications
        for channel in self.config.enabled_channels:
            try:
                if channel == NotificationChannel.PAGERDUTY and self.config.pagerduty:
                    await self._resolve_pagerduty_alert(alert)
                elif channel == NotificationChannel.SLACK and self.config.slack:
                    await self._send_slack_resolution(alert)
            except Exception as e:
                logger.error("alert_resolution_failed", channel=channel.value, alert_id=alert_id, error=str(e))

        # Move to history and remove from active
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        logger.info("alert_resolved", alert_id=alert_id, resolved_by=resolved_by)
        return True

    async def _send_pagerduty_alert(self, alert: Alert):
        """Send alert to PagerDuty"""
        if not self.session or not self.config.pagerduty:
            return

        payload = {
            "routing_key": self.config.pagerduty.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.name,
                "source": alert.source,
                "severity": alert.severity.value.upper(),
                "timestamp": alert.timestamp.isoformat(),
                "component": alert.source,
                "group": "ninaivalaigal",
                "class": alert.metric_name or "slo_violation",
                "custom_details": {
                    "alert_id": alert.id,
                    "message": alert.message,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "tags": alert.tags,
                },
            },
        }

        async with self.session.post("https://events.pagerduty.com/v2/enqueue", json=payload, timeout=30) as response:
            if response.status != 202:
                raise Exception(f"PagerDuty API error: {response.status}")

    async def _resolve_pagerduty_alert(self, alert: Alert):
        """Resolve alert in PagerDuty"""
        if not self.session or not self.config.pagerduty:
            return

        payload = {
            "routing_key": self.config.pagerduty.integration_key,
            "event_action": "resolve",
            "payload": {
                "summary": alert.name,
                "source": alert.source,
                "severity": alert.severity.value.upper(),
                "timestamp": alert.resolved_at.isoformat(),
                "component": alert.source,
                "group": "ninaivalaigal",
                "class": alert.metric_name or "slo_violation",
                "custom_details": {"alert_id": alert.id, "resolved_at": alert.resolved_at.isoformat()},
            },
        }

        async with self.session.post("https://events.pagerduty.com/v2/enqueue", json=payload, timeout=30) as response:
            if response.status != 202:
                raise Exception(f"PagerDuty resolution error: {response.status}")

    async def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack"""
        if not self.session or not self.config.slack:
            return

        # Determine color based on severity
        color_map = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "good",
        }

        # Build mentions
        mentions = []
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            mentions.extend([f"<@{user}>" for user in self.config.slack.mention_users])
            mentions.extend([f"<!channel>" for _ in self.config.slack.mention_channels])

        mention_text = " ".join(mentions) if mentions else ""

        payload = {
            "channel": self.config.slack.channel,
            "username": "Ninaivalaigal Alerts",
            "icon_emoji": ":warning:",
            "text": f"{mention_text}🚨 {alert.name}" if mention_text else f"🚨 {alert.name}",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "warning"),
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Message", "value": alert.message, "short": False},
                    ],
                    "footer": "ninaivalaigal",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ],
        }

        if alert.threshold is not None and alert.current_value is not None:
            payload["attachments"][0]["fields"].append(
                {
                    "title": "Metric",
                    "value": f"{alert.current_value:.3f} (threshold: {alert.threshold:.3f})",
                    "short": True,
                }
            )

        async with self.session.post(self.config.slack.webhook_url, json=payload, timeout=30) as response:
            if response.status != 200:
                raise Exception(f"Slack webhook error: {response.status}")

    async def _send_slack_resolution(self, alert: Alert):
        """Send resolution notification to Slack"""
        if not self.session or not self.config.slack:
            return

        duration = (alert.resolved_at - alert.timestamp).total_seconds()

        payload = {
            "channel": self.config.slack.channel,
            "username": "Ninaivalaigal Alerts",
            "icon_emoji": ":white_check_mark:",
            "text": f"✅ Resolved: {alert.name}",
            "attachments": [
                {
                    "color": "good",
                    "fields": [
                        {"title": "Alert ID", "value": alert.id, "short": True},
                        {"title": "Duration", "value": f"{duration:.1f} seconds", "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                    ],
                    "footer": "ninaivalaigal",
                    "ts": int(alert.resolved_at.timestamp()),
                }
            ],
        }

        async with self.session.post(self.config.slack.webhook_url, json=payload, timeout=30) as response:
            if response.status != 200:
                raise Exception(f"Slack resolution error: {response.status}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert (placeholder - would need SMTP implementation)"""
        logger.info("email_alert_sent", alert_id=alert.id, alert_name=alert.name)
        # TODO: Implement actual email sending with SMTP
        pass

    async def _send_webhook_alert(self, alert: Alert):
        """Send alert to custom webhook"""
        if not self.session or not self.config.webhook:
            return

        payload = {
            "alert_id": alert.id,
            "name": alert.name,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "message": alert.message,
            "source": alert.source,
            "timestamp": alert.timestamp.isoformat(),
            "metric_name": alert.metric_name,
            "threshold": alert.threshold,
            "current_value": alert.current_value,
            "tags": alert.tags,
        }

        async with self.session.request(
            self.config.webhook.method,
            self.config.webhook.url,
            json=payload,
            headers=self.config.webhook.headers,
            timeout=self.config.webhook.timeout,
        ) as response:
            if response.status >= 400:
                raise Exception(f"Webhook error: {response.status}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_by_severity = {}

        for alert in self.active_alerts.values():
            severity = alert.severity.value
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1

        return {
            "total_alerts": total_alerts,
            "active_alerts": len(self.active_alerts),
            "active_by_severity": active_by_severity,
            "last_24h": len([a for a in self.alert_history if a.timestamp > datetime.utcnow() - timedelta(hours=24)]),
        }


# Global alert manager instance
alert_manager: Optional[AlertManager] = None


def load_alerting_config() -> AlertingConfig:
    """Load alerting configuration from environment"""
    config = AlertingConfig()

    # PagerDuty configuration
    if os.getenv("PAGERDUTY_INTEGRATION_KEY"):
        config.pagerduty = PagerDutyConfig(
            integration_key=os.getenv("PAGERDUTY_INTEGRATION_KEY"),
            api_key=os.getenv("PAGERDUTY_API_KEY"),
            service_id=os.getenv("PAGERDUTY_SERVICE_ID"),
            escalation_policy=os.getenv("PAGERDUTY_ESCALATION_POLICY"),
        )
        config.enabled_channels.append(NotificationChannel.PAGERDUTY)

    # Slack configuration
    if os.getenv("SLACK_WEBHOOK_URL"):
        config.slack = SlackConfig(
            webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            channel=os.getenv("SLACK_CHANNEL", "#alerts"),
            mention_users=os.getenv("SLACK_MENTION_USERS", "").split(",") if os.getenv("SLACK_MENTION_USERS") else [],
            mention_channels=(
                os.getenv("SLACK_MENTION_CHANNELS", "").split(",") if os.getenv("SLACK_MENTION_CHANNELS") else []
            ),
        )
        config.enabled_channels.append(NotificationChannel.SLACK)

    # Email configuration
    if os.getenv("SMTP_HOST"):
        config.email = EmailConfig(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            from_address=os.getenv("EMAIL_FROM"),
            to_addresses=os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else [],
        )
        config.enabled_channels.append(NotificationChannel.EMAIL)

    # Webhook configuration
    if os.getenv("ALERT_WEBHOOK_URL"):
        config.webhook = WebhookConfig(
            url=os.getenv("ALERT_WEBHOOK_URL"),
            method=os.getenv("ALERT_WEBHOOK_METHOD", "POST"),
            headers=json.loads(os.getenv("ALERT_WEBHOOK_HEADERS", "{}")),
            timeout=int(os.getenv("ALERT_WEBHOOK_TIMEOUT", "30")),
        )
        config.enabled_channels.append(NotificationChannel.WEBHOOK)

    return config


async def initialize_alerting() -> AlertManager:
    """Initialize the global alert manager"""
    global alert_manager

    config = load_alerting_config()
    alert_manager = AlertManager(config)

    logger.info("alerting_initialized", enabled_channels=[c.value for c in config.enabled_channels])

    return alert_manager


def get_alert_manager() -> Optional[AlertManager]:
    """Get the global alert manager"""
    return alert_manager
