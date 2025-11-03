#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-004: Context Sharing Audit Logger
US-94: Context Sharing Audit Trail

Comprehensive audit logging system for context sharing operations
with compliance reporting, 90-day retention, and security monitoring.
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


class SharingAction(Enum):
    """Types of context sharing actions"""

    SHARED = "shared"
    UNSHARED = "unshared"
    PERMISSION_CHANGED = "permission_changed"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_REVOKED = "permission_revoked"


class ContextSharingAuditLogger:
    """
    Context Sharing Audit Logger

    Provides comprehensive audit logging for context sharing operations
    with 90-day retention policy and compliance reporting.
    """

    def __init__(self, db_pool: asyncpg.Pool, retention_days: int = 90):
        """Initialize the audit logger."""
        self.db_pool = db_pool
        self.retention_days = retention_days
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False

    async def start_services(self) -> None:
        """Start background cleanup service"""
        if self._cleanup_started:
            return

        async def cleanup_loop():
            """Periodically clean up old audit logs"""
            while True:
                await asyncio.sleep(3600)  # Run every hour
                try:
                    await self._cleanup_old_logs()
                except Exception as e:
                    logger.error(f"Error cleaning up audit logs: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        self._cleanup_started = True
        logger.info("Context sharing audit logger services started")

    async def stop_services(self) -> None:
        """Stop background services"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Context sharing audit logger services stopped")

    async def log_sharing_event(
        self,
        context_id: UUID,
        action: SharingAction,
        actor_user_id: UUID,
        target_user_id: Optional[UUID] = None,
        target_team_id: Optional[UUID] = None,
        target_organization_id: Optional[UUID] = None,
        old_permission: Optional[str] = None,
        new_permission: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a context sharing event to the database"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO context_sharing_audit_logs (
                        context_id, action, actor_user_id,
                        target_user_id, target_team_id, target_organization_id,
                        old_permission_level, new_permission_level,
                        message, ip_address, user_agent,
                        error_message, metadata, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """

                await conn.execute(
                    query,
                    context_id,
                    action.value,
                    actor_user_id,
                    target_user_id,
                    target_team_id,
                    target_organization_id,
                    old_permission,
                    new_permission,
                    None,  # message field
                    ip_address,
                    user_agent,
                    error_message,
                    json.dumps(metadata) if metadata else "{}",
                    datetime.now(timezone.utc),
                )

                logger.info(f"Audit log: {action.value} on context {context_id} " f"by user {actor_user_id}")
        except Exception as e:
            logger.error(f"Failed to log context sharing event: {e}", exc_info=True)
            # Don't raise - audit logging should not break the main operation

    async def log_share(
        self,
        context_id: UUID,
        actor_user_id: UUID,
        target_user_id: Optional[UUID] = None,
        target_team_id: Optional[UUID] = None,
        target_organization_id: Optional[UUID] = None,
        permission_level: str = "read",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log context sharing event"""
        await self.log_sharing_event(
            context_id=context_id,
            action=SharingAction.SHARED,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            target_team_id=target_team_id,
            target_organization_id=target_organization_id,
            new_permission=permission_level,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

    async def log_unshare(
        self,
        context_id: UUID,
        actor_user_id: UUID,
        target_user_id: Optional[UUID] = None,
        target_team_id: Optional[UUID] = None,
        target_organization_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log context unsharing event"""
        await self.log_sharing_event(
            context_id=context_id,
            action=SharingAction.UNSHARED,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            target_team_id=target_team_id,
            target_organization_id=target_organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_permission_change(
        self,
        context_id: UUID,
        actor_user_id: UUID,
        target_user_id: Optional[UUID] = None,
        target_team_id: Optional[UUID] = None,
        target_organization_id: Optional[UUID] = None,
        old_permission: str = None,
        new_permission: str = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log permission change event"""
        await self.log_sharing_event(
            context_id=context_id,
            action=SharingAction.PERMISSION_CHANGED,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            target_team_id=target_team_id,
            target_organization_id=target_organization_id,
            old_permission=old_permission,
            new_permission=new_permission,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_access_attempt(
        self,
        context_id: UUID,
        user_id: UUID,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log context access attempt"""
        action = SharingAction.ACCESS_GRANTED if granted else SharingAction.ACCESS_DENIED
        await self.log_sharing_event(
            context_id=context_id,
            action=action,
            actor_user_id=user_id,
            target_user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=granted,
            error_message=error_message,
        )

    async def get_audit_logs(
        self,
        context_id: Optional[UUID] = None,
        actor_user_id: Optional[UUID] = None,
        target_user_id: Optional[UUID] = None,
        action: Optional[SharingAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        try:
            conditions = []
            params = []
            param_idx = 1

            if context_id is not None:
                conditions.append(f"context_id = ${param_idx}")
                params.append(context_id)
                param_idx += 1

            if actor_user_id is not None:
                conditions.append(f"actor_user_id = ${param_idx}")
                params.append(actor_user_id)
                param_idx += 1

            if target_user_id is not None:
                conditions.append(f"target_user_id = ${param_idx}")
                params.append(target_user_id)
                param_idx += 1

            if action is not None:
                conditions.append(f"action = ${param_idx}")
                params.append(action.value)
                param_idx += 1

            if start_date is not None:
                conditions.append(f"timestamp >= ${param_idx}")
                params.append(start_date)
                param_idx += 1

            if end_date is not None:
                conditions.append(f"timestamp <= ${param_idx}")
                params.append(end_date)
                param_idx += 1

            where_clause = " AND ".join(conditions) if conditions else "TRUE"

            query = f"""
                SELECT
                    id, context_id, action, actor_user_id,
                    target_user_id, target_team_id, target_organization_id,
                    old_permission, new_permission,
                    timestamp, ip_address, user_agent,
                    success, error_message, metadata
                FROM context_sharing_audit_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

                return [
                    {
                        "id": str(row["id"]),
                        "context_id": row["context_id"],
                        "action": row["action"],
                        "actor_user_id": row["actor_user_id"],
                        "target_user_id": row["target_user_id"],
                        "target_team_id": row["target_team_id"],
                        "target_organization_id": row["target_organization_id"],
                        "old_permission": row["old_permission"],
                        "new_permission": row["new_permission"],
                        "timestamp": row["timestamp"].isoformat(),
                        "ip_address": row["ip_address"],
                        "user_agent": row["user_agent"],
                        "success": row["success"],
                        "error_message": row["error_message"],
                        "metadata": row["metadata"],
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}", exc_info=True)
            return []

    async def _cleanup_old_logs(self) -> None:
        """Remove audit logs older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM context_sharing_audit_logs
                    WHERE timestamp < $1
                    """,
                    cutoff_date,
                )

                deleted_count = int(result.split()[-1])
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old audit log entries")
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}", exc_info=True)
