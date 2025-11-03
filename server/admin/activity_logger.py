#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-005: Admin Dashboard
US-100: Admin Activity Logging System

Comprehensive audit logging system for admin operations
with compliance reporting, retention policy, and security monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class AdminAction(Enum):
    """Types of admin actions that should be logged"""

    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    DEACTIVATE_USER = "deactivate_user"
    ACTIVATE_USER = "activate_user"
    CHANGE_USER_ROLE = "change_user_role"
    CHANGE_USER_PERMISSIONS = "change_user_permissions"

    # Team management
    CREATE_TEAM = "create_team"
    UPDATE_TEAM = "update_team"
    DELETE_TEAM = "delete_team"
    ADD_TEAM_MEMBER = "add_team_member"
    REMOVE_TEAM_MEMBER = "remove_team_member"
    CHANGE_TEAM_ROLE = "change_team_role"

    # Organization management
    CREATE_ORGANIZATION = "create_organization"
    UPDATE_ORGANIZATION = "update_organization"
    DELETE_ORGANIZATION = "delete_organization"

    # Context management
    TRANSFER_CONTEXT_OWNERSHIP = "transfer_context_ownership"
    CHANGE_CONTEXT_PERMISSIONS = "change_context_permissions"
    DELETE_CONTEXT = "delete_context"

    # System administration
    CHANGE_SYSTEM_SETTINGS = "change_system_settings"
    OVERRIDE_ACCESS = "override_access"
    BULK_OPERATION = "bulk_operation"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"

    # Security
    RESOLVE_SECURITY_ALERT = "resolve_security_alert"
    CHANGE_SECURITY_POLICY = "change_security_policy"
    OVERRIDE_SECURITY = "override_security"


class AdminActivityLogger:
    """
    Admin Activity Logger

    Provides comprehensive audit logging for admin operations
    with configurable retention policy and compliance reporting.
    """

    def __init__(self, db_pool: asyncpg.Pool, retention_days: int = 90):
        """Initialize the admin activity logger."""
        self.db_pool = db_pool
        self.retention_days = retention_days
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False

    async def start_services(self) -> None:
        """Start background cleanup service"""
        if self._cleanup_started:
            return

        async def cleanup_loop():
            """Periodically clean up old admin activity logs"""
            while True:
                await asyncio.sleep(3600)  # Run every hour
                try:
                    await self._cleanup_old_logs()
                except Exception as e:
                    logger.error(f"Error cleaning up admin activity logs: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        self._cleanup_started = True
        logger.info("Admin activity logger services started")

    async def stop_services(self) -> None:
        """Stop background services"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Admin activity logger services stopped")

    async def log_activity(
        self,
        admin_user_id: UUID,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log an admin activity event to the database"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO admin_activity_log (
                        admin_user_id, action, target_type, target_id,
                        details, ip_address, user_agent, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """

                await conn.execute(
                    query,
                    admin_user_id,
                    action,
                    target_type,
                    target_id,
                    json.dumps(details) if details else "{}",
                    ip_address,
                    user_agent,
                    datetime.now(timezone.utc),
                )

                logger.info(
                    f"Admin activity logged: {action} by user {admin_user_id} "
                    f"on {target_type}:{target_id if target_id else 'N/A'}"
                )
        except Exception as e:
            logger.error(f"Failed to log admin activity: {e}", exc_info=True)
            # Don't raise - audit logging should not break the main operation

    async def get_activity_logs(
        self,
        admin_user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query admin activity logs with various filters"""
        try:
            async with self.db_pool.acquire() as conn:
                # Build WHERE clause dynamically
                conditions = []
                params = []
                param_idx = 1

                if admin_user_id:
                    conditions.append(f"admin_user_id = ${param_idx}")
                    params.append(admin_user_id)
                    param_idx += 1

                if action:
                    conditions.append(f"action = ${param_idx}")
                    params.append(action)
                    param_idx += 1

                if target_type:
                    conditions.append(f"target_type = ${param_idx}")
                    params.append(target_type)
                    param_idx += 1

                if target_id:
                    conditions.append(f"target_id = ${param_idx}")
                    params.append(target_id)
                    param_idx += 1

                if start_date:
                    conditions.append(f"timestamp >= ${param_idx}")
                    params.append(start_date)
                    param_idx += 1

                if end_date:
                    conditions.append(f"timestamp <= ${param_idx}")
                    params.append(end_date)
                    param_idx += 1

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = f"""
                    SELECT
                        id,
                        admin_user_id,
                        action,
                        target_type,
                        target_id,
                        details,
                        ip_address,
                        user_agent,
                        timestamp
                    FROM admin_activity_log
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """
                params.extend([limit, offset])

                rows = await conn.fetch(query, *params)

                return [
                    {
                        "id": str(row["id"]),
                        "admin_user_id": str(row["admin_user_id"]),
                        "action": row["action"],
                        "target_type": row["target_type"],
                        "target_id": str(row["target_id"]) if row["target_id"] else None,
                        "details": (
                            row["details"] if isinstance(row["details"], dict) else json.loads(row["details"] or "{}")
                        ),
                        "ip_address": row["ip_address"],
                        "user_agent": row["user_agent"],
                        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to query admin activity logs: {e}", exc_info=True)
            raise

    async def _cleanup_old_logs(self) -> None:
        """Remove logs older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM admin_activity_log WHERE timestamp < $1",
                    cutoff_date,
                )
                deleted_count = int(result.split()[-1]) if result else 0
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old admin activity logs")
        except Exception as e:
            logger.error(f"Error cleaning up old admin activity logs: {e}", exc_info=True)

    async def get_activity_summary(
        self,
        admin_user_id: Optional[UUID] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get summary statistics of admin activity"""
        try:
            async with self.db_pool.acquire() as conn:
                start_date = datetime.now(timezone.utc) - timedelta(days=days)

                conditions = ["timestamp >= $1"]
                params = [start_date]
                param_idx = 2

                if admin_user_id:
                    conditions.append(f"admin_user_id = ${param_idx}")
                    params.append(admin_user_id)
                    param_idx += 1

                where_clause = " AND ".join(conditions)

                # Get total count
                total_query = f"SELECT COUNT(*) as total FROM admin_activity_log WHERE {where_clause}"
                total_row = await conn.fetchrow(total_query, *params)
                total = total_row["total"] if total_row else 0

                # Get action distribution
                action_query = f"""
                    SELECT action, COUNT(*) as count
                    FROM admin_activity_log
                    WHERE {where_clause}
                    GROUP BY action
                    ORDER BY count DESC
                """
                action_rows = await conn.fetch(action_query, *params)
                action_distribution = {row["action"]: row["count"] for row in action_rows}

                # Get most active admin
                admin_query = f"""
                    SELECT admin_user_id, COUNT(*) as count
                    FROM admin_activity_log
                    WHERE {where_clause}
                    GROUP BY admin_user_id
                    ORDER BY count DESC
                    LIMIT 10
                """
                admin_rows = await conn.fetch(admin_query, *params)
                most_active_admins = [
                    {"admin_user_id": str(row["admin_user_id"]), "count": row["count"]} for row in admin_rows
                ]

                return {
                    "total_actions": total,
                    "action_distribution": action_distribution,
                    "most_active_admins": most_active_admins,
                    "period_days": days,
                    "start_date": start_date.isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get activity summary: {e}", exc_info=True)
            raise
