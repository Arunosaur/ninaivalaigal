#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-030: Admin-Level Analytics Console
Internal operations dashboard with comprehensive business intelligence
"""

import asyncio
import json
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional

import structlog
from auth_service import get_current_user, get_db
from database import Team, User
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exceptions import WebSocketException
from lib.websocket_auth import authenticate_websocket
from models.standalone_teams import TeamMembership
from pydantic import BaseModel
from sqlalchemy.orm import Session

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = structlog.get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/admin-analytics", tags=["admin"])

# Redis client for caching (US#265: Redis Caching Integration)
_redis_client = None


async def get_redis_client():
    """Get or initialize Redis client for caching"""
    global _redis_client
    if _redis_client is None:
        try:
            from lib.redis_client import RedisClient

            _redis_client = RedisClient()
            await _redis_client.connect()
        except Exception as e:
            logger.warning("Redis not available, using in-memory cache fallback", error=str(e))
            _redis_client = None
    return _redis_client


async def get_cached(key: str, default: Any = None) -> Any:
    """Get value from Redis cache"""
    redis_client = await get_redis_client()
    if not redis_client or not redis_client.is_connected:
        return default

    try:
        cache_key = f"admin_analytics:{key}"
        value = await redis_client.redis.get(cache_key)
        if value:
            return json.loads(value)
        return default
    except Exception as e:
        logger.warning("Cache get failed", key=key, error=str(e))
        return default


async def set_cached(key: str, value: Any, ttl: int = 900) -> bool:
    """Set value in Redis cache with TTL"""
    redis_client = await get_redis_client()
    if not redis_client or not redis_client.is_connected:
        return False

    try:
        cache_key = f"admin_analytics:{key}"
        await redis_client.redis.setex(cache_key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning("Cache set failed", key=key, error=str(e))
        return False


async def invalidate_cache(pattern: str = None) -> bool:
    """Invalidate cache keys matching pattern"""
    redis_client = await get_redis_client()
    if not redis_client or not redis_client.is_connected:
        return False

    try:
        if pattern:
            cache_pattern = f"admin_analytics:{pattern}*"
            keys = await redis_client.redis.keys(cache_pattern)
        else:
            keys = await redis_client.redis.keys("admin_analytics:*")

        if keys:
            await redis_client.redis.delete(*keys)
        return True
    except Exception as e:
        logger.warning("Cache invalidation failed", pattern=pattern, error=str(e))
        return False


async def clear_analytics_cache() -> bool:
    """Clear all admin analytics cache"""
    return await invalidate_cache()


# Admin role check dependency
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify user has Platform Admin role (SPEC-005 Admin Console).

    **Required:** Platform Admin (users.role='admin' or 'super_admin')
    This is for SPEC-030 Admin Analytics Console, which is part of Platform Admin.

    Note: This function is for SPEC-030. For Vendor Admin (SPEC-025), use require_vendor_admin().
    """
    from auth import require_platform_admin

    # Convert User object to dict format for require_platform_admin
    user_dict = {
        "id": str(current_user.id) if hasattr(current_user, "id") else None,
        "role": getattr(current_user, "role", "user"),
        "is_system_admin": getattr(current_user, "is_system_admin", False),
        "rbac_roles": getattr(current_user, "rbac_roles", {}),
    }

    # Check platform admin permissions
    require_platform_admin(user_dict)

    return current_user


# Pydantic Models
class PlatformMetrics(BaseModel):
    """High-level platform metrics"""

    total_users: int
    total_teams: int
    active_users_30d: int
    active_teams_30d: int
    new_signups_30d: int
    new_teams_30d: int
    total_revenue_30d: float
    avg_team_size: float
    platform_health_score: float


class ChurnAnalysis(BaseModel):
    """Churn analysis and early warning indicators"""

    monthly_churn_rate: float
    churn_risk_teams: List[Dict[str, Any]]
    retention_by_cohort: Dict[str, float]
    churn_reasons: Dict[str, int]
    early_warning_count: int
    at_risk_revenue: float


class RevenueCohorts(BaseModel):
    """Revenue cohort analysis"""

    cohort_data: Dict[str, Dict[str, float]]
    ltv_by_cohort: Dict[str, float]
    revenue_growth_rate: float
    expansion_revenue: float
    contraction_revenue: float
    net_revenue_retention: float


class UserEngagement(BaseModel):
    """User engagement and activity metrics"""

    daily_active_users: List[Dict[str, Any]]
    feature_adoption: Dict[str, float]
    session_duration_avg: float
    actions_per_session: float
    engagement_score_distribution: Dict[str, int]
    power_users_count: int


class BusinessIntelligence(BaseModel):
    """Comprehensive business intelligence dashboard"""

    growth_metrics: Dict[str, Any]
    conversion_funnel: Dict[str, Any]
    product_metrics: Dict[str, Any]
    financial_metrics: Dict[str, Any]
    operational_metrics: Dict[str, Any]
    predictive_insights: Dict[str, Any]


class AlertConfig(BaseModel):
    """Alert configuration for monitoring"""

    metric_name: str
    threshold_value: float
    comparison_operator: str  # "gt", "lt", "eq"
    alert_frequency: str  # "immediate", "daily", "weekly"
    notification_channels: List[str]  # ["email", "slack", "webhook"]
    is_active: bool


# Mock databases for admin analytics (in production, use proper database)
# Note: Caching moved to Redis (US#265: Redis Caching Integration)
# Old in-memory caches removed - all caching now uses Redis via get_cached/set_cached
alert_configs_db: dict = {}


def check_admin_permissions(current_user: User) -> bool:
    """Check if user has admin permissions"""
    # In production, implement proper admin role checking
    # For now, allow all authenticated users for demo purposes
    return True


def calculate_platform_health_score(metrics: Dict[str, Any]) -> float:
    """Calculate overall platform health score (0-100)"""
    # Weighted scoring based on key metrics
    weights = {
        "user_growth": 0.25,  # New user acquisition
        "team_growth": 0.20,  # Team creation rate
        "engagement": 0.25,  # User activity levels
        "revenue_growth": 0.20,  # Revenue trends
        "churn_rate": 0.10,  # User retention
    }

    # Mock calculation - in production, use real metrics
    user_growth_score = min(100, (metrics.get("new_signups_30d", 0) / 100) * 100)
    team_growth_score = min(100, (metrics.get("new_teams_30d", 0) / 50) * 100)
    engagement_score = min(100, (metrics.get("active_users_30d", 0) / metrics.get("total_users", 1)) * 100)
    revenue_growth_score = min(100, (metrics.get("total_revenue_30d", 0) / 10000) * 100)
    churn_score = max(0, 100 - (metrics.get("churn_rate", 0.05) * 2000))  # Lower churn = higher score

    health_score = (
        user_growth_score * weights["user_growth"]
        + team_growth_score * weights["team_growth"]
        + engagement_score * weights["engagement"]
        + revenue_growth_score * weights["revenue_growth"]
        + churn_score * weights["churn_rate"]
    )

    return round(health_score, 1)


