# database.py - Database models and operations for mem0

import json
import os
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
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class User(Base):
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


class ContextPermission(Base):
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


# New models for user management system
class OrganizationRegistration(Base):
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


# Update existing models to support sharing
class Context(Base):
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


class DatabaseManager:
    def __init__(self, config="postgresql://mem0user:mem0pass@localhost:5432/mem0db"):
        # Handle both string URL and config dict
        if isinstance(config, dict):
            database_url = config.get(
                "database_url", "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
            )
        else:
            database_url = config

        # Ensure we always use PostgreSQL
        if not database_url.startswith("postgresql"):
            database_url = "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        print(f"🐘 Using PostgreSQL: {database_url}")

        # PostgreSQL connection with pool settings
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()

    def migrate_from_json(self, json_file="mem0_data.json"):
        """Migrate existing JSON data to database"""
        if not os.path.exists(json_file):
            return

        try:
            with open(json_file) as f:
                data = json.load(f)

            session = self.get_session()
            try:
                # Migrate memories
                for memory_entry in data.get("memories", []):
                    memory = Memory(
                        context=memory_entry["context"],
                        type=memory_entry["payload"]["type"],
                        source=memory_entry["payload"]["source"],
                        data=memory_entry["payload"]["data"],
                    )
                    session.add(memory)

                # Migrate active recording context
                active_context = data.get("recording_context")
                if active_context:
                    # Clear any existing active contexts
                    session.query(Context).update({"is_active": False})

                    # Set or create the active context
                    context = (
                        session.query(Context).filter_by(name=active_context).first()
                    )
                    if context:
                        context.is_active = True
                    else:
                        context = Context(name=active_context, is_active=True)
                        session.add(context)

                session.commit()
                print(f"Successfully migrated data from {json_file}")

                # Backup the original file
                backup_file = f"{json_file}.backup"
                os.rename(json_file, backup_file)
                print(f"Original file backed up to {backup_file}")

            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            print(f"Error migrating from JSON: {e}")

    def set_active_context(
        self, context_name: str, user_id: int = None, scope: str = None
    ):
        session = self.get_session()
        try:
            context = self.resolve_context(context_name, user_id, scope, session)

            if context:
                context.is_active = True
            else:
                # Create new personal context if not found
                context = Context(
                    name=context_name,
                    is_active=True,
                    owner_id=user_id,
                    scope="personal",
                )
                session.add(context)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_context(
        self,
        name: str,
        description: str = None,
        user_id: int = None,
        team_id: int = None,
        organization_id: int = None,
        scope: str = None,
    ):
        """Create a new context with ownership scope"""
        session = self.get_session()
        try:
            # Determine scope if not provided
            if not scope:
                if user_id:
                    scope = "personal"
                elif team_id:
                    scope = "team"
                elif organization_id:
                    scope = "organization"
                else:
                    scope = "personal"  # default

            # Check if context already exists in same scope
            existing_query = session.query(Context).filter_by(name=name)
            if scope == "personal" and user_id:
                existing = existing_query.filter_by(
                    owner_id=user_id, scope=scope
                ).first()
            elif scope == "team" and team_id:
                existing = existing_query.filter_by(
                    team_id=team_id, scope=scope
                ).first()
            elif scope == "organization" and organization_id:
                existing = existing_query.filter_by(
                    organization_id=organization_id, scope=scope
                ).first()
            else:
                existing = None

            if existing:
                # Reactivate existing context instead of creating duplicate
                existing.is_active = True
                session.commit()
                session.refresh(existing)
                return existing

            context = Context(
                name=name,
                description=description or f"Context for {name}",
                owner_id=user_id if scope == "personal" else None,
                team_id=team_id if scope == "team" else None,
                organization_id=organization_id if scope == "organization" else None,
                scope=scope,
                is_active=True,
            )
            session.add(context)
            session.commit()
            session.refresh(context)
            return context
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_context(self, context_name: str, user_id: int):
        """Delete a recording context - requires user authentication"""
        if user_id is None:
            raise ValueError("User authentication required for delete operations")

        session = self.get_session()
        try:
            # Only allow deletion of contexts owned by the authenticated user
            context = (
                session.query(RecordingContext)
                .filter_by(name=context_name, owner_id=user_id)
                .first()
            )

            if context:
                # Check if context is active
                if context.is_active:
                    raise ValueError(
                        f"Cannot delete active context '{context_name}'. Stop it first."
                    )

                # Delete associated memories first (only for this user's context)
                session.query(Memory).filter_by(
                    context=context_name, user_id=user_id
                ).delete()
                # Delete the context
                session.delete(context)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def clear_active_context(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                session.query(Context).filter_by(owner_id=user_id).update(
                    {"is_active": False}
                )
            else:
                session.query(Context).update({"is_active": False})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_active_context(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = (
                    session.query(Context)
                    .filter_by(is_active=True, owner_id=user_id)
                    .all()
                )
            else:
                contexts = (
                    session.query(Context)
                    .filter_by(is_active=True, owner_id=None)
                    .all()
                )

            # Return the most recently created active context
            if contexts:
                latest_context = max(contexts, key=lambda c: c.created_at)
                return latest_context.name
            return None
        finally:
            session.close()

    def get_all_contexts(self, user_id: int = None):
        """Get all contexts accessible to a user"""
        session = self.get_session()
        try:
            if user_id:
                # Get personal contexts
                personal_contexts = (
                    session.query(Context).filter_by(owner_id=user_id).all()
                )

                # Get team contexts for user's teams
                user_teams = (
                    session.query(TeamMember.team_id)
                    .filter_by(user_id=user_id)
                    .subquery()
                )
                team_contexts = (
                    session.query(Context).filter(Context.team_id.in_(user_teams)).all()
                )

                # Get org contexts for user's organizations
                user_orgs = (
                    session.query(Team.organization_id)
                    .join(TeamMember)
                    .filter(TeamMember.user_id == user_id)
                    .distinct()
                    .subquery()
                )
                org_contexts = (
                    session.query(Context)
                    .filter(Context.organization_id.in_(user_orgs))
                    .all()
                )

                # Combine all contexts
                all_contexts = personal_contexts + team_contexts + org_contexts
            else:
                all_contexts = (
                    session.query(Context)
                    .filter_by(owner_id=None)
                    .order_by(Context.created_at)
                    .all()
                )

            return [
                {
                    "name": context.name,
                    "scope": context.scope or "personal",
                    "is_active": context.is_active,
                    "created_at": context.created_at.isoformat(),
                    "team_name": context.team.name if context.team else None,
                    "org_name": context.organization.name
                    if context.organization
                    else None,
                }
                for context in all_contexts
            ]
        finally:
            session.close()

    def resolve_context(
        self, context_name: str, user_id: int = None, scope: str = None, session=None
    ):
        """Resolve context based on name, user access, and scope priority"""
        if not session:
            session = self.get_session()
            close_session = True
        else:
            close_session = False

        try:
            contexts = []

            if scope == "personal":
                context = (
                    session.query(Context)
                    .filter_by(name=context_name, owner_id=user_id)
                    .first()
                )
                return context
            elif scope == "team":
                # Get user's teams and find team contexts
                user_teams = (
                    session.query(TeamMember.team_id)
                    .filter_by(user_id=user_id)
                    .subquery()
                )
                context = (
                    session.query(Context)
                    .filter(
                        Context.name == context_name, Context.team_id.in_(user_teams)
                    )
                    .first()
                )
                return context
            elif scope == "organization":
                # Get user's organizations and find org contexts
                user_orgs = (
                    session.query(Team.organization_id)
                    .join(TeamMember)
                    .filter(TeamMember.user_id == user_id)
                    .distinct()
                    .subquery()
                )
                context = (
                    session.query(Context)
                    .filter(
                        Context.name == context_name,
                        Context.organization_id.in_(user_orgs),
                    )
                    .first()
                )
                return context
            else:
                # Auto-resolve with priority: personal > team > org > shared

                # 1. Personal contexts (highest priority)
                personal = (
                    session.query(Context)
                    .filter_by(name=context_name, owner_id=user_id)
                    .first()
                )
                if personal:
                    contexts.append(("personal", personal))

                # 2. Team contexts
                user_teams = (
                    session.query(TeamMember.team_id)
                    .filter_by(user_id=user_id)
                    .subquery()
                )
                team_contexts = (
                    session.query(Context)
                    .filter(
                        Context.name == context_name, Context.team_id.in_(user_teams)
                    )
                    .all()
                )
                for ctx in team_contexts:
                    contexts.append(("team", ctx))

                # 3. Organization contexts
                user_orgs = (
                    session.query(Team.organization_id)
                    .join(TeamMember)
                    .filter(TeamMember.user_id == user_id)
                    .distinct()
                    .subquery()
                )
                org_contexts = (
                    session.query(Context)
                    .filter(
                        Context.name == context_name,
                        Context.organization_id.in_(user_orgs),
                    )
                    .all()
                )
                for ctx in org_contexts:
                    contexts.append(("organization", ctx))

                # 4. Shared contexts (via permissions)
                shared_contexts = (
                    session.query(Context)
                    .join(ContextPermission)
                    .filter(
                        Context.name == context_name,
                        ContextPermission.user_id == user_id,
                    )
                    .all()
                )
                for ctx in shared_contexts:
                    contexts.append(("shared", ctx))

                if len(contexts) == 1:
                    return contexts[0][1]
                elif len(contexts) > 1:
                    # Return highest priority (personal first)
                    return contexts[0][1]
                else:
                    return None
        finally:
            if close_session:
                session.close()

    def add_memory(
        self,
        context: str,
        memory_type: str,
        source: str,
        data: dict,
        user_id: int = None,
    ):
        session = self.get_session()
        try:
            memory = Memory(
                context=context,
                type=memory_type,
                source=source,
                data=data,
                user_id=user_id,
            )
            session.add(memory)
            session.commit()
            return memory.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_memories(self, context: str, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = (
                    session.query(Memory)
                    .filter_by(context=context, user_id=user_id)
                    .order_by(Memory.created_at.desc())
                    .all()
                )
            else:
                memories = (
                    session.query(Memory)
                    .filter_by(context=context, user_id=None)
                    .order_by(Memory.created_at.desc())
                    .all()
                )

            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "created_at": memory.created_at.isoformat(),
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_all_memories(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = (
                    session.query(Memory)
                    .filter_by(user_id=user_id)
                    .order_by(Memory.created_at.desc())
                    .all()
                )
            else:
                memories = (
                    session.query(Memory)
                    .filter_by(user_id=None)
                    .order_by(Memory.created_at.desc())
                    .all()
                )

            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat(),
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_recent_memories(self, limit: int = 50, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = (
                    session.query(Memory)
                    .filter_by(user_id=user_id)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .all()
                )
            else:
                memories = (
                    session.query(Memory)
                    .filter_by(user_id=None)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .all()
                )

            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat(),
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_contexts(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = (
                    session.query(Memory.context)
                    .filter_by(user_id=user_id)
                    .distinct()
                    .all()
                )
            else:
                contexts = (
                    session.query(Memory.context)
                    .filter_by(user_id=None)
                    .distinct()
                    .all()
                )

            return [context[0] for context in contexts if context[0]]
        finally:
            session.close()

    def start_context(self, context_name: str):
        # For MCP compatibility - could store active context state
        pass

    def stop_context(self, context_name: str = None):
        """Stop recording context - either specific context or all active contexts"""
        session = self.get_session()
        try:
            if context_name:
                # Stop specific context
                context = session.query(Context).filter_by(name=context_name).first()
                if context:
                    context.is_active = False
                    session.commit()
                    return context_name
                else:
                    raise ValueError(f"Context '{context_name}' not found")
            else:
                # Stop all active contexts
                active_contexts = session.query(Context).filter_by(is_active=True).all()
                stopped_contexts = []
                for context in active_contexts:
                    context.is_active = False
                    stopped_contexts.append(context.name)
                session.commit()
                return stopped_contexts
        finally:
            session.close()

    def stop_specific_context(self, context_name: str):
        """Stop specific context by name"""
        return self.stop_context(context_name)

    def create_organization(self, name: str, description: str = None):
        """Create a new organization"""
        session = self.get_session()
        try:
            org = Organization(name=name, description=description)
            session.add(org)
            session.commit()
            session.refresh(org)
            return org
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_organization_by_name(self, name: str):
        """Get organization by name"""
        session = self.get_session()
        try:
            return session.query(Organization).filter_by(name=name).first()
        finally:
            session.close()

    def create_team(
        self, name: str, organization_id: int = None, description: str = None
    ):
        """Create a new team"""
        session = self.get_session()
        try:
            team = Team(
                name=name, organization_id=organization_id, description=description
            )
            session.add(team)
            session.commit()
            session.refresh(team)
            return team
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_team_member(self, team_id: int, user_id: int, role: str = "member"):
        """Add a user to a team with a specific role"""
        session = self.get_session()
        try:
            # Check if user is already a member
            existing = (
                session.query(TeamMember)
                .filter_by(team_id=team_id, user_id=user_id)
                .first()
            )
            if existing:
                existing.role = role
            else:
                member = TeamMember(team_id=team_id, user_id=user_id, role=role)
                session.add(member)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_teams(self, user_id: int):
        """Get all teams a user belongs to"""
        session = self.get_session()
        try:
            return (
                session.query(Team)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .all()
            )
        finally:
            session.close()

    def get_all_organizations(self):
        """Get all organizations"""
        session = self.get_session()
        try:
            return session.query(Organization).all()
        finally:
            session.close()

    def get_organization_teams(self, organization_id: int):
        """Get all teams in an organization"""
        session = self.get_session()
        try:
            return session.query(Team).filter_by(organization_id=organization_id).all()
        finally:
            session.close()

    def get_user_organizations(self, user_id: int):
        """Get all organizations a user belongs to (via teams)"""
        session = self.get_session()
        try:
            # Simple approach: get organizations through team memberships
            orgs = (
                session.query(Organization)
                .join(Team)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .all()
            )
            # Remove duplicates manually to avoid DISTINCT on JSON columns
            seen_ids = set()
            unique_orgs = []
            for org in orgs:
                if org.id not in seen_ids:
                    seen_ids.add(org.id)
                    unique_orgs.append(org)
            return unique_orgs
        finally:
            session.close()

    def get_team_members(self, team_id: int):
        """Get all members of a team with their roles"""
        session = self.get_session()
        try:
            members = (
                session.query(TeamMember, User)
                .join(User)
                .filter(TeamMember.team_id == team_id)
                .all()
            )
            return [
                {"user": user, "role": member.role, "joined_at": member.joined_at}
                for member, user in members
            ]
        finally:
            session.close()

    def remove_team_member(self, team_id: int, user_id: int):
        """Remove a member from a team"""
        session = self.get_session()
        try:
            member = (
                session.query(TeamMember)
                .filter_by(team_id=team_id, user_id=user_id)
                .first()
            )
            if member:
                session.delete(member)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def share_context_with_user(
        self, context_id: int, user_id: int, permission_level: str, granted_by: int
    ):
        """Share a context with a specific user"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                user_id=user_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def share_context_with_team(
        self, context_id: int, team_id: int, permission_level: str, granted_by: int
    ):
        """Share a context with a team"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                team_id=team_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def share_context_with_organization(
        self,
        context_id: int,
        organization_id: int,
        permission_level: str,
        granted_by: int,
    ):
        """Share a context with an organization"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                organization_id=organization_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def check_context_permission(
        self, context_id: int, user_id: int, required_permission: str = "read"
    ):
        """Check if a user has permission to access a context"""
        session = self.get_session()
        try:
            # First check if user owns the context
            context = session.query(Context).filter_by(id=context_id).first()
            if not context:
                return False

            if context.owner_id == user_id:
                return True

            # Check direct user permissions
            user_perm = (
                session.query(ContextPermission)
                .filter_by(context_id=context_id, user_id=user_id)
                .first()
            )

            if user_perm:
                return self._has_permission_level(
                    user_perm.permission_level, required_permission
                )

            # Check team permissions
            user_teams = (
                session.query(TeamMember.team_id).filter_by(user_id=user_id).subquery()
            )
            team_perm = (
                session.query(ContextPermission)
                .filter(
                    ContextPermission.context_id == context_id,
                    ContextPermission.team_id.in_(user_teams),
                )
                .first()
            )

            if team_perm:
                return self._has_permission_level(
                    team_perm.permission_level, required_permission
                )

            # Check organization permissions
            user_orgs = (
                session.query(Team.organization_id)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .distinct()
                .subquery()
            )

            org_perm = (
                session.query(ContextPermission)
                .filter(
                    ContextPermission.context_id == context_id,
                    ContextPermission.organization_id.in_(user_orgs),
                )
                .first()
            )

            if org_perm:
                return self._has_permission_level(
                    org_perm.permission_level, required_permission
                )

            # Check context visibility
            if context.visibility == "public":
                return True
            elif context.visibility == "organization":
                # Check if user is in the same organization as context owner
                owner_orgs = (
                    session.query(Team.organization_id)
                    .join(TeamMember)
                    .filter(TeamMember.user_id == context.owner_id)
                    .distinct()
                    .all()
                )

                user_orgs = (
                    session.query(Team.organization_id)
                    .join(TeamMember)
                    .filter(TeamMember.user_id == user_id)
                    .distinct()
                    .all()
                )

                return bool(set(owner_orgs) & set(user_orgs))

            return False

        finally:
            session.close()

    def _has_permission_level(self, user_level: str, required_level: str) -> bool:
        """Check if user permission level meets required level"""
        levels = {"read": 1, "write": 2, "admin": 3, "owner": 4}
        return levels.get(user_level, 0) >= levels.get(required_level, 999)

    def get_user_contexts(self, user_id: int):
        """Get all contexts a user can access"""
        session = self.get_session()
        try:
            # Get user's own contexts
            own_contexts = session.query(Context).filter_by(owner_id=user_id).all()

            # Get contexts shared with user directly
            user_shared = (
                session.query(Context)
                .join(ContextPermission)
                .filter(ContextPermission.user_id == user_id)
                .all()
            )

            # Get contexts shared with user's teams
            user_teams = (
                session.query(TeamMember.team_id).filter_by(user_id=user_id).subquery()
            )
            team_shared = (
                session.query(Context)
                .join(ContextPermission)
                .filter(ContextPermission.team_id.in_(user_teams))
                .all()
            )

            # Get contexts shared with user's organizations
            user_orgs = (
                session.query(Team.organization_id)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .distinct()
                .subquery()
            )

            org_shared = (
                session.query(Context)
                .join(ContextPermission)
                .filter(ContextPermission.organization_id.in_(user_orgs))
                .all()
            )

            # Combine and deduplicate
            all_contexts = list(
                set(own_contexts + user_shared + team_shared + org_shared)
            )

            return [
                {
                    "id": ctx.id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "visibility": ctx.visibility,
                    "is_active": ctx.is_active,
                    "created_at": ctx.created_at.isoformat(),
                    "owner": ctx.owner.username if ctx.owner else None,
                }
                for ctx in all_contexts
            ]

        finally:
            session.close()

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def get_user_by_email(self, email):
        """Get user by email"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def get_user_by_username(self, username: str):
        """Get user by username"""
        session = self.get_session()
        try:
            return (
                session.query(User).filter_by(username=username, is_active=True).first()
            )
        finally:
            session.close()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Global database instance
_db_instance = None


def get_db():
    """Get database manager instance"""
    global _db_instance
    if _db_instance is None:
        # Get database URL from environment
        database_url = (
            os.getenv("NINAIVALAIGAL_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        )
        _db_instance = DatabaseManager(database_url)
    return _db_instance
