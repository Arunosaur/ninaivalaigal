"""
SPEC-020: Provider Management API Router
Complete provider management with security, health monitoring, and failover
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..auth_utils import get_current_user
from ..memory.failover_manager import OperationType, get_failover_manager
from ..memory.health_monitor import get_health_monitor
from ..memory.provider_registry import (
    ProviderConfig,
    ProviderType,
    get_provider_registry,
)
from ..memory.provider_security import (
    ProviderPermission,
    SecurityLevel,
    get_security_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/providers", tags=["memory-providers"])


class ProviderRegistrationRequest(BaseModel):
    name: str
    provider_type: str
    connection_string: str
    priority: int = 100
    security_level: str = "rbac"


class ProviderUpdateRequest(BaseModel):
    priority: Optional[int] = None
    enabled: Optional[bool] = None


@router.post("/register", status_code=201)
async def register_provider(
    request: ProviderRegistrationRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    registry=Depends(get_provider_registry),
    security_manager=Depends(get_security_manager),
):
    """Register a new memory provider with security validation"""
    try:
        config = ProviderConfig(
            name=request.name,
            provider_type=ProviderType(request.provider_type),
            connection_string=request.connection_string,
            priority=request.priority,
        )

        # Secure registration
        result = await security_manager.register_provider_securely(
            config=config,
            user_id=current_user["user_id"],
            security_level=SecurityLevel(request.security_level),
            source_ip=http_request.client.host,
        )

        # Register with registry
        from ..memory.providers.mem0_http import Mem0HttpMemoryProvider
        from ..memory.providers.postgres import PostgresMemoryProvider

        provider_classes = {
            ProviderType.POSTGRES: PostgresMemoryProvider,
            ProviderType.MEM0_HTTP: Mem0HttpMemoryProvider,
        }

        provider_class = provider_classes.get(config.provider_type)
        if provider_class:
            await registry.register_provider(config, provider_class)

        return result

    except Exception as e:
        logger.error(f"Provider registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_providers(
    current_user: dict = Depends(get_current_user),
    registry=Depends(get_provider_registry),
    health_monitor=Depends(get_health_monitor),
):
    """List all registered providers with health status"""
    try:
        providers = await registry.list_providers()
        health_data = await health_monitor.get_all_provider_health()

        # Combine provider info with health data
        for provider in providers:
            health = health_data.get(provider["name"])
            if health:
                provider["health_status"] = health.status.value
                provider["uptime_percentage"] = health.uptime_percentage
                provider["avg_response_time_ms"] = health.avg_response_time_ms

        return {"providers": providers}

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list providers")


@router.get("/{provider_name}/health")
async def get_provider_health(
    provider_name: str,
    current_user: dict = Depends(get_current_user),
    health_monitor=Depends(get_health_monitor),
):
    """Get detailed health information for a provider"""
    try:
        health = await health_monitor.get_provider_health(provider_name)
        if not health:
            raise HTTPException(status_code=404, detail="Provider not found")

        return {
            "provider_name": provider_name,
            "status": health.status.value,
            "uptime_percentage": health.uptime_percentage,
            "avg_response_time_ms": health.avg_response_time_ms,
            "error_rate": health.error_rate,
            "last_check": health.last_check.isoformat(),
            "consecutive_failures": health.consecutive_failures,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider health")


@router.get("/failover/statistics")
async def get_failover_statistics(
    current_user: dict = Depends(get_current_user),
    failover_manager=Depends(get_failover_manager),
):
    """Get failover and routing statistics"""
    try:
        stats = await failover_manager.get_failover_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get failover statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.post("/{provider_name}/failover")
async def trigger_failover(
    provider_name: str,
    current_user: dict = Depends(get_current_user),
    registry=Depends(get_provider_registry),
):
    """Manually trigger failover from a provider"""
    try:
        backup_provider = await registry.failover_to_backup(provider_name)

        if backup_provider:
            return {
                "message": f"Failover successful",
                "failed_provider": provider_name,
                "backup_provider": backup_provider,
            }
        else:
            raise HTTPException(status_code=503, detail="No backup providers available")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failover failed: {e}")
        raise HTTPException(status_code=500, detail="Failover failed")


@router.get("/security/audit")
async def get_security_audit_logs(
    provider_name: Optional[str] = None,
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    security_manager=Depends(get_security_manager),
):
    """Get security audit logs (admin only)"""
    try:
        logs = await security_manager.get_security_audit_logs(
            provider_name=provider_name,
            hours=hours,
            admin_user_id=current_user["user_id"],
        )

        return {"audit_logs": logs}

    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")


@router.get("/health")
async def providers_health_check(
    registry=Depends(get_provider_registry), health_monitor=Depends(get_health_monitor)
):
    """Overall provider system health check"""
    try:
        providers = await registry.list_providers()
        health_data = await health_monitor.get_all_provider_health()

        total_providers = len(providers)
        healthy_providers = sum(
            1
            for name, health in health_data.items()
            if health.status.value == "healthy"
        )

        overall_status = (
            "healthy" if healthy_providers == total_providers else "degraded"
        )
        if healthy_providers == 0:
            overall_status = "critical"

        return {
            "status": overall_status,
            "total_providers": total_providers,
            "healthy_providers": healthy_providers,
            "provider_health": {
                name: health.status.value for name, health in health_data.items()
            },
        }

    except Exception as e:
        logger.error(f"Provider health check failed: {e}")
        raise HTTPException(status_code=503, detail="Provider health check failed")
