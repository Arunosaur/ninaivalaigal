#!/usr/bin/env python3
"""
Cross-Team Memory Approval Workflow System
Handles approval requests for sharing memories between teams
"""

import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

# Import existing components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import Base, DatabaseManager


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CrossTeamApprovalRequest(Base):
    """Model for cross-team memory sharing approval requests"""

    __tablename__ = "cross_team_approval_requests"

    id = Column(Integer, primary_key=True)
    context_id = Column(
        Integer, nullable=False
    )  # Will add FK when contexts table exists
    requesting_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    target_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_level = Column(String(50), nullable=False)  # read, write, admin
    justification = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=ApprovalStatus.PENDING.value)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    # Note: RecordingContext relationship will be established when contexts table exists
    requesting_team = relationship("Team", foreign_keys=[requesting_team_id])
    target_team = relationship("Team", foreign_keys=[target_team_id])
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    rejector = relationship("User", foreign_keys=[rejected_by])


class ApprovalWorkflowManager:
    """Manages cross-team memory sharing approval workflows"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.default_expiry_days = 7  # Requests expire after 7 days

    def request_cross_team_access(
        self,
        context_id: int,
        requesting_team_id: int,
        target_team_id: int,
        requested_by: int,
        permission_level: str,
        justification: str = None,
    ) -> dict[str, Any]:
        """Create a cross-team access request"""
        session = self.db.get_session()
        try:
            # Validate permission level
            if permission_level not in ["read", "write", "admin"]:
                return {"success": False, "error": "Invalid permission level"}

            # Check if requester is member of requesting team
            if not self._is_team_member(requesting_team_id, requested_by):
                return {
                    "success": False,
                    "error": "User is not a member of the requesting team",
                }

            # Check if context belongs to target team or is accessible
            context = session.query(self.db.Context).filter_by(id=context_id).first()
            if not context:
                return {"success": False, "error": "Context not found"}

            if context.team_id != target_team_id:
                return {
                    "success": False,
                    "error": "Context does not belong to target team",
                }

            # Check for existing pending request
            existing = (
                session.query(CrossTeamApprovalRequest)
                .filter_by(
                    context_id=context_id,
                    requesting_team_id=requesting_team_id,
                    target_team_id=target_team_id,
                    status=ApprovalStatus.PENDING.value,
                )
                .first()
            )

            if existing:
                return {"success": False, "error": "Pending request already exists"}

            # Create approval request
            expires_at = datetime.utcnow() + timedelta(days=self.default_expiry_days)
            request = CrossTeamApprovalRequest(
                context_id=context_id,
                requesting_team_id=requesting_team_id,
                target_team_id=target_team_id,
                requested_by=requested_by,
                permission_level=permission_level,
                justification=justification,
                expires_at=expires_at,
            )

            session.add(request)
            session.commit()
            session.refresh(request)

            return {
                "success": True,
                "request_id": request.id,
                "expires_at": expires_at.isoformat(),
                "message": "Cross-team access request created successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def approve_request(self, request_id: int, approved_by: int) -> dict[str, Any]:
        """Approve a cross-team access request"""
        session = self.db.get_session()
        try:
            request = (
                session.query(CrossTeamApprovalRequest).filter_by(id=request_id).first()
            )
            if not request:
                return {"success": False, "error": "Request not found"}

            if request.status != ApprovalStatus.PENDING.value:
                return {
                    "success": False,
                    "error": f"Request is already {request.status}",
                }

            # Check if approver has permission (team admin/owner)
            if not self._can_approve_for_team(request.target_team_id, approved_by):
                return {
                    "success": False,
                    "error": "Insufficient permissions to approve this request",
                }

            # Check if request has expired
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED.value
                session.commit()
                return {"success": False, "error": "Request has expired"}

            # Approve the request
            request.status = ApprovalStatus.APPROVED.value
            request.approved_by = approved_by
            request.approved_at = datetime.utcnow()

            # Grant the actual permission
            self.db.share_context_with_team(
                request.context_id,
                request.requesting_team_id,
                request.permission_level,
                approved_by,
            )

            session.commit()

            return {
                "success": True,
                "message": "Request approved and permissions granted",
                "approved_at": request.approved_at.isoformat(),
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def reject_request(
        self, request_id: int, rejected_by: int, reason: str = None
    ) -> dict[str, Any]:
        """Reject a cross-team access request"""
        session = self.db.get_session()
        try:
            request = (
                session.query(CrossTeamApprovalRequest).filter_by(id=request_id).first()
            )
            if not request:
                return {"success": False, "error": "Request not found"}

            if request.status != ApprovalStatus.PENDING.value:
                return {
                    "success": False,
                    "error": f"Request is already {request.status}",
                }

            # Check if rejector has permission
            if not self._can_approve_for_team(request.target_team_id, rejected_by):
                return {
                    "success": False,
                    "error": "Insufficient permissions to reject this request",
                }

            # Reject the request
            request.status = ApprovalStatus.REJECTED.value
            request.rejected_by = rejected_by
            request.rejected_at = datetime.utcnow()
            request.rejection_reason = reason

            session.commit()

            return {
                "success": True,
                "message": "Request rejected",
                "rejected_at": request.rejected_at.isoformat(),
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def get_pending_requests_for_team(self, team_id: int) -> list[dict[str, Any]]:
        """Get all pending approval requests for a team"""
        session = self.db.get_session()
        try:
            requests = (
                session.query(CrossTeamApprovalRequest)
                .filter_by(target_team_id=team_id, status=ApprovalStatus.PENDING.value)
                .filter(CrossTeamApprovalRequest.expires_at > datetime.utcnow())
                .all()
            )

            result = []
            for req in requests:
                result.append(
                    {
                        "id": req.id,
                        "context_name": req.context.name,
                        "requesting_team": req.requesting_team.name,
                        "requester": req.requester.username,
                        "permission_level": req.permission_level,
                        "justification": req.justification,
                        "created_at": req.created_at.isoformat(),
                        "expires_at": req.expires_at.isoformat(),
                    }
                )

            return result

        finally:
            session.close()

    def get_request_status(self, request_id: int) -> dict[str, Any]:
        """Get status of a specific request"""
        session = self.db.get_session()
        try:
            request = (
                session.query(CrossTeamApprovalRequest).filter_by(id=request_id).first()
            )
            if not request:
                return {"success": False, "error": "Request not found"}

            result = {
                "id": request.id,
                "status": request.status,
                "context_name": request.context.name,
                "requesting_team": request.requesting_team.name,
                "target_team": request.target_team.name,
                "permission_level": request.permission_level,
                "created_at": request.created_at.isoformat(),
                "expires_at": request.expires_at.isoformat(),
            }

            if request.approved_at:
                result["approved_at"] = request.approved_at.isoformat()
                result["approved_by"] = request.approver.username

            if request.rejected_at:
                result["rejected_at"] = request.rejected_at.isoformat()
                result["rejected_by"] = request.rejector.username
                result["rejection_reason"] = request.rejection_reason

            return {"success": True, "request": result}

        finally:
            session.close()

    def cleanup_expired_requests(self) -> int:
        """Clean up expired requests"""
        session = self.db.get_session()
        try:
            expired_count = (
                session.query(CrossTeamApprovalRequest)
                .filter(
                    CrossTeamApprovalRequest.status == ApprovalStatus.PENDING.value,
                    CrossTeamApprovalRequest.expires_at <= datetime.utcnow(),
                )
                .update({"status": ApprovalStatus.EXPIRED.value})
            )

            session.commit()
            return expired_count

        finally:
            session.close()

    def _is_team_member(self, team_id: int, user_id: int) -> bool:
        """Check if user is a member of the team"""
        session = self.db.get_session()
        try:
            member = (
                session.query(self.db.TeamMember)
                .filter_by(team_id=team_id, user_id=user_id)
                .first()
            )
            return member is not None
        finally:
            session.close()

    def _can_approve_for_team(self, team_id: int, user_id: int) -> bool:
        """Check if user can approve requests for the team (admin or owner role)"""
        session = self.db.get_session()
        try:
            member = (
                session.query(self.db.TeamMember)
                .filter_by(team_id=team_id, user_id=user_id)
                .first()
            )

            if not member:
                return False

            return member.role in ["admin", "owner"]
        finally:
            session.close()
