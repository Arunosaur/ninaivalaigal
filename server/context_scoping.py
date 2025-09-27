"""
Context Scoping System - Graph-Ready Memory Organization
Links memories to context objects, enabling graph traversal and reasoning
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from auth_utils import get_current_user

router = APIRouter(prefix="/contexts", tags=["contexts"])

# Context Model - Graph nodes that organize memories
CONTEXTS_DB = [
    {
        "id": 1,
        "name": "Auth System Development",
        "description": "All memories related to authentication system development",
        "created_by": 123,
        "team_id": 1,
        "created_at": "2025-01-20T10:00:00Z",
        "context_type": "project",
        "tags": ["authentication", "development", "security"],
        "status": "active"
    },
    {
        "id": 2,
        "name": "Team Alpha Sprint Planning",
        "description": "Sprint planning and decision context for Team Alpha",
        "created_by": 123,
        "team_id": 1,
        "created_at": "2025-01-22T14:00:00Z",
        "context_type": "sprint",
        "tags": ["planning", "sprint", "team-alpha"],
        "status": "active"
    },
    {
        "id": 3,
        "name": "API Architecture Decisions",
        "description": "Architectural decisions and technical discussions",
        "created_by": 456,
        "team_id": 2,
        "created_at": "2025-01-18T09:30:00Z",
        "context_type": "architecture",
        "tags": ["architecture", "api", "decisions"],
        "status": "active"
    }
]

# Memory-Context Links - Graph edges connecting memories to contexts
MEMORY_CONTEXT_LINKS_DB = [
    {
        "id": 1,
        "memory_id": 1,  # "Remember to implement async authentication"
        "context_id": 1,  # "Auth System Development"
        "linked_by": 123,
        "linked_at": "2025-01-20T10:30:00Z",
        "relationship_type": "belongs_to",
        "relevance_score": 0.95
    },
    {
        "id": 2,
        "memory_id": 2,  # "Team decision: Use GET-based endpoints"
        "context_id": 1,  # "Auth System Development"
        "linked_by": 123,
        "linked_at": "2025-01-20T14:20:00Z",
        "relationship_type": "decision_in",
        "relevance_score": 0.90
    },
    {
        "id": 3,
        "memory_id": 2,  # Same memory can be in multiple contexts
        "context_id": 2,  # "Team Alpha Sprint Planning"
        "linked_by": 123,
        "linked_at": "2025-01-22T14:30:00Z",
        "relationship_type": "discussed_in",
        "relevance_score": 0.85
    },
    {
        "id": 4,
        "memory_id": 3,  # "Code review: Auth system looks solid"
        "context_id": 1,  # "Auth System Development"
        "linked_by": 456,
        "linked_at": "2025-01-22T16:50:00Z",
        "relationship_type": "review_of",
        "relevance_score": 0.88
    }
]

# Team memberships (from teams_working.py)
TEAM_MEMBERSHIPS_DB = [
    {"id": 1, "team_id": 1, "user_id": 123, "role": "team_admin"},
    {"id": 2, "team_id": 1, "user_id": 789, "role": "member"},
    {"id": 3, "team_id": 2, "user_id": 456, "role": "team_admin"},
    {"id": 4, "team_id": 2, "user_id": 123, "role": "member"},
]

def get_user_team_role(user_id: int, team_id: int) -> Optional[str]:
    """Get user's role in a specific team"""
    membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == user_id), 
        None
    )
    return membership["role"] if membership else None

def can_access_context(user_id: int, context: Dict[str, Any], user_role: str) -> bool:
    """Check if user can access a context"""
    # Global admins can access all contexts
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Team members can access team contexts
    if context["team_id"]:
        team_role = get_user_team_role(user_id, context["team_id"])
        return team_role is not None
    
    # Personal contexts (team_id is None) - only creator can access
    return context["created_by"] == user_id

