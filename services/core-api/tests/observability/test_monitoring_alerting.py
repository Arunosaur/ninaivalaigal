#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Test suite for monitoring and alerting infrastructure.

Tests the complete alerting system including:
- Alert manager functionality
- SLO alerting integration
- Monitoring automation
- Grafana dashboard generation
- API endpoints
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "lib"))

from observability.alerting import (
    Alert,
    AlertingConfig,
    AlertManager,
    AlertSeverity,
    AlertStatus,
    PagerDutyConfig,
    SlackConfig,
    load_alerting_config,
)
from observability.grafana_dashboards import GrafanaDashboardBuilder, get_all_dashboards
from observability.monitoring_automation import (
    DatabaseHealthCheck,
    HealthCheck,
    HealthCheckStatus,
    MonitoringAutomation,
    RedisHealthCheck,
    SLOHealthCheck,
)
from observability.slo_alerting import (
    SLOAlertConfig,
    SLOAlerter,
    SLOViolationState,
    initialize_slo_alerting,
    trigger_manual_slo_alert,
)


class TestAlertManager:
    """Test alert manager functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create mock alerting configuration"""
        config = AlertingConfig()
        config.enabled_channels = []  # No external channels for testing
        config.rate_limit_minutes = 1
        config.deduplication_window = 60
        return config

    @pytest.fixture
    async def alert_manager(self, mock_config):
        """Create alert manager for testing"""
        manager = AlertManager(mock_config)
        async with manager:
            yield manager

    @pytest.mark.asyncio
    async def test_alert_creation(self, mock_config):
        """Test alert creation and validation"""
        alert = Alert(
            id="test-alert-1",
            name="Test Alert",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.FIRING,
            message="Test alert message",
            source="test-source",
            metric_name="availability",
            threshold=0.999,
            current_value=0.995,
            timestamp=datetime.utcnow(),
            resolved_at=None,
            acknowledged_by=None,
            tags={"test": "true"},
        )

        assert alert.id == "test-alert-1"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.status == AlertStatus.FIRING
        assert alert.tags["test"] == "true"

    @pytest.mark.asyncio
    async def test_send_alert_success(self, alert_manager):
        """Test successful alert sending"""
        alert = Alert(
            id="test-alert-2",
            name="Test Alert",
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.FIRING,
            message="Test alert message",
            source="test-source",
            metric_name="response_time_p95",
            threshold=0.2,
            current_value=0.3,
            timestamp=datetime.utcnow(),
            resolved_at=None,
            acknowledged_by=None,
        )

        success = await alert_manager.send_alert(alert)
        assert success is True

        # Check alert is stored
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].id == "test-alert-2"

    @pytest.mark.asyncio
    async def test_alert_resolution(self, alert_manager):
        """Test alert resolution"""
        # First send an alert
        alert = Alert(
            id="test-alert-3",
            name="Test Alert",
            severity=AlertSeverity.LOW,
            status=AlertStatus.FIRING,
            message="Test alert message",
            source="test-source",
            metric_name="error_rate",
            threshold=0.001,
            current_value=0.002,
            timestamp=datetime.utcnow(),
            resolved_at=None,
            acknowledged_by=None,
        )

        await alert_manager.send_alert(alert)

        # Resolve the alert
        success = await alert_manager.resolve_alert("test-alert-3")
        assert success is True

        # Check alert is no longer active
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 0

    @pytest.mark.asyncio
    async def test_alert_throttling(self, alert_manager):
        """Test alert rate limiting"""
        alert = Alert(
            id="test-alert-throttle",
            name="Test Alert",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.FIRING,
            message="Test alert message",
            source="test-source",
            metric_name="availability",
            threshold=0.999,
            current_value=0.995,
            timestamp=datetime.utcnow(),
            resolved_at=None,
            acknowledged_by=None,
        )

        # Send first alert
        success1 = await alert_manager.send_alert(alert)
        assert success1 is True

        # Send second identical alert (should be throttled)
        alert2 = Alert(
            id="test-alert-throttle-2",
            name="Test Alert",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.FIRING,
            message="Test alert message",
            source="test-source",
            metric_name="availability",
            threshold=0.999,
            current_value=0.995,
            timestamp=datetime.utcnow(),
            resolved_at=None,
            acknowledged_by=None,
        )

        success2 = await alert_manager.send_alert(alert2)
        assert success2 is False  # Should be throttled

    def test_alert_statistics(self, alert_manager):
        """Test alert statistics calculation"""
        stats = alert_manager.get_alert_stats()

        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "active_by_severity" in stats
        assert "last_24h" in stats
        assert stats["total_alerts"] == 0
        assert stats["active_alerts"] == 0


