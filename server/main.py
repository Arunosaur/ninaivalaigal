# main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
from database import DatabaseManager, User, Organization, Team, TeamMember, ContextPermission, RecordingContext
from auth import (
    get_current_user_optional, create_access_token, get_current_user
)
from performance_monitor import (
    get_performance_monitor,
    record_request,
    record_db_query,
    start_performance_monitoring
)
from approval_workflow import ApprovalWorkflowManager
from auto_recording import get_auto_recorder
from token_refresh import get_token_manager, auto_refresh_tokens
from signup_api import router as signup_router
import json as json_lib

# Configuration loading
def load_config():
    config_path = "../mem0.config.json"
    default_config = {
        "storage": {
            "type": "postgresql",
            "url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        },
        "database_url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",
        "jwt_secret": "your-secret-key-here"
    }
    
    # Load from environment variables first (highest priority)
    env_database_url = os.getenv('MEM0_DATABASE_URL')
    env_jwt_secret = os.getenv('MEM0_JWT_SECRET')
    
    # Load from config file
    config = default_config.copy()
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in file_config:
                    file_config[key] = value
            config = file_config
    
    # Override with environment variables (highest priority)
    if env_database_url:
        config["database_url"] = env_database_url
    if env_jwt_secret:
        config["jwt_secret"] = env_jwt_secret
    
    return config

# Initialize database and performance monitoring
config = load_config()
if isinstance(config, str):
    database_url = config
else:
    database_url = config["database_url"]
db_manager = DatabaseManager(database_url)
db = db_manager  # Alias for backward compatibility
auto_recorder = get_auto_recorder(db_manager)
approval_manager = ApprovalWorkflowManager(db_manager)

# Performance monitoring
performance_monitor = get_performance_monitor()
start_performance_monitoring()

# Start background token refresh service
import asyncio
asyncio.create_task(auto_refresh_tokens(db_manager))

# Initialize approval workflow manager
approval_manager = ApprovalWorkflowManager(db_manager)

# Initialize auto-recorder for CCTV-style recording
auto_recorder = get_auto_recorder(db_manager)

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

class CrossTeamAccessRequest(BaseModel):
    context_id: int
    target_team_id: int
    permission_level: str  # "read", "write", "admin"
    justification: Optional[str] = None

class ApprovalAction(BaseModel):
    request_id: int
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

# --- Configuration ---
# Configuration moved to auth.py to avoid circular import
# Remove duplicate import - load_config is already defined above

# --- FastAPI App ---
app = FastAPI(
    title="mem0 API",
    description="Universal Memory Layer for AI Agents and Developers",
    version="1.0.0"
)

# Include signup/auth router
app.include_router(signup_router)

@app.post("/auth/register")
def register_user(user_data: dict):
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

@app.post("/auth/login")
def login_user(user_data: dict):
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
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mem0"}

# Serve frontend static files
import os
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_signup():
    """Serve signup page as default"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))

@app.get("/signup")
def serve_signup_page():
    """Serve signup page"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))

@app.get("/signup.html")
def serve_signup_page_html():
    """Serve signup page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))

@app.get("/login")
def serve_login_page():
    """Serve login page"""
    return FileResponse(os.path.join(frontend_dir, "login.html"))

@app.get("/login.html")
def serve_login_page_html():
    """Serve login page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "login.html"))

@app.get("/dashboard")
def serve_dashboard_page():
    """Serve dashboard page"""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))

@app.get("/dashboard.html")
def serve_dashboard_page_html():
    """Serve dashboard page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))

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

        return {"message": "Context shared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share context: {str(e)}")

@app.post("/cross-team-request")
async def request_cross_team_access(
    request_data: CrossTeamAccessRequest,
    current_user: User = Depends(get_current_user)
):
    """Request cross-team access to a context"""
    # Get user's team for the request
    user_teams = db.get_user_teams(current_user.id)
    if not user_teams:
        raise HTTPException(status_code=400, detail="User must be a member of a team to request cross-team access")
    
    # Use the first team the user belongs to as requesting team
    requesting_team_id = user_teams[0].id
    
    result = approval_manager.request_cross_team_access(
        context_id=request_data.context_id,
        requesting_team_id=requesting_team_id,
        target_team_id=request_data.target_team_id,
        requested_by=current_user.id,
        permission_level=request_data.permission_level,
        justification=request_data.justification
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/approval-action")
async def handle_approval_action(
    action_data: ApprovalAction,
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a cross-team access request"""
    if action_data.action == "approve":
        result = approval_manager.approve_request(action_data.request_id, current_user.id)
    elif action_data.action == "reject":
        result = approval_manager.reject_request(action_data.request_id, current_user.id, action_data.reason)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/pending-approvals")
