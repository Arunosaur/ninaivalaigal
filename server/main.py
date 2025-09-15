# main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from database import DatabaseManager, User, Context, Memory, Team, TeamMember, ContextPermission
from auth import get_db, signup_user, login_user, signup_router
from secret_redaction import redact_api_response, redact_log_message
from shell_injection_prevention import safe_run_command
from input_validation import get_api_validator, InputValidationError
from rate_limiting import rate_limit_middleware
from spec_kit import SpecKitContextManager, ContextSpec, ContextScope, ContextPermissionSpec, PermissionLevel
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
    config_path = "../ninaivalaigal.config.json"
    default_config = {
        "storage": {
            "type": "postgresql",
            "url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        },
        "database_url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",
    }
    
    # Load from environment variables first (highest priority)
    env_database_url = os.getenv('NINAIVALAIGAL_DATABASE_URL')
    env_jwt_secret = os.getenv('NINAIVALAIGAL_JWT_SECRET')
    
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

# Initialize database and spec-kit
db = DatabaseManager()
spec_context_manager = SpecKitContextManager(db)

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
# Note: Token refresh will be handled by the FastAPI server when it starts
# asyncio.create_task(auto_refresh_tokens(db_manager))  # Removed - causes issues in MCP server context

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

class ContextCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str = "personal"  # "personal", "team", "organization"
    team_id: Optional[int] = None
    organization_id: Optional[int] = None

class ContextShare(BaseModel):
    target_type: str  # "user", "team", or "organization"
    target_id: int
    permission_level: str  # "read", "write", "admin", "owner"

class ContextTransfer(BaseModel):
    target_type: str  # "user", "team", or "organization"
    target_id: int

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

# Add rate limiting middleware (before CORS)
app.middleware("http")(rate_limit_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include signup/auth router
app.include_router(signup_router)

# Remove duplicate auth endpoints - handled by signup_router

# Login endpoint handled by signup_router

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
            "created_at": org.created_at.isoformat(),
            "message": "Organization created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

@app.get("/organizations")
def get_organizations(current_user: User = Depends(get_current_user)):
    """Get all organizations"""
    try:
        organizations = db.get_all_organizations()
        return {"organizations": [
            {
                "id": org.id,
                "name": org.name,
                "description": org.description,
                "created_at": org.created_at.isoformat() if org.created_at else None
            }
            for org in organizations
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")

@app.get("/users/me/organizations")
def get_user_organizations(current_user: User = Depends(get_current_user)):
    """Get organizations the current user belongs to"""
    try:
        organizations = db.get_user_organizations(current_user.id)
        return {"organizations": [
            {
                "id": org.id,
                "name": org.name,
                "description": org.description,
                "created_at": org.created_at.isoformat()
            }
            for org in organizations
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user organizations: {str(e)}")

@app.get("/organizations/{org_id}/teams")
def get_organization_teams(org_id: int, current_user: User = Depends(get_current_user)):
    """Get all teams in an organization"""
    try:
        teams = db.get_organization_teams(org_id)
        return {"teams": [
            {
                "id": team.id,
                "name": team.name,
                "organization_id": team.organization_id,
                "description": team.description,
                "created_at": team.created_at.isoformat()
            }
            for team in teams
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization teams: {str(e)}")

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
        # Automatically add creator as team admin
        db.add_team_member(team.id, current_user.id, "admin")
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
        # In a real implementation, check if current user has permission to add members
        db.add_team_member(team_id, member_data.user_id, member_data.role)
        return {
            "success": True,
            "message": f"User {member_data.user_id} added to team {team_id} with role {member_data.role}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add team member: {str(e)}")

@app.delete("/teams/{team_id}/members/{user_id}")
def remove_team_member(team_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    """Remove a member from a team"""
    try:
        # In a real implementation, check if current user has permission to remove members
        db.remove_team_member(team_id, user_id)
        return {
            "success": True,
            "message": f"User {user_id} removed from team {team_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove team member: {str(e)}")

@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int, current_user: User = Depends(get_current_user)):
    """Get team members"""
    try:
        members = db.get_team_members(team_id)
        return {"members": [
            {
                "user_id": member["user"].id,
                "username": member["user"].username,
                "email": member["user"].email,
                "name": member["user"].name,
                "role": member["role"],
                "joined_at": member["joined_at"].isoformat()
            }
            for member in members
        ]}
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
                "description": team.description,
                "created_at": team.created_at.isoformat()
            }
            for team in teams
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user teams: {str(e)}")

@app.get("/teams")
def get_all_teams(current_user: User = Depends(get_current_user)):
    """Get all teams (admin endpoint)"""
    try:
        # In a real implementation, this would check admin permissions
        teams = db.get_user_teams(current_user.id)  # For now, just return user's teams
        return {"teams": [
            {
                "id": team.id,
                "name": team.name,
                "organization_id": team.organization_id,
                "description": team.description,
                "created_at": team.created_at.isoformat()
            }
            for team in teams
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get teams: {str(e)}")

# Context sharing endpoint
@app.post("/contexts/{context_id}/share")
def share_context(context_id: int, share_data: ContextShare, current_user: User = Depends(get_current_user)):
    """Share context with user/team/organization"""
    try:
        # Validate ownership/admin permission
        if not db.check_context_permission(context_id, current_user.id, "admin"):
            raise HTTPException(403, "Only context owners/admins can share contexts")
        
        session = db.get_session()
        try:
            # Create permission entry
            permission = ContextPermission(
                context_id=context_id,
                user_id=share_data.target_id if share_data.target_type == "user" else None,
                team_id=share_data.target_id if share_data.target_type == "team" else None,
                organization_id=share_data.target_id if share_data.target_type == "organization" else None,
                permission_level=share_data.permission_level,
                granted_by=current_user.id
            )
            session.add(permission)
            session.commit()
            
            return {
                "success": True,
                "message": f"Context shared with {share_data.target_type} {share_data.target_id}"
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
def create_context(context_data: ContextCreate, current_user: User = Depends(get_current_user)):
    """Create a new context with scope-based ownership through spec-kit"""
    try:
        # Create context spec
        spec = ContextSpec(
            name=context_data.name,
            description=context_data.description,
            scope=ContextScope(context_data.scope),
            owner_id=current_user.id if context_data.scope == "personal" else None,
            team_id=context_data.team_id if context_data.scope == "team" else None,
            organization_id=context_data.organization_id if context_data.scope == "organization" else None
        )
        
        # Use spec-kit for creation
        result = spec_context_manager.create_context(spec, current_user.id)
        
        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory")
def store_memory(entry: MemoryPayload, current_user: User = Depends(get_current_user)):
    """Store a memory entry with user isolation and duplicate filtering"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

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
def get_memory(context: str, current_user: User = Depends(get_current_user)):
    """Retrieve memories for a context with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        memories = db.get_memories(context, user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/memory/all")
def get_all_memories(current_user: User = Depends(get_current_user)):
    """Retrieve all memories with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        memories = db.get_all_memories(user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/context/start")
async def start_recording(context: str, current_user: User = Depends(get_current_user)):
    """Start CCTV-style automatic recording to a context"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

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
async def stop_recording(context: str = None, current_user: User = Depends(get_current_user)):
    """Stop CCTV-style automatic recording"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

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
async def get_recording_status(current_user: User = Depends(get_current_user)):
    """Get CCTV recording status for all contexts"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id
        
        status = await auto_recorder.get_recording_status()
        return {
            "recording_status": "🎥 CCTV Active" if status["active_contexts"] > 0 else "🔴 CCTV Inactive",
            "active_contexts": status["active_contexts"],
            "contexts": status["contexts"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recording status: {str(e)}")

@app.get("/memory/recall")
async def recall_hierarchical(query: str, context: str = None, current_user: User = Depends(get_current_user)):
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
                           metadata: dict = None, current_user: User = Depends(get_current_user)):
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
def get_active_recording_context(current_user: User = Depends(get_current_user)):
    """Get active recording context with user isolation (legacy endpoint)"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        active_context = db.get_active_context(user_id)
        return {"recording_context": active_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/contexts")
def get_all_contexts(current_user: User = Depends(get_current_user)):
    """Get all contexts with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        contexts = db.get_all_contexts(user_id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share context: {str(e)}")

@app.post("/contexts/{context_id}/transfer")
def transfer_context(context_id: int, transfer_data: ContextTransfer, current_user: User = Depends(get_current_user)):
    """Transfer context ownership"""
    try:
        session = db.get_session()
        try:
            # Get context and validate current ownership
            context = session.query(Context).filter_by(id=context_id).first()
            if not context:
                raise HTTPException(404, "Context not found")
            
            # Check if current user is owner
            is_owner = False
            if context.owner_id == current_user.id:
                is_owner = True
            elif context.team_id:
                # Check if user is team admin
                team_member = session.query(TeamMember).filter_by(
                    team_id=context.team_id,
                    user_id=current_user.id
                ).first()
                if team_member and team_member.role in ["admin", "owner"]:
                    is_owner = True
            elif context.organization_id and current_user.role == "admin":
                is_owner = True
            
            if not is_owner:
                raise HTTPException(403, "Only context owners can transfer ownership")
            
            # Update ownership based on target type
            if transfer_data.target_type == "user":
                context.owner_id = transfer_data.target_id
                context.team_id = None
                context.organization_id = None
                context.scope = "personal"
            elif transfer_data.target_type == "team":
                context.owner_id = None
                context.team_id = transfer_data.target_id
                context.organization_id = None
                context.scope = "team"
            elif transfer_data.target_type == "organization":
                context.owner_id = None
                context.team_id = None
                context.organization_id = transfer_data.target_id
                context.scope = "organization"
            
            session.commit()
            
            return {
                "success": True,
                "message": f"Context transferred to {transfer_data.target_type} {transfer_data.target_id}"
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/context/{context_name}")
def delete_context(context_name: str, current_user: User = Depends(get_current_user)):
    """Delete context with mandatory user authentication"""
    try:
        # Require authenticated user - no fallback to None
        user_id = current_user.id

        success = db.delete_context(context_name, user_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Context '{context_name}' not found or not owned by user")
        
        return {"message": f"Context '{context_name}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=13370, reload=True)
