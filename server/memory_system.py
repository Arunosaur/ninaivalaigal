"""
Memory System Integration with Team-Based Access Control
The heart of Ninaivalaigal - user and team memory management
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from auth_utils import get_current_user
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/memory", tags=["memory"])


# Memory Model (simplified for GET-based API)
class Memory:
    def __init__(
        self,
        id: int,
        user_id: int,
        team_id: Optional[int],
        content: str,
        created_at: str,
    ):
        self.id = id
        self.user_id = user_id
        self.team_id = team_id
        self.content = content
        self.created_at = created_at
        self.tags = []
        self.type = "text"  # text, url, structured


# Mock Memory Database
MEMORIES_DB = [
    {
        "id": 1,
        "user_id": 123,
        "team_id": None,  # Personal memory
        "content": "Remember to implement async authentication for better performance",
        "created_at": "2025-01-15T10:30:00Z",
        "tags": ["development", "authentication", "performance"],
        "type": "text",
    },
    {
        "id": 2,
        "user_id": 123,
        "team_id": 1,  # Team memory
        "content": "Team decision: Use GET-based endpoints for MVP to bypass POST issues",
        "created_at": "2025-01-20T14:15:00Z",
        "tags": ["team-decision", "architecture", "mvp"],
        "type": "text",
    },
    {
        "id": 3,
        "user_id": 456,
        "team_id": 1,  # Team memory from different user
        "content": "Code review: Auth system looks solid, ready for production",
        "created_at": "2025-01-22T09:45:00Z",
        "tags": ["code-review", "auth", "production"],
        "type": "text",
    },
    {
        "id": 4,
        "user_id": 123,
        "team_id": None,  # Personal structured memory
        "content": json.dumps(
            {
                "type": "URL",
                "content": "https://fastapi.tiangolo.com/advanced/middleware/",
                "tags": ["documentation", "fastapi", "middleware"],
                "team_id": None,
            }
        ),
        "created_at": "2025-01-25T16:20:00Z",
        "tags": ["documentation", "fastapi", "middleware"],
        "type": "structured",
    },
]

# Team memberships (from teams_working.py)
TEAM_MEMBERSHIPS_DB = [
    {"id": 1, "team_id": 1, "user_id": 123, "role": "team_admin"},
    {"id": 2, "team_id": 1, "user_id": 789, "role": "member"},
    {"id": 3, "team_id": 2, "user_id": 456, "role": "team_admin"},
    {"id": 4, "team_id": 2, "user_id": 123, "role": "member"},
]


def check_team_access(user_id: int, team_id: int) -> Optional[str]:
    """Check if user has access to team and return their role"""
    membership = next(
        (
            m
            for m in TEAM_MEMBERSHIPS_DB
            if m["team_id"] == team_id and m["user_id"] == user_id
        ),
        None,
    )
    return membership["role"] if membership else None


def can_access_memory(memory: Dict[str, Any], user_id: int, user_role: str) -> bool:
    """Check if user can access a specific memory"""
    # Own personal memory
    if memory["team_id"] is None and memory["user_id"] == user_id:
        return True

    # Team memory - check team membership
    if memory["team_id"] is not None:
        team_role = check_team_access(user_id, memory["team_id"])
        if team_role:  # User is a team member
            return True

    # Global admin access
    if user_role in ["admin", "org_admin"]:
        return True

    return False


@router.get("/my")
async def get_my_memories(
    team_filter: Optional[int] = None,
    tag_filter: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List user's accessible memories with optional filters"""
    user_id = user["user_id"]
    user_role = user["role"]

    # Filter memories user can access
    accessible_memories = []
    for memory in MEMORIES_DB:
        if can_access_memory(memory, user_id, user_role):
            # Apply filters
            if team_filter is not None and memory["team_id"] != team_filter:
                continue
            if tag_filter and tag_filter not in memory["tags"]:
                continue

            accessible_memories.append(memory)

    # Sort by creation date (newest first)
    accessible_memories.sort(key=lambda m: m["created_at"], reverse=True)

    return {
        "success": True,
        "memories": accessible_memories,
        "count": len(accessible_memories),
        "filters": {"team_filter": team_filter, "tag_filter": tag_filter},
        "user_id": user_id,
    }


