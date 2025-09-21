"""
Security Management API Endpoints

Provides endpoints for managing security configuration, viewing audit logs,
and monitoring security alerts.
"""

from datetime import datetime

from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from rbac.permissions import Action, Resource
from rbac_middleware import get_rbac_context, require_permission
from security.audit import AlertSeverity, security_alert_manager
from security.redaction.config import ContextSensitivity, redaction_config
from security_integration import security_manager

# Router for security endpoints
security_router = APIRouter(prefix="/security", tags=["security"])


class SecurityConfigUpdate(BaseModel):
    """Security configuration update model"""
    redaction_enabled: bool | None = None
    default_tier: str | None = None
    audit_enabled: bool | None = None
    min_entropy: float | None = None
    min_length: int | None = None


class AlertResolution(BaseModel):
    """Alert resolution model"""
    alert_id: str
    reason: str | None = None


@security_router.get("/status")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_security_status(request: Request, current_user: User = Depends(get_current_user)):
    """Get overall security system status"""
    try:
        status = security_manager.get_security_status()

        # Add alert statistics
        active_alerts = security_alert_manager.get_active_alerts()
        critical_alerts = security_alert_manager.get_active_alerts(AlertSeverity.CRITICAL)

        status.update({
            'active_alerts_count': len(active_alerts),
            'critical_alerts_count': len(critical_alerts),
            'recent_events_count': len(security_alert_manager.recent_events),
            'last_updated': datetime.utcnow().isoformat()
        })

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security status: {str(e)}")


@security_router.get("/config")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_security_config(request: Request, current_user: User = Depends(get_current_user)):
    """Get current security configuration"""
    try:
        config = {
            'redaction_enabled': redaction_config.enabled,
            'default_tier': redaction_config.default_tier.value,
            'audit_enabled': redaction_config.audit_enabled,
            'min_entropy': redaction_config.min_entropy,
            'min_length': redaction_config.min_length,
            'available_tiers': [tier.value for tier in ContextSensitivity],
            'tier_descriptions': {
                'public': 'No redaction - publicly shareable content',
                'internal': 'Light redaction - internal company use',
                'confidential': 'Moderate redaction - confidential information',
                'restricted': 'Heavy redaction - restricted access only',
                'secrets': 'Maximum redaction - secrets and credentials'
            }
        }

        return config

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security config: {str(e)}")


