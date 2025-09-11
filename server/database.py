# database.py - Database models and operations for mem0

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships for sharing system
    owned_contexts = relationship("RecordingContext", foreign_keys="[RecordingContext.owner_id]", back_populates="owner")
    team_memberships = relationship("TeamMember", back_populates="user")
    granted_permissions = relationship("ContextPermission", foreign_keys="[ContextPermission.granted_by]", back_populates="granted_by_user")
    user_permissions = relationship("ContextPermission", foreign_keys="[ContextPermission.user_id]")

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="organization")
    contexts = relationship("RecordingContext", back_populates="organization")
    permissions = relationship("ContextPermission", back_populates="organization")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # NULL for cross-org teams
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    contexts = relationship("RecordingContext", back_populates="team")
    permissions = relationship("ContextPermission", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class ContextPermission(Base):
    __tablename__ = "context_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(Integer, ForeignKey("recording_contexts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for team/org permissions
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL for user/org permissions
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # NULL for user/team permissions
    permission_level = Column(String(50), nullable=False)  # owner, admin, write, read
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    context = relationship("RecordingContext", back_populates="permissions")
    user = relationship("User")
    team = relationship("Team")
    organization = relationship("Organization")
    granted_by_user = relationship("User", foreign_keys=[granted_by])

# Update existing models to support sharing
class RecordingContext(Base):
    __tablename__ = "recording_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for team/org owned contexts
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL for user/org owned contexts
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # NULL for user/team owned contexts
    visibility = Column(String(50), nullable=False, default="private")  # private, team, organization, public
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    team = relationship("Team")
    organization = relationship("Organization")
    permissions = relationship("ContextPermission", back_populates="context")

class DatabaseManager:
    def __init__(self, database_url="postgresql://mem0:mem0@localhost:5432/mem0"):
        # Use different connection args for PostgreSQL vs SQLite
        if database_url.startswith("sqlite"):
            self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        else:
            self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
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
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            session = self.get_session()
            try:
                # Migrate memories
                for memory_entry in data.get("memories", []):
                    memory = Memory(
                        context=memory_entry["context"],
                        type=memory_entry["payload"]["type"],
                        source=memory_entry["payload"]["source"],
                        data=memory_entry["payload"]["data"]
                    )
                    session.add(memory)
                
                # Migrate active recording context
                active_context = data.get("recording_context")
                if active_context:
                    # Clear any existing active contexts
                    session.query(RecordingContext).update({"is_active": False})
                    
                    # Set or create the active context
                    context = session.query(RecordingContext).filter_by(name=active_context).first()
                    if context:
                        context.is_active = True
                    else:
                        context = RecordingContext(name=active_context, is_active=True)
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
    
    
    def set_active_context(self, context_name: str, user_id: int = None):
        session = self.get_session()
        try:
            # Don't clear other active contexts - allow multiple active contexts per user
            # Just set this specific context to active
            if user_id:
                context = session.query(RecordingContext).filter_by(name=context_name, user_id=user_id).first()
            else:
                context = session.query(RecordingContext).filter_by(name=context_name, user_id=None).first()
            
            if context:
                context.is_active = True
            else:
                context = RecordingContext(name=context_name, is_active=True, user_id=user_id)
                session.add(context)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def clear_active_context(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                session.query(RecordingContext).filter_by(user_id=user_id).update({"is_active": False})
            else:
                session.query(RecordingContext).update({"is_active": False})
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
                contexts = session.query(RecordingContext).filter_by(is_active=True, user_id=user_id).all()
            else:
                contexts = session.query(RecordingContext).filter_by(is_active=True, user_id=None).all()
            
            # Return the most recently created active context
            if contexts:
                latest_context = max(contexts, key=lambda c: c.created_at)
                return latest_context.name
            return None
        finally:
            session.close()
    
    def get_all_contexts(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(RecordingContext).filter_by(user_id=user_id).order_by(RecordingContext.created_at).all()
            else:
                contexts = session.query(RecordingContext).filter_by(user_id=None).order_by(RecordingContext.created_at).all()
            return [
                {
                    "name": context.name,
                    "is_active": context.is_active,
                    "created_at": context.created_at.isoformat()
                }
                for context in contexts
            ]
        finally:
            session.close()
    
    def add_memory(self, context: str, memory_type: str, source: str, data: dict, user_id: int = None):
        session = self.get_session()
        try:
            memory = Memory(
                context=context,
                type=memory_type,
                source=source,
                data=data,
                user_id=user_id
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
                memories = session.query(Memory).filter_by(context=context, user_id=user_id).order_by(Memory.created_at.desc()).all()
            else:
                memories = session.query(Memory).filter_by(context=context, user_id=None).order_by(Memory.created_at.desc()).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_all_memories(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = session.query(Memory).filter_by(user_id=user_id).order_by(Memory.created_at.desc()).all()
            else:
                memories = session.query(Memory).filter_by(user_id=None).order_by(Memory.created_at.desc()).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_recent_memories(self, limit: int = 50, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = session.query(Memory).filter_by(user_id=user_id).order_by(Memory.created_at.desc()).limit(limit).all()
            else:
                memories = session.query(Memory).filter_by(user_id=None).order_by(Memory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_contexts(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(Memory.context).filter_by(user_id=user_id).distinct().all()
            else:
                contexts = session.query(Memory.context).filter_by(user_id=None).distinct().all()
            
            return [context[0] for context in contexts if context[0]]
        finally:
            session.close()

    def start_context(self, context_name: str):
        # For MCP compatibility - could store active context state
        pass

    def stop_context(self):
        # For MCP compatibility - could clear active context state
        pass
    
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
    
    def create_team(self, name: str, organization_id: int = None, description: str = None):
        """Create a new team"""
        session = self.get_session()
        try:
            team = Team(name=name, organization_id=organization_id, description=description)
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
            existing = session.query(TeamMember).filter_by(team_id=team_id, user_id=user_id).first()
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
            return session.query(Team).join(TeamMember).filter(TeamMember.user_id == user_id).all()
        finally:
            session.close()
    
    def get_team_members(self, team_id: int):
        """Get all members of a team with their roles"""
        session = self.get_session()
        try:
            members = session.query(TeamMember, User).join(User).filter(TeamMember.team_id == team_id).all()
            return [{"user": user, "role": member.role, "joined_at": member.joined_at} for member, user in members]
        finally:
            session.close()
    
    def share_context_with_user(self, context_id: int, user_id: int, permission_level: str, granted_by: int):
        """Share a context with a specific user"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                user_id=user_id,
                permission_level=permission_level,
                granted_by=granted_by
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def share_context_with_team(self, context_id: int, team_id: int, permission_level: str, granted_by: int):
        """Share a context with a team"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                team_id=team_id,
                permission_level=permission_level,
                granted_by=granted_by
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def share_context_with_organization(self, context_id: int, organization_id: int, permission_level: str, granted_by: int):
        """Share a context with an organization"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                organization_id=organization_id,
                permission_level=permission_level,
                granted_by=granted_by
            )
            session.add(permission)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def check_context_permission(self, context_id: int, user_id: int, required_permission: str = "read"):
        """Check if a user has permission to access a context"""
        session = self.get_session()
        try:
            # First check if user owns the context
            context = session.query(RecordingContext).filter_by(id=context_id).first()
            if not context:
                return False
            
            if context.owner_id == user_id:
                return True
            
            # Check direct user permissions
            user_perm = session.query(ContextPermission).filter_by(
                context_id=context_id, user_id=user_id
            ).first()
            
            if user_perm:
                return self._has_permission_level(user_perm.permission_level, required_permission)
            
            # Check team permissions
            user_teams = session.query(TeamMember.team_id).filter_by(user_id=user_id).subquery()
            team_perm = session.query(ContextPermission).filter(
                ContextPermission.context_id == context_id,
                ContextPermission.team_id.in_(user_teams)
            ).first()
            
            if team_perm:
                return self._has_permission_level(team_perm.permission_level, required_permission)
            
            # Check organization permissions
            user_orgs = session.query(Team.organization_id).join(TeamMember).filter(
                TeamMember.user_id == user_id
            ).distinct().subquery()
            
            org_perm = session.query(ContextPermission).filter(
                ContextPermission.context_id == context_id,
                ContextPermission.organization_id.in_(user_orgs)
            ).first()
            
            if org_perm:
                return self._has_permission_level(org_perm.permission_level, required_permission)
            
            # Check context visibility
            if context.visibility == "public":
                return True
            elif context.visibility == "organization":
                # Check if user is in the same organization as context owner
                owner_orgs = session.query(Team.organization_id).join(TeamMember).filter(
                    TeamMember.user_id == context.owner_id
                ).distinct().all()
                
                user_orgs = session.query(Team.organization_id).join(TeamMember).filter(
                    TeamMember.user_id == user_id
                ).distinct().all()
                
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
            own_contexts = session.query(RecordingContext).filter_by(owner_id=user_id).all()
            
            # Get contexts shared with user directly
            user_shared = session.query(RecordingContext).join(ContextPermission).filter(
                ContextPermission.user_id == user_id
            ).all()
            
            # Get contexts shared with user's teams
            user_teams = session.query(TeamMember.team_id).filter_by(user_id=user_id).subquery()
            team_shared = session.query(RecordingContext).join(ContextPermission).filter(
                ContextPermission.team_id.in_(user_teams)
            ).all()
            
            # Get contexts shared with user's organizations
            user_orgs = session.query(Team.organization_id).join(TeamMember).filter(
                TeamMember.user_id == user_id
            ).distinct().subquery()
            
            org_shared = session.query(RecordingContext).join(ContextPermission).filter(
                ContextPermission.organization_id.in_(user_orgs)
            ).all()
            
            # Combine and deduplicate
            all_contexts = list(set(own_contexts + user_shared + team_shared + org_shared))
            
            return [
                {
                    "id": ctx.id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "visibility": ctx.visibility,
                    "is_active": ctx.is_active,
                    "created_at": ctx.created_at.isoformat(),
                    "owner": ctx.owner.username if ctx.owner else None
                }
                for ctx in all_contexts
            ]
            
        finally:
            session.close()
            raise e
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(id=user_id, is_active=True).first()
        finally:
            session.close()
    
    def get_user_by_username(self, username: str):
        """Get user by username"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(username=username, is_active=True).first()
        finally:
            session.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
