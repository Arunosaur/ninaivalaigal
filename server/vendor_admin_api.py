"""
SPEC-025: Vendor Admin Console (Medhasys Control Panel)
Multi-tenant management, usage analytics, rate limiting, and audit logging
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from auth import get_current_user, require_admin_role
from database.operations import DatabaseOperations, get_db
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/vendor/admin", tags=["vendor_admin"])


# Request/Response Models
class TenantInfo(BaseModel):
    tenant_id: str
    organization_name: str
    subscription_tier: str
    created_at: datetime
    last_active: datetime
    total_users: int
    total_memories: int
    storage_used_mb: float
    api_calls_today: int
    status: str  # active, suspended, trial


class UsageMetrics(BaseModel):
    tenant_id: str
    date: str
    api_calls: int
    memory_operations: int
    storage_mb: float
    active_users: int
    response_time_p95: float


class RateLimitConfig(BaseModel):
    tenant_id: str
    api_calls_per_minute: int
    memory_operations_per_hour: int
    storage_limit_gb: float
    user_limit: int


class AdminAuditLog(BaseModel):
    log_id: str
    admin_user_id: str
    action: str
    target_tenant_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: str


class SystemHealthMetrics(BaseModel):
    total_tenants: int
    active_tenants_24h: int
    total_api_calls_24h: int
    average_response_time: float
    error_rate_percent: float
    storage_usage_gb: float
    revenue_metrics: Dict[str, float]


# Vendor Admin Dashboard Endpoints
@router.get("/dashboard/overview")
async def get_admin_dashboard_overview(
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> SystemHealthMetrics:
    """
    Get high-level system overview for vendor admin dashboard.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Get system-wide metrics
        total_tenants = await db.get_total_tenant_count()
        active_tenants = await db.get_active_tenants_count(hours=24)
        api_calls = await db.get_api_calls_count(hours=24)
        avg_response_time = await db.get_average_response_time(hours=24)
        error_rate = await db.get_error_rate_percent(hours=24)
        storage_usage = await db.get_total_storage_usage_gb()

        # Calculate revenue metrics (placeholder for billing integration)
        revenue_metrics = {
            "mrr": 0.0,  # Monthly Recurring Revenue
            "arr": 0.0,  # Annual Recurring Revenue
            "churn_rate": 0.0,
            "ltv": 0.0,  # Lifetime Value
        }

        return SystemHealthMetrics(
            total_tenants=total_tenants,
            active_tenants_24h=active_tenants,
            total_api_calls_24h=api_calls,
            average_response_time=avg_response_time,
            error_rate_percent=error_rate,
            storage_usage_gb=storage_usage,
            revenue_metrics=revenue_metrics,
        )

    except Exception as e:
        logger.error("Failed to get admin dashboard overview", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/tenants")
async def list_all_tenants(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, Any]:
    """
    List all tenants with pagination and filtering.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        offset = (page - 1) * limit

        tenants_data = await db.get_tenants_with_metrics(
            offset=offset, limit=limit, status_filter=status_filter
        )

        tenants = []
        for tenant_data in tenants_data:
            tenant = TenantInfo(
                tenant_id=tenant_data["tenant_id"],
                organization_name=tenant_data["organization_name"],
                subscription_tier=tenant_data["subscription_tier"],
                created_at=tenant_data["created_at"],
                last_active=tenant_data["last_active"],
                total_users=tenant_data["total_users"],
                total_memories=tenant_data["total_memories"],
                storage_used_mb=tenant_data["storage_used_mb"],
                api_calls_today=tenant_data["api_calls_today"],
                status=tenant_data["status"],
            )
            tenants.append(tenant)

        total_count = await db.get_total_tenant_count(status_filter=status_filter)

        return {
            "tenants": tenants,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
            },
        }

    except Exception as e:
        logger.error("Failed to list tenants", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tenants")


@router.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage_analytics(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> List[UsageMetrics]:
    """
    Get detailed usage analytics for a specific tenant.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Verify tenant exists
        tenant = await db.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Get usage data for the specified period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        usage_data = await db.get_tenant_usage_metrics(
            tenant_id=tenant_id, start_date=start_date, end_date=end_date
        )

        metrics = []
        for data in usage_data:
            metric = UsageMetrics(
                tenant_id=tenant_id,
                date=data["date"].isoformat(),
                api_calls=data["api_calls"],
                memory_operations=data["memory_operations"],
                storage_mb=data["storage_mb"],
                active_users=data["active_users"],
                response_time_p95=data["response_time_p95"],
            )
            metrics.append(metric)

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get tenant usage analytics", tenant_id=tenant_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve usage analytics"
        )


