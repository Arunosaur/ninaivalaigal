"""
Database Models for ninaivalaigal
Extracted from monolithic database.py for better organization

This addresses external code review feedback:
- Break down monolithic files (database.py 1285 lines → focused modules)
- Improve code organization and maintainability
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model with authentication and RBAC support"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(255), unique=True, nullable=True, index=True
    )  # Made nullable for email-only signup
    email = Column(
        String(255), unique=True, nullable=False, index=True
    )  # Made required
    name = Column(String(255), nullable=False)  # Full name
    password_hash = Column(String(255), nullable=False)
    account_type = Column(
        String(50), nullable=False, default="individual"
    )  # individual, team_member, organization_admin
    subscription_tier = Column(
        String(50), nullable=False, default="free"
    )  # free, team, enterprise
    personal_contexts_limit = Column(Integer, default=10)
    role = Column(
        String(50), nullable=False, default="user"
    )  # user, admin, super_admin
    created_via = Column(
        String(50), nullable=False, default="signup"
    )  # signup, invite, admin
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # RBAC fields
    default_role = Column(String(50), default="MEMBER")
    is_system_admin = Column(Boolean, default=False)

    # Relationships for sharing system
    owned_contexts = relationship(
        "Context", foreign_keys="[Context.owner_id]", back_populates="owner"
    )
    team_memberships = relationship("TeamMember", back_populates="user")
    granted_permissions = relationship(
        "ContextPermission",
        foreign_keys="[ContextPermission.granted_by]",
        back_populates="granted_by_user",
    )
    user_permissions = relationship(
        "ContextPermission", foreign_keys="[ContextPermission.user_id]"
    )


class Memory(Base):
    """Memory storage model"""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # NULL for backward compatibility
    context = Column(String(255), index=True, nullable=False)
    type = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Organization(Base):
    """Organization model for multi-tenant support"""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)  # Company domain
    settings = Column(JSON, nullable=True)  # Organization settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = relationship("Team", back_populates="organization")
    contexts = relationship("Context", back_populates="organization")
    permissions = relationship("ContextPermission", back_populates="organization")


class Team(Base):
    """Team model for collaborative workspaces"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=True
    )  # NULL for cross-org teams
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    contexts = relationship("Context", back_populates="team")
    permissions = relationship("ContextPermission", back_populates="team")


class TeamMember(Base):
    """Team membership model with role-based access"""

    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(
        String(50), nullable=False, default="member"
    )  # owner, admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Context(Base):
    """Context model for memory organization and sharing"""

    __tablename__ = "contexts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # NULL for team/org owned contexts
    team_id = Column(
        Integer, ForeignKey("teams.id"), nullable=True
    )  # NULL for user/org owned contexts
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=True
    )  # NULL for user/team owned contexts
    visibility = Column(
        String(50), nullable=False, default="private"
    )  # private, team, organization, public
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scope = Column(String(20), nullable=True)  # personal, team, organization

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    team = relationship("Team")
    organization = relationship("Organization")
    permissions = relationship("ContextPermission", back_populates="context")


class ContextPermission(Base):
    """Context permission model for fine-grained access control"""

    __tablename__ = "context_permissions"

    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(Integer, ForeignKey("contexts.id"), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # NULL for team/org permissions
    team_id = Column(
        Integer, ForeignKey("teams.id"), nullable=True
    )  # NULL for user/org permissions
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=True
    )  # NULL for user/team permissions
    permission_level = Column(String(50), nullable=False)  # owner, admin, write, read
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships with explicit foreign_keys to resolve ambiguity
    context = relationship("Context", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], overlaps="user_permissions")
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class OrganizationRegistration(Base):
    """Organization registration model for signup tracking"""

    __tablename__ = "organization_registrations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    registration_data = Column(JSON, nullable=True)  # Additional signup data
    status = Column(
        String(50), nullable=False, default="active"
    )  # active, suspended, cancelled
    billing_email = Column(String(255), nullable=False)
    company_size = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class UserInvitation(Base):
    """User invitation model for team/organization invites"""

    __tablename__ = "user_invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="user")
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    invitation_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    team = relationship("Team")
    inviter = relationship("User")