@security_router.put("/config")
@require_permission(Resource.SYSTEM, Action.ADMINISTER)
async def update_security_config(
    request: Request,
    config_update: SecurityConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update security configuration"""
    try:
        rbac_context = get_rbac_context(request)

        # Log admin action
        from security_integration import log_admin_action
        await log_admin_action(
            rbac_context,
            "update_security_config",
            "system:security_config",
            config_update.dict(exclude_none=True)
        )

        # Update configuration
        updated_fields = []

        if config_update.redaction_enabled is not None:
            redaction_config.enabled = config_update.redaction_enabled
            updated_fields.append("redaction_enabled")

        if config_update.default_tier is not None:
            try:
                redaction_config.default_tier = ContextSensitivity(config_update.default_tier)
                updated_fields.append("default_tier")
            except ValueError:
                raise HTTPException(400, f"Invalid tier: {config_update.default_tier}")

        if config_update.audit_enabled is not None:
            redaction_config.audit_enabled = config_update.audit_enabled
            updated_fields.append("audit_enabled")

        if config_update.min_entropy is not None:
            redaction_config.min_entropy = config_update.min_entropy
            updated_fields.append("min_entropy")

        if config_update.min_length is not None:
            redaction_config.min_length = config_update.min_length
            updated_fields.append("min_length")

        return {
            "success": True,
            "message": f"Security configuration updated: {', '.join(updated_fields)}",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update security config: {str(e)}")


@security_router.get("/alerts")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_security_alerts(
    request: Request,
    current_user: User = Depends(get_current_user),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    resolved: bool | None = Query(None, description="Filter by resolution status")
):
    """Get security alerts"""
    try:
        # Get all alerts
        if resolved is False:
            alerts = security_alert_manager.get_active_alerts()
        else:
            alerts = security_alert_manager.active_alerts

        # Filter by severity if specified
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
                alerts = [alert for alert in alerts if alert.severity == severity_filter]
            except ValueError:
                raise HTTPException(400, f"Invalid severity: {severity}")

        # Filter by resolution status if specified
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]

        # Limit results
        alerts = alerts[:limit]

        # Convert to dict format
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value,
                "event_type": alert.event_type.value,
                "title": alert.title,
                "message": alert.message,
                "user_id": alert.user_id,
                "context_id": alert.context_id,
                "metadata": alert.metadata,
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })

        return {
            "alerts": alert_data,
            "total_count": len(alert_data),
            "filters_applied": {
                "severity": severity,
                "resolved": resolved,
                "limit": limit
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security alerts: {str(e)}")


@security_router.post("/alerts/{alert_id}/resolve")
@require_permission(Resource.SYSTEM, Action.ADMINISTER)
async def resolve_security_alert(
    request: Request,
    alert_id: str,
    resolution: AlertResolution,
    current_user: User = Depends(get_current_user)
):
    """Resolve a security alert"""
    try:
        rbac_context = get_rbac_context(request)

        # Log admin action
        from security_integration import log_admin_action
        await log_admin_action(
            rbac_context,
            "resolve_security_alert",
            f"alert:{alert_id}",
            {"alert_id": alert_id, "reason": resolution.reason}
        )

        # Resolve the alert
        await security_alert_manager.resolve_alert(alert_id, current_user.id)

        return {
            "success": True,
            "message": f"Alert {alert_id} resolved successfully",
            "resolved_by": current_user.id,
            "resolved_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@security_router.get("/statistics")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_security_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
    hours: int = Query(24, description="Time period in hours")
):
    """Get security statistics for the specified time period"""
    try:
        if hours > 168:  # Limit to 1 week
            raise HTTPException(400, "Time period cannot exceed 168 hours (1 week)")

        stats = security_alert_manager.get_security_statistics(hours)

        return {
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat(),
            "time_period_hours": hours
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security statistics: {str(e)}")


@security_router.get("/audit/redaction")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_redaction_audit_logs(
    request: Request,
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, description="Maximum number of logs to return"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    context_id: int | None = Query(None, description="Filter by context ID"),
    tier: str | None = Query(None, description="Filter by sensitivity tier")
):
    """Get redaction audit logs"""
    try:
        # This would typically query the database for redaction audit logs
        # For now, return a placeholder response

        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if context_id:
            filters["context_id"] = context_id
        if tier:
            filters["sensitivity_tier"] = tier

        # In a real implementation, this would query the RedactionAudit table
        return {
            "audit_logs": [],  # Placeholder - would contain actual audit records
            "total_count": 0,
            "filters_applied": filters,
            "limit": limit,
            "message": "Redaction audit logs endpoint - database integration pending"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get redaction audit logs: {str(e)}")


@security_router.post("/test/redaction")
@require_permission(Resource.SYSTEM, Action.READ)
async def test_redaction(
    request: Request,
    test_text: str,
    tier: str | None = Query("internal", description="Sensitivity tier to test"),
    current_user: User = Depends(get_current_user)
):
    """Test redaction on sample text"""
    try:
        # Validate tier
        try:
            sensitivity_tier = ContextSensitivity(tier)
        except ValueError:
            raise HTTPException(400, f"Invalid tier: {tier}")

        # Apply redaction
        from security_integration import redact_text
        rbac_context = get_rbac_context(request)
        redacted_text = await redact_text(test_text, sensitivity_tier, rbac_context)

        return {
            "original_text": test_text,
            "redacted_text": redacted_text,
            "sensitivity_tier": tier,
            "redaction_applied": redacted_text != test_text,
            "original_length": len(test_text),
            "redacted_length": len(redacted_text)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test redaction: {str(e)}")
