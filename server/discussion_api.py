"""
Discussion Layer API - The Platform's Voice
Comments, reviews, and collaborative feedback on memories and approvals
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from auth_utils import get_current_user

router = APIRouter(prefix="/comments", tags=["discussion"])

# Comments Database - Threaded discussions on memories and approvals
COMMENTS_DB = [
    {
        "id": 1,
        "memory_id": 2,  # GET-based endpoints decision
        "approval_id": None,
        "parent_id": None,  # Top-level comment
        "user_id": 456,
        "user_name": "Project Owner",
        "text": "Great decision! This approach will definitely help us move faster while we debug the POST issue.",
        "created_at": "2025-01-22T17:00:00Z",
        "updated_at": "2025-01-22T17:00:00Z",
        "team_id": 1,
        "sentiment": "positive",
        "metadata": {
            "comment_type": "feedback",
            "edited": False,
            "reactions": {"👍": 2, "💡": 1}
        }
    },
    {
        "id": 2,
        "memory_id": 2,
        "approval_id": None,
        "parent_id": 1,  # Reply to comment 1
        "user_id": 123,
        "user_name": "Team Admin",
        "text": "Thanks! I was worried it might seem like a hack, but it's actually quite elegant for our use case.",
        "created_at": "2025-01-22T17:15:00Z",
        "updated_at": "2025-01-22T17:15:00Z",
        "team_id": 1,
        "sentiment": "neutral",
        "metadata": {
            "comment_type": "response",
            "edited": False,
            "reactions": {"👍": 1}
        }
    },
    {
        "id": 3,
        "memory_id": 1,  # Authentication performance note
        "approval_id": None,
        "parent_id": None,
        "user_id": 789,
        "user_name": "Team Member",
        "text": "Have you considered using FastAPI's background tasks for this? Might be worth exploring.",
        "created_at": "2025-01-23T09:30:00Z",
        "updated_at": "2025-01-23T09:30:00Z",
        "team_id": 1,
        "sentiment": "constructive",
        "metadata": {
            "comment_type": "suggestion",
            "edited": False,
            "reactions": {"🤔": 1, "💡": 2}
        }
    },
    {
        "id": 4,
        "memory_id": None,
        "approval_id": 1,  # Comment on approval process
        "parent_id": None,
        "user_id": 789,
        "user_name": "Team Member",
        "text": "The approval process worked really smoothly here. Clear submission note made it easy to review.",
        "created_at": "2025-01-22T18:00:00Z",
        "updated_at": "2025-01-22T18:00:00Z",
        "team_id": 1,
        "sentiment": "positive",
        "metadata": {
            "comment_type": "process_feedback",
            "edited": False,
            "reactions": {"✅": 3}
        }
    },
    {
        "id": 5,
        "memory_id": 3,  # Code review memory
        "approval_id": None,
        "parent_id": None,
        "user_id": 123,
        "user_name": "Team Admin",
        "text": "This review was incredibly thorough. Really appreciate the detailed analysis of the auth flow.",
        "created_at": "2025-01-25T10:45:00Z",
        "updated_at": "2025-01-25T10:45:00Z",
        "team_id": 1,
        "sentiment": "appreciative",
        "metadata": {
            "comment_type": "appreciation",
            "edited": False,
            "reactions": {"🙏": 2, "⭐": 1}
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

def can_access_memory_comments(user_id: int, memory_id: int, user_role: str) -> bool:
    """Check if user can access comments for a memory"""
    # Mock memory lookup - in real implementation, query memory system
    mock_memories = {
        1: {"user_id": 123, "team_id": None},  # Personal memory
        2: {"user_id": 123, "team_id": 1},     # Team memory
        3: {"user_id": 456, "team_id": 1},     # Team memory
        5: {"user_id": 789, "team_id": 2}      # Team memory
    }
    
    memory = mock_memories.get(memory_id)
    if not memory:
        return False
    
    # Global admins can access all
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Personal memories - only owner can access
    if memory["team_id"] is None:
        return memory["user_id"] == user_id
    
    # Team memories - team members can access
    team_role = get_user_team_role(user_id, memory["team_id"])
    return team_role is not None

def can_access_approval_comments(user_id: int, approval_id: int, user_role: str) -> bool:
    """Check if user can access comments for an approval"""
    # Mock approval lookup - in real implementation, query approval system
    mock_approvals = {
        1: {"team_id": 1, "submitted_by": 123},
        2: {"team_id": 1, "submitted_by": 456},
        3: {"team_id": 2, "submitted_by": 789}
    }
    
    approval = mock_approvals.get(approval_id)
    if not approval:
        return False
    
    # Global admins can access all
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Team members can access team approvals
    team_role = get_user_team_role(user_id, approval["team_id"])
    return team_role is not None

def build_comment_tree(comments: List[Dict]) -> List[Dict]:
    """Build threaded comment tree from flat list"""
    comment_map = {c["id"]: {**c, "replies": []} for c in comments}
    root_comments = []
    
    for comment in comments:
        if comment["parent_id"] is None:
            root_comments.append(comment_map[comment["id"]])
        else:
            parent = comment_map.get(comment["parent_id"])
            if parent:
                parent["replies"].append(comment_map[comment["id"]])
    
    return root_comments

@router.get("/{memory_id}")
async def get_memory_comments(
    memory_id: int,
    include_approval_comments: bool = False,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comments for a specific memory"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check access to memory comments
    if not can_access_memory_comments(user_id, memory_id, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - cannot view comments for this memory"
        )
    
    # Get memory comments
    memory_comments = [c for c in COMMENTS_DB if c["memory_id"] == memory_id]
    
    # Optionally include approval comments for this memory
    approval_comments = []
    if include_approval_comments:
        # Find approvals for this memory and get their comments
        for comment in COMMENTS_DB:
            if comment["approval_id"] and comment["memory_id"] is None:
                # Mock check if this approval is for our memory
                # In real implementation, query approval system
                if comment["approval_id"] in [1, 2]:  # Mock approvals for memory_id
                    approval_comments.append(comment)
    
    all_comments = memory_comments + approval_comments
    
    # Build comment tree
    comment_tree = build_comment_tree(all_comments)
    
    # Sort by creation date (newest first)
    comment_tree.sort(key=lambda c: c["created_at"], reverse=True)
    
    return {
        "success": True,
        "memory_id": memory_id,
        "comments": comment_tree,
        "comment_count": len(all_comments),
        "metadata": {
            "memory_comments": len(memory_comments),
            "approval_comments": len(approval_comments),
            "include_approval_comments": include_approval_comments
        }
    }

@router.get("/approval/{approval_id}")
async def get_approval_comments(
    approval_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comments for a specific approval"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check access to approval comments
    if not can_access_approval_comments(user_id, approval_id, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - cannot view comments for this approval"
        )
    
    # Get approval comments
    approval_comments = [c for c in COMMENTS_DB if c["approval_id"] == approval_id]
    
    # Build comment tree
    comment_tree = build_comment_tree(approval_comments)
    
    # Sort by creation date (newest first)
    comment_tree.sort(key=lambda c: c["created_at"], reverse=True)
    
    return {
        "success": True,
        "approval_id": approval_id,
        "comments": comment_tree,
        "comment_count": len(approval_comments)
    }

@router.get("/add")
async def add_comment(
    text: str,
    mem_id: Optional[int] = None,
    approval_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    comment_type: str = "comment",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add a comment to a memory or approval"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Validate that either mem_id or approval_id is provided
    if not mem_id and not approval_id:
        raise HTTPException(
            status_code=400, 
            detail="Either mem_id or approval_id must be provided"
        )
    
    if mem_id and approval_id:
        raise HTTPException(
            status_code=400, 
            detail="Cannot comment on both memory and approval simultaneously"
        )
    
    # Check access permissions
    if mem_id:
        if not can_access_memory_comments(user_id, mem_id, user_role):
            raise HTTPException(
                status_code=403, 
                detail="Access denied - cannot comment on this memory"
            )
        target_team_id = 1  # Mock - get from memory system
    
    if approval_id:
        if not can_access_approval_comments(user_id, approval_id, user_role):
            raise HTTPException(
                status_code=403, 
                detail="Access denied - cannot comment on this approval"
            )
        target_team_id = 1  # Mock - get from approval system
    
    # Validate parent comment if replying
    if parent_id:
        parent_comment = next((c for c in COMMENTS_DB if c["id"] == parent_id), None)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        
        # Ensure parent comment is for the same target
        if mem_id and parent_comment["memory_id"] != mem_id:
            raise HTTPException(
                status_code=400, 
                detail="Parent comment is not for the specified memory"
            )
        
        if approval_id and parent_comment["approval_id"] != approval_id:
            raise HTTPException(
                status_code=400, 
                detail="Parent comment is not for the specified approval"
            )
    
    # Simple sentiment analysis (in real implementation, use ML model)
    def analyze_sentiment(text: str) -> str:
        positive_words = ["great", "excellent", "good", "thanks", "appreciate", "love", "awesome"]
        negative_words = ["bad", "terrible", "hate", "awful", "wrong", "issue", "problem"]
        constructive_words = ["suggest", "consider", "might", "could", "perhaps", "idea"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in constructive_words):
            return "constructive"
        elif any(word in text_lower for word in positive_words):
            return "positive"
        elif any(word in text_lower for word in negative_words):
            return "negative"
        else:
            return "neutral"
    
    # Create new comment
    new_comment_id = max([c["id"] for c in COMMENTS_DB]) + 1 if COMMENTS_DB else 1
    
    new_comment = {
        "id": new_comment_id,
        "memory_id": mem_id,
        "approval_id": approval_id,
        "parent_id": parent_id,
        "user_id": user_id,
        "user_name": user.get("name", f"User {user_id}"),
        "text": text,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "team_id": target_team_id,
        "sentiment": analyze_sentiment(text),
        "metadata": {
            "comment_type": comment_type,
            "edited": False,
            "reactions": {}
        }
    }
    
    COMMENTS_DB.append(new_comment)
    
    return {
        "success": True,
        "comment": new_comment,
        "message": "Comment added successfully",
        "sentiment_detected": new_comment["sentiment"]
    }

@router.get("/delete")
async def delete_comment(
    id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete a comment (only by author or admin)"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find comment
    comment = next((c for c in COMMENTS_DB if c["id"] == id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check permissions - only author or admin can delete
    if comment["user_id"] != user_id and user_role not in ["admin", "org_admin"]:
        # Team admins can delete comments in their team
        if user_role == "team_admin":
            user_team_role = get_user_team_role(user_id, comment["team_id"])
            if user_team_role != "team_admin":
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied - can only delete your own comments"
                )
        else:
            raise HTTPException(
                status_code=403, 
                detail="Access denied - can only delete your own comments"
            )
    
    # Remove comment from database
    COMMENTS_DB.remove(comment)
    
    # Also remove any replies to this comment
    replies_to_remove = [c for c in COMMENTS_DB if c["parent_id"] == id]
    for reply in replies_to_remove:
        COMMENTS_DB.remove(reply)
    
    return {
        "success": True,
        "message": f"Comment and {len(replies_to_remove)} replies deleted successfully",
        "deleted_comment": comment,
        "deleted_replies": len(replies_to_remove)
    }

@router.get("/thread/{memory_id}")
async def get_comment_thread_widget(
    memory_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comment thread data optimized for frontend widget"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check access
    if not can_access_memory_comments(user_id, memory_id, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - cannot view comments for this memory"
        )
    
    # Get memory comments
    memory_comments = [c for c in COMMENTS_DB if c["memory_id"] == memory_id]
    
    # Build comment tree
    comment_tree = build_comment_tree(memory_comments)
    
    # Sort by creation date (oldest first for better thread flow)
    comment_tree.sort(key=lambda c: c["created_at"])
    
    # Calculate thread statistics
    total_comments = len(memory_comments)
    sentiment_counts = {}
    reaction_counts = {}
    
    for comment in memory_comments:
        sentiment = comment["sentiment"]
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        for reaction, count in comment["metadata"]["reactions"].items():
            reaction_counts[reaction] = reaction_counts.get(reaction, 0) + count
    
    # Get user permissions for this thread
    user_permissions = {
        "can_comment": True,  # All team members can comment
        "can_delete_own": True,
        "can_moderate": user_role in ["admin", "org_admin", "team_admin"]
    }
    
    return {
        "success": True,
        "memory_id": memory_id,
        "thread": {
            "comments": comment_tree,
            "total_comments": total_comments,
            "sentiment_analysis": sentiment_counts,
            "reaction_summary": reaction_counts,
            "last_activity": max([c["created_at"] for c in memory_comments]) if memory_comments else None
        },
        "user_permissions": user_permissions,
        "widget_config": {
            "show_reactions": True,
            "show_sentiment": True,
            "enable_threading": True,
            "max_depth": 3,
            "sort_order": "chronological"
        }
    }

@router.get("/stats")
async def get_discussion_stats(
    days_back: int = 30,
    team_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get discussion statistics and engagement metrics"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Filter comments by time and access
    from datetime import timedelta
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    accessible_comments = []
    for comment in COMMENTS_DB:
        comment_time = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))
        if start_time <= comment_time <= end_time:
            # Check access based on team membership
            if team_filter is not None and comment["team_id"] != team_filter:
                continue
            
            # Check if user can access this comment
            can_access = False
            if user_role in ["admin", "org_admin"]:
                can_access = True
            elif comment["team_id"]:
                team_role = get_user_team_role(user_id, comment["team_id"])
                can_access = team_role is not None
            elif comment["user_id"] == user_id:
                can_access = True
            
            if can_access:
                accessible_comments.append(comment)
    
    # Calculate statistics
    stats = {
        "total_comments": len(accessible_comments),
        "sentiment_distribution": {},
        "comment_types": {},
        "reaction_popularity": {},
        "user_engagement": {},
        "memory_engagement": {},
        "approval_engagement": {},
        "thread_depth_analysis": {
            "top_level": 0,
            "replies": 0,
            "max_depth": 0
        }
    }
    
    # Analyze comments
    for comment in accessible_comments:
        # Sentiment distribution
        sentiment = comment["sentiment"]
        stats["sentiment_distribution"][sentiment] = stats["sentiment_distribution"].get(sentiment, 0) + 1
        
        # Comment types
        comment_type = comment["metadata"]["comment_type"]
        stats["comment_types"][comment_type] = stats["comment_types"].get(comment_type, 0) + 1
        
        # Reaction popularity
        for reaction, count in comment["metadata"]["reactions"].items():
            stats["reaction_popularity"][reaction] = stats["reaction_popularity"].get(reaction, 0) + count
        
        # User engagement
        user_id_comment = comment["user_id"]
        if user_id_comment not in stats["user_engagement"]:
            stats["user_engagement"][user_id_comment] = {
                "name": comment["user_name"],
                "comment_count": 0,
                "sentiment_mix": {}
            }
        stats["user_engagement"][user_id_comment]["comment_count"] += 1
        user_sentiment = stats["user_engagement"][user_id_comment]["sentiment_mix"]
        user_sentiment[sentiment] = user_sentiment.get(sentiment, 0) + 1
        
        # Memory engagement
        if comment["memory_id"]:
            memory_id = comment["memory_id"]
            stats["memory_engagement"][memory_id] = stats["memory_engagement"].get(memory_id, 0) + 1
        
        # Approval engagement
        if comment["approval_id"]:
            approval_id = comment["approval_id"]
            stats["approval_engagement"][approval_id] = stats["approval_engagement"].get(approval_id, 0) + 1
        
        # Thread depth analysis
        if comment["parent_id"] is None:
            stats["thread_depth_analysis"]["top_level"] += 1
        else:
            stats["thread_depth_analysis"]["replies"] += 1
    
    return {
        "success": True,
        "stats": stats,
        "time_window": {
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z",
            "days": days_back
        },
        "filters": {
            "team_filter": team_filter
        },
        "engagement_insights": {
            "most_discussed_memory": max(stats["memory_engagement"].items(), key=lambda x: x[1]) if stats["memory_engagement"] else None,
            "most_active_user": max(stats["user_engagement"].items(), key=lambda x: x[1]["comment_count"]) if stats["user_engagement"] else None,
            "dominant_sentiment": max(stats["sentiment_distribution"].items(), key=lambda x: x[1]) if stats["sentiment_distribution"] else None,
            "engagement_rate": len(accessible_comments) / max(days_back, 1)  # Comments per day
        }
    }