@router.get("/tenants/{tenant_id}/rate-limits")
async def get_tenant_rate_limits(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> RateLimitConfig:
    """
    Get current rate limit configuration for a tenant.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Verify tenant exists
        tenant = await db.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        rate_limits = await db.get_tenant_rate_limits(tenant_id)

        return RateLimitConfig(
            tenant_id=tenant_id,
            api_calls_per_minute=rate_limits["api_calls_per_minute"],
            memory_operations_per_hour=rate_limits["memory_operations_per_hour"],
            storage_limit_gb=rate_limits["storage_limit_gb"],
            user_limit=rate_limits["user_limit"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get tenant rate limits", tenant_id=tenant_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limits")


@router.put("/tenants/{tenant_id}/rate-limits")
async def update_tenant_rate_limits(
    tenant_id: str,
    rate_config: RateLimitConfig,
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, str]:
    """
    Update rate limit configuration for a tenant.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Verify tenant exists
        tenant = await db.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Update rate limits
        await db.update_tenant_rate_limits(
            tenant_id=tenant_id,
            api_calls_per_minute=rate_config.api_calls_per_minute,
            memory_operations_per_hour=rate_config.memory_operations_per_hour,
            storage_limit_gb=rate_config.storage_limit_gb,
            user_limit=rate_config.user_limit,
        )

        # Log admin action
        await db.log_admin_action(
            admin_user_id=current_user["user_id"],
            action="update_rate_limits",
            target_tenant_id=tenant_id,
            details=rate_config.dict(),
            ip_address=getattr(current_user, "ip_address", "unknown"),
        )

        logger.info(
            "Rate limits updated for tenant",
            tenant_id=tenant_id,
            admin_user=current_user["user_id"],
        )

        return {"status": "success", "message": "Rate limits updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update tenant rate limits", tenant_id=tenant_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to update rate limits")


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, str]:
    """
    Suspend a tenant (disable access while preserving data).
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Verify tenant exists and is not already suspended
        tenant = await db.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        if tenant["status"] == "suspended":
            raise HTTPException(status_code=400, detail="Tenant is already suspended")

        # Suspend tenant
        await db.update_tenant_status(tenant_id, "suspended")

        # Log admin action
        await db.log_admin_action(
            admin_user_id=current_user["user_id"],
            action="suspend_tenant",
            target_tenant_id=tenant_id,
            details={"reason": reason},
            ip_address=getattr(current_user, "ip_address", "unknown"),
        )

        logger.warning(
            "Tenant suspended",
            tenant_id=tenant_id,
            reason=reason,
            admin_user=current_user["user_id"],
        )

        return {
            "status": "success",
            "message": f"Tenant {tenant_id} suspended successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to suspend tenant", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to suspend tenant")


@router.post("/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, str]:
    """
    Reactivate a suspended tenant.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Verify tenant exists and is suspended
        tenant = await db.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        if tenant["status"] != "suspended":
            raise HTTPException(status_code=400, detail="Tenant is not suspended")

        # Reactivate tenant
        await db.update_tenant_status(tenant_id, "active")

        # Log admin action
        await db.log_admin_action(
            admin_user_id=current_user["user_id"],
            action="reactivate_tenant",
            target_tenant_id=tenant_id,
            details={},
            ip_address=getattr(current_user, "ip_address", "unknown"),
        )

        logger.info(
            "Tenant reactivated",
            tenant_id=tenant_id,
            admin_user=current_user["user_id"],
        )

        return {
            "status": "success",
            "message": f"Tenant {tenant_id} reactivated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reactivate tenant", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reactivate tenant")


@router.get("/audit-logs")
async def get_admin_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    action_filter: Optional[str] = Query(None),
    tenant_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get admin audit logs with pagination and filtering.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        offset = (page - 1) * limit

        logs_data = await db.get_admin_audit_logs(
            offset=offset,
            limit=limit,
            action_filter=action_filter,
            tenant_filter=tenant_filter,
        )

        logs = []
        for log_data in logs_data:
            log = AdminAuditLog(
                log_id=log_data["log_id"],
                admin_user_id=log_data["admin_user_id"],
                action=log_data["action"],
                target_tenant_id=log_data["target_tenant_id"],
                details=log_data["details"],
                timestamp=log_data["timestamp"],
                ip_address=log_data["ip_address"],
            )
            logs.append(log)

        total_count = await db.get_admin_audit_logs_count(
            action_filter=action_filter, tenant_filter=tenant_filter
        )

        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
            },
        }

    except Exception as e:
        logger.error("Failed to get audit logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/system/health")
async def get_system_health_detailed(
    current_user: dict = Depends(get_current_user),
    db: DatabaseOperations = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed system health information for vendor admin.
    """
    require_admin_role(current_user, "vendor_admin")

    try:
        # Get comprehensive system health metrics
        health_data = {
            "database": {
                "status": "healthy",
                "connection_pool": await db.get_connection_pool_stats(),
                "query_performance": await db.get_query_performance_stats(),
                "storage_usage": await db.get_storage_usage_stats(),
            },
            "redis": {
                "status": "healthy",
                "memory_usage": await db.get_redis_memory_stats(),
                "hit_rate": await db.get_redis_hit_rate(),
                "operations_per_sec": await db.get_redis_ops_stats(),
            },
            "api": {
                "status": "healthy",
                "response_times": await db.get_api_response_time_stats(),
                "error_rates": await db.get_api_error_rate_stats(),
                "throughput": await db.get_api_throughput_stats(),
            },
            "tenants": {
                "total": await db.get_total_tenant_count(),
                "active_24h": await db.get_active_tenants_count(hours=24),
                "suspended": await db.get_suspended_tenants_count(),
                "trial": await db.get_trial_tenants_count(),
            },
        }

        return health_data

    except Exception as e:
        logger.error("Failed to get system health", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")
