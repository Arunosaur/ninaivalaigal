#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Grafana Dashboard Configuration

Provides pre-configured Grafana dashboards for monitoring ninaivalaigal
infrastructure, SLO compliance, and system health.

Features:
- SLO Compliance Dashboard
- System Health Dashboard
- Performance Metrics Dashboard
- Alert Management Dashboard
- Business Intelligence Dashboard
"""

import json
from datetime import datetime
from typing import Any, Dict, List


class GrafanaDashboardBuilder:
    """Builds Grafana dashboard configurations"""

    def __init__(self):
        self.dashboard_defaults = {
            "id": None,
            "title": "",
            "tags": ["ninaivalaigal"],
            "timezone": "browser",
            "panels": [],
            "time": {"from": "now-1h", "to": "now"},
            "refresh": "30s",
            "schemaVersion": 37,
            "version": 1,
            "editable": True,
            "gnetId": None,
            "graphTooltip": 0,
            "links": [],
        }

    def create_slo_compliance_dashboard(self) -> Dict[str, Any]:
        """Create SLO compliance monitoring dashboard"""
        dashboard = self.dashboard_defaults.copy()
        dashboard.update(
            {
                "title": "Ninaivalaigal - SLO Compliance",
                "description": "Service Level Objective compliance monitoring",
                "tags": ["ninaivalaigal", "slo", "compliance"],
                "panels": [
                    # Overall SLO Status
                    {
                        "id": 1,
                        "title": "Overall SLO Status",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": 'slo_overall_status{job="ninaivalaigal"}',
                                "legendFormat": "{{window}}",
                                "refId": "A",
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": 0},
                                        {"color": "yellow", "value": 0.5},
                                        {"color": "green", "value": 1},
                                    ]
                                },
                                "mappings": [
                                    {"options": {"0": {"text": "DEGRADED", "color": "red"}}},
                                    {"options": {"1": {"text": "HEALTHY", "color": "green"}}},
                                ],
                            }
                        },
                    },
                    # Availability Gauge
                    {
                        "id": 2,
                        "title": "Availability (1h)",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                        "targets": [{"expr": 'slo_availability{job="ninaivalaigal",window="1h"}', "refId": "A"}],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "min": 0,
                                "max": 1,
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": 0},
                                        {"color": "yellow", "value": 0.995},
                                        {"color": "green", "value": 0.999},
                                    ]
                                },
                            }
                        },
                    },
                    # Response Time P95
                    {
                        "id": 3,
                        "title": "Response Time P95 (1h)",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                        "targets": [{"expr": 'slo_response_time_p95{job="ninaivalaigal",window="1h"}', "refId": "A"}],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "s",
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 0.1},
                                        {"color": "red", "value": 0.2},
                                    ]
                                },
                            }
                        },
                    },
                    # Error Rate
                    {
                        "id": 4,
                        "title": "Error Rate (1h)",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
                        "targets": [{"expr": 'slo_error_rate{job="ninaivalaigal",window="1h"}', "refId": "A"}],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 0.0005},
                                        {"color": "red", "value": 0.001},
                                    ]
                                },
                            }
                        },
                    },
                    # SLO Trends
                    {
                        "id": 5,
                        "title": "SLO Trends (24h)",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 8},
                        "targets": [
                            {
                                "expr": 'slo_availability{job="ninaivalaigal",window="24h"}',
                                "legendFormat": "Availability",
                                "refId": "A",
                            },
                            {
                                "expr": 'slo_response_time_p95{job="ninaivalaigal",window="24h"}',
                                "legendFormat": "Response Time P95",
                                "refId": "B",
                            },
                            {
                                "expr": 'slo_error_rate{job="ninaivalaigal",window="24h"}',
                                "legendFormat": "Error Rate",
                                "refId": "C",
                            },
                        ],
                        "fieldConfig": {"defaults": {"unit": "short"}},
                    },
                ],
            }
        )

        return dashboard

    def create_system_health_dashboard(self) -> Dict[str, Any]:
        """Create system health monitoring dashboard"""
        dashboard = self.dashboard_defaults.copy()
        dashboard.update(
            {
                "title": "Ninaivalaigal - System Health",
                "description": "Overall system health and component status",
                "tags": ["ninaivalaigal", "health", "infrastructure"],
                "panels": [
                    # Service Status
                    {
                        "id": 1,
                        "title": "Service Status",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                        "targets": [{"expr": 'up{job="ninaivalaigal"}', "legendFormat": "{{instance}}", "refId": "A"}],
                        "fieldConfig": {
                            "defaults": {
                                "mappings": [
                                    {"options": {"0": {"text": "DOWN", "color": "red"}}},
                                    {"options": {"1": {"text": "UP", "color": "green"}}},
                                ]
                            }
                        },
                    },
                    # Request Rate
                    {
                        "id": 2,
                        "title": "Request Rate",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{job="ninaivalaigal"}[5m])',
                                "legendFormat": "{{method}} {{route}}",
                                "refId": "A",
                            }
                        ],
                    },
                    # Response Time
                    {
                        "id": 3,
                        "title": "Response Time",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
                        "targets": [
                            {
                                "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="ninaivalaigal"}[5m]))',
                                "legendFormat": "P95",
                                "refId": "A",
                            },
                            {
                                "expr": 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job="ninaivalaigal"}[5m]))',
                                "legendFormat": "P50",
                                "refId": "B",
                            },
                        ],
                    },
                    # Database Health
                    {
                        "id": 4,
                        "title": "Database Connections",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6},
                        "targets": [
                            {
                                "expr": 'pg_stat_database_numbackends{job="ninaivalaigal"}',
                                "legendFormat": "Connections",
                                "refId": "A",
                            }
                        ],
                    },
                    # Redis Health
                    {
                        "id": 5,
                        "title": "Redis Operations",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 6},
                        "targets": [
                            {
                                "expr": 'rate(redis_commands_total{job="ninaivalaigal"}[5m])',
                                "legendFormat": "Commands/sec",
                                "refId": "A",
                            }
                        ],
                    },
                    # Error Rate
                    {
                        "id": 6,
                        "title": "Error Rate by Endpoint",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12},
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{job="ninaivalaigal",code=~"5.."}[5m]) / rate(http_requests_total{job="ninaivalaigal"}[5m])',
                                "legendFormat": "{{route}}",
                                "refId": "A",
                            }
                        ],
                        "fieldConfig": {"defaults": {"unit": "percentunit"}},
                    },
                ],
            }
        )

        return dashboard

    def create_performance_dashboard(self) -> Dict[str, Any]:
        """Create performance metrics dashboard"""
        dashboard = self.dashboard_defaults.copy()
        dashboard.update(
            {
                "title": "Ninaivalaigal - Performance Metrics",
                "description": "Detailed performance monitoring and analysis",
                "tags": ["ninaivalaigal", "performance", "metrics"],
                "panels": [
                    # Response Time Distribution
                    {
                        "id": 1,
                        "title": "Response Time Distribution",
                        "type": "heatmap",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": 'rate(http_request_duration_seconds_bucket{job="ninaivalaigal"}[5m])',
                                "legendFormat": "{{le}}",
                                "refId": "A",
                            }
                        ],
                    },
                    # Top Slow Endpoints
                    {
                        "id": 2,
                        "title": "Top Slow Endpoints (P95)",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="ninaivalaigal"}[5m]))',
                                "legendFormat": "{{route}}",
                                "refId": "A",
                                "format": "table",
                            }
                        ],
                    },
                    # Memory Usage
                    {
                        "id": 3,
                        "title": "Memory Usage",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": 'process_resident_memory_bytes{job="ninaivalaigal"}',
                                "legendFormat": "RSS",
                                "refId": "A",
                            }
                        ],
                    },
                    # CPU Usage
                    {
                        "id": 4,
                        "title": "CPU Usage",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": 'rate(process_cpu_seconds_total{job="ninaivalaigal"}[5m])',
                                "legendFormat": "CPU",
                                "refId": "A",
                            }
                        ],
                    },
                    # Cache Hit Rates
                    {
                        "id": 5,
                        "title": "Cache Hit Rates",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 14},
                        "targets": [
                            {
                                "expr": 'redis_cache_hit_rate{job="ninaivalaigal"}',
                                "legendFormat": "{{cache_type}}",
                                "refId": "A",
                            }
                        ],
                        "fieldConfig": {"defaults": {"unit": "percentunit"}},
                    },
                    # Concurrent Requests
                    {
                        "id": 6,
                        "title": "Concurrent Requests",
                        "type": "graph",
                        "gridPos": {"h": 6, "w": 16, "x": 8, "y": 14},
                        "targets": [
                            {
                                "expr": 'http_requests_in_flight{job="ninaivalaigal"}',
                                "legendFormat": "{{endpoint}}",
                                "refId": "A",
                            }
                        ],
                    },
                ],
            }
        )

        return dashboard

    def create_alert_management_dashboard(self) -> Dict[str, Any]:
        """Create alert management dashboard"""
        dashboard = self.dashboard_defaults.copy()
        dashboard.update(
            {
                "title": "Ninaivalaigal - Alert Management",
                "description": "Alert status and management interface",
                "tags": ["ninaivalaigal", "alerts", "incidents"],
                "panels": [
                    # Active Alerts
                    {
                        "id": 1,
                        "title": "Active Alerts",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": 'alertmanager_alerts{job="ninaivalaigal"}',
                                "legendFormat": "{{alertname}} - {{severity}}",
                                "refId": "A",
                                "format": "table",
                            }
                        ],
                    },
                    # Alert Rate
                    {
                        "id": 2,
                        "title": "Alert Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": 'rate(alertmanager_alerts_total{job="ninaivalaigal"}[5m])',
                                "legendFormat": "{{severity}}",
                                "refId": "A",
                            }
                        ],
                    },
                    # SLO Violations
                    {
                        "id": 3,
                        "title": "SLO Violations",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": 'slo_violations_total{job="ninaivalaigal"}',
                                "legendFormat": "{{metric_name}}",
                                "refId": "A",
                            }
                        ],
                    },
                    # Mean Time to Resolution
                    {
                        "id": 4,
                        "title": "MTTR (Hours)",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 6, "y": 8},
                        "targets": [
                            {
                                "expr": 'alertmanager_mean_time_to_resolution_seconds{job="ninaivalaigal"} / 3600',
                                "legendFormat": "MTTR",
                                "refId": "A",
                            }
                        ],
                    },
                    # Alert Severity Distribution
                    {
                        "id": 5,
                        "title": "Alert Severity Distribution",
                        "type": "piechart",
                        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": 'count by (severity) (alertmanager_alerts{job="ninaivalaigal"})',
                                "legendFormat": "{{severity}}",
                                "refId": "A",
                            }
                        ],
                    },
                    # Recent Incidents
                    {
                        "id": 6,
                        "title": "Recent Incidents (24h)",
                        "type": "table",
                        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 14},
                        "targets": [
                            {
                                "expr": 'alertmanager_alerts{job="ninaivalaigal"}',
                                "legendFormat": "{{alertname}}",
                                "refId": "A",
                                "format": "table",
                            }
                        ],
                    },
                ],
            }
        )

        return dashboard

    def create_business_intelligence_dashboard(self) -> Dict[str, Any]:
        """Create business intelligence dashboard"""
        dashboard = self.dashboard_defaults.copy()
        dashboard.update(
            {
                "title": "Ninaivalaigal - Business Intelligence",
                "description": "Business metrics and KPIs",
                "tags": ["ninaivalaigal", "business", "kpi"],
                "panels": [
                    # Active Users
                    {
                        "id": 1,
                        "title": "Active Users (24h)",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
                        "targets": [{"expr": 'active_users_total{job="ninaivalaigal"}', "refId": "A"}],
                    },
                    # New Signups
                    {
                        "id": 2,
                        "title": "New Signups (24h)",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 6, "y": 0},
                        "targets": [{"expr": 'increase(user_signups_total{job="ninaivalaigal"}[24h])', "refId": "A"}],
                    },
                    # Memory Operations
                    {
                        "id": 3,
                        "title": "Memory Operations (24h)",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0},
                        "targets": [
                            {"expr": 'increase(memory_operations_total{job="ninaivalaigal"}[24h])', "refId": "A"}
                        ],
                    },
                    # Team Activity
                    {
                        "id": 4,
                        "title": "Active Teams (24h)",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0},
                        "targets": [{"expr": 'active_teams_total{job="ninaivalaigal"}', "refId": "A"}],
                    },
                    # User Growth
                    {
                        "id": 5,
                        "title": "User Growth (30d)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
                        "targets": [
                            {
                                "expr": 'increase(user_signups_total{job="ninaivalaigal"}[30d])',
                                "legendFormat": "New Users",
                                "refId": "A",
                            }
                        ],
                    },
                    # Memory Usage Trends
                    {
                        "id": 6,
                        "title": "Memory Usage Trends (30d)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
                        "targets": [
                            {
                                "expr": 'increase(memory_operations_total{job="ninaivalaigal"}[30d])',
                                "legendFormat": "Memory Operations",
                                "refId": "A",
                            }
                        ],
                    },
                    # Top Teams by Activity
                    {
                        "id": 7,
                        "title": "Top Teams by Activity",
                        "type": "table",
                        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 14},
                        "targets": [
                            {
                                "expr": 'topk(10, team_activity_total{job="ninaivalaigal"})',
                                "legendFormat": "{{team_name}}",
                                "refId": "A",
                                "format": "table",
                            }
                        ],
                    },
                ],
            }
        )

        return dashboard


def get_all_dashboards() -> Dict[str, Dict[str, Any]]:
    """Get all configured dashboards"""
    builder = GrafanaDashboardBuilder()

    return {
        "slo-compliance": builder.create_slo_compliance_dashboard(),
        "system-health": builder.create_system_health_dashboard(),
        "performance": builder.create_performance_dashboard(),
        "alert-management": builder.create_alert_management_dashboard(),
        "business-intelligence": builder.create_business_intelligence_dashboard(),
    }


def export_dashboard_json(dashboard_name: str) -> str:
    """Export dashboard as JSON string"""
    dashboards = get_all_dashboards()

    if dashboard_name not in dashboards:
        raise ValueError(f"Unknown dashboard: {dashboard_name}")

    return json.dumps(dashboards[dashboard_name], indent=2)


def save_dashboard_files(output_dir: str = "/tmp/grafana-dashboards"):
    """Save all dashboards to JSON files"""
    import os

    os.makedirs(output_dir, exist_ok=True)

    dashboards = get_all_dashboards()

    for name, dashboard in dashboards.items():
        filename = f"{output_dir}/ninaivalaigal-{name}.json"

        with open(filename, "w") as f:
            json.dump(dashboard, f, indent=2)

        print(f"✅ Saved dashboard: {filename}")

    print(f"\n📊 Saved {len(dashboards)} dashboards to {output_dir}")


# Example usage and configuration
if __name__ == "__main__":
    # Save all dashboards
    save_dashboard_files()

    # Export specific dashboard
    slo_dashboard = export_dashboard_json("slo-compliance")
    print(f"\n🎯 SLO Dashboard JSON Preview:")
    print(slo_dashboard[:500] + "...")
