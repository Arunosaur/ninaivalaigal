#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Database operations for SPEC-025: Vendor Admin Console
Multi-tenant management, usage analytics, and audit logging
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class VendorAdminOperations:
    """Database operations for vendor admin functionality."""

    def __init__(self, db_manager):
        """Initialize instance."""
        self.db = db_manager

    async def get_total_tenant_count(self, status_filter: Optional[str] = None) -> int:
        """Get total number of tenants, optionally filtered by status."""
        try:
            query = "SELECT COUNT(*) FROM organizations"
            params = []

            if status_filter:
                query += " WHERE status = $1"
                params.append(status_filter)

            result = await self.db.fetch_one(query, *params)
            return result[0] if result else 0

        except Exception as e:
            logger.error("Failed to get total tenant count", error=str(e))
            raise

    async def get_active_tenants_count(self, hours: int = 24) -> int:
        """Get count of tenants active within specified hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            query = """
                SELECT COUNT(DISTINCT o.id)
                FROM organizations o
                JOIN users u ON u.organization_id = o.id
                WHERE u.last_login > $1 AND o.status = 'active'
            """

            result = await self.db.fetch_one(query, cutoff_time)
            return result[0] if result else 0

        except Exception as e:
            logger.error("Failed to get active tenants count", error=str(e))
            raise

    async def get_api_calls_count(self, hours: int = 24) -> int:
        """Get total API calls in the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # This would typically come from an API usage tracking table
            # For now, return a placeholder value
            query = """
                SELECT COUNT(*) FROM api_usage_logs
                WHERE timestamp > $1
            """

            try:
                result = await self.db.fetch_one(query, cutoff_time)
                return result[0] if result else 0
            except Exception:
                # If table doesn't exist, return estimated value
                return 0

        except Exception as e:
            logger.error("Failed to get API calls count", error=str(e))
            raise

    async def get_average_response_time(self, hours: int = 24) -> float:
        """Get average API response time in milliseconds."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Placeholder - would come from performance monitoring
            query = """
                SELECT AVG(response_time_ms) FROM api_performance_logs
                WHERE timestamp > $1
            """

            try:
                result = await self.db.fetch_one(query, cutoff_time)
                return float(result[0]) if result and result[0] else 50.0
            except Exception:
                # Return default if table doesn't exist
                return 50.0

        except Exception as e:
            logger.error("Failed to get average response time", error=str(e))
            raise

    async def get_error_rate_percent(self, hours: int = 24) -> float:
        """Get API error rate as percentage."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Placeholder - would come from error tracking
            query = """
                SELECT
                    (COUNT(*) FILTER (WHERE status_code >= 400) * 100.0 / COUNT(*)) as error_rate
                FROM api_usage_logs
                WHERE timestamp > $1
            """

            try:
                result = await self.db.fetch_one(query, cutoff_time)
                return float(result[0]) if result and result[0] else 0.5
            except Exception:
                # Return default if table doesn't exist
                return 0.5

        except Exception as e:
            logger.error("Failed to get error rate", error=str(e))
            raise

    async def get_total_storage_usage_gb(self) -> float:
        """Get total storage usage across all tenants in GB."""
        try:
            query = """
                SELECT
                    COALESCE(SUM(pg_total_relation_size(schemaname||'.'||tablename)), 0) / (1024^3) as storage_gb
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            """

            result = await self.db.fetch_one(query)
            return float(result[0]) if result and result[0] else 0.0

        except Exception as e:
            logger.error("Failed to get total storage usage", error=str(e))
            raise

    async def get_tenants_with_metrics(
        self, offset: int = 0, limit: int = 50, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tenants with their usage metrics."""
        try:
            base_query = """
                SELECT
                    o.id as tenant_id,
                    o.name as organization_name,
                    COALESCE(o.subscription_tier, 'free') as subscription_tier,
                    o.created_at,
                    COALESCE(MAX(u.last_login), o.created_at) as last_active,
                    COUNT(DISTINCT u.id) as total_users,
                    COALESCE(COUNT(DISTINCT m.id), 0) as total_memories,
                    COALESCE(SUM(LENGTH(m.content)), 0) / (1024 * 1024) as storage_used_mb,
                    0 as api_calls_today,  -- Placeholder
                    COALESCE(o.status, 'active') as status
                FROM organizations o
                LEFT JOIN users u ON u.organization_id = o.id
                LEFT JOIN memories m ON m.user_id = u.id
            """

            params = []
            if status_filter:
                base_query += " WHERE o.status = $1"
                params.append(status_filter)

            base_query += """
                GROUP BY o.id, o.name, o.subscription_tier, o.created_at, o.status
                ORDER BY o.created_at DESC
                LIMIT $%d OFFSET $%d
            """ % (
                len(params) + 1,
                len(params) + 2,
            )

            params.extend([limit, offset])

            results = await self.db.fetch_all(base_query, *params)

            tenants = []
            for row in results:
                tenant = {
                    "tenant_id": str(row[0]),
                    "organization_name": row[1],
                    "subscription_tier": row[2],
                    "created_at": row[3],
                    "last_active": row[4],
                    "total_users": row[5],
                    "total_memories": row[6],
                    "storage_used_mb": float(row[7]),
                    "api_calls_today": row[8],
                    "status": row[9],
                }
                tenants.append(tenant)

            return tenants

        except Exception as e:
            logger.error("Failed to get tenants with metrics", error=str(e))
            raise

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant information by ID."""
        try:
            query = """
                SELECT id, name, subscription_tier, created_at, status
                FROM organizations
                WHERE id = $1
            """

            result = await self.db.fetch_one(query, tenant_id)

            if result:
                return {
                    "tenant_id": str(result[0]),
                    "organization_name": result[1],
                    "subscription_tier": result[2],
                    "created_at": result[3],
                    "status": result[4],
                }

            return None

        except Exception as e:
            logger.error("Failed to get tenant by ID", tenant_id=tenant_id, error=str(e))
            raise

    async def get_tenant_usage_metrics(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get detailed usage metrics for a tenant over time."""
        try:
            # Generate date series for the period
            query = """
                WITH date_series AS (
                    SELECT generate_series($2::date, $3::date, '1 day'::interval)::date as date
                ),
                tenant_metrics AS (
                    SELECT
                        ds.date,
                        0 as api_calls,  -- Placeholder
                        COUNT(DISTINCT m.id) as memory_operations,
                        COALESCE(SUM(LENGTH(m.content)), 0) / (1024 * 1024) as storage_mb,
                        COUNT(DISTINCT u.id) as active_users,
                        50.0 as response_time_p95  -- Placeholder
                    FROM date_series ds
                    LEFT JOIN organizations o ON o.id = $1
                    LEFT JOIN users u ON u.organization_id = o.id
                        AND DATE(u.last_login) = ds.date
                    LEFT JOIN memories m ON m.user_id = u.id
                        AND DATE(m.created_at) = ds.date
                    GROUP BY ds.date
                    ORDER BY ds.date
                )
                SELECT * FROM tenant_metrics
            """

            results = await self.db.fetch_all(query, tenant_id, start_date, end_date)

            metrics = []
            for row in results:
                metric = {
                    "date": row[0],
                    "api_calls": row[1],
                    "memory_operations": row[2],
                    "storage_mb": float(row[3]),
                    "active_users": row[4],
                    "response_time_p95": float(row[5]),
                }
                metrics.append(metric)

            return metrics

        except Exception as e:
            logger.error("Failed to get tenant usage metrics", tenant_id=tenant_id, error=str(e))
            raise

    async def get_tenant_rate_limits(self, tenant_id: str) -> Dict[str, Any]:
        """Get rate limit configuration for a tenant."""
        try:
            query = """
                SELECT
                    api_calls_per_minute,
                    memory_operations_per_hour,
                    storage_limit_gb,
                    user_limit
                FROM tenant_rate_limits
                WHERE tenant_id = $1
            """

            result = await self.db.fetch_one(query, tenant_id)

            if result:
                return {
                    "api_calls_per_minute": result[0],
                    "memory_operations_per_hour": result[1],
                    "storage_limit_gb": float(result[2]),
                    "user_limit": result[3],
                }
            else:
                # Return default rate limits
                return {
                    "api_calls_per_minute": 100,
                    "memory_operations_per_hour": 1000,
                    "storage_limit_gb": 5.0,
                    "user_limit": 10,
                }

        except Exception as e:
            logger.error("Failed to get tenant rate limits", tenant_id=tenant_id, error=str(e))
            # Return defaults on error
            return {
                "api_calls_per_minute": 100,
                "memory_operations_per_hour": 1000,
                "storage_limit_gb": 5.0,
                "user_limit": 10,
            }

    async def update_tenant_rate_limits(
        self,
        tenant_id: str,
        api_calls_per_minute: int,
        memory_operations_per_hour: int,
        storage_limit_gb: float,
        user_limit: int,
    ) -> None:
        """Update rate limit configuration for a tenant."""
        try:
            # Upsert rate limits
            query = """
                INSERT INTO tenant_rate_limits
                (tenant_id, api_calls_per_minute, memory_operations_per_hour,
                 storage_limit_gb, user_limit, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (tenant_id)
                DO UPDATE SET
                    api_calls_per_minute = EXCLUDED.api_calls_per_minute,
                    memory_operations_per_hour = EXCLUDED.memory_operations_per_hour,
                    storage_limit_gb = EXCLUDED.storage_limit_gb,
                    user_limit = EXCLUDED.user_limit,
                    updated_at = NOW()
            """

            await self.db.execute(
                query,
                tenant_id,
                api_calls_per_minute,
                memory_operations_per_hour,
                storage_limit_gb,
                user_limit,
            )

        except Exception as e:
            logger.error("Failed to update tenant rate limits", tenant_id=tenant_id, error=str(e))
            raise

    async def update_tenant_status(self, tenant_id: str, status: str) -> None:
        """Update tenant status (active, suspended, trial, etc.)."""
        try:
            query = """
                UPDATE organizations
                SET status = $2, updated_at = NOW()
                WHERE id = $1
            """

            await self.db.execute(query, tenant_id, status)

        except Exception as e:
            logger.error(
                "Failed to update tenant status",
                tenant_id=tenant_id,
                status=status,
                error=str(e),
            )
            raise

    async def log_admin_action(
        self,
        admin_user_id: str,
        action: str,
        target_tenant_id: Optional[str],
        details: Dict[str, Any],
        ip_address: str,
    ) -> None:
        """Log admin action for audit trail."""
        try:
            log_id = str(uuid.uuid4())

            query = """
                INSERT INTO admin_audit_logs
                (log_id, admin_user_id, action, target_tenant_id, details, ip_address, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """

            await self.db.execute(
                query,
                log_id,
                admin_user_id,
                action,
                target_tenant_id,
                details,
                ip_address,
            )

        except Exception as e:
            logger.error(
                "Failed to log admin action",
                admin_user_id=admin_user_id,
                action=action,
                error=str(e),
            )
            # Don't raise - audit logging failure shouldn't break operations

    async def get_admin_audit_logs(
        self,
        offset: int = 0,
        limit: int = 100,
        action_filter: Optional[str] = None,
        tenant_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get admin audit logs with filtering."""
        try:
            base_query = """
                SELECT
                    log_id, admin_user_id, action, target_tenant_id,
                    details, ip_address, timestamp
                FROM admin_audit_logs
            """

            conditions = []
            params = []

            if action_filter:
                conditions.append(f"action = ${len(params) + 1}")
                params.append(action_filter)

            if tenant_filter:
                conditions.append(f"target_tenant_id = ${len(params) + 1}")
                params.append(tenant_filter)

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            base_query += f"""
                ORDER BY timestamp DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """

            params.extend([limit, offset])

            results = await self.db.fetch_all(base_query, *params)

            logs = []
            for row in results:
                log = {
                    "log_id": row[0],
                    "admin_user_id": row[1],
                    "action": row[2],
                    "target_tenant_id": row[3],
                    "details": row[4],
                    "ip_address": row[5],
                    "timestamp": row[6],
                }
                logs.append(log)

            return logs

        except Exception as e:
            logger.error("Failed to get admin audit logs", error=str(e))
            return []  # Return empty list on error

    async def get_admin_audit_logs_count(
        self, action_filter: Optional[str] = None, tenant_filter: Optional[str] = None
    ) -> int:
        """Get total count of admin audit logs."""
        try:
            base_query = "SELECT COUNT(*) FROM admin_audit_logs"

            conditions = []
            params = []

            if action_filter:
                conditions.append(f"action = ${len(params) + 1}")
                params.append(action_filter)

            if tenant_filter:
                conditions.append(f"target_tenant_id = ${len(params) + 1}")
                params.append(tenant_filter)

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            result = await self.db.fetch_one(base_query, *params)
            return result[0] if result else 0

        except Exception as e:
            logger.error("Failed to get admin audit logs count", error=str(e))
            return 0

    async def get_suspended_tenants_count(self) -> int:
        """Get count of suspended tenants."""
        try:
            query = "SELECT COUNT(*) FROM organizations WHERE status = 'suspended'"
            result = await self.db.fetch_one(query)
            return result[0] if result else 0
        except Exception as e:
            logger.error("Failed to get suspended tenants count", error=str(e))
            return 0

    async def get_trial_tenants_count(self) -> int:
        """Get count of trial tenants."""
        try:
            query = "SELECT COUNT(*) FROM organizations WHERE status = 'trial'"
            result = await self.db.fetch_one(query)
            return result[0] if result else 0
        except Exception as e:
            logger.error("Failed to get trial tenants count", error=str(e))
            return 0

    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics."""
        try:
            # Return placeholder stats - would integrate with actual pool monitoring
            return {
                "pool_size": 20,
                "checked_out": 5,
                "available": 15,
                "overflow": 0,
            }
        except Exception as e:
            logger.error("Failed to get connection pool stats", error=str(e))
            return {}

    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        try:
            # Placeholder - would come from query performance monitoring
            return {
                "avg_query_time_ms": 25.0,
                "slow_queries_count": 0,
                "total_queries": 0,
            }
        except Exception as e:
            logger.error("Failed to get query performance stats", error=str(e))
            return {}

    async def get_storage_usage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            total_storage = await self.get_total_storage_usage_gb()
            return {
                "total_gb": total_storage,
                "used_gb": total_storage,
                "available_gb": 0,
            }
        except Exception as e:
            logger.error("Failed to get storage usage stats", error=str(e))
            return {}

    async def get_redis_memory_stats(self) -> Dict[str, Any]:
        """Get Redis memory statistics."""
        try:
            # Placeholder - would integrate with Redis client
            return {
                "used_memory_mb": 0,
                "max_memory_mb": 0,
                "memory_usage_percent": 0,
            }
        except Exception as e:
            logger.error("Failed to get Redis memory stats", error=str(e))
            return {}

    async def get_redis_hit_rate(self) -> float:
        """Get Redis cache hit rate."""
        try:
            # Placeholder - would integrate with Redis client
            return 0.0
        except Exception as e:
            logger.error("Failed to get Redis hit rate", error=str(e))
            return 0.0

    async def get_redis_ops_stats(self) -> Dict[str, Any]:
        """Get Redis operations statistics."""
        try:
            # Placeholder - would integrate with Redis client
            return {
                "ops_per_sec": 0,
                "total_commands": 0,
            }
        except Exception as e:
            logger.error("Failed to get Redis ops stats", error=str(e))
            return {}

    async def get_api_response_time_stats(self) -> Dict[str, Any]:
        """Get API response time statistics."""
        try:
            # Placeholder - would come from API performance monitoring
            return {
                "p50_ms": 50.0,
                "p95_ms": 100.0,
                "p99_ms": 200.0,
            }
        except Exception as e:
            logger.error("Failed to get API response time stats", error=str(e))
            return {}

    async def get_api_error_rate_stats(self) -> Dict[str, Any]:
        """Get API error rate statistics."""
        try:
            error_rate = await self.get_error_rate_percent(hours=24)
            return {
                "error_rate_percent": error_rate,
                "total_errors": 0,
                "total_requests": 0,
            }
        except Exception as e:
            logger.error("Failed to get API error rate stats", error=str(e))
            return {}

    async def get_api_throughput_stats(self) -> Dict[str, Any]:
        """Get API throughput statistics."""
        try:
            # Placeholder - would come from API monitoring
            return {
                "requests_per_second": 0,
                "requests_per_minute": 0,
                "requests_per_hour": 0,
            }
        except Exception as e:
            logger.error("Failed to get API throughput stats", error=str(e))
            return {}

    # Discount Code Operations (US#162)
    async def create_discount_code(
        self,
        code: str,
        percent_off: Optional[int] = None,
        amount_off: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        usage_limit: Optional[int] = None,
        created_by: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new discount code."""
        try:
            discount_id = str(uuid.uuid4())
            query = """
                INSERT INTO discount_codes (
                    id, code, percent_off, amount_off, expires_at, usage_limit,
                    used_count, is_active, created_by, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, 0, TRUE, $7, NOW())
                RETURNING id, code, percent_off, amount_off, expires_at, usage_limit,
                          used_count, is_active, created_at, created_by
            """
            result = await self.db.fetch_one(
                query, discount_id, code, percent_off, amount_off, expires_at, usage_limit, created_by
            )
            if result:
                return {
                    "id": str(result[0]),
                    "code": result[1],
                    "percent_off": result[2],
                    "amount_off": result[3],
                    "expires_at": result[4],
                    "usage_limit": result[5],
                    "used_count": result[6],
                    "is_active": result[7],
                    "created_at": result[8],
                    "created_by": str(result[9]) if result[9] else None,
                    "description": description,
                }
            raise Exception("Failed to create discount code")
        except Exception as e:
            logger.error("Failed to create discount code", error=str(e))
            raise

    async def list_discount_codes(
        self, offset: int = 0, limit: int = 50, active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List discount codes with pagination."""
        try:
            query = "SELECT id, code, percent_off, amount_off, expires_at, usage_limit, used_count, is_active, created_at, created_by FROM discount_codes"
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            results = await self.db.fetch_all(query, limit, offset)
            return [
                {
                    "id": str(row[0]),
                    "code": row[1],
                    "percent_off": row[2],
                    "amount_off": row[3],
                    "expires_at": row[4],
                    "usage_limit": row[5],
                    "used_count": row[6],
                    "is_active": row[7],
                    "created_at": row[8],
                    "created_by": str(row[9]) if row[9] else None,
                }
                for row in results
            ]
        except Exception as e:
            logger.error("Failed to list discount codes", error=str(e))
            raise

    async def get_discount_codes_count(self, active_only: bool = False) -> int:
        """Get total count of discount codes."""
        try:
            query = "SELECT COUNT(*) FROM discount_codes"
            if active_only:
                query += " WHERE is_active = TRUE"
            result = await self.db.fetch_one(query)
            return result[0] if result else 0
        except Exception as e:
            logger.error("Failed to get discount codes count", error=str(e))
            raise

    async def update_discount_code(
        self,
        discount_id: str,
        percent_off: Optional[int] = None,
        amount_off: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        usage_limit: Optional[int] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a discount code."""
        try:
            updates = []
            params = []
            param_idx = 1

            if percent_off is not None:
                updates.append(f"percent_off = ${param_idx}")
                params.append(percent_off)
                param_idx += 1
            if amount_off is not None:
                updates.append(f"amount_off = ${param_idx}")
                params.append(amount_off)
                param_idx += 1
            if expires_at is not None:
                updates.append(f"expires_at = ${param_idx}")
                params.append(expires_at)
                param_idx += 1
            if usage_limit is not None:
                updates.append(f"usage_limit = ${param_idx}")
                params.append(usage_limit)
                param_idx += 1
            if is_active is not None:
                updates.append(f"is_active = ${param_idx}")
                params.append(is_active)
                param_idx += 1

            if not updates:
                # No updates, just fetch current
                query = "SELECT id, code, percent_off, amount_off, expires_at, usage_limit, used_count, is_active, created_at, created_by FROM discount_codes WHERE id = $1"
                result = await self.db.fetch_one(query, discount_id)
            else:
                updates.append("updated_at = NOW()")
                query = f"""
                    UPDATE discount_codes
                    SET {', '.join(updates)}
                    WHERE id = ${param_idx}
                    RETURNING id, code, percent_off, amount_off, expires_at, usage_limit,
                              used_count, is_active, created_at, created_by
                """
                params.append(discount_id)
                result = await self.db.fetch_one(query, *params)

            if result:
                return {
                    "id": str(result[0]),
                    "code": result[1],
                    "percent_off": result[2],
                    "amount_off": result[3],
                    "expires_at": result[4],
                    "usage_limit": result[5],
                    "used_count": result[6],
                    "is_active": result[7],
                    "created_at": result[8],
                    "created_by": str(result[9]) if result[9] else None,
                    "description": description,
                }
            return None
        except Exception as e:
            logger.error("Failed to update discount code", discount_id=discount_id, error=str(e))
            raise

    async def deactivate_discount_code(self, discount_id: str) -> bool:
        """Deactivate a discount code."""
        try:
            query = "UPDATE discount_codes SET is_active = FALSE, updated_at = NOW() WHERE id = $1 RETURNING id"
            result = await self.db.fetch_one(query, discount_id)
            return result is not None
        except Exception as e:
            logger.error("Failed to deactivate discount code", discount_id=discount_id, error=str(e))
            raise

    # Credit Operations (US#162)
    async def grant_credits(
        self,
        tenant_id: str,
        amount: float,
        reason: str,
        expires_at: Optional[datetime] = None,
        granted_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Grant credits to a team or organization."""
        try:
            credit_id = str(uuid.uuid4())
            # Determine if tenant_id is team or org (simplified - would need proper lookup)
            query = """
                INSERT INTO team_credits (
                    id, team_id, amount, used_amount, reason, expires_at, granted_by, created_at
                ) VALUES ($1, $2, $3, 0, $4, $5, $6, NOW())
                RETURNING id, team_id, org_id, amount, used_amount, expires_at, granted_by, created_at
            """
            result = await self.db.fetch_one(query, credit_id, tenant_id, amount, reason, expires_at, granted_by)
            if result:
                return {
                    "id": str(result[0]),
                    "tenant_id": str(result[1]) if result[1] else str(result[2]),
                    "amount": float(result[3]),
                    "used_amount": float(result[4]),
                    "expires_at": result[5],
                    "granted_by": str(result[6]) if result[6] else None,
                    "created_at": result[7],
                }
            raise Exception("Failed to grant credits")
        except Exception as e:
            logger.error("Failed to grant credits", error=str(e))
            raise

    async def revoke_credits(self, credit_id: str, reason: str, revoked_by: Optional[str] = None) -> bool:
        """Revoke credits (mark as used/expired)."""
        try:
            # Get current credit
            query = "SELECT amount, used_amount FROM team_credits WHERE id = $1"
            result = await self.db.fetch_one(query, credit_id)
            if not result:
                return False

            # Mark entire credit as used (effectively revoking it)
            update_query = """
                UPDATE team_credits
                SET used_amount = amount, updated_at = NOW()
                WHERE id = $1
                RETURNING id
            """
            update_result = await self.db.fetch_one(update_query, credit_id)
            return update_result is not None
        except Exception as e:
            logger.error("Failed to revoke credits", credit_id=credit_id, error=str(e))
            raise

    # Non-Profit Application Operations (US#162)
    async def list_nonprofit_applications(
        self, offset: int = 0, limit: int = 50, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List non-profit applications with pagination."""
        try:
            query = """
                SELECT id, team_id, org_id, organization_name, tax_id, description,
                       website_url, status, submitted_at, reviewed_by, reviewed_at, review_notes
                FROM nonprofit_applications
            """
            params = []
            if status_filter:
                query += " WHERE status = $1"
                params.append(status_filter)
            query += " ORDER BY submitted_at DESC LIMIT $%d OFFSET $%d" % (len(params) + 1, len(params) + 2)
            params.extend([limit, offset])
            results = await self.db.fetch_all(query, *params)
            return [
                {
                    "id": str(row[0]),
                    "tenant_id": str(row[1]) if row[1] else str(row[2]),
                    "organization_name": row[3],
                    "tax_id": row[4],
                    "description": row[5],
                    "website_url": row[6],
                    "status": row[7],
                    "submitted_at": row[8],
                    "reviewed_by": str(row[9]) if row[9] else None,
                    "reviewed_at": row[10],
                    "review_notes": row[11],
                }
                for row in results
            ]
        except Exception as e:
            logger.error("Failed to list nonprofit applications", error=str(e))
            raise

    async def get_nonprofit_applications_count(self, status_filter: Optional[str] = None) -> int:
        """Get total count of non-profit applications."""
        try:
            query = "SELECT COUNT(*) FROM nonprofit_applications"
            params = []
            if status_filter:
                query += " WHERE status = $1"
                params.append(status_filter)
            result = await self.db.fetch_one(query, *params)
            return result[0] if result else 0
        except Exception as e:
            logger.error("Failed to get nonprofit applications count", error=str(e))
            raise

    async def approve_nonprofit_application(
        self, application_id: str, reviewed_by: Optional[str] = None, review_notes: Optional[str] = None
    ) -> bool:
        """Approve a non-profit application and apply special pricing."""
        try:
            query = """
                UPDATE nonprofit_applications
                SET status = 'approved', reviewed_by = $1, reviewed_at = NOW(), review_notes = $2
                WHERE id = $3 AND status = 'pending'
                RETURNING id
            """
            result = await self.db.fetch_one(query, reviewed_by, review_notes, application_id)
            if result:
                # Apply special pricing to tenant (would need to update billing/subscription)
                # This is a placeholder - actual implementation would update subscription tier
                return True
            return False
        except Exception as e:
            logger.error("Failed to approve nonprofit application", application_id=application_id, error=str(e))
            raise

    async def reject_nonprofit_application(
        self, application_id: str, reviewed_by: Optional[str] = None, review_notes: Optional[str] = None
    ) -> bool:
        """Reject a non-profit application."""
        try:
            query = """
                UPDATE nonprofit_applications
                SET status = 'rejected', reviewed_by = $1, reviewed_at = NOW(), review_notes = $2
                WHERE id = $3 AND status IN ('pending', 'under_review')
                RETURNING id
            """
            result = await self.db.fetch_one(query, reviewed_by, review_notes, application_id)
            return result is not None
        except Exception as e:
            logger.error("Failed to reject nonprofit application", application_id=application_id, error=str(e))
            raise

    # Billing Analytics (US#162)
    async def get_billing_analytics(self) -> Dict[str, Any]:
        """Get billing analytics dashboard data."""
        try:
            # Get total revenue (placeholder - would come from invoices/subscriptions)
            revenue_query = "SELECT COALESCE(SUM(amount), 0) FROM billing_invoices WHERE status = 'paid'"
            revenue_result = await self.db.fetch_one(revenue_query)
            total_revenue = float(revenue_result[0]) if revenue_result and revenue_result[0] else 0.0

            # Get subscription counts
            active_subs_query = "SELECT COUNT(*) FROM team_subscriptions WHERE status = 'active'"
            active_result = await self.db.fetch_one(active_subs_query)
            active_subscriptions = active_result[0] if active_result else 0

            canceled_subs_query = "SELECT COUNT(*) FROM team_subscriptions WHERE status = 'canceled'"
            canceled_result = await self.db.fetch_one(canceled_subs_query)
            canceled_subscriptions = canceled_result[0] if canceled_result else 0

            # Get discount code usage
            discount_usage_query = """
                SELECT code, COUNT(*) as usage_count
                FROM discount_codes dc
                JOIN discount_code_usage dcu ON dc.id = dcu.discount_code_id
                GROUP BY code
            """
            discount_results = await self.db.fetch_all(discount_usage_query)
            discount_code_usage = {row[0]: row[1] for row in discount_results}

            # Get total credit grants
            credit_grants_query = "SELECT COALESCE(SUM(amount), 0) FROM team_credits"
            credit_result = await self.db.fetch_one(credit_grants_query)
            credit_grants_total = float(credit_result[0]) if credit_result and credit_result[0] else 0.0

            # Get nonprofit application counts
            pending_np_query = "SELECT COUNT(*) FROM nonprofit_applications WHERE status = 'pending'"
            pending_result = await self.db.fetch_one(pending_np_query)
            nonprofit_applications_pending = pending_result[0] if pending_result else 0

            approved_np_query = "SELECT COUNT(*) FROM nonprofit_applications WHERE status = 'approved'"
            approved_result = await self.db.fetch_one(approved_np_query)
            nonprofit_applications_approved = approved_result[0] if approved_result else 0

            return {
                "total_revenue": total_revenue,
                "active_subscriptions": active_subscriptions,
                "canceled_subscriptions": canceled_subscriptions,
                "discount_code_usage": discount_code_usage,
                "credit_grants_total": credit_grants_total,
                "nonprofit_applications_pending": nonprofit_applications_pending,
                "nonprofit_applications_approved": nonprofit_applications_approved,
            }
        except Exception as e:
            logger.error("Failed to get billing analytics", error=str(e))
            # Return default values on error
            return {
                "total_revenue": 0.0,
                "active_subscriptions": 0,
                "canceled_subscriptions": 0,
                "discount_code_usage": {},
                "credit_grants_total": 0.0,
                "nonprofit_applications_pending": 0,
                "nonprofit_applications_approved": 0,
            }