@router.get("/create")
async def create_memory(
    content: str,
    team_id: Optional[int] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    memory_type: str = "text",
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new memory (personal or team-scoped)"""
    user_id = user["user_id"]

    # Validate team access if team_id provided
    if team_id is not None:
        team_role = check_team_access(user_id, team_id)
        if not team_role and user["role"] not in ["admin", "org_admin"]:
            raise HTTPException(
                status_code=403, detail="Access denied - not a team member"
            )

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # Create new memory
    new_memory_id = max([m["id"] for m in MEMORIES_DB]) + 1 if MEMORIES_DB else 1

    new_memory = {
        "id": new_memory_id,
        "user_id": user_id,
        "team_id": team_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "tags": tag_list,
        "type": memory_type,
    }

    MEMORIES_DB.append(new_memory)

    scope = "team" if team_id else "personal"

    return {
        "success": True,
        "memory": new_memory,
        "message": f"Memory created successfully ({scope})",
        "scope": scope,
    }


@router.get("/team/{team_id}")
async def get_team_memories(
    team_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List memories for a specific team"""
    user_id = user["user_id"]
    user_role = user["role"]

    # Check team access
    team_role = check_team_access(user_id, team_id)
    if not team_role and user_role not in ["admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Access denied - not a team member")

    # Get team memories
    team_memories = [m for m in MEMORIES_DB if m["team_id"] == team_id]
    team_memories.sort(key=lambda m: m["created_at"], reverse=True)

    return {
        "success": True,
        "memories": team_memories,
        "count": len(team_memories),
        "team_id": team_id,
        "your_role": team_role or "admin",
        "scope": "team",
    }


@router.get("/search")
async def search_memories(
    query: str,
    team_id: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Search memories by content or tags"""
    user_id = user["user_id"]
    user_role = user["role"]

    # Get accessible memories
    accessible_memories = []
    for memory in MEMORIES_DB:
        if can_access_memory(memory, user_id, user_role):
            # Apply team filter if specified
            if team_id is not None and memory["team_id"] != team_id:
                continue
            accessible_memories.append(memory)

    # Search in content and tags
    query_lower = query.lower()
    matching_memories = []

    for memory in accessible_memories:
        # Search in content
        if query_lower in memory["content"].lower():
            matching_memories.append({**memory, "match_type": "content"})
            continue

        # Search in tags
        for tag in memory["tags"]:
            if query_lower in tag.lower():
                matching_memories.append({**memory, "match_type": "tag"})
                break

    # Remove duplicates and sort by relevance
    unique_memories = []
    seen_ids = set()
    for memory in matching_memories:
        if memory["id"] not in seen_ids:
            unique_memories.append(memory)
            seen_ids.add(memory["id"])

    unique_memories.sort(key=lambda m: m["created_at"], reverse=True)

    return {
        "success": True,
        "memories": unique_memories,
        "count": len(unique_memories),
        "query": query,
        "team_filter": team_id,
        "scope": "search_results",
    }


@router.get("/tags")
async def get_available_tags(
    team_id: Optional[int] = None, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all available tags from user's accessible memories"""
    user_id = user["user_id"]
    user_role = user["role"]

    # Get accessible memories
    accessible_memories = []
    for memory in MEMORIES_DB:
        if can_access_memory(memory, user_id, user_role):
            if team_id is not None and memory["team_id"] != team_id:
                continue
            accessible_memories.append(memory)

    # Collect all tags
    all_tags = set()
    for memory in accessible_memories:
        all_tags.update(memory["tags"])

    # Count tag usage
    tag_counts = {}
    for memory in accessible_memories:
        for tag in memory["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort tags by usage
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "success": True,
        "tags": [{"tag": tag, "count": count} for tag, count in sorted_tags],
        "total_tags": len(sorted_tags),
        "team_filter": team_id,
        "scope": "tag_cloud",
    }


@router.get("/stats")
async def get_memory_stats(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get memory statistics for the user"""
    user_id = user["user_id"]
    user_role = user["role"]

    # Count accessible memories
    personal_count = 0
    team_memories = {}
    total_accessible = 0

    for memory in MEMORIES_DB:
        if can_access_memory(memory, user_id, user_role):
            total_accessible += 1

            if memory["team_id"] is None:
                personal_count += 1
            else:
                team_id = memory["team_id"]
                if team_id not in team_memories:
                    team_memories[team_id] = 0
                team_memories[team_id] += 1

    return {
        "success": True,
        "stats": {
            "total_accessible": total_accessible,
            "personal_memories": personal_count,
            "team_memories": dict(team_memories),
            "teams_with_memories": len(team_memories),
        },
        "user_id": user_id,
        "scope": "statistics",
    }