class TestSLOAlerter:
    """Test SLO alerting functionality"""

    @pytest.fixture
    async def slo_alerter(self):
        """Create SLO alerter for testing"""
        mock_alert_manager = Mock()
        mock_alert_manager.send_alert = AsyncMock(return_value=True)
        mock_alert_manager.resolve_alert = AsyncMock(return_value=True)

        alerter = SLOAlerter(mock_alert_manager)
        return alerter

    @pytest.mark.asyncio
    async def test_slo_violation_detection(self, slo_alerter):
        """Test SLO violation detection"""
        # Test availability violation
        severity = slo_alerter._get_violation_severity("availability", 0.99)
        assert severity == AlertSeverity.MEDIUM  # Below 99.9% target

        # Test response time violation
        severity = slo_alerter._get_violation_severity("response_time_p95", 0.3)
        assert severity == AlertSeverity.HIGH  # Above 200ms target

        # Test error rate violation
        severity = slo_alerter._get_violation_severity("error_rate", 0.002)
        assert severity == AlertSeverity.HIGH  # Above 0.1% target

        # Test no violation
        severity = slo_alerter._get_violation_severity("availability", 0.9995)
        assert severity is None

    def test_violation_severity_thresholds(self, slo_alerter):
        """Test violation severity thresholds"""
        config = slo_alerter.config

        # Check critical thresholds
        assert config.severity_thresholds["availability"][AlertSeverity.CRITICAL] == 0.995
        assert config.severity_thresholds["response_time_p95"][AlertSeverity.CRITICAL] == 1.0
        assert config.severity_thresholds["error_rate"][AlertSeverity.CRITICAL] == 0.01

    @pytest.mark.asyncio
    async def test_manual_slo_alert_trigger(self):
        """Test manual SLO alert triggering"""
        with patch("observability.slo_alerting.get_alert_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_manager.send_alert = AsyncMock(return_value=True)
            mock_get_manager.return_value = mock_manager

            success = await trigger_manual_slo_alert("availability", "1h", 0.99, AlertSeverity.HIGH)

            assert success is True
            mock_manager.send_alert.assert_called_once()

    def test_monitoring_status(self, slo_alerter):
        """Test SLO monitoring status"""
        status = slo_alerter.get_monitoring_status()

        assert "monitoring_active" in status
        assert "check_interval_seconds" in status
        assert "active_violations" in status
        assert "total_violation_states" in status
        assert status["monitoring_active"] is False


class TestMonitoringAutomation:
    """Test monitoring automation functionality"""

    @pytest.fixture
    def monitoring_automation(self):
        """Create monitoring automation instance"""
        automation = MonitoringAutomation()
        return automation

    def test_health_check_setup(self, monitoring_automation):
        """Test health check initialization"""
        assert len(monitoring_automation.health_checks) == 3
        assert any(isinstance(hc, DatabaseHealthCheck) for hc in monitoring_automation.health_checks)
        assert any(isinstance(hc, RedisHealthCheck) for hc in monitoring_automation.health_checks)
        assert any(isinstance(hc, SLOHealthCheck) for hc in monitoring_automation.health_checks)

    def test_recovery_procedure_setup(self, monitoring_automation):
        """Test recovery procedure initialization"""
        assert len(monitoring_automation.recovery_procedures) >= 2
        # Should have restart and cache clearing procedures

    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check"""
        with patch("observability.monitoring_automation.check_database") as mock_check_db:
            mock_check_db.return_value = {"connected": True, "pool_stats": {"active": 5, "total": 20}}

            hc = DatabaseHealthCheck()
            result = await hc.execute_check()

            assert result.component == "database"
            assert result.status in [HealthCheckStatus.HEALTHY, HealthCheckStatus.DEGRADED]
            assert result.metrics["connected"] is True

    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check"""
        with patch("observability.monitoring_automation.check_redis_memory_cache") as mock_check_redis:
            mock_check_redis.return_value = {
                "status": "healthy",
                "info": {"used_memory": 1000000, "connected_clients": 5},
                "hit_rate": 0.95,
            }

            hc = RedisHealthCheck()
            result = await hc.execute_check()

            assert result.component == "redis"
            assert result.status == HealthCheckStatus.HEALTHY
            assert result.metrics["hit_rate"] == 0.95

    @pytest.mark.asyncio
    async def test_slo_health_check(self):
        """Test SLO health check"""
        with patch("observability.monitoring_automation.get_slo_status") as mock_get_slo:
            mock_get_slo.return_value = {
                "overall_status": "healthy",
                "current": {"availability": 0.9995, "response_time_p95": 0.15, "error_rate": 0.0005},
            }

            hc = SLOHealthCheck()
            result = await hc.execute_check()

            assert result.component == "slo"
            assert result.status == HealthCheckStatus.HEALTHY

    def test_monitoring_status(self, monitoring_automation):
        """Test monitoring automation status"""
        status = monitoring_automation.get_monitoring_status()

        assert "monitoring_active" in status
        assert "health_checks" in status
        assert "recent_health_checks" in status
        assert "total_health_checks" in status
        assert len(status["health_checks"]) == 3

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, monitoring_automation):
        """Test monitoring start/stop lifecycle"""
        # Start monitoring
        await monitoring_automation.start_monitoring()
        assert monitoring_automation.running is True
        assert monitoring_automation.monitor_task is not None

        # Stop monitoring
        await monitoring_automation.stop_monitoring()
        assert monitoring_automation.running is False