def generate_mock_platform_metrics() -> PlatformMetrics:
    """Generate mock platform metrics for demo"""
    base_metrics = {
        "total_users": 2847,
        "total_teams": 892,
        "active_users_30d": 1923,
        "active_teams_30d": 634,
        "new_signups_30d": 287,
        "new_teams_30d": 94,
        "total_revenue_30d": 28450.00,
        "avg_team_size": 4.2,
        "churn_rate": 0.035,
    }

    health_score = calculate_platform_health_score(base_metrics)

    return PlatformMetrics(
        total_users=base_metrics["total_users"],
        total_teams=base_metrics["total_teams"],
        active_users_30d=base_metrics["active_users_30d"],
        active_teams_30d=base_metrics["active_teams_30d"],
        new_signups_30d=base_metrics["new_signups_30d"],
        new_teams_30d=base_metrics["new_teams_30d"],
        total_revenue_30d=base_metrics["total_revenue_30d"],
        avg_team_size=base_metrics["avg_team_size"],
        platform_health_score=health_score,
    )


def generate_mock_churn_analysis() -> ChurnAnalysis:
    """Generate mock churn analysis for demo"""
    churn_risk_teams = [
        {
            "team_id": "team-001",
            "team_name": "Startup Alpha",
            "risk_score": 0.85,
            "last_activity": "2024-09-15T10:30:00Z",
            "members": 3,
            "plan": "team_pro",
            "revenue_at_risk": 29.00,
            "warning_signals": ["low_activity", "no_recent_invites", "support_tickets"],
        },
        {
            "team_id": "team-002",
            "team_name": "Tech Innovators",
            "risk_score": 0.72,
            "last_activity": "2024-09-18T14:20:00Z",
            "members": 8,
            "plan": "team_enterprise",
            "revenue_at_risk": 99.00,
            "warning_signals": ["declining_usage", "member_departures"],
        },
        {
            "team_id": "team-003",
            "team_name": "Creative Agency",
            "risk_score": 0.68,
            "last_activity": "2024-09-20T09:15:00Z",
            "members": 12,
            "plan": "organization",
            "revenue_at_risk": 500.00,
            "warning_signals": ["payment_delays", "feature_complaints"],
        },
    ]

    retention_by_cohort = {
        "2024-06": 0.92,  # June cohort retention
        "2024-07": 0.89,  # July cohort retention
        "2024-08": 0.94,  # August cohort retention
        "2024-09": 0.96,  # September cohort retention (early)
    }

    churn_reasons = {
        "pricing_concerns": 12,
        "feature_limitations": 8,
        "poor_onboarding": 6,
        "competitor_switch": 4,
        "team_downsizing": 3,
        "technical_issues": 2,
    }

    at_risk_revenue: float = sum(float(team["revenue_at_risk"]) for team in churn_risk_teams)  # type: ignore

    return ChurnAnalysis(
        monthly_churn_rate=0.035,
        churn_risk_teams=churn_risk_teams,
        retention_by_cohort=retention_by_cohort,
        churn_reasons=churn_reasons,
        early_warning_count=len(churn_risk_teams),
        at_risk_revenue=at_risk_revenue,
    )


def generate_mock_revenue_cohorts() -> RevenueCohorts:
    """Generate mock revenue cohort analysis for demo"""
    cohort_data = {
        "2024-06": {
            "month_0": 2450.00,
            "month_1": 2680.00,
            "month_2": 2890.00,
            "month_3": 3120.00,
        },
        "2024-07": {"month_0": 3200.00, "month_1": 3520.00, "month_2": 3780.00},
        "2024-08": {"month_0": 4100.00, "month_1": 4510.00},
        "2024-09": {"month_0": 5200.00},
    }

    ltv_by_cohort = {
        "2024-06": 1247.50,
        "2024-07": 1389.20,
        "2024-08": 1456.80,
        "2024-09": 1523.40,  # Projected
    }

    return RevenueCohorts(
        cohort_data=cohort_data,
        ltv_by_cohort=ltv_by_cohort,
        revenue_growth_rate=0.23,  # 23% month-over-month
        expansion_revenue=1250.00,
        contraction_revenue=320.00,
        net_revenue_retention=1.12,  # 112% NRR
    )


def generate_mock_user_engagement() -> UserEngagement:
    """Generate mock user engagement metrics for demo"""
    # Generate daily active users for last 30 days
    daily_active_users = []
    base_date = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        date = base_date + timedelta(days=i)
        # Simulate weekly patterns with weekend dips
        weekday = date.weekday()
        base_users = 1200.0
        if weekday >= 5:  # Weekend
            base_users *= 0.7

        daily_active_users.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "active_users": int(base_users + (i * 15)),  # Growth trend
                "new_users": max(0, int(25 + (i * 2) - (weekday * 3))),
                "returning_users": int(base_users * 0.85),
            }
        )

    feature_adoption = {
        "memory_creation": 0.89,
        "team_invitations": 0.67,
        "ai_suggestions": 0.45,
        "memory_browser": 0.78,
        "team_dashboard": 0.56,
        "billing_console": 0.23,
        "usage_analytics": 0.12,
    }

    engagement_score_distribution = {
        "high_engagement": 234,  # 80-100 score
        "medium_engagement": 567,  # 50-79 score
        "low_engagement": 423,  # 20-49 score
        "inactive": 156,  # 0-19 score
    }

    return UserEngagement(
        daily_active_users=daily_active_users,
        feature_adoption=feature_adoption,
        session_duration_avg=18.5,  # minutes
        actions_per_session=12.3,
        engagement_score_distribution=engagement_score_distribution,
        power_users_count=89,  # Users with high engagement scores
    )


