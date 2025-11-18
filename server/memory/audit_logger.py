#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-128: Memory Sharing Audit Logger
# US#848: Phase 3 - Rate Limits & Audit
#
"""
Comprehensive audit logging for memory sharing operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SharingAuditLogger:
    """Audit logger for memory sharing operations"""

    def __init__(self, db_session: Session):
        """
        Initialize audit logger.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    def log_action(
        self,
        action: str,  # share, transfer, copy, revoke
        memory_id: UUID,
        from_entity_type: str,  # user, team, org
        from_entity_id: UUID,
        to_entity_type: str,  # user, team, org
        to_entity_id: UUID,
        performed_by: UUID,
        reason: Optional[str] = None,
        permission: Optional[str] = None,
        is_external: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log a sharing/transfer/copy action.

        Args:
            action: Action type (share, transfer, copy, revoke)
            memory_id: Memory ID
            from_entity_type: Source entity type
            from_entity_id: Source entity ID
            to_entity_type: Target entity type
            to_entity_id: Target entity ID
            performed_by: User ID who performed the action
            reason: Optional reason
            permission: Optional permission level
            is_external: Whether this is external sharing
            metadata: Optional metadata

        Returns:
            Audit log record
        """
        from uuid import uuid4

        from server.memory.audit_models import SharingAuditLog

        audit_log = SharingAuditLog(
            id=uuid4(),
            action=action,
            memory_id=memory_id,
            from_entity_type=from_entity_type,
            from_entity_id=from_entity_id,
            to_entity_type=to_entity_type,
            to_entity_id=to_entity_id,
            performed_by=performed_by,
            timestamp=datetime.utcnow(),
            reason=reason,
            permission=permission,
            is_external=str(is_external).lower(),
            audit_metadata=metadata or {},
        )

        self.db_session.add(audit_log)
        self.db_session.commit()

        logger.info(
            f"Audit log created: action={action}, memory={memory_id}, "
            f"from={from_entity_type}:{from_entity_id}, to={to_entity_type}:{to_entity_id}"
        )

        return {
            "id": str(audit_log.id),
            "action": action,
            "memory_id": str(memory_id),
            "timestamp": audit_log.timestamp.isoformat(),
        }

    def log_revocation(
        self,
        audit_log_id: UUID,
        revoked_by: UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log a revocation of a share/transfer.

        Args:
            audit_log_id: Original audit log ID
            revoked_by: User ID revoking
            reason: Optional reason

        Returns:
            Updated audit log record
        """
        from server.memory.audit_models import SharingAuditLog

        audit_log = self.db_session.query(SharingAuditLog).filter(SharingAuditLog.id == audit_log_id).first()

        if not audit_log:
            raise ValueError(f"Audit log not found: {audit_log_id}")

        audit_log.revoked_at = datetime.utcnow()
        audit_log.revoked_by = revoked_by

        # Update metadata
        if audit_log.audit_metadata:
            audit_log.audit_metadata["revocation_reason"] = reason
        else:
            audit_log.audit_metadata = {"revocation_reason": reason}

        self.db_session.commit()

        logger.info(f"Audit log updated with revocation: {audit_log_id}")

        return {
            "id": str(audit_log.id),
            "revoked_at": audit_log.revoked_at.isoformat(),
            "revoked_by": str(revoked_by),
        }

    def get_audit_history(
        self,
        memory_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        org_id: Optional[UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get audit history with filters.

        Args:
            memory_id: Optional memory ID filter
            user_id: Optional user ID filter (performed_by)
            team_id: Optional team ID filter
            org_id: Optional org ID filter
            action: Optional action filter
            limit: Maximum number of records

        Returns:
            List of audit log records
        """
        from server.memory.audit_models import SharingAuditLog

        query = self.db_session.query(SharingAuditLog)

        if memory_id:
            query = query.filter(SharingAuditLog.memory_id == memory_id)
        if user_id:
            query = query.filter(SharingAuditLog.performed_by == user_id)
        if team_id:
            query = query.filter(
                ((SharingAuditLog.from_entity_type == "team") & (SharingAuditLog.from_entity_id == team_id))
                | ((SharingAuditLog.to_entity_type == "team") & (SharingAuditLog.to_entity_id == team_id))
            )
        if org_id:
            query = query.filter(
                ((SharingAuditLog.from_entity_type == "org") & (SharingAuditLog.from_entity_id == org_id))
                | ((SharingAuditLog.to_entity_type == "org") & (SharingAuditLog.to_entity_id == org_id))
            )
        if action:
            query = query.filter(SharingAuditLog.action == action)

        logs = query.order_by(SharingAuditLog.timestamp.desc()).limit(limit).all()

        return [
            {
                "id": str(log.id),
                "action": log.action,
                "memory_id": str(log.memory_id),
                "from_entity": {
                    "type": log.from_entity_type,
                    "id": str(log.from_entity_id),
                },
                "to_entity": {
                    "type": log.to_entity_type,
                    "id": str(log.to_entity_id),
                },
                "performed_by": str(log.performed_by),
                "timestamp": log.timestamp.isoformat(),
                "reason": log.reason,
                "permission": log.permission,
                "is_external": log.is_external == "true",
                "revoked_at": log.revoked_at.isoformat() if log.revoked_at else None,
                "revoked_by": str(log.revoked_by) if log.revoked_by else None,
            }
            for log in logs
        ]