class TestGrafanaDashboards:
    """Test Grafana dashboard generation"""

    @pytest.fixture
    def dashboard_builder(self):
        """Create dashboard builder"""
        return GrafanaDashboardBuilder()

    def test_slo_compliance_dashboard(self, dashboard_builder):
        """Test SLO compliance dashboard creation"""
        dashboard = dashboard_builder.create_slo_compliance_dashboard()

        assert dashboard["title"] == "Ninaivalaigal - SLO Compliance"
        assert "slo" in dashboard["tags"]
        assert "compliance" in dashboard["tags"]
        assert len(dashboard["panels"]) >= 5  # Should have multiple panels

        # Check for key panels
        panel_titles = [panel["title"] for panel in dashboard["panels"]]
        assert "Overall SLO Status" in panel_titles
        assert "Availability (1h)" in panel_titles
        assert "Response Time P95 (1h)" in panel_titles

    def test_system_health_dashboard(self, dashboard_builder):
        """Test system health dashboard creation"""
        dashboard = dashboard_builder.create_system_health_dashboard()

        assert dashboard["title"] == "Ninaivalaigal - System Health"
        assert "health" in dashboard["tags"]
        assert "infrastructure" in dashboard["tags"]
        assert len(dashboard["panels"]) >= 6

        # Check for key panels
        panel_titles = [panel["title"] for panel in dashboard["panels"]]
        assert "Service Status" in panel_titles
        assert "Request Rate" in panel_titles
        assert "Response Time" in panel_titles

    def test_performance_dashboard(self, dashboard_builder):
        """Test performance metrics dashboard"""
        dashboard = dashboard_builder.create_performance_dashboard()

        assert dashboard["title"] == "Ninaivalaigal - Performance Metrics"
        assert "performance" in dashboard["tags"]
        assert len(dashboard["panels"]) >= 6

    def test_alert_management_dashboard(self, dashboard_builder):
        """Test alert management dashboard"""
        dashboard = dashboard_builder.create_alert_management_dashboard()

        assert dashboard["title"] == "Ninaivalaigal - Alert Management"
        assert "alerts" in dashboard["tags"]
        assert len(dashboard["panels"]) >= 6

    def test_business_intelligence_dashboard(self, dashboard_builder):
        """Test business intelligence dashboard"""
        dashboard = dashboard_builder.create_business_intelligence_dashboard()

        assert dashboard["title"] == "Ninaivalaigal - Business Intelligence"
        assert "business" in dashboard["tags"]
        assert "kpi" in dashboard["tags"]
        assert len(dashboard["panels"]) >= 7

    def test_all_dashboards_collection(self):
        """Test getting all dashboards"""
        dashboards = get_all_dashboards()

        assert len(dashboards) == 5
        assert "slo-compliance" in dashboards
        assert "system-health" in dashboards
        assert "performance" in dashboards
        assert "alert-management" in dashboards
        assert "business-intelligence" in dashboards

        # Check all dashboards have required fields
        for name, dashboard in dashboards.items():
            assert "title" in dashboard
            assert "panels" in dashboard
            assert "tags" in dashboard
            assert "ninaivalaigal" in dashboard["tags"]