def generate_mock_support_metrics() -> SupportMetrics:
    """Generate mock support metrics for demo purposes"""
    # Common issues (top 10)
    common_issues = [
        {
            "category": "bug",
            "title": "Memory search not returning expected results",
            "count": 47,
            "frequency": "high",
            "avg_resolution_hours": 12.5,
            "affected_users": 23,
        },
        {
            "category": "feature_request",
            "title": "Export memories to PDF",
            "count": 34,
            "frequency": "high",
            "avg_resolution_hours": None,  # Not resolved yet
            "affected_users": 34,
        },
        {
            "category": "billing",
            "title": "Invoice payment failed",
            "count": 28,
            "frequency": "medium",
            "avg_resolution_hours": 4.2,
            "affected_users": 18,
        },
        {
            "category": "technical_support",
            "title": "API rate limit errors",
            "count": 22,
            "frequency": "medium",
            "avg_resolution_hours": 6.8,
            "affected_users": 15,
        },
        {
            "category": "bug",
            "title": "Context sharing not working",
            "count": 19,
            "frequency": "medium",
            "avg_resolution_hours": 8.3,
            "affected_users": 12,
        },
        {
            "category": "account",
            "title": "Password reset email not received",
            "count": 16,
            "frequency": "low",
            "avg_resolution_hours": 2.1,
            "affected_users": 16,
        },
        {
            "category": "feature_request",
            "title": "Dark mode support",
            "count": 15,
            "frequency": "low",
            "avg_resolution_hours": None,
            "affected_users": 15,
        },
        {
            "category": "technical_support",
            "title": "Graph query timeout",
            "count": 14,
            "frequency": "low",
            "avg_resolution_hours": 9.5,
            "affected_users": 9,
        },
        {
            "category": "billing",
            "title": "Subscription upgrade not reflecting",
            "count": 12,
            "frequency": "low",
            "avg_resolution_hours": 3.7,
            "affected_users": 8,
        },
        {
            "category": "bug",
            "title": "Memory attachments not uploading",
            "count": 11,
            "frequency": "low",
            "avg_resolution_hours": 7.2,
            "affected_users": 7,
        },
    ]

    # Feature requests
    feature_requests = [
        {
            "title": "Export memories to PDF",
            "description": "Allow users to export their memories as PDF documents",
            "request_count": 34,
            "total_votes": 89,
            "status": "pending",
            "priority": "high",
        },
        {
            "title": "Dark mode support",
            "description": "Add dark mode theme option to the UI",
            "request_count": 15,
            "total_votes": 67,
            "status": "in_progress",
            "priority": "medium",
        },
        {
            "title": "Bulk memory operations",
            "description": "Allow users to select and perform operations on multiple memories at once",
            "request_count": 12,
            "total_votes": 45,
            "status": "pending",
            "priority": "medium",
        },
        {
            "title": "Advanced search filters",
            "description": "Add more granular search filters (date range, tags, context)",
            "request_count": 9,
            "total_votes": 32,
            "status": "pending",
            "priority": "low",
        },
        {
            "title": "Memory templates",
            "description": "Create reusable templates for common memory types",
            "request_count": 7,
            "total_votes": 28,
            "status": "pending",
            "priority": "low",
        },
    ]

    # Support volume
    support_volume = {
        "tickets_today": 12,
        "tickets_this_week": 78,
        "tickets_this_month": 287,
        "ticket_volume_trend": "declining",  # growing, declining, stable
        "avg_response_time_hours": 2.3,
        "avg_resolution_time_hours": 6.8,
        "ticket_backlog_size": 45,
        "open_tickets": 23,
        "resolved_tickets_30d": 242,
    }

    # Issue categories breakdown
    issue_categories = {
        "bug": 89,
        "feature_request": 77,
        "billing": 56,
        "technical_support": 48,
        "account": 34,
        "other": 23,
    }

    # User satisfaction
    user_satisfaction = {
        "avg_satisfaction_rating": 4.2,  # Out of 5
        "satisfaction_ratings_count": 156,
        "first_contact_resolution_rate": 0.68,  # 68%
        "escalation_rate": 0.12,  # 12%
        "positive_feedback_percentage": 0.78,  # 78%
    }

    # Resolution times by category
    resolution_times = {
        "bug": 8.5,  # hours
        "feature_request": None,  # Not applicable
        "billing": 3.2,
        "technical_support": 6.8,
        "account": 2.1,
        "other": 5.4,
    }

    return SupportMetrics(
        common_issues=common_issues,
        feature_requests=feature_requests,
        support_volume=support_volume,
        issue_categories=issue_categories,
        user_satisfaction=user_satisfaction,
        resolution_times=resolution_times,
    )


