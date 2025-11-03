#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074: GDPR Data Collector

Collects all user data from various sources for GDPR compliance:
- User profile data
- Memories (from memory.memory_records)
- Contexts
- Team memberships
- Audit logs
- Billing information (if applicable)

Status: Phase 1 - In Progress
Assigned To: Developer G
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GDPRDataCollector:
    """
    Collects all user data for GDPR compliance.

    Implements comprehensive data collection for:
    - Data Subject Access Requests (DSAR - Article 15)
    - Data Portability (Article 20)
    - Data export generation
    """

    def __init__(self, db_session: Session):
        """
        Initialize GDPR Data Collector.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        logger.info("GDPR Data Collector initialized")

    async def collect_all_user_data(self, user_id: UUID) -> Dict[str, Any]:
        """
        Collect all user data for GDPR export.

        GDPR Article 15 (Right of Access) and Article 20 (Portability)
        require comprehensive data collection including:
        - User profile
        - All memories
        - All contexts
        - Team memberships
        - Audit logs
        - Processing records

        Args:
            user_id: User ID to collect data for

        Returns:
            Dictionary containing all user data organized by category
        """
        logger.info(f"Collecting all data for user {user_id}")

        data = {"user_id": str(user_id), "exported_at": datetime.utcnow().isoformat(), "data": {}}

        try:
            # 1. User Profile Data
            data["data"]["profile"] = await self._collect_user_profile(user_id)

            # 2. Memories
            data["data"]["memories"] = await self._collect_memories(user_id)

            # 3. Contexts
            data["data"]["contexts"] = await self._collect_contexts(user_id)

            # 4. Team Memberships
            data["data"]["team_memberships"] = await self._collect_team_memberships(user_id)

            # 5. Organizations
            data["data"]["organizations"] = await self._collect_organizations(user_id)

            # 6. Audit Logs (if available)
            data["data"]["audit_logs"] = await self._collect_audit_logs(user_id)

            # 7. Data Subject Requests History
            data["data"]["data_subject_requests"] = await self._collect_data_subject_requests(user_id)

            # 8. Data Exports History
            data["data"]["data_exports"] = await self._collect_data_exports(user_id)

            logger.info(f"Successfully collected data for user {user_id}")
            return data

        except Exception as e:
            logger.error(f"Error collecting data for user {user_id}: {e}")
            # Rollback transaction on error to allow subsequent operations
            try:
                self.db_session.rollback()
            except Exception:
                pass
            raise

    async def _collect_user_profile(self, user_id: UUID) -> Dict[str, Any]:
        """Collect user profile data from public.users."""
        try:
            # Query user from public.users
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        id, email, name, username, account_type,
                        subscription_tier, role, email_verified,
                        is_active, created_at, updated_at, last_login
                    FROM public.users
                    WHERE id = :user_id
                """
                ),
                {"user_id": user_id},
            ).fetchone()

            if result:
                return {
                    "id": str(result.id),
                    "email": result.email,
                    "name": result.name,
                    "username": result.username,
                    "account_type": result.account_type,
                    "subscription_tier": result.subscription_tier,
                    "role": result.role,
                    "email_verified": result.email_verified,
                    "is_active": result.is_active,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else None,
                    "last_login": result.last_login.isoformat() if result.last_login else None,
                }
            return {}
        except Exception as e:
            logger.error(f"Error collecting user profile: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return {}

    async def _collect_memories(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect all memories from memory.memory_records."""
        try:
            # Query from memory.memory_records (canonical table)
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        id, scope, kind, text, metadata,
                        team_id, org_id, created_at, updated_at
                    FROM memory.memory_records
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            memories = []
            for row in result:
                memories.append(
                    {
                        "id": str(row.id),
                        "scope": row.scope,
                        "kind": row.kind,
                        "text": row.text,
                        "metadata": row.metadata if row.metadata else {},
                        "team_id": str(row.team_id) if row.team_id else None,
                        "org_id": str(row.org_id) if row.org_id else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    }
                )

            logger.info(f"Collected {len(memories)} memories for user {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error collecting memories: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            # If memory schema doesn't exist yet, return empty list
            return []

    async def _collect_contexts(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect all contexts for user."""
        try:
            # Query contexts - personal, team, and org contexts
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        c.id, c.name, c.scope, c.is_active,
                        c.team_id, c.organization_id, c.created_at, c.updated_at,
                        t.name as team_name, o.name as org_name
                    FROM public.contexts c
                    LEFT JOIN public.teams t ON c.team_id = t.id
                    LEFT JOIN public.organizations o ON c.organization_id = o.id
                    WHERE c.owner_id = :user_id
                       OR c.team_id IN (
                           SELECT team_id FROM public.team_memberships WHERE user_id = :user_id
                       )
                       OR c.organization_id IN (
                           SELECT DISTINCT t.organization_id
                           FROM public.teams t
                           JOIN public.team_memberships tm ON t.id = tm.team_id
                           WHERE tm.user_id = :user_id
                       )
                    ORDER BY c.created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            contexts = []
            for row in result:
                contexts.append(
                    {
                        "id": str(row.id),
                        "name": row.name,
                        "scope": row.scope,
                        "is_active": row.is_active,
                        "team_id": str(row.team_id) if row.team_id else None,
                        "team_name": row.team_name,
                        "organization_id": str(row.organization_id) if row.organization_id else None,
                        "org_name": row.org_name,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    }
                )

            logger.info(f"Collected {len(contexts)} contexts for user {user_id}")
            return contexts
        except Exception as e:
            logger.error(f"Error collecting contexts: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []

    async def _collect_team_memberships(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect team memberships."""
        try:
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        tm.id, tm.team_id, tm.role, tm.created_at,
                        t.name as team_name
                    FROM public.team_memberships tm
                    JOIN public.teams t ON tm.team_id = t.id
                    WHERE tm.user_id = :user_id
                    ORDER BY tm.created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            memberships = []
            for row in result:
                memberships.append(
                    {
                        "id": str(row.id),
                        "team_id": str(row.team_id),
                        "team_name": row.team_name,
                        "role": row.role,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                )

            logger.info(f"Collected {len(memberships)} team memberships for user {user_id}")
            return memberships
        except Exception as e:
            logger.error(f"Error collecting team memberships: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []

    async def _collect_organizations(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect organizations user is part of (via teams)."""
        try:
            result = self.db_session.execute(
                text(
                    """
                    SELECT DISTINCT
                        o.id, o.name, o.domain, o.is_active,
                        o.created_at
                    FROM public.organizations o
                    JOIN public.teams t ON o.id = t.organization_id
                    JOIN public.team_memberships tm ON t.id = tm.team_id
                    WHERE tm.user_id = :user_id
                    ORDER BY o.created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            organizations = []
            for row in result:
                organizations.append(
                    {
                        "id": str(row.id),
                        "name": row.name,
                        "domain": row.domain,
                        "is_active": row.is_active,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                )

            logger.info(f"Collected {len(organizations)} organizations for user {user_id}")
            return organizations
        except Exception as e:
            logger.error(f"Error collecting organizations: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []

    async def _collect_audit_logs(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect audit logs (if audit table exists)."""
        try:
            # Try to query audit logs if table exists
            # This is a placeholder - adjust based on actual audit table structure
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        id, action, resource_type, resource_id,
                        metadata, created_at
                    FROM public.audit_logs
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            logs = []
            for row in result:
                logs.append(
                    {
                        "id": str(row.id),
                        "action": row.action,
                        "resource_type": row.resource_type,
                        "resource_id": str(row.resource_id) if row.resource_id else None,
                        "metadata": row.metadata if row.metadata else {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                )

            logger.info(f"Collected {len(logs)} audit logs for user {user_id}")
            return logs
        except Exception as e:
            # Audit table might not exist - that's OK
            logger.debug(f"Audit logs not available: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []

    async def _collect_data_subject_requests(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect history of data subject requests."""
        try:
            from .gdpr_models import DataSubjectRequest

            # Use raw SQL to avoid transaction state issues
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        id, request_type, status, description,
                        completed_at, created_at
                    FROM data_subject_requests
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            requests = [
                {
                    "id": str(row.id),
                    "request_type": row.request_type,
                    "status": row.status,
                    "description": row.description,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in result
            ]

            return requests
        except Exception as e:
            logger.error(f"Error collecting data subject requests: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []

    async def _collect_data_exports(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Collect history of data exports."""
        try:
            # Use raw SQL to avoid transaction state issues
            result = self.db_session.execute(
                text(
                    """
                    SELECT
                        id, format, status,
                        created_at, expires_at, downloaded_at
                    FROM data_exports
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """
                ),
                {"user_id": user_id},
            ).fetchall()

            return [
                {
                    "id": str(row.id),
                    "format": row.format,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    "downloaded_at": row.downloaded_at.isoformat() if row.downloaded_at else None,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error collecting data exports: {e}")
            try:
                self.db_session.rollback()
            except Exception:
                pass
            return []
