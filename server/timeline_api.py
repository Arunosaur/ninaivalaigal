"""
Knowledge Timeline API - Chronological Graph View
Shows the evolution of knowledge and decisions with approval milestones
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from auth_utils import get_current_user

router = APIRouter(prefix="/timeline", tags=["timeline"])

# Mock data from our existing systems
# In real implementation, this would query memory_system, approval_workflows, context_scoping

# Timeline Events - Chronological view of all activities
TIMELINE_EVENTS = [
    {
        "id": 1,
        "timestamp": "2025-01-15T10:00:00Z",
        "event_type": "memory_created",
        "user_id": 123,
        "user_name": "Team Admin",
        "title": "Authentication Performance Note",
        "description": "Remember to implement async authentication for better performance",
        "memory_id": 1,
        "team_id": None,
        "context_id": None,
        "tags": ["development", "authentication", "performance"],
        "metadata": {
            "memory_type": "text",
            "scope": "personal"
        }
    },
    {
        "id": 2,
        "timestamp": "2025-01-20T14:20:00Z",
        "event_type": "memory_created",
        "user_id": 123,
        "user_name": "Team Admin",
        "title": "GET-based Endpoints Decision",
        "description": "Team decision: Use GET-based endpoints for MVP to bypass POST issues",
        "memory_id": 2,
        "team_id": 1,
        "context_id": 1,
        "tags": ["team-decision", "architecture", "mvp"],
        "metadata": {
            "memory_type": "text",
            "scope": "team"
        }
    },
    {
        "id": 3,
        "timestamp": "2025-01-20T14:30:00Z",
        "event_type": "context_created",
        "user_id": 123,
        "user_name": "Team Admin",
        "title": "Auth System Development Context",
        "description": "Created context for organizing authentication system work",
        "context_id": 1,
        "team_id": 1,
        "tags": ["authentication", "development", "security"],
        "metadata": {
            "context_type": "project",
            "scope": "team"
        }
    },
    {
        "id": 4,
        "timestamp": "2025-01-22T10:00:00Z",
        "event_type": "approval_submitted",
        "user_id": 123,
        "user_name": "Team Admin",
        "title": "Submitted for Team Approval",
        "description": "GET-based endpoints decision submitted for team approval",
        "memory_id": 2,
        "approval_id": 1,
        "team_id": 1,
        "context_id": 1,
        "tags": ["approval", "team-decision"],
        "metadata": {
            "submission_note": "Important architectural decision for the team",
            "scope": "team"
        }
    },
    {
        "id": 5,
        "timestamp": "2025-01-22T16:45:00Z",
        "event_type": "approval_approved",
        "user_id": 456,
        "user_name": "Project Owner",
        "title": "Decision Approved",
        "description": "GET-based endpoints decision approved for team sharing",
        "memory_id": 2,
        "approval_id": 1,
        "team_id": 1,
        "context_id": 1,
        "tags": ["approval", "approved"],
        "metadata": {
            "review_note": "Approved - excellent analysis and ready for team sharing",
            "reviewer_role": "team_admin",
            "scope": "team"
        }
    },
    {
        "id": 6,
        "timestamp": "2025-01-25T09:15:00Z",
        "event_type": "memory_linked",
        "user_id": 123,
        "user_name": "Team Admin",
        "title": "Memory Linked to Context",
        "description": "Authentication note linked to Auth System Development context",
        "memory_id": 1,
        "context_id": 1,
        "team_id": 1,
        "tags": ["linking", "organization"],
        "metadata": {
            "relationship_type": "belongs_to",
            "relevance_score": 0.95,
            "scope": "team"
        }
    },
    {
        "id": 7,
        "timestamp": "2025-01-26T11:30:00Z",
        "event_type": "memory_created",
        "user_id": 789,
        "user_name": "Team Member",
        "title": "Performance Optimization Results",
        "description": "Database queries reduced by 40% through optimization",
        "memory_id": 5,
        "team_id": 2,
        "context_id": 3,
        "tags": ["performance", "optimization", "database"],
        "metadata": {
            "memory_type": "text",
            "scope": "team"
        }
    },
    {
        "id": 8,
        "timestamp": "2025-01-26T14:00:00Z",
        "event_type": "approval_submitted",
        "user_id": 789,
        "user_name": "Team Member",
        "title": "Performance Results Submitted",
        "description": "Performance optimization results submitted for team approval",
        "memory_id": 5,
        "approval_id": 3,
        "team_id": 2,
        "context_id": 3,
        "tags": ["approval", "performance"],
        "metadata": {
            "submission_note": "Performance improvement results to share with team",
            "scope": "team"
        }
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

def can_view_team_timeline(user_id: int, team_id: int, user_role: str) -> bool:
    """Check if user can view team timeline"""
    # Global admins can see all
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Team members can see their team's timeline
    team_role = get_user_team_role(user_id, team_id)
    return team_role is not None

def filter_events_by_access(events: List[Dict], user_id: int, user_role: str) -> List[Dict]:
    """Filter timeline events based on user access permissions"""
    accessible_events = []
    
    for event in events:
        can_view = False
        
        # Personal events - only owner can see
        if event.get("team_id") is None:
            can_view = event["user_id"] == user_id or user_role in ["admin", "org_admin"]
        
        # Team events - team members can see
        elif event.get("team_id"):
            can_view = can_view_team_timeline(user_id, event["team_id"], user_role)
        
        # Global admins can see everything
        if user_role in ["admin", "org_admin"]:
            can_view = True
        
        if can_view:
            accessible_events.append(event)
    
    return accessible_events

@router.get("/my")
async def get_my_timeline(
    days_back: int = 30,
    event_types: Optional[str] = None,
    team_filter: Optional[int] = None,
    context_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's timeline of knowledge activities"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Filter events by time window
    filtered_events = []
    for event in TIMELINE_EVENTS:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if start_time <= event_time <= end_time:
            filtered_events.append(event)
    
    # Filter by access permissions
    accessible_events = filter_events_by_access(filtered_events, user_id, user_role)
    
    # Apply additional filters
    if event_types:
        type_list = [t.strip() for t in event_types.split(",")]
        accessible_events = [e for e in accessible_events if e["event_type"] in type_list]
    
    if team_filter is not None:
        accessible_events = [e for e in accessible_events if e.get("team_id") == team_filter]
    
    if context_filter is not None:
        accessible_events = [e for e in accessible_events if e.get("context_id") == context_filter]
    
    # Sort by timestamp (newest first)
    accessible_events.sort(key=lambda e: e["timestamp"], reverse=True)
    
    return {
        "success": True,
        "timeline": accessible_events,
        "count": len(accessible_events),
        "filters": {
            "days_back": days_back,
            "event_types": event_types,
            "team_filter": team_filter,
            "context_filter": context_filter
        },
        "time_window": {
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z"
        },
        "user_id": user_id
    }

@router.get("/team/{team_id}")
async def get_team_timeline(
    team_id: int,
    days_back: int = 30,
    event_types: Optional[str] = None,
    context_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get timeline for a specific team"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check team access
    if not can_view_team_timeline(user_id, team_id, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - not a team member"
        )
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Filter events for this team and time window
    team_events = []
    for event in TIMELINE_EVENTS:
        if event.get("team_id") == team_id:
            event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            if start_time <= event_time <= end_time:
                team_events.append(event)
    
    # Apply additional filters
    if event_types:
        type_list = [t.strip() for t in event_types.split(",")]
        team_events = [e for e in team_events if e["event_type"] in type_list]
    
    if context_filter is not None:
        team_events = [e for e in team_events if e.get("context_id") == context_filter]
    
    # Sort by timestamp (newest first)
    team_events.sort(key=lambda e: e["timestamp"], reverse=True)
    
    return {
        "success": True,
        "team_id": team_id,
        "timeline": team_events,
        "count": len(team_events),
        "filters": {
            "days_back": days_back,
            "event_types": event_types,
            "context_filter": context_filter
        },
        "time_window": {
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z"
        },
        "user_permissions": {
            "team_role": get_user_team_role(user_id, team_id),
            "can_view": True
        }
    }

@router.get("/context/{context_id}")
async def get_context_timeline(
    context_id: int,
    days_back: int = 30,
    event_types: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get timeline for a specific context"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Filter events for this context and time window
    context_events = []
    for event in TIMELINE_EVENTS:
        if event.get("context_id") == context_id:
            event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            if start_time <= event_time <= end_time:
                context_events.append(event)
    
    # Filter by access permissions
    accessible_events = filter_events_by_access(context_events, user_id, user_role)
    
    # Apply additional filters
    if event_types:
        type_list = [t.strip() for t in event_types.split(",")]
        accessible_events = [e for e in accessible_events if e["event_type"] in type_list]
    
    # Sort by timestamp (newest first)
    accessible_events.sort(key=lambda e: e["timestamp"], reverse=True)
    
    return {
        "success": True,
        "context_id": context_id,
        "timeline": accessible_events,
        "count": len(accessible_events),
        "filters": {
            "days_back": days_back,
            "event_types": event_types
        },
        "time_window": {
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z"
        }
    }

@router.get("/visualization")
async def get_timeline_visualization(
    days_back: int = 30,
    team_filter: Optional[int] = None,
    granularity: str = "day",  # day, week, month
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get timeline data formatted for D3.js visualization"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Get accessible events
    filtered_events = []
    for event in TIMELINE_EVENTS:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if start_time <= event_time <= end_time:
            filtered_events.append(event)
    
    accessible_events = filter_events_by_access(filtered_events, user_id, user_role)
    
    # Apply team filter
    if team_filter is not None:
        accessible_events = [e for e in accessible_events if e.get("team_id") == team_filter]
    
    # Group events by time granularity
    time_buckets = {}
    for event in accessible_events:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        
        # Create time bucket key based on granularity
        if granularity == "day":
            bucket_key = event_time.strftime("%Y-%m-%d")
        elif granularity == "week":
            # Get Monday of the week
            monday = event_time - timedelta(days=event_time.weekday())
            bucket_key = monday.strftime("%Y-%m-%d")
        elif granularity == "month":
            bucket_key = event_time.strftime("%Y-%m")
        else:
            bucket_key = event_time.strftime("%Y-%m-%d")
        
        if bucket_key not in time_buckets:
            time_buckets[bucket_key] = {
                "date": bucket_key,
                "events": [],
                "event_counts": {},
                "total_events": 0
            }
        
        time_buckets[bucket_key]["events"].append(event)
        time_buckets[bucket_key]["total_events"] += 1
        
        # Count by event type
        event_type = event["event_type"]
        if event_type not in time_buckets[bucket_key]["event_counts"]:
            time_buckets[bucket_key]["event_counts"][event_type] = 0
        time_buckets[bucket_key]["event_counts"][event_type] += 1
    
    # Convert to D3.js-friendly format
    timeline_data = []
    for bucket_key in sorted(time_buckets.keys()):
        bucket = time_buckets[bucket_key]
        timeline_data.append({
            "date": bucket_key,
            "total_events": bucket["total_events"],
            "event_types": bucket["event_counts"],
            "events": bucket["events"]
        })
    
    # Create nodes and links for network visualization
    nodes = []
    links = []
    node_map = {}
    
    # Add user nodes
    users_seen = set()
    for event in accessible_events:
        user_id_event = event["user_id"]
        if user_id_event not in users_seen:
            users_seen.add(user_id_event)
            node_id = f"user_{user_id_event}"
            nodes.append({
                "id": node_id,
                "type": "user",
                "label": event["user_name"],
                "group": "users"
            })
            node_map[user_id_event] = node_id
    
    # Add context/memory nodes and links
    for event in accessible_events:
        user_node = node_map[event["user_id"]]
        
        if event["event_type"] == "memory_created" and event.get("memory_id"):
            memory_node = f"memory_{event['memory_id']}"
            if memory_node not in [n["id"] for n in nodes]:
                nodes.append({
                    "id": memory_node,
                    "type": "memory",
                    "label": event["title"],
                    "group": "memories"
                })
            
            links.append({
                "source": user_node,
                "target": memory_node,
                "type": "created",
                "timestamp": event["timestamp"]
            })
        
        elif event["event_type"] == "context_created" and event.get("context_id"):
            context_node = f"context_{event['context_id']}"
            if context_node not in [n["id"] for n in nodes]:
                nodes.append({
                    "id": context_node,
                    "type": "context",
                    "label": event["title"],
                    "group": "contexts"
                })
            
            links.append({
                "source": user_node,
                "target": context_node,
                "type": "created",
                "timestamp": event["timestamp"]
            })
    
    return {
        "success": True,
        "visualization": {
            "timeline_data": timeline_data,
            "network_graph": {
                "nodes": nodes,
                "links": links
            },
            "metadata": {
                "total_events": len(accessible_events),
                "time_range": {
                    "start": start_time.isoformat() + "Z",
                    "end": end_time.isoformat() + "Z"
                },
                "granularity": granularity,
                "team_filter": team_filter
            }
        },
        "d3_config": {
            "timeline": {
                "width": 800,
                "height": 400,
                "margin": {"top": 20, "right": 30, "bottom": 40, "left": 50}
            },
            "network": {
                "width": 600,
                "height": 600,
                "force_strength": -300,
                "link_distance": 100
            }
        }
    }

@router.get("/stats")
async def get_timeline_stats(
    days_back: int = 30,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get timeline statistics and activity patterns"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Get accessible events in time window
    filtered_events = []
    for event in TIMELINE_EVENTS:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if start_time <= event_time <= end_time:
            filtered_events.append(event)
    
    accessible_events = filter_events_by_access(filtered_events, user_id, user_role)
    
    # Calculate statistics
    stats = {
        "total_events": len(accessible_events),
        "event_types": {},
        "daily_activity": {},
        "team_activity": {},
        "context_activity": {},
        "user_activity": {},
        "approval_pipeline": {
            "submitted": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0
        }
    }
    
    # Count by event type
    for event in accessible_events:
        event_type = event["event_type"]
        if event_type not in stats["event_types"]:
            stats["event_types"][event_type] = 0
        stats["event_types"][event_type] += 1
        
        # Daily activity
        event_date = event["timestamp"][:10]  # YYYY-MM-DD
        if event_date not in stats["daily_activity"]:
            stats["daily_activity"][event_date] = 0
        stats["daily_activity"][event_date] += 1
        
        # Team activity
        if event.get("team_id"):
            team_id = event["team_id"]
            if team_id not in stats["team_activity"]:
                stats["team_activity"][team_id] = 0
            stats["team_activity"][team_id] += 1
        
        # Context activity
        if event.get("context_id"):
            context_id = event["context_id"]
            if context_id not in stats["context_activity"]:
                stats["context_activity"][context_id] = 0
            stats["context_activity"][context_id] += 1
        
        # User activity
        user_id_event = event["user_id"]
        if user_id_event not in stats["user_activity"]:
            stats["user_activity"][user_id_event] = {
                "name": event["user_name"],
                "count": 0
            }
        stats["user_activity"][user_id_event]["count"] += 1
        
        # Approval pipeline
        if event_type == "approval_submitted":
            stats["approval_pipeline"]["submitted"] += 1
        elif event_type == "approval_approved":
            stats["approval_pipeline"]["approved"] += 1
        elif event_type == "approval_rejected":
            stats["approval_pipeline"]["rejected"] += 1
    
    # Calculate pending approvals (submitted but not approved/rejected)
    stats["approval_pipeline"]["pending"] = (
        stats["approval_pipeline"]["submitted"] - 
        stats["approval_pipeline"]["approved"] - 
        stats["approval_pipeline"]["rejected"]
    )
    
    return {
        "success": True,
        "stats": stats,
        "time_window": {
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z",
            "days": days_back
        },
        "user_id": user_id
    }
