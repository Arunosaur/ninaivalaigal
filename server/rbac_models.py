#!/usr/bin/env python3
"""
RBAC Database Models - Enhanced database models for Role-Based Access Control
Extends existing database schema with RBAC-specific tables and relationships
"""

from datetime import datetime

from database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from rbac.permissions import Action, Resource, Role


class RoleAssignment(Base):
    """Role assignments for users in different scopes"""

    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(SQLEnum(Role), nullable=False)
    scope_type = Column(
        String(20), nullable=False, index=True
    )  # 'global', 'org', 'team', 'context'
    scope_id = Column(String(50), nullable=True, index=True)  # ID of org/team/context
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="role_assignments"
    )
    granted_by_user = relationship("User", foreign_keys=[granted_by])

    def __repr__(self):
        return f"<RoleAssignment(user_id={self.user_id}, role={self.role.name}, scope={self.scope_type}:{self.scope_id})>"


class PermissionAudit(Base):
    """Audit log for all permission checks and access attempts"""

    __tablename__ = "permission_audits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(SQLEnum(Action), nullable=False, index=True)
    resource = Column(SQLEnum(Resource), nullable=False, index=True)
    resource_id = Column(String(50), nullable=True, index=True)
    scope_type = Column(String(20), nullable=True)  # 'global', 'org', 'team', 'context'
    scope_id = Column(String(50), nullable=True)
    allowed = Column(Boolean, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)

    # Relationships
    user = relationship("User", back_populates="permission_audits")

    def __repr__(self):
        return f"<PermissionAudit(user_id={self.user_id}, action={self.action.name}, resource={self.resource.name}, allowed={self.allowed})>"


class PermissionDelegation(Base):
    """Temporary permission delegations between users"""

    __tablename__ = "permission_delegations"

    id = Column(Integer, primary_key=True, index=True)
    delegator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delegate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource = Column(SQLEnum(Resource), nullable=False)
    actions = Column(String(255), nullable=False)  # Comma-separated action names
    resource_id = Column(String(50), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(String(50), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    reason = Column(Text, nullable=True)

    # Relationships
    delegator = relationship("User", foreign_keys=[delegator_id])
    delegate = relationship("User", foreign_keys=[delegate_id])

    def get_actions(self):
        """Get list of Action enums from stored string"""
        if not self.actions:
            return []
        return [
            Action[action.strip()]
            for action in self.actions.split(",")
            if action.strip()
        ]

    def set_actions(self, actions):
        """Set actions from list of Action enums"""
        self.actions = ",".join([action.name for action in actions])

    def __repr__(self):
        return f"<PermissionDelegation(delegator_id={self.delegator_id}, delegate_id={self.delegate_id}, resource={self.resource.name})>"


class AccessRequest(Base):
    """Requests for elevated access or permissions"""

    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource = Column(SQLEnum(Resource), nullable=False)
    action = Column(SQLEnum(Action), nullable=False)
    resource_id = Column(String(50), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(String(50), nullable=True)
    justification = Column(Text, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<AccessRequest(requester_id={self.requester_id}, resource={self.resource.name}, action={self.action.name}, status={self.status})>"


# Import User model and add RBAC relationships
from database import User
from sqlalchemy.orm import relationship

# Add RBAC relationships to User model
User.role_assignments = relationship(
    "RoleAssignment", foreign_keys="RoleAssignment.user_id", back_populates="user"
)

User.permission_audits = relationship("PermissionAudit", back_populates="user")


# Helper functions for RBAC operations
def get_user_roles(db, user_id: int, scope_type: str = None, scope_id: str = None):
    """Get all active role assignments for a user"""
    session = db.get_session()
    query = session.query(RoleAssignment).filter(
        RoleAssignment.user_id == user_id, RoleAssignment.is_active == True
    )

    if scope_type:
        query = query.filter(RoleAssignment.scope_type == scope_type)

    if scope_id:
        query = query.filter(RoleAssignment.scope_id == scope_id)

    return query.all()


def get_effective_permissions(
    db, user_id: int, scope_type: str = None, scope_id: str = None
):
    """Get effective permissions for a user in given scope"""
    from rbac.permissions import POLICY

    # Get user's role assignments
    role_assignments = get_user_roles(db, user_id, scope_type, scope_id)

    if not role_assignments:
        return {}

    # Get the highest precedence role
    roles = [ra.role for ra in role_assignments]
    from rbac.permissions import ROLE_PRECEDENCE

    effective_user_role = max(roles, key=lambda r: ROLE_PRECEDENCE.index(r))

    # Get permissions for the effective role
    permissions = {}
    for (role, resource), actions in POLICY.items():
        if role == effective_user_role:
            permissions[resource.name] = [action.name for action in actions]

    return permissions


def audit_permission_attempt(
    db,
    user_id: int,
    action: Action,
    resource: Resource,
    resource_id: str = None,
    allowed: bool = False,
    request_ip: str = None,
    user_agent: str = None,
    endpoint: str = None,
    method: str = None,
):
    """Log a permission attempt to the audit trail"""
    audit_entry = PermissionAudit(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        allowed=allowed,
        request_ip=request_ip,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
    )

    db.session.add(audit_entry)
    db.session.commit()

    return audit_entry


def assign_role(
    db,
    user_id: int,
    role: Role,
    scope_type: str,
    scope_id: str = None,
    granted_by: int = None,
    expires_at=None,
):
    """Assign a role to a user in a specific scope"""
    # Check if role assignment already exists
    existing = (
        db.session.query(RoleAssignment)
        .filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.scope_type == scope_type,
            RoleAssignment.scope_id == scope_id,
            RoleAssignment.is_active == True,
        )
        .first()
    )

    if existing:
        # Update existing assignment
        existing.role = role
        existing.granted_by = granted_by
        existing.granted_at = datetime.utcnow()
        existing.expires_at = expires_at
    else:
        # Create new assignment
        assignment = RoleAssignment(
            user_id=user_id,
            role=role,
            scope_type=scope_type,
            scope_id=scope_id,
            granted_by=granted_by,
            expires_at=expires_at,
        )
        db.session.add(assignment)

    db.session.commit()
    return assignment if not existing else existing


def revoke_role(db, user_id: int, scope_type: str, scope_id: str = None):
    """Revoke a role assignment"""
    assignment = (
        db.session.query(RoleAssignment)
        .filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.scope_type == scope_type,
            RoleAssignment.scope_id == scope_id,
            RoleAssignment.is_active == True,
        )
        .first()
    )

    if assignment:
        assignment.is_active = False
        db.session.commit()

    return assignment
