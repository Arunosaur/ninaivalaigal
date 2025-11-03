#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Monitoring and Alerting API

Provides REST endpoints for monitoring infrastructure,
managing alerts, and accessing SLO metrics.

Endpoints:
- GET /monitoring/health - System health status
- GET /monitoring/slo - SLO metrics and compliance
- GET /monitoring/alerts - Active alerts management
- POST /monitoring/alerts/{id}/resolve - Resolve alert
- GET /monitoring/dashboards - Grafana dashboard configs
- GET /monitoring/status - Monitoring system status
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from ..observability.alerting import Alert, AlertStatus, get_alert_manager
from ..observability.grafana_dashboards import get_all_dashboards
from ..observability.monitoring_automation import get_monitoring_automation
from ..observability.slo_alerting import get_slo_alerter, trigger_manual_slo_alert
from ..observability.slo_monitoring import get_slo_status, get_slo_summary

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Response Models
class HealthCheckResponse(BaseModel):
    """Health check response model"""

    component: str = Field(description="Component name")
    status: str = Field(description="Health status")
    message: str = Field(description="Status message")
    metrics: Dict[str, Any] = Field(description="Component metrics")
    timestamp: datetime = Field(description="Check timestamp")
    duration_ms: float = Field(description="Check duration in milliseconds")


class SystemHealthResponse(BaseModel):
    """System health response model"""

    overall_status: str = Field(description="Overall system status")
    components: List[HealthCheckResponse] = Field(description="Component health status")
    timestamp: datetime = Field(description="Response timestamp")
    uptime_seconds: int = Field(description="System uptime in seconds")


class SLOMetricsResponse(BaseModel):
    """SLO metrics response model"""

    window: str = Field(description="Time window")
    targets: Dict[str, float] = Field(description="SLO targets")
    current: Dict[str, float] = Field(description="Current metrics")
    compliance: Dict[str, bool] = Field(description="Compliance status")
    overall_status: str = Field(description="Overall SLO status")
    timestamp: datetime = Field(description="Metrics timestamp")


class AlertResponse(BaseModel):
    """Alert response model"""

    id: str = Field(description="Alert ID")
    name: str = Field(description="Alert name")
    severity: str = Field(description="Alert severity")
    status: str = Field(description="Alert status")
    message: str = Field(description="Alert message")
    source: str = Field(description="Alert source")
    timestamp: datetime = Field(description="Alert timestamp")
    resolved_at: Optional[datetime] = Field(description="Resolution timestamp")
    tags: Dict[str, str] = Field(description="Alert tags")


class DashboardInfo(BaseModel):
    """Dashboard information model"""

    name: str = Field(description="Dashboard name")
    title: str = Field(description="Dashboard title")
    description: str = Field(description="Dashboard description")
    tags: List[str] = Field(description="Dashboard tags")
    panel_count: int = Field(description="Number of panels")


class MonitoringStatusResponse(BaseModel):
    """Monitoring system status response"""

    monitoring_active: bool = Field(description="Monitoring automation status")
    slo_monitoring_active: bool = Field(description="SLO monitoring status")
    alerting_enabled: bool = Field(description="Alerting system status")
    health_checks: List[Dict[str, Any]] = Field(description="Health check status")
    active_alerts_count: int = Field(description="Number of active alerts")
    last_check: datetime = Field(description="Last system check")