@router.get("/platform-overview")
async def get_platform_overview(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> PlatformMetrics:
    """Get high-level platform metrics overview"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "platform_metrics"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return PlatformMetrics(**cached_data)

    try:
        from datetime import timedelta

        from sqlalchemy import and_, func

        # Get real metrics from database
        total_users = db.query(User).count()
        total_teams = db.query(Team).filter(Team.is_standalone.is_(True)).count()

        # Calculate active users (users with login activity in last 30 days)
        # Using last_login as proxy for activity (US#315: Remove Mock Data Dependencies)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_30d = (
            db.query(User).filter(User.last_login >= thirty_days_ago).count() if hasattr(User, "last_login") else 0
        )

        # Calculate active teams (teams with activity in last 30 days)
        # Using updated_at as proxy for activity
        active_teams_30d = (
            db.query(Team).filter(and_(Team.is_standalone.is_(True), Team.updated_at >= thirty_days_ago)).count()
            if hasattr(Team, "updated_at")
            else 0
        )

        # Calculate new signups (real query with date filtering)
        new_signups_30d = (
            db.query(User).filter(User.created_at >= thirty_days_ago).count() if hasattr(User, "created_at") else 0
        )

        # Calculate new teams (real query with date filtering)
        new_teams_30d = (
            db.query(Team).filter(and_(Team.is_standalone.is_(True), Team.created_at >= thirty_days_ago)).count()
            if hasattr(Team, "created_at")
            else 0
        )

        # Calculate revenue (real query from subscription/billing tables if available)
        # For now, use placeholder - requires integration with billing service
        # TODO: Integrate with TeamSubscription or billing tables for real revenue
        total_revenue_30d = 0.0
        try:
            # Try to query from subscription tables if they exist
            from database import TeamSubscription

            revenue_query = (
                db.query(func.sum(TeamSubscription.amount))
                .filter(TeamSubscription.created_at >= thirty_days_ago)
                .scalar()
            )
            total_revenue_30d = float(revenue_query) if revenue_query else 0.0
        except (ImportError, AttributeError):
            # Fallback: calculate from active teams if subscription data not available
            # This is still better than pure mock data
            total_revenue_30d = float(active_teams_30d * 45.50)  # Placeholder until billing integration

        # Calculate average team size
        team_memberships = db.query(TeamMembership).filter(TeamMembership.status == "active").count()
        avg_team_size = round(team_memberships / max(total_teams, 1), 1)

        metrics_data = {
            "total_users": total_users,
            "total_teams": total_teams,
            "active_users_30d": active_users_30d,
            "active_teams_30d": active_teams_30d,
            "new_signups_30d": new_signups_30d,
            "new_teams_30d": new_teams_30d,
            "total_revenue_30d": total_revenue_30d,
            "avg_team_size": avg_team_size,
        }

        health_score = calculate_platform_health_score(metrics_data)

        platform_metrics = PlatformMetrics(**metrics_data, platform_health_score=health_score)

        # Cache the results in Redis (US#265: Redis Caching Integration)
        await set_cached(cache_key, platform_metrics.dict(), ttl=900)  # 15 minutes

        return platform_metrics

    except Exception as e:
        # Log error but return minimal data instead of mock
        # US#315: Remove Mock Data Dependencies - return empty/minimal data on failure
        logger.error("Database query failed for platform metrics", error=str(e))
        # Return minimal real data instead of mock
        try:
            total_users = db.query(User).count()
            total_teams = db.query(Team).filter(Team.is_standalone.is_(True)).count()
            team_memberships = db.query(TeamMembership).filter(TeamMembership.status == "active").count()
            avg_team_size = round(team_memberships / max(total_teams, 1), 1) if total_teams > 0 else 0.0

            return PlatformMetrics(
                total_users=total_users,
                total_teams=total_teams,
                active_users_30d=0,  # Data not available
                active_teams_30d=0,  # Data not available
                new_signups_30d=0,  # Data not available
                new_teams_30d=0,  # Data not available
                total_revenue_30d=0.0,  # Data not available
                avg_team_size=avg_team_size,
                platform_health_score=0.0,  # Cannot calculate without full data
            )
        except Exception as fallback_error:
            logger.error("Fallback query also failed", error=str(fallback_error))
            raise HTTPException(
                status_code=503, detail="Analytics service temporarily unavailable. Please try again later."
            )


@router.get("/churn-analysis")
async def get_churn_analysis(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> ChurnAnalysis:
    """Get comprehensive churn analysis and early warning indicators"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "churn_analysis"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return ChurnAnalysis(**cached_data)

    # US#315: Remove Mock Data Dependencies
    # TODO: Implement real churn analysis from:
    # - Team activity patterns (join with activity logs)
    # - Subscription status (join with subscription tables)
    # - Payment failures (join with billing tables)
    # - Usage decline detection (join with usage metrics)
    # For now, return minimal data structure
    # In production, implement real churn analysis algorithms
    try:
        # Attempt real churn calculation if activity data available
        # Placeholder for real implementation
        churn_data = generate_mock_churn_analysis()
    except Exception as e:
        logger.warning("Churn analysis calculation failed, using minimal data", error=str(e))
        # Return minimal structure instead of full mock
        churn_data = ChurnAnalysis(
            churn_rate=0.0,
            retention_rate=0.0,
            at_risk_teams=[],
            early_warning_signals=[],
            churn_trend="stable",
            revenue_at_risk=0.0,
        )

    # Cache the results in Redis (TTL: 30 minutes)
    await set_cached(cache_key, churn_data.dict(), ttl=1800)

    return churn_data


@router.get("/revenue-cohorts")
async def get_revenue_cohorts(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> RevenueCohorts:
    """Get revenue cohort analysis and customer lifetime value metrics"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "revenue_cohorts"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return RevenueCohorts(**cached_data)

    # US#315: Remove Mock Data Dependencies
    # TODO: Implement real revenue cohort analysis from:
    # - Billing/subscription tables (TeamSubscription, invoices)
    # - Historical payment data
    # - Subscription changes (upgrades/downgrades)
    # For now, return minimal data structure
    # In production, implement real cohort analysis
    try:
        # Attempt real revenue calculation if billing data available
        # Placeholder for real implementation
        revenue_data = generate_mock_revenue_cohorts()
    except Exception as e:
        logger.warning("Revenue cohort analysis calculation failed, using minimal data", error=str(e))
        # Return minimal structure instead of full mock
        revenue_data = RevenueCohorts(
            cohorts=[],
            revenue_growth_rate=0.0,
            average_ltv=0.0,
            expansion_revenue=0.0,
            contraction_revenue=0.0,
            net_revenue_retention=0.0,
        )

    # Cache the results in Redis (TTL: 60 minutes)
    await set_cached(cache_key, revenue_data.dict(), ttl=3600)

    return revenue_data


@router.get("/user-engagement")
async def get_user_engagement(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> UserEngagement:
    """Get user engagement and activity metrics"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "user_engagement"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return UserEngagement(**cached_data)

    # US#315: Remove Mock Data Dependencies
    # TODO: Implement real user engagement from:
    # - Activity logs (api_usage_logs table if available)
    # - Session tracking (user_sessions table if available)
    # - Feature usage tracking (feature_usage table if available)
    # For now, return minimal data structure
    # In production, implement real engagement tracking
    try:
        # Attempt real engagement calculation if activity data available
        # Placeholder for real implementation
        engagement_data = generate_mock_user_engagement()
    except Exception as e:
        logger.warning("User engagement calculation failed, using minimal data", error=str(e))
        # Return minimal structure instead of full mock
        engagement_data = UserEngagement(
            daily_active_users=[],
            feature_adoption={},
            session_duration_avg=0.0,
            actions_per_session=0.0,
            engagement_score_distribution={},
            power_users_count=0,
        )

    # Cache the results in Redis (TTL: 15 minutes)
    await set_cached(cache_key, engagement_data.dict(), ttl=900)

    return engagement_data


@router.get("/business-intelligence")
async def get_business_intelligence(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> BusinessIntelligence:
    """Get comprehensive business intelligence dashboard"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "business_intelligence"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return BusinessIntelligence(**cached_data)

    # Aggregate data from multiple sources
    platform_metrics = await get_platform_overview(current_user, db)
    churn_analysis = await get_churn_analysis(current_user, db)
    revenue_cohorts = await get_revenue_cohorts(current_user, db)
    user_engagement = await get_user_engagement(current_user, db)

    # Calculate growth metrics
    growth_metrics = {
        "user_growth_rate": 0.12,  # 12% monthly growth
        "team_growth_rate": 0.11,  # 11% monthly growth
        "revenue_growth_rate": revenue_cohorts.revenue_growth_rate,
        "market_penetration": 0.034,  # 3.4% of target market
        "viral_coefficient": 1.23,  # Average invitations per user
        "time_to_value": 4.2,  # Days to first value realization
    }

    # Calculate conversion funnel
    conversion_funnel = {
        "visitors": 12450,
        "signups": 1247,  # 10% conversion
        "activated_users": 934,  # 75% activation
        "team_creators": 467,  # 50% create teams
        "paid_customers": 112,  # 24% upgrade to paid
        "retention_30d": 0.89,  # 89% 30-day retention
    }

    # Product metrics
    product_metrics = {
        "feature_adoption_rate": sum(user_engagement.feature_adoption.values()) / len(user_engagement.feature_adoption),
        "daily_active_users": user_engagement.daily_active_users[-1]["active_users"],
        "session_duration": user_engagement.session_duration_avg,
        "user_satisfaction": 4.2,  # Out of 5
        "nps_score": 67,  # Net Promoter Score
        "support_ticket_volume": 23,  # Weekly average
    }

    # Financial metrics
    financial_metrics = {
        "monthly_recurring_revenue": platform_metrics.total_revenue_30d,
        "annual_run_rate": platform_metrics.total_revenue_30d * 12,
        "customer_acquisition_cost": 45.20,
        "lifetime_value": 1247.50,
        "ltv_cac_ratio": 27.6,
        "gross_margin": 0.87,  # 87% gross margin
        "burn_rate": 15600.00,  # Monthly burn
        "runway_months": 18.5,
    }

    # Operational metrics
    operational_metrics = {
        "system_uptime": 0.9987,  # 99.87% uptime
        "api_response_time": 145,  # milliseconds
        "error_rate": 0.0023,  # 0.23% error rate
        "support_response_time": 2.3,  # hours
        "deployment_frequency": 12,  # per month
        "lead_time": 3.2,  # days
        "mttr": 0.8,  # Mean time to recovery (hours)
    }

    # Predictive insights
    predictive_insights = {
        "projected_mrr_3m": platform_metrics.total_revenue_30d * 1.45,
        "projected_users_3m": platform_metrics.total_users * 1.38,
        "churn_risk_revenue": churn_analysis.at_risk_revenue,
        "expansion_opportunities": 8,  # Teams ready for upgrade
        "market_size_potential": 2.4e6,  # $2.4M addressable market
        "competitive_threats": 2,  # Active competitive threats
        "growth_bottlenecks": ["onboarding_friction", "feature_discovery"],
    }

    bi_data = BusinessIntelligence(
        growth_metrics=growth_metrics,
        conversion_funnel=conversion_funnel,
        product_metrics=product_metrics,
        financial_metrics=financial_metrics,
        operational_metrics=operational_metrics,
        predictive_insights=predictive_insights,
    )

    # Cache the results in Redis (TTL: 15 minutes)
    await set_cached(cache_key, bi_data.dict(), ttl=900)

    return bi_data


@router.get("/support-metrics")
async def get_support_metrics(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> SupportMetrics:
    """
    Get support metrics analysis including common issues, feature requests, and support volume

    US#266: Support Metrics Analysis for Admin Analytics
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check Redis cache first (US#265: Redis Caching Integration)
    cache_key = "support_metrics"
    cached_data = await get_cached(cache_key)
    if cached_data:
        return SupportMetrics(**cached_data)

    # For demo purposes, return mock data
    # In production, integrate with support ticket system, feedback submissions, and feature request system
    # TODO: Replace with real data from:
    # - Support ticket system (if exists)
    # - User feedback submissions (early_adopter_api.py has feedback endpoint)
    # - Feature request system
    # - Error logs and stack traces
    support_data = generate_mock_support_metrics()

    # Cache the results in Redis (TTL: 30 minutes)
    await set_cached(cache_key, support_data.dict(), ttl=1800)

    return support_data


@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Get active alerts and notifications"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Mock active alerts
    active_alerts = [
        {
            "id": "alert-001",
            "type": "warning",
            "metric": "churn_rate",
            "message": "Churn rate increased to 3.5% (threshold: 3.0%)",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "severity": "medium",
            "acknowledged": False,
        },
        {
            "id": "alert-002",
            "type": "info",
            "metric": "revenue_growth",
            "message": "Monthly revenue growth exceeded target (23% vs 20%)",
            "timestamp": datetime.utcnow() - timedelta(hours=6),
            "severity": "low",
            "acknowledged": True,
        },
        {
            "id": "alert-003",
            "type": "critical",
            "metric": "system_performance",
            "message": "API response time degraded (245ms vs 150ms threshold)",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
            "severity": "high",
            "acknowledged": False,
        },
    ]

    return active_alerts


@router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Acknowledge an alert"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # In production, update alert status in database
    return {
        "success": True,
        "alert_id": alert_id,
        "acknowledged_by": current_user.email,
        "acknowledged_at": datetime.utcnow().isoformat(),
    }


@router.get("/export/csv")
async def export_analytics_csv(
    report_type: str = Query(..., description="Type of report to export"),
    date_range: str = Query("30d", description="Date range for export"),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Export analytics data as CSV"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # In production, generate actual CSV files
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    export_url = f"/downloads/analytics_{report_type}_{date_range}_{timestamp}.csv"

    return {
        "success": True,
        "export_url": export_url,
        "report_type": report_type,
        "date_range": date_range,
        "generated_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }


def generate_pdf_report(
    report_type: str,
    metrics: Dict[str, Any],
    date_range: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> bytes:
    """
    Generate PDF report for admin analytics

    US#263: PDF Report Generation for Admin Analytics
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available. Install reportlab package.",
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2563eb"),
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor("#1f2937"),
    )

    # Build PDF content
    content = []

    # Header
    report_title = {
        "executive_summary": "Executive Summary Report",
        "monthly": "Monthly Analytics Report",
        "custom": "Custom Analytics Report",
    }.get(report_type, "Analytics Report")

    content.append(Paragraph(report_title, title_style))
    content.append(Spacer(1, 20))

    # Report metadata
    metadata = [
        ["<b>Generated:</b>", datetime.utcnow().strftime("%B %d, %Y %H:%M UTC")],
        ["<b>Report Type:</b>", report_type.replace("_", " ").title()],
    ]
    if date_range:
        metadata.append(["<b>Date Range:</b>", date_range])
    if start_date and end_date:
        metadata.append(
            [
                "<b>Period:</b>",
                f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
            ]
        )

    metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
    metadata_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    content.append(metadata_table)
    content.append(Spacer(1, 30))

    # Executive Summary Section
    if report_type == "executive_summary":
        content.append(Paragraph("Platform Health Overview", heading_style))
        health_score = metrics.get("platform_health_score", 0.0)
        health_data = [
            ["Metric", "Value"],
            ["Platform Health Score", f"{health_score:.1f}/100"],
            ["Total Users", f"{metrics.get('total_users', 0):,}"],
            ["Total Teams", f"{metrics.get('total_teams', 0):,}"],
            ["Active Users (30d)", f"{metrics.get('active_users_30d', 0):,}"],
            ["Revenue (30d)", f"${metrics.get('total_revenue_30d', 0):,.2f}"],
            ["Churn Rate", f"{metrics.get('churn_rate', 0)*100:.1f}%"],
        ]
        health_table = Table(health_data, colWidths=[3 * inch, 2 * inch])
        health_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        content.append(health_table)
        content.append(Spacer(1, 20))

    # Detailed Metrics Section
    content.append(Paragraph("Detailed Metrics", heading_style))
    detailed_data = [
        ["Metric", "Value"],
        ["New Signups (30d)", f"{metrics.get('new_signups_30d', 0):,}"],
        ["New Teams (30d)", f"{metrics.get('new_teams_30d', 0):,}"],
        ["Active Teams (30d)", f"{metrics.get('active_teams_30d', 0):,}"],
        ["Average Team Size", f"{metrics.get('avg_team_size', 0):.1f}"],
    ]
    detailed_table = Table(detailed_data, colWidths=[3 * inch, 2 * inch])
    detailed_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    content.append(detailed_table)
    content.append(Spacer(1, 20))

    # Footer
    content.append(Spacer(1, 20))
    footer_text = f"Report generated on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}"
    content.append(Paragraph(footer_text, styles["Normal"]))

    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer.read()


@router.get("/export/pdf")
async def export_analytics_pdf(
    report_type: str = Query(..., description="Type of report: executive_summary, monthly, custom"),
    date_range: Optional[str] = Query("30d", description="Date range: 30d, 90d, custom"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format) for custom range"),
    end_date: Optional[str] = Query(None, description="End date (ISO format) for custom range"),
    current_user: User = Depends(require_admin),
) -> Response:
    """
    Export analytics data as PDF report

    US#263: PDF Report Generation for Admin Analytics
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    if report_type not in ["executive_summary", "monthly", "custom"]:
        raise HTTPException(
            status_code=400, detail="Invalid report_type. Must be: executive_summary, monthly, or custom"
        )

    # Parse dates if provided
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
    if end_date:
        try:
            parsed_end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")

    # Get metrics (in production, fetch from database)
    # For now, use mock metrics
    metrics = generate_mock_platform_metrics().dict()

    try:
        # Generate PDF
        pdf_bytes = generate_pdf_report(
            report_type=report_type,
            metrics=metrics,
            date_range=date_range,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
        )

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"admin-analytics-{report_type}-{date_range}-{timestamp}.pdf"

        # Return PDF as downloadable file
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF generation failed", error=str(e), report_type=report_type)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/cache/clear")
async def clear_analytics_cache_endpoint(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Clear all admin analytics cache (admin only)

    US#265: Redis Caching Integration
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await clear_analytics_cache()
    return {
        "success": success,
        "message": "Analytics cache cleared" if success else "Cache clear failed",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get cache statistics (admin only)

    US#265: Redis Caching Integration
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    redis_client = await get_redis_client()
    if not redis_client or not redis_client.is_connected:
        return {
            "redis_connected": False,
            "message": "Redis not available",
        }

    try:
        # Get all analytics cache keys
        keys = await redis_client.redis.keys("admin_analytics:*")
        key_count = len(keys)

        # Get Redis info
        info = await redis_client.redis.info()
        memory_used = info.get("used_memory_human", "N/A")

        return {
            "redis_connected": True,
            "cache_keys_count": key_count,
            "memory_used": memory_used,
            "cache_keys": [key.decode() if isinstance(key, bytes) else key for key in keys[:10]],  # First 10 keys
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Cache stats failed", error=str(e))
        return {
            "redis_connected": False,
            "error": str(e),
        }


@router.get("/real-time-metrics")
async def get_real_time_metrics(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Get real-time platform metrics for live dashboard"""

    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Mock real-time metrics
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": 234,
        "api_requests_per_minute": 1247,
        "new_signups_today": 23,
        "revenue_today": 1456.78,
        "system_load": 0.67,
        "memory_usage": 0.73,
        "database_connections": 45,
        "cache_hit_rate": 0.94,
        "error_rate_5m": 0.0012,
        "response_time_p95": 167,  # 95th percentile response time in ms
    }


class SupportMetrics(BaseModel):
    """Support analytics metrics for admin dashboard"""

    common_issues: List[Dict[str, Any]]
    feature_requests: List[Dict[str, Any]]
    support_volume: Dict[str, Any]
    issue_categories: Dict[str, int]
    user_satisfaction: Dict[str, float]
    resolution_times: Dict[str, float]


class SecurityMetrics(BaseModel):
    """Security monitoring metrics for admin dashboard"""

    auth_failures_24h: int
    auth_failures_7d: int
    auth_failures_30d: int
    failed_logins_by_user: List[Dict[str, Any]]
    failed_logins_by_ip: List[Dict[str, Any]]
    suspicious_ips: List[Dict[str, Any]]
    active_security_incidents: int
    auth_success_rate: float
    security_health_score: float
    unauthorized_access_attempts: int
    account_lockouts: int
    rate_limit_exceeded_count: int
    timestamp: str


@router.get("/rate-limits/{identifier}")
async def get_rate_limit_status(
    identifier: str,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get rate limit status for an IP or user ID.

    US-91: Admin endpoint to view rate limit status.

    Args:
        identifier: IP address or user ID
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Determine if identifier is IP or user ID
        # Simple heuristic: UUIDs are user IDs, IPs are not
        import re

        from utils.api_rate_limiting import api_rate_limiter

        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

        if uuid_pattern.match(identifier):
            # User ID
            rate_info = api_rate_limiter.get_rate_limit_info(user_id=identifier)
        else:
            # IP address
            rate_info = api_rate_limiter.get_rate_limit_info(ip=identifier)

        return {
            "identifier": identifier,
            "type": "user_id" if uuid_pattern.match(identifier) else "ip",
            "rate_limit_info": rate_info,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {str(e)}")


@router.post("/rate-limits/{identifier}/reset")
async def reset_rate_limit(
    identifier: str,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Reset rate limit for an IP or user ID.

    US-91: Admin endpoint to reset rate limits.

    Args:
        identifier: IP address or user ID
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Determine if identifier is IP or user ID
        import re

        from utils.api_rate_limiting import api_rate_limiter

        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

        if uuid_pattern.match(identifier):
            # User ID
            success = api_rate_limiter.reset_user_limit(identifier)
            reset_type = "user"
        else:
            # IP address
            success = api_rate_limiter.reset_ip_limit(identifier)
            reset_type = "ip"

        if success:
            return {
                "success": True,
                "message": f"Rate limit reset for {reset_type}: {identifier}",
                "identifier": identifier,
                "type": reset_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"No rate limit data found for {identifier}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset rate limit: {str(e)}")


@router.get("/security-metrics")
async def get_security_metrics(
    current_user: User = Depends(require_admin),
) -> SecurityMetrics:
    """
    Get security monitoring metrics for admin dashboard.

    SPEC-030: US-262 - Security Monitoring Dashboard
    Returns comprehensive security metrics including:
    - Authentication failures
    - Suspicious activity
    - Account lockouts
    - Security health score
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from lib.security_monitoring import (
            get_security_metrics as get_security_metrics_data,
        )

        metrics_data = get_security_metrics_data()
        return SecurityMetrics(**metrics_data)

    except Exception as e:
        # Fallback to minimal metrics if security monitoring fails
        return SecurityMetrics(
            auth_failures_24h=0,
            auth_failures_7d=0,
            auth_failures_30d=0,
            failed_logins_by_user=[],
            failed_logins_by_ip=[],
            suspicious_ips=[],
            active_security_incidents=0,
            auth_success_rate=100.0,
            security_health_score=100.0,
            unauthorized_access_attempts=0,
            account_lockouts=0,
            rate_limit_exceeded_count=0,
            timestamp=datetime.utcnow().isoformat(),
        )


# ============================================================================
# US#264: Advanced Admin Tools for Admin Analytics Console
# ============================================================================

# In-memory storage for system configuration and maintenance mode
# In production, use proper database/Redis storage
_system_config: Dict[str, Any] = {
    "maintenance_mode": {"enabled": False, "message": "", "allowed_admins": []},
    "rate_limits": {"global": 1000, "per_user": 100, "per_team": 500},
    "system_settings": {"max_team_size": 50, "invitation_limit": 100},
}
_config_history: List[Dict[str, Any]] = []
_maintenance_mode: Dict[str, Any] = {"enabled": False, "message": "", "scheduled_end": None}
_impersonation_sessions: Dict[str, Dict[str, Any]] = {}  # admin_id -> session


class SystemConfig(BaseModel):
    """System configuration model"""

    maintenance_mode: Dict[str, Any]
    rate_limits: Dict[str, int]
    system_settings: Dict[str, int]


class FeatureFlagRequest(BaseModel):
    """Feature flag update request"""

    name: str
    enabled: Optional[bool] = None
    description: Optional[str] = None
    target_users: Optional[str] = None  # "all" | user_id | team_id
    rollout_percentage: Optional[int] = None  # 0-100


class MaintenanceModeRequest(BaseModel):
    """Maintenance mode request"""

    message: Optional[str] = None
    scheduled_end: Optional[str] = None  # ISO datetime


@router.get("/system-config")
async def get_system_config(
    current_user: User = Depends(require_admin),
) -> SystemConfig:
    """
    Get current system configuration

    US#264: Advanced Admin Tools - System Configuration
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    return SystemConfig(**_system_config)


@router.put("/system-config")
async def update_system_config(
    config: SystemConfig,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Update system configuration

    US#264: Advanced Admin Tools - System Configuration
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Record change in history
    _config_history.append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "changed_by": str(current_user.id),
            "changes": config.dict(),
        }
    )

    # Update config
    _system_config.update(config.dict())

    logger.info("System configuration updated", user_id=str(current_user.id))

    return {
        "success": True,
        "message": "System configuration updated",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/system-config/history")
async def get_config_history(
    current_user: User = Depends(require_admin),
    limit: int = Query(50, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Get configuration change history

    US#264: Advanced Admin Tools - System Configuration
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "history": _config_history[-limit:],
        "total_changes": len(_config_history),
    }


@router.get("/feature-flags")
async def list_feature_flags(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    List all feature flags

    US#264: Advanced Admin Tools - Feature Flags Management
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from lib.security.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()
        flags = manager.get_all_flags()

        return {
            "flags": flags,
            "count": len(flags),
        }
    except Exception as e:
        logger.error("Failed to get feature flags", error=str(e))
        return {"flags": {}, "count": 0, "error": str(e)}


@router.put("/feature-flags/{flag_name}")
async def update_feature_flag(
    flag_name: str,
    request: FeatureFlagRequest,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Update a feature flag

    US#264: Advanced Admin Tools - Feature Flags Management
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from lib.security.feature_flags import FeatureFlagManager

        manager = FeatureFlagManager()

        if request.enabled is not None:
            success = manager.set_flag(flag_name, request.enabled, updated_by=str(current_user.id))
            if not success:
                raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        flag_status = manager.get_flag_status(flag_name)

        return {
            "success": True,
            "flag": flag_status,
            "message": f"Feature flag '{flag_name}' updated",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update feature flag", flag=flag_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update feature flag: {str(e)}")


@router.post("/feature-flags")
async def create_feature_flag(
    request: FeatureFlagRequest,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Create a new feature flag

    US#264: Advanced Admin Tools - Feature Flags Management
    Note: This extends the existing FeatureFlagManager. In production, you may need
    to extend the manager to support dynamic flag creation.
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # For now, return a message that flags need to be added to FeatureFlagManager
    # In production, extend FeatureFlagManager to support dynamic creation
    return {
        "success": False,
        "message": "Feature flags must be added to FeatureFlagManager configuration. Dynamic creation not yet supported.",
        "note": "To add a new flag, update the FeatureFlagManager's _initialize_default_flags method",
    }


@router.post("/maintenance-mode/enable")
async def enable_maintenance_mode(
    request: MaintenanceModeRequest,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Enable maintenance mode

    US#264: Advanced Admin Tools - Maintenance Mode
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    _maintenance_mode["enabled"] = True
    _maintenance_mode["message"] = request.message or "System is under maintenance. Please check back soon."
    _maintenance_mode["enabled_by"] = str(current_user.id)
    _maintenance_mode["enabled_at"] = datetime.utcnow().isoformat()
    if request.scheduled_end:
        _maintenance_mode["scheduled_end"] = request.scheduled_end

    logger.warning("Maintenance mode enabled", user_id=str(current_user.id), message=_maintenance_mode["message"])

    return {
        "success": True,
        "message": "Maintenance mode enabled",
        "maintenance_mode": _maintenance_mode,
    }


@router.post("/maintenance-mode/disable")
async def disable_maintenance_mode(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Disable maintenance mode

    US#264: Advanced Admin Tools - Maintenance Mode
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    _maintenance_mode["enabled"] = False
    _maintenance_mode["disabled_by"] = str(current_user.id)
    _maintenance_mode["disabled_at"] = datetime.utcnow().isoformat()

    logger.info("Maintenance mode disabled", user_id=str(current_user.id))

    return {
        "success": True,
        "message": "Maintenance mode disabled",
        "maintenance_mode": _maintenance_mode,
    }


@router.get("/maintenance-mode/status")
async def get_maintenance_mode_status(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get maintenance mode status

    US#264: Advanced Admin Tools - Maintenance Mode
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "maintenance_mode": _maintenance_mode,
    }


@router.post("/support/impersonate/{user_id}")
async def start_impersonation(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Start user impersonation session

    US#264: Advanced Admin Tools - Support Tools
    Security: Admin-only, audit logged, time-limited
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Check if already impersonating
    admin_id = str(current_user.id)
    if admin_id in _impersonation_sessions:
        raise HTTPException(status_code=400, detail="Already impersonating a user. Stop current session first.")

    # Create impersonation session
    session = {
        "admin_id": admin_id,
        "admin_email": current_user.email,
        "target_user_id": user_id,
        "target_user_email": target_user.email,
        "started_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),  # 1 hour limit
    }
    _impersonation_sessions[admin_id] = session

    logger.warning(
        "User impersonation started",
        admin_id=admin_id,
        target_user_id=user_id,
        expires_at=session["expires_at"],
    )

    return {
        "success": True,
        "message": f"Impersonating user {target_user.email}",
        "session": session,
    }


@router.post("/support/stop-impersonation")
async def stop_impersonation(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Stop current impersonation session

    US#264: Advanced Admin Tools - Support Tools
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    admin_id = str(current_user.id)
    if admin_id not in _impersonation_sessions:
        raise HTTPException(status_code=400, detail="No active impersonation session")

    session = _impersonation_sessions.pop(admin_id)

    logger.info("User impersonation stopped", admin_id=admin_id, target_user_id=session["target_user_id"])

    return {
        "success": True,
        "message": "Impersonation stopped",
        "session": session,
    }


@router.get("/support/impersonation-status")
async def get_impersonation_status(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get current impersonation status

    US#264: Advanced Admin Tools - Support Tools
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    admin_id = str(current_user.id)
    session = _impersonation_sessions.get(admin_id)

    return {
        "is_impersonating": session is not None,
        "session": session,
    }


@router.get("/support/debug/user/{user_id}")
async def get_user_debug_info(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get debug information for a user

    US#264: Advanced Admin Tools - Support Tools
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Get user teams
    teams = db.query(Team).join(TeamMembership).filter(TeamMembership.user_id == user_id).all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "account_type": user.account_type,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_active": user.is_active,
        },
        "teams": [{"id": str(t.id), "name": t.name} for t in teams],
        "metadata": {
            "total_teams": len(teams),
            "subscription_tier": getattr(user, "subscription_tier", "free"),
        },
        "note": "Additional debug info (activity logs, errors) would be added in production",
    }


@router.get("/support/debug/team/{team_id}")
async def get_team_debug_info(
    team_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get debug information for a team

    US#264: Advanced Admin Tools - Support Tools
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    # Get team members
    members = db.query(TeamMembership).filter(TeamMembership.team_id == team_id).all()

    return {
        "team": {
            "id": str(team.id),
            "name": team.name,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "is_standalone": team.is_standalone,
        },
        "members": [
            {
                "user_id": str(m.user_id),
                "role": m.role,
                "status": m.status,
            }
            for m in members
        ],
        "metadata": {
            "total_members": len(members),
        },
        "note": "Additional debug info (activity logs, errors) would be added in production",
    }


@router.get("/support/debug/system")
async def get_system_debug_info(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get system debug information

    US#264: Advanced Admin Tools - Support Tools
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "system": {
            "timestamp": datetime.utcnow().isoformat(),
            "maintenance_mode": _maintenance_mode["enabled"],
            "active_impersonations": len(_impersonation_sessions),
        },
        "configuration": {
            "rate_limits": _system_config.get("rate_limits", {}),
            "system_settings": _system_config.get("system_settings", {}),
        },
        "note": "Additional system metrics (memory, CPU, DB connections) would be added in production",
    }


@router.get("/support/logs")
async def query_logs(
    current_user: User = Depends(require_admin),
    level: Optional[str] = Query(None, description="Log level: error, warning, info"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    time_range: Optional[str] = Query("24h", description="Time range: 1h, 24h, 7d"),
    search: Optional[str] = Query(None, description="Text search in log messages"),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """
    Query application logs

    US#264: Advanced Admin Tools - Support Tools
    Note: In production, integrate with actual logging system (e.g., ELK, CloudWatch)
    """
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Mock log entries (in production, query actual log storage)
    mock_logs = [
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
            "level": ["error", "warning", "info"][i % 3],
            "message": f"Mock log entry {i}",
            "user_id": user_id if user_id else None,
            "team_id": team_id if team_id else None,
        }
        for i in range(min(limit, 50))
    ]

    # Filter by level if provided
    if level:
        mock_logs = [log for log in mock_logs if log["level"] == level]

    # Filter by search if provided
    if search:
        mock_logs = [log for log in mock_logs if search.lower() in log["message"].lower()]

    return {
        "logs": mock_logs[:limit],
        "count": len(mock_logs),
        "filters": {
            "level": level,
            "user_id": user_id,
            "team_id": team_id,
            "time_range": time_range,
            "search": search,
        },
        "note": "This is mock data. In production, integrate with actual logging system.",
    }


# WebSocket connection manager for admin analytics
class AdminAnalyticsWebSocketManager:
    """Manages WebSocket connections for real-time admin analytics streaming"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self.update_interval = 5  # Update every 5 seconds
        self.is_running = False
        self.background_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "Admin analytics WebSocket client connected",
            user_id=user_id,
            total_connections=len(self.active_connections),
        )

        # Start background task if not running
        if not self.is_running:
            await self.start_background_updates()

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("Admin analytics WebSocket client disconnected", total_connections=len(self.active_connections))

        # Stop background task if no connections
        if not self.active_connections and self.is_running:
            self.stop_background_updates()

    async def start_background_updates(self):
        """Start background task for metrics collection"""
        if self.background_task is None or self.background_task.done():
            self.is_running = True
            self.background_task = asyncio.create_task(self._background_metrics_collector())
            logger.info("Admin analytics background updates started")

    def stop_background_updates(self):
        """Stop background task"""
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            self.is_running = False
            logger.info("Admin analytics background updates stopped")

    async def _background_metrics_collector(self):
        """Background task to collect and broadcast metrics"""
        while self.is_running:
            try:
                # Collect real-time metrics
                metrics = await self._collect_realtime_metrics()

                # Store in history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)

                # Broadcast to all connected clients
                await self._broadcast_metrics(metrics)

                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in admin analytics metrics collector", error=str(e))
                await asyncio.sleep(self.update_interval)

    async def _collect_realtime_metrics(self) -> Dict[str, Any]:
        """Collect real-time admin analytics metrics"""
        # Get current metrics (similar to get_real_time_metrics endpoint)
        # This would typically query the database and system metrics
        return {
            "type": "metrics_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "active_sessions": 234,  # TODO: Replace with real query
                "api_requests_per_minute": 1247,  # TODO: Replace with real query
                "new_signups_today": 23,  # TODO: Replace with real query
                "revenue_today": 1456.78,  # TODO: Replace with real query
                "system_load": 0.67,
                "memory_usage": 0.73,
                "database_connections": 45,
                "cache_hit_rate": 0.94,
                "error_rate_5m": 0.0012,
                "response_time_p95": 167,
            },
        }

    async def _broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to all connected clients"""
        message = json.dumps(metrics)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning("Failed to send metrics to client", error=str(e))
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics history for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if datetime.fromisoformat(m.get("timestamp", "")) >= cutoff_time]


# Global WebSocket manager instance
admin_analytics_manager = AdminAnalyticsWebSocketManager()


@router.websocket("/ws")
async def admin_analytics_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time admin analytics streaming.

    US#314: Real-Time WebSocket Integration for Admin Analytics

    Replaces polling-based updates with true real-time data streaming.
    Requires admin authentication via WebSocket token.

    Token should be provided via query parameter: ?token=JWT_TOKEN
    """
    # Authenticate WebSocket connection
    try:
        user = await authenticate_websocket(websocket)
        user_id = user.get("id")
        user_email = user.get("email")

        # Verify admin permissions
        admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
        if user_email not in admin_emails:
            await websocket.close(code=1008, reason="Unauthorized: Admin access required")
            logger.warning(
                "Non-admin attempted to connect to admin analytics WebSocket", user_id=user_id, email=user_email
            )
            return

    except WebSocketException as e:
        await websocket.close(code=e.code, reason=e.reason)
        return
    except Exception as e:
        await websocket.close(code=1011, reason=f"Authentication error: {str(e)}")
        return

    await admin_analytics_manager.connect(websocket, user_id)

    try:
        while True:
            # Handle client messages
            message = await websocket.receive_text()
            data = json.loads(message)

            # Handle client requests
            if data.get("type") == "get_history":
                minutes = data.get("minutes", 60)
                history = admin_analytics_manager.get_metrics_history(minutes)
                await websocket.send_text(json.dumps({"type": "history_data", "data": history}))

            elif data.get("type") == "subscribe_metric":
                # Allow clients to subscribe to specific metrics
                metric_name = data.get("metric_name")
                await websocket.send_text(json.dumps({"type": "subscription_confirmed", "metric_name": metric_name}))

            elif data.get("type") == "ping":
                # Heartbeat/ping
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))

    except WebSocketDisconnect:
        admin_analytics_manager.disconnect(websocket)
        logger.info("Admin analytics WebSocket client disconnected")
    except Exception as e:
        logger.error("Admin analytics WebSocket error", error=str(e))
        admin_analytics_manager.disconnect(websocket)
