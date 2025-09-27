"""
Gamification API - Badge System and Leaderboards
Drives engagement through recognition and friendly competition
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from auth_utils import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/gamification", tags=["gamification"])


# Badge System
class BadgeType(str, Enum):
    TOP_COMMENTER = "top_commenter"
    FASTEST_APPROVER = "fastest_approver"
    AI_TAG_HELPER = "ai_tag_helper"
    MEMORY_CREATOR = "memory_creator"
    FEEDBACK_CHAMPION = "feedback_champion"
    KNOWLEDGE_CONNECTOR = "knowledge_connector"
    SENTIMENT_BOOSTER = "sentiment_booster"
    QUALITY_CURATOR = "quality_curator"


class BadgeLevel(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Badge(BaseModel):
    id: str
    type: BadgeType
    level: BadgeLevel
    title: str
    description: str
    icon: str
    criteria: Dict[str, Any]
    points: int
    rarity: float  # 0.0 to 1.0, lower = more rare


class UserBadge(BaseModel):
    badge: Badge
    earned_at: datetime
    progress: Dict[str, Any]
    next_level: Optional[Badge] = None


# Badge Definitions
BADGE_DEFINITIONS = {
    BadgeType.TOP_COMMENTER: {
        BadgeLevel.BRONZE: Badge(
            id="top_commenter_bronze",
            type=BadgeType.TOP_COMMENTER,
            level=BadgeLevel.BRONZE,
            title="Discussion Starter",
            description="Added 10+ thoughtful comments",
            icon="💬",
            criteria={"comments_count": 10, "avg_sentiment": 0.6},
            points=100,
            rarity=0.3,
        ),
        BadgeLevel.SILVER: Badge(
            id="top_commenter_silver",
            type=BadgeType.TOP_COMMENTER,
            level=BadgeLevel.SILVER,
            title="Conversation Catalyst",
            description="Added 50+ high-quality comments",
            icon="🗣️",
            criteria={"comments_count": 50, "avg_sentiment": 0.7},
            points=250,
            rarity=0.15,
        ),
        BadgeLevel.GOLD: Badge(
            id="top_commenter_gold",
            type=BadgeType.TOP_COMMENTER,
            level=BadgeLevel.GOLD,
            title="Discussion Master",
            description="Added 100+ exceptional comments",
            icon="🎯",
            criteria={"comments_count": 100, "avg_sentiment": 0.8},
            points=500,
            rarity=0.05,
        ),
    },
    BadgeType.FASTEST_APPROVER: {
        BadgeLevel.BRONZE: Badge(
            id="fastest_approver_bronze",
            type=BadgeType.FASTEST_APPROVER,
            level=BadgeLevel.BRONZE,
            title="Quick Reviewer",
            description="Approved 10+ memories within 2 hours",
            icon="⚡",
            criteria={"approvals_count": 10, "avg_approval_time_hours": 2},
            points=150,
            rarity=0.25,
        ),
        BadgeLevel.SILVER: Badge(
            id="fastest_approver_silver",
            type=BadgeType.FASTEST_APPROVER,
            level=BadgeLevel.SILVER,
            title="Lightning Approver",
            description="Approved 25+ memories within 1 hour",
            icon="⚡⚡",
            criteria={"approvals_count": 25, "avg_approval_time_hours": 1},
            points=300,
            rarity=0.1,
        ),
        BadgeLevel.GOLD: Badge(
            id="fastest_approver_gold",
            type=BadgeType.FASTEST_APPROVER,
            level=BadgeLevel.GOLD,
            title="Approval Ninja",
            description="Approved 50+ memories within 30 minutes",
            icon="🥷",
            criteria={"approvals_count": 50, "avg_approval_time_hours": 0.5},
            points=600,
            rarity=0.03,
        ),
    },
    BadgeType.AI_TAG_HELPER: {
        BadgeLevel.BRONZE: Badge(
            id="ai_tag_helper_bronze",
            type=BadgeType.AI_TAG_HELPER,
            level=BadgeLevel.BRONZE,
            title="AI Assistant",
            description="Accepted 20+ AI tag suggestions",
            icon="🤖",
            criteria={"ai_tags_accepted": 20},
            points=120,
            rarity=0.4,
        ),
        BadgeLevel.SILVER: Badge(
            id="ai_tag_helper_silver",
            type=BadgeType.AI_TAG_HELPER,
            level=BadgeLevel.SILVER,
            title="AI Collaborator",
            description="Accepted 50+ AI suggestions with 80%+ accuracy",
            icon="🤖✨",
            criteria={"ai_tags_accepted": 50, "ai_accuracy_rate": 0.8},
            points=250,
            rarity=0.2,
        ),
        BadgeLevel.GOLD: Badge(
            id="ai_tag_helper_gold",
            type=BadgeType.AI_TAG_HELPER,
            level=BadgeLevel.GOLD,
            title="AI Whisperer",
            description="Perfect AI collaboration - 100+ accepted with 90%+ accuracy",
            icon="🧠",
            criteria={"ai_tags_accepted": 100, "ai_accuracy_rate": 0.9},
            points=500,
            rarity=0.08,
        ),
    },
}


def calculate_user_stats(user_id: str) -> Dict[str, Any]:
    """Calculate user statistics for badge evaluation"""
    # Mock data - would come from actual database queries
    return {
        "comments_count": 45,
        "avg_sentiment": 0.75,
        "approvals_count": 18,
        "avg_approval_time_hours": 1.5,
        "ai_tags_accepted": 32,
        "ai_accuracy_rate": 0.82,
        "memories_created": 23,
        "quality_score": 0.78,
        "connections_made": 15,
        "sentiment_boost_count": 8,
    }


def evaluate_badges(user_stats: Dict[str, Any]) -> List[UserBadge]:
    """Evaluate which badges a user has earned"""
    earned_badges = []

    for badge_type, levels in BADGE_DEFINITIONS.items():
        highest_earned = None

        for level in [BadgeLevel.BRONZE, BadgeLevel.SILVER, BadgeLevel.GOLD]:
            if level not in levels:
                continue

            badge = levels[level]
            criteria_met = True

            for criterion, required_value in badge.criteria.items():
                user_value = user_stats.get(criterion, 0)
                if isinstance(required_value, (int, float)):
                    if user_value < required_value:
                        criteria_met = False
                        break

            if criteria_met:
                highest_earned = badge
            else:
                break

        if highest_earned:
            # Calculate progress toward next level
            next_level = None
            if (
                highest_earned.level == BadgeLevel.BRONZE
                and BadgeLevel.SILVER in levels
            ):
                next_level = levels[BadgeLevel.SILVER]
            elif (
                highest_earned.level == BadgeLevel.SILVER and BadgeLevel.GOLD in levels
            ):
                next_level = levels[BadgeLevel.GOLD]

            progress = {}
            if next_level:
                for criterion, required_value in next_level.criteria.items():
                    user_value = user_stats.get(criterion, 0)
                    progress[criterion] = {
                        "current": user_value,
                        "required": required_value,
                        "percentage": min(100, (user_value / required_value) * 100),
                    }

            earned_badges.append(
                UserBadge(
                    badge=highest_earned,
                    earned_at=datetime.utcnow() - timedelta(days=5),  # Mock earned date
                    progress=progress,
                    next_level=next_level,
                )
            )

    return earned_badges


def calculate_leaderboard(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Calculate team leaderboard"""
    # Mock leaderboard data
    return [
        {
            "user_id": "user_1",
            "username": "alex_dev",
            "display_name": "Alex Chen",
            "total_points": 1250,
            "badges_count": 8,
            "recent_activity": "Earned AI Whisperer badge",
            "avatar": "👨‍💻",
            "rank": 1,
            "rank_change": 0,
        },
        {
            "user_id": "user_2",
            "username": "sarah_pm",
            "display_name": "Sarah Johnson",
            "total_points": 1100,
            "badges_count": 6,
            "recent_activity": "Discussion Master achievement",
            "avatar": "👩‍💼",
            "rank": 2,
            "rank_change": 1,
        },
        {
            "user_id": "user_3",
            "username": "mike_design",
            "display_name": "Mike Rodriguez",
            "total_points": 950,
            "badges_count": 5,
            "recent_activity": "Lightning Approver earned",
            "avatar": "🎨",
            "rank": 3,
            "rank_change": -1,
        },
    ]