# API Endpoints
@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get comprehensive system health status"""
    try:
        monitoring = get_monitoring_automation()

        if not monitoring:
            # Return basic health if monitoring not initialized
            return SystemHealthResponse(
                overall_status="unknown", components=[], timestamp=datetime.utcnow(), uptime_seconds=0
            )

        # Get monitoring status
        status = monitoring.get_monitoring_status()

        # Build component health list
        components = []
        for hc_status in status["health_checks"]:
            components.append(
                HealthCheckResponse(
                    component=hc_status["name"],
                    status=hc_status["last_status"] or "unknown",
                    message=f"Last check: {hc_status['last_check'] or 'Never'}",
                    metrics={"consecutive_failures": hc_status["consecutive_failures"]},
                    timestamp=(
                        datetime.fromisoformat(hc_status["last_check"])
                        if hc_status["last_check"]
                        else datetime.utcnow()
                    ),
                    duration_ms=0,
                )
            )

        # Determine overall status
        overall_status = "healthy"
        for component in components:
            if component.status in ["unhealthy", "unknown"]:
                overall_status = "unhealthy"
                break
            elif component.status == "degraded":
                overall_status = "degraded"

        return SystemHealthResponse(
            overall_status=overall_status,
            components=components,
            timestamp=datetime.utcnow(),
            uptime_seconds=0,  # TODO: Implement uptime tracking
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/slo", response_model=SLOMetricsResponse)
async def get_slo_metrics(window: str = Query(default="1h", regex="^(1h|24h|7d)$")):
    """Get SLO metrics and compliance status"""
    try:
        slo_status = get_slo_status(window)

        if "error" in slo_status:
            raise HTTPException(status_code=500, detail=slo_status["error"])

        return SLOMetricsResponse(
            window=slo_status["window"],
            targets=slo_status["targets"],
            current=slo_status["current"],
            compliance=slo_status["compliance"],
            overall_status=slo_status["overall_status"],
            timestamp=datetime.fromisoformat(slo_status["timestamp"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLO metrics: {str(e)}")


@router.get("/slo/summary")
async def get_slo_metrics_summary():
    """Get SLO metrics summary for all windows"""
    try:
        summary = get_slo_summary()
        return {"summary": summary, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLO summary: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(severity: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    """Get active alerts with optional filtering"""
    try:
        alert_manager = get_alert_manager()

        if not alert_manager:
            raise HTTPException(status_code=503, detail="Alert manager not available")

        alerts = alert_manager.get_active_alerts()

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]

        if status:
            alerts = [a for a in alerts if a.status.value == status]

        # Convert to response model
        alert_responses = []
        for alert in alerts:
            alert_responses.append(
                AlertResponse(
                    id=alert.id,
                    name=alert.name,
                    severity=alert.severity.value,
                    status=alert.status.value,
                    message=alert.message,
                    source=alert.source,
                    timestamp=alert.timestamp,
                    resolved_at=alert.resolved_at,
                    tags=alert.tags,
                )
            )

        return alert_responses

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, background_tasks: BackgroundTasks):
    """Resolve an active alert"""
    try:
        alert_manager = get_alert_manager()

        if not alert_manager:
            raise HTTPException(status_code=503, detail="Alert manager not available")

        # Resolve alert in background
        background_tasks.add_task(alert_manager.resolve_alert, alert_id, "api-request")

        return {"message": f"Alert {alert_id} resolution initiated", "alert_id": alert_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get("/alerts/stats")
async def get_alert_statistics():
    """Get alert statistics"""
    try:
        alert_manager = get_alert_manager()

        if not alert_manager:
            raise HTTPException(status_code=503, detail="Alert manager not available")

        stats = alert_manager.get_alert_stats()
        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")


@router.post("/slo/alert/trigger")
async def trigger_slo_alert(
    metric_name: str = Query(..., regex="^(availability|response_time_p95|error_rate)$"),
    window: str = Query(default="1h", regex="^(1h|24h)$"),
    current_value: float = Query(...),
    severity: str = Query(default="high", regex="^(critical|high|medium|low)$"),
):
    """Manually trigger an SLO alert (for testing)"""
    try:
        from ..observability.alerting import AlertSeverity

        severity_enum = AlertSeverity(severity)

        success = await trigger_manual_slo_alert(metric_name, window, current_value, severity_enum)

        if success:
            return {"message": "SLO alert triggered successfully", "alert_id": "manual-trigger"}
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger SLO alert")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger SLO alert: {str(e)}")


@router.get("/dashboards", response_model=List[DashboardInfo])
async def get_available_dashboards():
    """Get list of available Grafana dashboards"""
    try:
        dashboards = get_all_dashboards()

        dashboard_list = []
        for name, config in dashboards.items():
            dashboard_list.append(
                DashboardInfo(
                    name=name,
                    title=config["title"],
                    description=config.get("description", ""),
                    tags=config.get("tags", []),
                    panel_count=len(config.get("panels", [])),
                )
            )

        return dashboard_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboards: {str(e)}")


@router.get("/dashboards/{dashboard_name}")
async def get_dashboard_json(dashboard_name: str):
    """Get Grafana dashboard JSON configuration"""
    try:
        dashboards = get_all_dashboards()

        if dashboard_name not in dashboards:
            raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' not found")

        return dashboards[dashboard_name]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status():
    """Get monitoring system status"""
    try:
        monitoring = get_monitoring_automation()
        slo_alerter_instance = get_slo_alerter()
        alert_manager = get_alert_manager()

        # Get monitoring automation status
        monitoring_status = {}
        health_checks = []

        if monitoring:
            monitoring_status = monitoring.get_monitoring_status()
            health_checks = monitoring_status.get("health_checks", [])

        # Get alert count
        active_alerts_count = 0
        if alert_manager:
            stats = alert_manager.get_alert_stats()
            active_alerts_count = stats.get("active_alerts", 0)

        return MonitoringStatusResponse(
            monitoring_active=monitoring_status.get("monitoring_active", False),
            slo_monitoring_active=slo_alerter_instance is not None,
            alerting_enabled=alert_manager is not None,
            health_checks=health_checks,
            active_alerts_count=active_alerts_count,
            last_check=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring_system(background_tasks: BackgroundTasks):
    """Start the monitoring automation system"""
    try:
        from ..observability.monitoring_automation import start_monitoring_automation
        from ..observability.slo_alerting import start_slo_monitoring

        # Start monitoring in background
        background_tasks.add_task(start_monitoring_automation)
        background_tasks.add_task(start_slo_monitoring)

        return {"message": "Monitoring system startup initiated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring_system(background_tasks: BackgroundTasks):
    """Stop the monitoring automation system"""
    try:
        from ..observability.monitoring_automation import stop_monitoring_automation
        from ..observability.slo_alerting import stop_slo_monitoring

        # Stop monitoring in background
        background_tasks.add_task(stop_monitoring_automation)
        background_tasks.add_task(stop_slo_monitoring)

        return {"message": "Monitoring system shutdown initiated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


# Health check endpoints for load balancers
@router.get("/health/simple")
async def get_simple_health():
    """Simple health check for load balancers"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def get_readiness_status():
    """Readiness check for Kubernetes"""
    try:
        # Check critical components
        monitoring = get_monitoring_automation()
        alert_manager = get_alert_manager()

        if monitoring and alert_manager:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}

    except Exception:
        return {"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}


@router.get("/live")
async def get_liveness_status():
    """Liveness check for Kubernetes"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