async def get_pending_approvals(current_user: User = Depends(get_current_user)):
    """Get pending approval requests for user's teams"""
    user_teams = db.get_user_teams(current_user.id)
    all_requests = []
    
    for team in user_teams:
        team_requests = approval_manager.get_pending_requests_for_team(team.id)
        all_requests.extend(team_requests)
    
    return {"pending_requests": all_requests}

@app.get("/approval-status/{request_id}")
async def get_approval_status(
    request_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get status of a specific approval request"""
    result = approval_manager.get_request_status(request_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

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

@app.post("/memory")
def store_memory(entry: MemoryPayload, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Store a memory entry with user isolation and duplicate filtering"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        # Extract context from data if provided, otherwise use default
        context = entry.data.get("context", "default") if hasattr(entry, 'data') and entry.data else "default"
        
        # If Windsurf is sending to hardcoded "test-context", redirect to actual active context
        if context == "test-context" and entry.source == "zsh_session":
            active_contexts = db.get_all_contexts()
            active_context_names = [ctx.get('name') for ctx in active_contexts if ctx.get('is_active', False)]
            if active_context_names:
                # Use the first active context instead of hardcoded test-context
                context = active_context_names[0]
                # Also update the data.context field to match the redirected context
                if hasattr(entry, 'data') and entry.data:
                    entry.data["context"] = context
            else:
                # No active context - block the capture
                return {"message": "Skipped capture - no active context (camera off)", "id": None}
        
        # Skip terminal_command entries if we're getting duplicates from Windsurf
        if entry.type == "terminal_command" and entry.source == "zsh_session":
            return {"message": "Skipped duplicate terminal_command entry", "id": None}
        
        
        memory_id = db.add_memory(
            context=context,
            memory_type=entry.type,
            source=entry.source,
            data=entry.data,
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
async def start_recording(context: str, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Start CCTV-style automatic recording to a context"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        # Start automatic CCTV recording
        result = await auto_recorder.start_recording(context, user_id)
        
        if result["success"]:
            return {
                "message": result["message"],
                "context": context,
                "auto_recording": True,
                "context_id": result.get("context_id")
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

@app.post("/context/stop")
async def stop_recording(context: str = None, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Stop CCTV-style automatic recording"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None

        if context:
            # Stop specific context recording
            result = await auto_recorder.stop_recording(context)
            if result["success"]:
                return {
                    "message": result["message"],
                    "context": context,
                    "messages_recorded": result.get("messages_recorded", 0)
                }
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        else:
            # Stop all active recordings for user
            status = await auto_recorder.get_recording_status()
            stopped_contexts = []
            for context_name in list(status["contexts"].keys()):
                result = await auto_recorder.stop_recording(context_name)
                if result["success"]:
                    stopped_contexts.append(context_name)
            
            return {
                "message": f"🛑 Stopped recording for {len(stopped_contexts)} contexts",
                "stopped_contexts": stopped_contexts
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/context/status")
async def get_recording_status(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get CCTV recording status for all contexts"""
    try:
        # Use authenticated user ID or None for backward compatibility
        user_id = current_user.id if current_user else None
        
        status = await auto_recorder.get_recording_status()
        return {
            "recording_status": "🎥 CCTV Active" if status["active_contexts"] > 0 else "🔴 CCTV Inactive",
            "active_contexts": status["active_contexts"],
            "contexts": status["contexts"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recording status: {str(e)}")

@app.get("/memory/recall")
async def recall_hierarchical(query: str, context: str = None, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Hierarchical memory recall: Personal -> Team -> Organization"""
    try:
        user_id = current_user.id if current_user else None
        
        results = await auto_recorder.recall_hierarchical(query, user_id, context)
        
        return {
            "query": query,
            "context": context,
            "results": {
                "personal": results.get("personal", []),
                "team": results.get("team", []),
                "organization": results.get("organization", [])
            },
            "total_memories": len(results.get("personal", [])) + len(results.get("team", [])) + len(results.get("organization", []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recall memories: {str(e)}")

@app.post("/memory/record")
async def record_interaction(context: str, interaction_type: str, content: str, 
                           metadata: dict = None, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Record AI interaction automatically (CCTV capture)"""
    try:
        user_id = current_user.id if current_user else None
        
        success = await auto_recorder.record_interaction(context, interaction_type, content, metadata)
        
        if success:
            return {
                "message": "🎥 Interaction recorded automatically",
                "context": context,
                "type": interaction_type
            }
        else:
            return {
                "message": f"Context '{context}' not actively recording. Start recording first.",
                "context": context,
                "recording_active": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")

@app.get("/context/active")
def get_active_recording_context(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get active recording context with user isolation (legacy endpoint)"""
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