# API Endpoints
@router.get("/badges/available")
async def get_available_badges():
    """Get all available badges and their criteria"""

    badges_list = []
    for badge_type, levels in BADGE_DEFINITIONS.items():
        for level, badge in levels.items():
            badges_list.append(badge.dict())

    return {"success": True, "badges": badges_list, "total_badges": len(badges_list)}


@router.get("/badges/user/{user_id}")
async def get_user_badges(
    user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get badges earned by a specific user"""

    # Check permissions (users can view their own badges, admins can view any)
    if current_user["id"] != user_id and current_user.get("role") not in [
        "team_admin",
        "org_admin",
    ]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_stats = calculate_user_stats(user_id)
    earned_badges = evaluate_badges(user_stats)

    total_points = sum(badge.badge.points for badge in earned_badges)

    return {
        "success": True,
        "user_id": user_id,
        "badges": [badge.dict() for badge in earned_badges],
        "total_points": total_points,
        "total_badges": len(earned_badges),
        "user_stats": user_stats,
    }


@router.get("/badges/my-badges")
async def get_my_badges(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user's badges"""
    return await get_user_badges(current_user["id"], current_user)


@router.get("/leaderboard")
async def get_leaderboard(
    team_id: Optional[int] = None,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get team leaderboard"""

    # Use user's team if no team specified
    if team_id is None:
        team_id = current_user.get("team_id")

    leaderboard = calculate_leaderboard(team_id)[:limit]

    # Find current user's position
    user_position = None
    for i, entry in enumerate(leaderboard):
        if entry["user_id"] == current_user["id"]:
            user_position = i + 1
            break

    return {
        "success": True,
        "leaderboard": leaderboard,
        "team_id": team_id,
        "user_position": user_position,
        "total_participants": len(leaderboard),
    }


@router.get("/progress/{user_id}")
async def get_badge_progress(
    user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed progress toward next badges"""

    if current_user["id"] != user_id and current_user.get("role") not in [
        "team_admin",
        "org_admin",
    ]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_stats = calculate_user_stats(user_id)
    earned_badges = evaluate_badges(user_stats)

    # Find badges user is close to earning
    close_badges = []
    for badge_type, levels in BADGE_DEFINITIONS.items():
        # Check if user already has this badge type
        has_badge = any(b.badge.type == badge_type for b in earned_badges)

        if not has_badge:
            # Check progress toward bronze level
            bronze_badge = levels.get(BadgeLevel.BRONZE)
            if bronze_badge:
                progress = {}
                total_progress = 0
                criteria_count = 0

                for criterion, required_value in bronze_badge.criteria.items():
                    user_value = user_stats.get(criterion, 0)
                    percentage = min(100, (user_value / required_value) * 100)
                    progress[criterion] = {
                        "current": user_value,
                        "required": required_value,
                        "percentage": percentage,
                    }
                    total_progress += percentage
                    criteria_count += 1

                avg_progress = (
                    total_progress / criteria_count if criteria_count > 0 else 0
                )

                if avg_progress >= 50:  # Show badges that are at least 50% complete
                    close_badges.append(
                        {
                            "badge": bronze_badge.dict(),
                            "progress": progress,
                            "overall_progress": avg_progress,
                        }
                    )

    # Sort by progress percentage
    close_badges.sort(key=lambda x: x["overall_progress"], reverse=True)

    return {
        "success": True,
        "user_id": user_id,
        "earned_badges": len(earned_badges),
        "close_badges": close_badges[:5],  # Top 5 closest badges
        "user_stats": user_stats,
    }


@router.post("/celebrate/{badge_id}")
async def celebrate_badge(
    badge_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark a badge as celebrated (for UI feedback)"""

    # This would typically update a database flag
    # For now, just return success

    return {
        "success": True,
        "message": f"Congratulations on earning {badge_id}! 🎉",
        "celebration_unlocked": True,
    }


# Widget Integration
@router.get("/widget-data")
async def get_gamification_widget_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get gamification data for dashboard widgets"""

    user_stats = calculate_user_stats(current_user["id"])
    earned_badges = evaluate_badges(user_stats)
    leaderboard = calculate_leaderboard(current_user.get("team_id"))

    # Find user's rank
    user_rank = None
    for i, entry in enumerate(leaderboard):
        if entry["user_id"] == current_user["id"]:
            user_rank = i + 1
            break

    total_points = sum(badge.badge.points for badge in earned_badges)

    return {
        "success": True,
        "user_summary": {
            "total_points": total_points,
            "total_badges": len(earned_badges),
            "team_rank": user_rank or "Unranked",
            "recent_badges": [
                badge.dict() for badge in earned_badges[-3:]
            ],  # Last 3 earned
        },
        "team_leaderboard": leaderboard[:5],  # Top 5
        "badge_progress": await get_badge_progress(current_user["id"], current_user),
    }
