"""
Intelligent Session Management API - SPEC-045
RESTful API for intelligent session management and analytics
"""

import json
from typing import Any, Optional

import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Request
from intelligent_session import (
    IntelligentSessionManager,
    get_session_analytics,
    get_session_manager,
    track_activity,
)
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth/session", tags=["intelligent-sessions"])


# Request/Response models
class SessionPreferencesRequest(BaseModel):
    auto_renew: bool = True
    notification_preferences: dict[str, bool] = {}
    timeout_preference: Optional[str] = None  # 'short', 'medium', 'long'


class SessionAnalyticsResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    duration_minutes: float
    timeout_minutes: float
    remaining_minutes: float
    activity_count: int
    intelligent_features: dict[str, bool]
    session_health: dict[str, Any]


class RenewalRecommendationResponse(BaseModel):
    session_id: str
    should_renew: bool
    confidence: float
    reasons: list
    remaining_minutes: float
    recommended_action: str
    renewal_urgency: str


@router.get("/analytics", response_model=SessionAnalyticsResponse)
async def get_current_session_analytics(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Get analytics for current session - SPEC-045"""
    try:
        # Extract session ID from request (would normally come from JWT or session cookie)
        session_id = getattr(
            request.state, "session_id", f"session_{current_user.user_id}"
        )

        analytics = await get_session_analytics(session_id)

        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return SessionAnalyticsResponse(**analytics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting session analytics",
            user_id=current_user.user_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=RenewalRecommendationResponse)
async def get_renewal_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Get intelligent renewal recommendations - SPEC-045"""
    try:
        session_id = getattr(
            request.state, "session_id", f"session_{current_user.user_id}"
        )

        recommendation = await session_manager.get_renewal_recommendation(session_id)

        if "error" in recommendation:
            raise HTTPException(status_code=404, detail=recommendation["error"])

        return RenewalRecommendationResponse(**recommendation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting renewal recommendations",
            user_id=current_user.user_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/renew")
async def renew_session_intelligently(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Intelligently renew current session - SPEC-045"""
    try:
        session_id = getattr(
            request.state, "session_id", f"session_{current_user.user_id}"
        )

        result = await session_manager.renew_session_intelligently(session_id)

        logger.info(
            "Session renewed via API",
            user_id=current_user.user_id,
            session_id=session_id,
            new_timeout_minutes=result.get("new_timeout_minutes"),
        )

        return result

    except Exception as e:
        logger.error(
            "Error renewing session", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activity")
async def track_session_activity(
    activity_type: str,
    metadata: Optional[dict[str, Any]] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Track session activity for intelligence - SPEC-045"""
    try:
        session_id = getattr(
            request.state, "session_id", f"session_{current_user.user_id}"
        )

        await track_activity(session_id, activity_type, metadata or {})

        logger.debug(
            "Session activity tracked via API",
            user_id=current_user.user_id,
            session_id=session_id,
            activity_type=activity_type,
        )

        return {
            "session_id": session_id,
            "activity_tracked": True,
            "activity_type": activity_type,
            "timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
        }

    except Exception as e:
        logger.error(
            "Error tracking session activity",
            user_id=current_user.user_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def update_session_preferences(
    preferences: SessionPreferencesRequest,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Update session behavior preferences - SPEC-045"""
    try:
        # Store user preferences (would integrate with user profile system)
        user_prefs = {
            "user_id": current_user.user_id,
            "auto_renew": preferences.auto_renew,
            "notification_preferences": preferences.notification_preferences,
            "timeout_preference": preferences.timeout_preference,
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # In a real implementation, this would update user preferences in database
        # and influence intelligent timeout calculations

        logger.info(
            "Session preferences updated",
            user_id=current_user.user_id,
            preferences=user_prefs,
        )

        return {
            "user_id": current_user.user_id,
            "preferences_updated": True,
            "preferences": user_prefs,
        }

    except Exception as e:
        logger.error(
            "Error updating session preferences",
            user_id=current_user.user_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_session_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Get current session status and health - SPEC-045"""
    try:
        session_id = getattr(
            request.state, "session_id", f"session_{current_user.user_id}"
        )

        analytics = await get_session_analytics(session_id)

        if "error" in analytics:
            return {
                "session_id": session_id,
                "status": "not_found",
                "message": "Session not found or expired",
            }

        session_health = analytics.get("session_health", {})

        return {
            "session_id": session_id,
            "user_id": current_user.user_id,
            "status": "active" if session_health.get("active") else "expired",
            "remaining_minutes": analytics.get("remaining_minutes", 0),
            "renewal_recommended": session_health.get("renewal_recommended", False),
            "expires_at": session_health.get("expires_at"),
            "intelligent_features_enabled": analytics.get("intelligent_features", {}),
            "activity_count": analytics.get("activity_count", 0),
        }

    except Exception as e:
        logger.error(
            "Error getting session status", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_session_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Get user's session history for analytics - SPEC-045"""
    try:
        if not session_manager.redis.is_connected:
            raise HTTPException(status_code=500, detail="Redis not connected")

        # Get user session history
        user_key = session_manager._make_user_session_key(current_user.user_id)
        user_data = await session_manager.redis.redis.get(user_key)

        if not user_data:
            return {
                "user_id": current_user.user_id,
                "sessions": [],
                "total_sessions": 0,
                "message": "No session history found",
            }

        data = json.loads(user_data)
        recent_sessions = data.get("recent_sessions", [])[-limit:]

        return {
            "user_id": current_user.user_id,
            "sessions": recent_sessions,
            "total_sessions": data.get("total_sessions", 0),
            "limit": limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting session history", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_expired_sessions(
    current_user: User = Depends(get_current_user),
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Cleanup expired sessions for current user - SPEC-045"""
    try:
        # Only allow admins to cleanup sessions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403, detail="Admin access required for session cleanup"
            )

        if not session_manager.redis.is_connected:
            raise HTTPException(status_code=500, detail="Redis not connected")

        # Find and cleanup expired sessions
        # This is a simplified implementation
        patterns = [
            "session:*",
            "session:meta:*",
            "session:activity:*",
            "session:renewal:*",
        ]

        total_cleaned = 0
        for pattern in patterns:
            keys = await session_manager.redis.redis.keys(pattern)

            # Check each key for expiration (simplified)
            expired_keys = []
            for key in keys:
                ttl = await session_manager.redis.redis.ttl(key)
                if ttl == -1 or ttl < 0:  # No TTL or expired
                    expired_keys.append(key)

            if expired_keys:
                deleted = await session_manager.redis.redis.delete(*expired_keys)
                total_cleaned += deleted

        logger.info(
            "Session cleanup completed",
            cleaned_by=current_user.user_id,
            sessions_cleaned=total_cleaned,
        )

        return {
            "cleanup_completed": True,
            "sessions_cleaned": total_cleaned,
            "cleaned_by": current_user.user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error cleaning up sessions", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def session_system_health(
    session_manager: IntelligentSessionManager = Depends(get_session_manager),
):
    """Health check for intelligent session system - SPEC-045"""
    try:
        redis_connected = session_manager.redis.is_connected
        config_loaded = session_manager.config is not None

        status = "healthy" if (redis_connected and config_loaded) else "degraded"

        return {
            "status": status,
            "redis_connected": redis_connected,
            "config_loaded": config_loaded,
            "features": {
                "intelligent_timeouts": True,
                "activity_tracking": True,
                "renewal_recommendations": True,
                "session_analytics": True,
                "context_awareness": True,
            },
            "config": {
                "base_timeout_minutes": session_manager.config.base_timeout_minutes,
                "max_timeout_minutes": session_manager.config.max_timeout_minutes,
                "renewal_threshold": session_manager.config.renewal_threshold,
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "redis_connected": False,
            "config_loaded": False,
        }