@router.get("/create")
async def create_context(
    name: str,
    description: str = "",
    context_type: str = "general",
    team_id: Optional[int] = None,
    tags: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new context for organizing memories"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Validate team access if team_id provided
    if team_id is not None:
        team_role = get_user_team_role(user_id, team_id)
        if not team_role and user_role not in ["admin", "org_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - not a team member"
            )
    
    # Parse tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create new context
    new_context_id = max([c["id"] for c in CONTEXTS_DB]) + 1 if CONTEXTS_DB else 1
    
    new_context = {
        "id": new_context_id,
        "name": name,
        "description": description,
        "created_by": user_id,
        "team_id": team_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "context_type": context_type,
        "tags": tag_list,
        "status": "active"
    }
    
    CONTEXTS_DB.append(new_context)
    
    scope = "team" if team_id else "personal"
    
    return {
        "success": True,
        "context": new_context,
        "message": f"Context '{name}' created successfully ({scope})",
        "scope": scope
    }

@router.get("/my")
async def get_my_contexts(
    team_filter: Optional[int] = None,
    context_type_filter: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List user's accessible contexts with optional filters"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Filter contexts user can access
    accessible_contexts = []
    for context in CONTEXTS_DB:
        if can_access_context(user_id, context, user_role):
            # Apply filters
            if team_filter is not None and context["team_id"] != team_filter:
                continue
            if context_type_filter and context["context_type"] != context_type_filter:
                continue
                
            accessible_contexts.append(context)
    
    # Sort by creation date (newest first)
    accessible_contexts.sort(key=lambda c: c["created_at"], reverse=True)
    
    return {
        "success": True,
        "contexts": accessible_contexts,
        "count": len(accessible_contexts),
        "filters": {
            "team_filter": team_filter,
            "context_type_filter": context_type_filter
        },
        "user_id": user_id
    }

@router.get("/{context_id}/add-memory")
async def add_memory_to_context(
    context_id: int,
    memory_id: int,
    relationship_type: str = "belongs_to",
    relevance_score: float = 1.0,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Associate a memory with a context (create graph edge)"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find context
    context = next((c for c in CONTEXTS_DB if c["id"] == context_id), None)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Check context access
    if not can_access_context(user_id, context, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - cannot access this context"
        )
    
    # Check if link already exists
    existing_link = next(
        (l for l in MEMORY_CONTEXT_LINKS_DB 
         if l["memory_id"] == memory_id and l["context_id"] == context_id), 
        None
    )
    
    if existing_link:
        return {
            "success": False,
            "error": "Memory already linked to this context",
            "existing_link": existing_link
        }
    
    # Create new memory-context link (graph edge)
    new_link_id = max([l["id"] for l in MEMORY_CONTEXT_LINKS_DB]) + 1 if MEMORY_CONTEXT_LINKS_DB else 1
    
    new_link = {
        "id": new_link_id,
        "memory_id": memory_id,
        "context_id": context_id,
        "linked_by": user_id,
        "linked_at": datetime.utcnow().isoformat() + "Z",
        "relationship_type": relationship_type,
        "relevance_score": min(max(relevance_score, 0.0), 1.0)  # Clamp to 0-1
    }
    
    MEMORY_CONTEXT_LINKS_DB.append(new_link)
    
    return {
        "success": True,
        "link": new_link,
        "context": context,
        "message": f"Memory linked to context '{context['name']}' successfully",
        "relationship": relationship_type
    }

@router.get("/{context_id}/graph")
async def get_context_graph(
    context_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get graph representation of context with nodes and edges"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find context
    context = next((c for c in CONTEXTS_DB if c["id"] == context_id), None)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Check context access
    if not can_access_context(user_id, context, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - cannot access this context"
        )
    
    # Get all memory links for this context
    context_links = [l for l in MEMORY_CONTEXT_LINKS_DB if l["context_id"] == context_id]
    
    # Build graph nodes and edges
    nodes = []
    edges = []
    
    # Add context as central node
    nodes.append({
        "id": f"context_{context_id}",
        "type": "context",
        "label": context["name"],
        "data": context
    })
    
    # Add memory nodes and edges
    for link in context_links:
        memory_id = link["memory_id"]
        
        # Mock memory data (in real implementation, fetch from memory system)
        mock_memory = {
            "id": memory_id,
            "content": f"Memory content for ID {memory_id}",
            "tags": ["sample", "tag"],
            "created_at": "2025-01-20T10:00:00Z"
        }
        
        # Add memory node
        nodes.append({
            "id": f"memory_{memory_id}",
            "type": "memory",
            "label": mock_memory["content"][:50] + "...",
            "data": mock_memory
        })
        
        # Add edge between context and memory
        edges.append({
            "id": f"link_{link['id']}",
            "source": f"context_{context_id}",
            "target": f"memory_{memory_id}",
            "type": link["relationship_type"],
            "weight": link["relevance_score"],
            "data": link
        })
    
    return {
        "success": True,
        "context": context,
        "graph": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        },
        "metadata": {
            "context_id": context_id,
            "memory_count": len(context_links),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

@router.get("/team/{team_id}/graph")
async def get_team_context_graph(
    team_id: int,
    include_memories: bool = True,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get complete graph for team's contexts and memories"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check team access
    team_role = get_user_team_role(user_id, team_id)
    if not team_role and user_role not in ["admin", "org_admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Access denied - not a team member"
        )
    
    # Get team contexts
    team_contexts = [c for c in CONTEXTS_DB if c["team_id"] == team_id]
    
    # Build comprehensive graph
    nodes = []
    edges = []
    
    # Add team as root node
    nodes.append({
        "id": f"team_{team_id}",
        "type": "team",
        "label": f"Team {team_id}",
        "data": {"id": team_id, "type": "team"}
    })
    
    # Add context nodes and team-context edges
    for context in team_contexts:
        context_node_id = f"context_{context['id']}"
        
        nodes.append({
            "id": context_node_id,
            "type": "context",
            "label": context["name"],
            "data": context
        })
        
        # Edge from team to context
        edges.append({
            "id": f"team_context_{context['id']}",
            "source": f"team_{team_id}",
            "target": context_node_id,
            "type": "contains",
            "weight": 1.0
        })
        
        # Add memories if requested
        if include_memories:
            context_links = [l for l in MEMORY_CONTEXT_LINKS_DB if l["context_id"] == context["id"]]
            
            for link in context_links:
                memory_id = link["memory_id"]
                memory_node_id = f"memory_{memory_id}"
                
                # Add memory node if not already added
                if not any(n["id"] == memory_node_id for n in nodes):
                    mock_memory = {
                        "id": memory_id,
                        "content": f"Memory content for ID {memory_id}",
                        "tags": ["sample"],
                        "created_at": "2025-01-20T10:00:00Z"
                    }
                    
                    nodes.append({
                        "id": memory_node_id,
                        "type": "memory",
                        "label": mock_memory["content"][:30] + "...",
                        "data": mock_memory
                    })
                
                # Add context-memory edge
                edges.append({
                    "id": f"context_memory_{link['id']}",
                    "source": context_node_id,
                    "target": memory_node_id,
                    "type": link["relationship_type"],
                    "weight": link["relevance_score"],
                    "data": link
                })
    
    return {
        "success": True,
        "team_id": team_id,
        "graph": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        },
        "metadata": {
            "contexts_count": len(team_contexts),
            "user_role": team_role or user_role,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
