#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Observability package for ninaivalaigal.

Provides comprehensive monitoring, alerting, and observability infrastructure
including SLO monitoring, health checks, metrics collection, and alerting.
"""

from .alerting import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertStatus,
    get_alert_manager,
    initialize_alerting,
)
from .grafana_dashboards import (
    GrafanaDashboardBuilder,
    export_dashboard_json,
    get_all_dashboards,
    save_dashboard_files,
)
from .health import router as health_router
from .memory_health import router as memory_health_router
from .metrics import MetricsMiddleware
from .metrics import router as metrics_router
from .monitoring_automation import (
    MonitoringAutomation,
    get_monitoring_automation,
    initialize_monitoring_automation,
    start_monitoring_automation,
    stop_monitoring_automation,
)
from .slo_alerting import (
    SLOAlerter,
    get_slo_alerter,
    initialize_slo_alerting,
    start_slo_monitoring,
    stop_slo_monitoring,
    trigger_manual_slo_alert,
)
from .slo_monitoring import get_slo_status, get_slo_summary, record_slo_request

__all__ = [
    # Routers
    "health_router",
    "metrics_router",
    "memory_health_router",
    # Middleware
    "MetricsMiddleware",
    # SLO Monitoring
    "get_slo_status",
    "get_slo_summary",
    "record_slo_request",
    # Alerting
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "initialize_alerting",
    "get_alert_manager",
    # SLO Alerting
    "SLOAlerter",
    "initialize_slo_alerting",
    "start_slo_monitoring",
    "stop_slo_monitoring",
    "get_slo_alerter",
    "trigger_manual_slo_alert",
    # Monitoring Automation
    "MonitoringAutomation",
    "initialize_monitoring_automation",
    "start_monitoring_automation",
    "stop_monitoring_automation",
    "get_monitoring_automation",
    # Grafana Dashboards
    "GrafanaDashboardBuilder",
    "get_all_dashboards",
    "export_dashboard_json",
    "save_dashboard_files",
]
