# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json
import os
from database import DatabaseManager, User, Organization, Team, TeamMember, ContextPermission, RecordingContext
from auth import (
    User, UserCreate, UserLogin, Token, 
    get_current_user, get_current_user_optional, create_access_token
)
import json as json_lib

# --- Data Models ---
class MemoryPayload(BaseModel):
    type: str
    source: str
    data: dict

class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(BaseModel):
    name: str
    organization_id: Optional[int] = None
    description: Optional[str] = None

class TeamMemberAdd(BaseModel):
    user_id: int
    role: str = "member"

class ContextShare(BaseModel):
    target_type: str  # "user", "team", or "organization"
    target_id: int
    permission_level: str  # "read", "write", "admin", "owner"

# --- Configuration ---
def load_config():
    config_path = "../mem0.config.json"
    default_config = {
        "storage": {
            "database_url": "sqlite:///./mem0.db"
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json_lib.load(f)
                if "storage" in user_config and "database_url" in user_config["storage"]:
                    return user_config["storage"]["database_url"]
        return default_config["storage"]["database_url"]
    except Exception:
        return default_config["storage"]["database_url"]

# --- Database Setup ---
database_url = load_config()
db = DatabaseManager(database_url)

# Migrate existing JSON data if it exists
db.migrate_from_json()

@app.post("/auth/register", response_model=Token)
def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = db.create_user(user_data.username, user_data.password, user_data.email)
        if not user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
def login_user(user_data: UserLogin):
    """Login user and return JWT token"""
    try:
        user = db.authenticate_user(user_data.username, user_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat()
    }

# --- Organization Management ---
@app.post("/organizations")
def create_organization(org_data: OrganizationCreate, current_user: User = Depends(get_current_user)):
    """Create a new organization"""
    try:
        org = db.create_organization(org_data.name, org_data.description)
        return {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "created_at": org.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

@app.get("/organizations")
def get_organizations(current_user: User = Depends(get_current_user)):
    """Get all organizations"""
    try:
        # For now, return all organizations - could be filtered by user permissions later
        organizations = []
        # This would need to be implemented in DatabaseManager
        return {"organizations": organizations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")

# --- Team Management ---
@app.post("/teams")
def create_team(team_data: TeamCreate, current_user: User = Depends(get_current_user)):
    """Create a new team"""
    try:
        team = db.create_team(team_data.name, team_data.organization_id, team_data.description)
        return {
            "id": team.id,
            "name": team.name,
            "organization_id": team.organization_id,
            "description": team.description,
            "created_at": team.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

@app.post("/teams/{team_id}/members")
def add_team_member(team_id: int, member_data: TeamMemberAdd, current_user: User = Depends(get_current_user)):
    """Add a member to a team"""
    try:
        db.add_team_member(team_id, member_data.user_id, member_data.role)
        return {"message": f"User {member_data.user_id} added to team {team_id} with role {member_data.role}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add team member: {str(e)}")

@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int, current_user: User = Depends(get_current_user)):
    """Get team members"""
    try:
        members = db.get_team_members(team_id)
        return {"members": members}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team members: {str(e)}")

@app.get("/users/me/teams")
def get_user_teams(current_user: User = Depends(get_current_user)):
    """Get teams the current user belongs to"""
    try:
        teams = db.get_user_teams(current_user.id)
        return {"teams": [
            {
                "id": team.id,
                "name": team.name,
                "organization_id": team.organization_id,
                "description": team.description
            }
            for team in teams
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user teams: {str(e)}")

# --- Context Sharing ---
@app.post("/contexts/{context_id}/share")
def share_context(context_id: int, share_data: ContextShare, current_user: User = Depends(get_current_user)):
    """Share a context with user, team, or organization"""
    try:
        # Check if user has permission to share this context
        if not db.check_context_permission(context_id, current_user.id, "admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions to share this context")

        if share_data.target_type == "user":
            db.share_context_with_user(context_id, share_data.target_id, share_data.permission_level, current_user.id)
        elif share_data.target_type == "team":
            db.share_context_with_team(context_id, share_data.target_id, share_data.permission_level, current_user.id)
        elif share_data.target_type == "organization":
            db.share_context_with_organization(context_id, share_data.target_id, share_data.permission_level, current_user.id)
        else:
            raise HTTPException(status_code=400, detail="Invalid target_type. Must be 'user', 'team', or 'organization'")

        return {"message": f"Context {context_id} shared with {share_data.target_type} {share_data.target_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share context: {str(e)}")

@app.get("/users/me/contexts")
def get_user_accessible_contexts(current_user: User = Depends(get_current_user)):
    """Get all contexts the user can access"""
    try:
        contexts = db.get_user_contexts(current_user.id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user contexts: {str(e)}")

# --- Context Creation with Ownership ---
@app.post("/contexts")
def create_context(context_data: dict, current_user: User = Depends(get_current_user)):
    """Create a new context with ownership"""
    try:
        context_name = context_data.get("name")
        description = context_data.get("description", "")
        visibility = context_data.get("visibility", "private")

        # Create context record
        session = db.get_session()
        try:
            context = RecordingContext(
                name=context_name,
                description=description,
                owner_id=current_user.id,
                visibility=visibility
            )
            session.add(context)
            session.commit()
            session.refresh(context)
            
            return {
                "id": context.id,
                "name": context.name,
                "description": context.description,
                "owner_id": context.owner_id,
                "visibility": context.visibility,
                "created_at": context.created_at.isoformat()
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create context: {str(e)}")
    """Store a memory entry with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        memory_id = db.add_memory(
            context=entry.context,
            memory_type=entry.payload.type,
            source=entry.payload.source,
            data=entry.payload.data,
            user_id=user_id
        )
        return {"message": "Memory entry recorded.", "id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/memory")
def get_memory(context: str, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve memories for a context with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        memories = db.get_memories(context, user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/memory/all")
def get_all_memories(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve all memories with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        memories = db.get_all_memories(user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/context/start")
def start_recording(context: str, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Start recording to a context with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        db.set_active_context(context, user_id)
        return {"message": f"Now recording to context: {context}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/context/stop")
def stop_recording(context: str = None, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Stop recording with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        if context:
            # Stop specific context
            db.stop_specific_context(context, user_id)
            return {"message": f"Recording stopped for context: {context}"}
        else:
            # Stop only the currently active context
            active_context = db.get_active_context(user_id)
            if active_context:
                db.stop_specific_context(active_context, user_id)
                return {"message": f"Recording stopped for active context: {active_context}"}
            else:
                return {"message": "No active context to stop."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/context/active")
def get_active_recording_context(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get active recording context with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        active_context = db.get_active_context(user_id)
        return {"recording_context": active_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/contexts")
def get_all_contexts(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get all contexts with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        contexts = db.get_all_contexts(user_id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/context/{context_name}")
def delete_context(context_name: str, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Delete context with user isolation"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        db.delete_context(context_name, user_id)
        return {"message": f"Context '{context_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