class TestAlertingConfiguration:
    """Test alerting configuration loading"""

    def test_load_empty_config(self):
        """Test loading configuration with no environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            config = load_alerting_config()

            assert config.pagerduty is None
            assert config.slack is None
            assert config.email is None
            assert config.webhook is None
            assert len(config.enabled_channels) == 0

    def test_load_slack_config(self):
        """Test loading Slack configuration"""
        env_vars = {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test",
            "SLACK_CHANNEL": "#alerts",
            "SLACK_MENTION_USERS": "user1,user2",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_alerting_config()

            assert config.slack is not None
            assert config.slack.webhook_url == "https://hooks.slack.com/test"
            assert config.slack.channel == "#alerts"
            assert len(config.slack.mention_users) == 2
            assert "slack" in [c.value for c in config.enabled_channels]

    def test_load_pagerduty_config(self):
        """Test loading PagerDuty configuration"""
        env_vars = {"PAGERDUTY_INTEGRATION_KEY": "test-key-123", "PAGERDUTY_SERVICE_ID": "service-456"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_alerting_config()

            assert config.pagerduty is not None
            assert config.pagerduty.integration_key == "test-key-123"
            assert config.pagerduty.service_id == "service-456"
            assert "pagerduty" in [c.value for c in config.enabled_channels]


class TestIntegration:
    """Integration tests for the complete monitoring system"""

    @pytest.mark.asyncio
    async def test_end_to_end_alert_flow(self):
        """Test complete alert flow from creation to resolution"""
        with patch.dict(os.environ, {}, clear=True):
            # Initialize alerting
            config = AlertingConfig()
            config.enabled_channels = []  # No external channels

            async with AlertManager(config) as alert_manager:
                # Create SLO alerter
                slo_alerter = SLOAlerter(alert_manager)

                # Simulate SLO violation
                alert = await slo_alerter._create_slo_alert("availability", "1h", 0.99, 0.999, AlertSeverity.MEDIUM)

                # Send alert
                success = await alert_manager.send_alert(alert)
                assert success is True

                # Check alert is active
                active_alerts = alert_manager.get_active_alerts()
                assert len(active_alerts) == 1
                assert active_alerts[0].severity == AlertSeverity.MEDIUM

                # Resolve alert
                await alert_manager.resolve_alert(alert.id)

                # Check alert is resolved
                active_alerts = alert_manager.get_active_alerts()
                assert len(active_alerts) == 0

    @pytest.mark.asyncio
    async def test_monitoring_with_health_checks(self):
        """Test monitoring automation with health checks"""
        with (
            patch("observability.monitoring_automation.check_database") as mock_db,
            patch("observability.monitoring_automation.check_redis_memory_cache") as mock_redis,
            patch("observability.monitoring_automation.get_slo_status") as mock_slo,
        ):

            # Setup mocks
            mock_db.return_value = {"connected": True, "pool_stats": {"active": 5, "total": 20}}
            mock_redis.return_value = {"status": "healthy", "info": {"used_memory": 1000000}, "hit_rate": 0.95}
            mock_slo.return_value = {"overall_status": "healthy", "current": {"availability": 0.9995}}

            # Create monitoring automation
            automation = MonitoringAutomation()

            # Execute health checks
            await automation._execute_health_checks()

            # Check results
            assert len(automation.health_history) == 3

            # All health checks should be healthy
            for result in automation.health_history:
                assert result.status in [HealthCheckStatus.HEALTHY, HealthCheckStatus.DEGRADED]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
