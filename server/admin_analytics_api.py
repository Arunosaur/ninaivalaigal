"""
SPEC-030: Admin-Level Analytics Console
Internal operations dashboard with comprehensive business intelligence
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from collections import defaultdict
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, text
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User
from models.standalone_teams import StandaloneTeamManager, TeamMembership

# Initialize router
router = APIRouter(prefix="/admin-analytics", tags=["admin-analytics"])


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
platform_metrics_cache = {}
churn_analysis_cache = {}
revenue_cohorts_cache = {}
user_engagement_cache = {}
alert_configs_db = {}


def check_admin_permissions(current_user: User) -> bool:
    """Check if user has admin permissions"""
    # In production, implement proper admin role checking
    # For now, allow all authenticated users for demo purposes
    return True


def calculate_platform_health_score(metrics: Dict[str, Any]) -> float:
    """Calculate overall platform health score (0-100)"""
    # Weighted scoring based on key metrics
    weights = {
        'user_growth': 0.25,      # New user acquisition
        'team_growth': 0.20,      # Team creation rate
        'engagement': 0.25,       # User activity levels
        'revenue_growth': 0.20,   # Revenue trends
        'churn_rate': 0.10        # User retention
    }
    
    # Mock calculation - in production, use real metrics
    user_growth_score = min(100, (metrics.get('new_signups_30d', 0) / 100) * 100)
    team_growth_score = min(100, (metrics.get('new_teams_30d', 0) / 50) * 100)
    engagement_score = min(100, (metrics.get('active_users_30d', 0) / metrics.get('total_users', 1)) * 100)
    revenue_growth_score = min(100, (metrics.get('total_revenue_30d', 0) / 10000) * 100)
    churn_score = max(0, 100 - (metrics.get('churn_rate', 0.05) * 2000))  # Lower churn = higher score
    
    health_score = (
        user_growth_score * weights['user_growth'] +
        team_growth_score * weights['team_growth'] +
        engagement_score * weights['engagement'] +
        revenue_growth_score * weights['revenue_growth'] +
        churn_score * weights['churn_rate']
    )
    
    return round(health_score, 1)


def generate_mock_platform_metrics() -> PlatformMetrics:
    """Generate mock platform metrics for demo"""
    base_metrics = {
        'total_users': 2847,
        'total_teams': 892,
        'active_users_30d': 1923,
        'active_teams_30d': 634,
        'new_signups_30d': 287,
        'new_teams_30d': 94,
        'total_revenue_30d': 28450.00,
        'avg_team_size': 4.2,
        'churn_rate': 0.035
    }
    
    health_score = calculate_platform_health_score(base_metrics)
    
    return PlatformMetrics(
        total_users=base_metrics['total_users'],
        total_teams=base_metrics['total_teams'],
        active_users_30d=base_metrics['active_users_30d'],
        active_teams_30d=base_metrics['active_teams_30d'],
        new_signups_30d=base_metrics['new_signups_30d'],
        new_teams_30d=base_metrics['new_teams_30d'],
        total_revenue_30d=base_metrics['total_revenue_30d'],
        avg_team_size=base_metrics['avg_team_size'],
        platform_health_score=health_score
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
            "warning_signals": ["low_activity", "no_recent_invites", "support_tickets"]
        },
        {
            "team_id": "team-002", 
            "team_name": "Tech Innovators",
            "risk_score": 0.72,
            "last_activity": "2024-09-18T14:20:00Z",
            "members": 8,
            "plan": "team_enterprise",
            "revenue_at_risk": 99.00,
            "warning_signals": ["declining_usage", "member_departures"]
        },
        {
            "team_id": "team-003",
            "team_name": "Creative Agency",
            "risk_score": 0.68,
            "last_activity": "2024-09-20T09:15:00Z",
            "members": 12,
            "plan": "organization",
            "revenue_at_risk": 500.00,
            "warning_signals": ["payment_delays", "feature_complaints"]
        }
    ]
    
    retention_by_cohort = {
        "2024-06": 0.92,  # June cohort retention
        "2024-07": 0.89,  # July cohort retention
        "2024-08": 0.94,  # August cohort retention
        "2024-09": 0.96   # September cohort retention (early)
    }
    
    churn_reasons = {
        "pricing_concerns": 12,
        "feature_limitations": 8,
        "poor_onboarding": 6,
        "competitor_switch": 4,
        "team_downsizing": 3,
        "technical_issues": 2
    }
    
    at_risk_revenue = sum(team["revenue_at_risk"] for team in churn_risk_teams)
    
    return ChurnAnalysis(
        monthly_churn_rate=0.035,
        churn_risk_teams=churn_risk_teams,
        retention_by_cohort=retention_by_cohort,
        churn_reasons=churn_reasons,
        early_warning_count=len(churn_risk_teams),
        at_risk_revenue=at_risk_revenue
    )


def generate_mock_revenue_cohorts() -> RevenueCohorts:
    """Generate mock revenue cohort analysis for demo"""
    cohort_data = {
        "2024-06": {
            "month_0": 2450.00,
            "month_1": 2680.00,
            "month_2": 2890.00,
            "month_3": 3120.00
        },
        "2024-07": {
            "month_0": 3200.00,
            "month_1": 3520.00,
            "month_2": 3780.00
        },
        "2024-08": {
            "month_0": 4100.00,
            "month_1": 4510.00
        },
        "2024-09": {
            "month_0": 5200.00
        }
    }
    
    ltv_by_cohort = {
        "2024-06": 1247.50,
        "2024-07": 1389.20,
        "2024-08": 1456.80,
        "2024-09": 1523.40  # Projected
    }
    
    return RevenueCohorts(
        cohort_data=cohort_data,
        ltv_by_cohort=ltv_by_cohort,
        revenue_growth_rate=0.23,  # 23% month-over-month
        expansion_revenue=1250.00,
        contraction_revenue=320.00,
        net_revenue_retention=1.12  # 112% NRR
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
        base_users = 1200
        if weekday >= 5:  # Weekend
            base_users *= 0.7
        
        daily_active_users.append({
            "date": date.strftime("%Y-%m-%d"),
            "active_users": int(base_users + (i * 15)),  # Growth trend
            "new_users": max(0, int(25 + (i * 2) - (weekday * 3))),
            "returning_users": int(base_users * 0.85)
        })
    
    feature_adoption = {
        "memory_creation": 0.89,
        "team_invitations": 0.67,
        "ai_suggestions": 0.45,
        "memory_browser": 0.78,
        "team_dashboard": 0.56,
        "billing_console": 0.23,
        "usage_analytics": 0.12
    }
    
    engagement_score_distribution = {
        "high_engagement": 234,      # 80-100 score
        "medium_engagement": 567,    # 50-79 score
        "low_engagement": 423,       # 20-49 score
        "inactive": 156              # 0-19 score
    }
    
    return UserEngagement(
        daily_active_users=daily_active_users,
        feature_adoption=feature_adoption,
        session_duration_avg=18.5,  # minutes
        actions_per_session=12.3,
        engagement_score_distribution=engagement_score_distribution,
        power_users_count=89  # Users with high engagement scores
    )


@router.get("/platform-overview")
async def get_platform_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlatformMetrics:
    """Get high-level platform metrics overview"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check cache first
    cache_key = "platform_metrics"
    if cache_key in platform_metrics_cache:
        cached_data = platform_metrics_cache[cache_key]
        if datetime.utcnow() - cached_data["timestamp"] < timedelta(minutes=15):
            return PlatformMetrics(**cached_data["data"])
    
    try:
        # Get real metrics from database
        total_users = db.query(User).count()
        total_teams = db.query(Team).filter(Team.is_standalone.is_(True)).count()
        
        # Calculate active users (users with activity in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # In production, join with activity/session tables
        active_users_30d = int(total_users * 0.68)  # Mock 68% activity rate
        
        # Calculate active teams
        active_teams_30d = int(total_teams * 0.71)  # Mock 71% team activity rate
        
        # Calculate new signups (mock data)
        new_signups_30d = int(total_users * 0.12)  # Mock 12% growth rate
        new_teams_30d = int(total_teams * 0.11)    # Mock 11% team growth
        
        # Calculate revenue (mock data)
        total_revenue_30d = float(active_teams_30d * 45.50)  # Mock average revenue per team
        
        # Calculate average team size
        team_memberships = db.query(TeamMembership).filter(
            TeamMembership.status == "active"
        ).count()
        avg_team_size = round(team_memberships / max(total_teams, 1), 1)
        
        metrics_data = {
            'total_users': total_users,
            'total_teams': total_teams,
            'active_users_30d': active_users_30d,
            'active_teams_30d': active_teams_30d,
            'new_signups_30d': new_signups_30d,
            'new_teams_30d': new_teams_30d,
            'total_revenue_30d': total_revenue_30d,
            'avg_team_size': avg_team_size
        }
        
        health_score = calculate_platform_health_score(metrics_data)
        
        platform_metrics = PlatformMetrics(
            **metrics_data,
            platform_health_score=health_score
        )
        
        # Cache the results
        platform_metrics_cache[cache_key] = {
            "data": platform_metrics.dict(),
            "timestamp": datetime.utcnow()
        }
        
        return platform_metrics
        
    except Exception as e:
        # Fallback to mock data if database queries fail
        print(f"Database query failed, using mock data: {e}")
        return generate_mock_platform_metrics()


@router.get("/churn-analysis")
async def get_churn_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChurnAnalysis:
    """Get comprehensive churn analysis and early warning indicators"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # For demo purposes, return mock data
    # In production, implement real churn analysis algorithms
    return generate_mock_churn_analysis()


@router.get("/revenue-cohorts")
async def get_revenue_cohorts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RevenueCohorts:
    """Get revenue cohort analysis and customer lifetime value metrics"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # For demo purposes, return mock data
    # In production, implement real cohort analysis
    return generate_mock_revenue_cohorts()


@router.get("/user-engagement")
async def get_user_engagement(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserEngagement:
    """Get user engagement and activity metrics"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # For demo purposes, return mock data
    # In production, implement real engagement tracking
    return generate_mock_user_engagement()


@router.get("/business-intelligence")
async def get_business_intelligence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BusinessIntelligence:
    """Get comprehensive business intelligence dashboard"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
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
        "time_to_value": 4.2  # Days to first value realization
    }
    
    # Calculate conversion funnel
    conversion_funnel = {
        "visitors": 12450,
        "signups": 1247,  # 10% conversion
        "activated_users": 934,  # 75% activation
        "team_creators": 467,  # 50% create teams
        "paid_customers": 112,  # 24% upgrade to paid
        "retention_30d": 0.89  # 89% 30-day retention
    }
    
    # Product metrics
    product_metrics = {
        "feature_adoption_rate": sum(user_engagement.feature_adoption.values()) / len(user_engagement.feature_adoption),
        "daily_active_users": user_engagement.daily_active_users[-1]["active_users"],
        "session_duration": user_engagement.session_duration_avg,
        "user_satisfaction": 4.2,  # Out of 5
        "nps_score": 67,  # Net Promoter Score
        "support_ticket_volume": 23  # Weekly average
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
        "runway_months": 18.5
    }
    
    # Operational metrics
    operational_metrics = {
        "system_uptime": 0.9987,  # 99.87% uptime
        "api_response_time": 145,  # milliseconds
        "error_rate": 0.0023,  # 0.23% error rate
        "support_response_time": 2.3,  # hours
        "deployment_frequency": 12,  # per month
        "lead_time": 3.2,  # days
        "mttr": 0.8  # Mean time to recovery (hours)
    }
    
    # Predictive insights
    predictive_insights = {
        "projected_mrr_3m": platform_metrics.total_revenue_30d * 1.45,
        "projected_users_3m": platform_metrics.total_users * 1.38,
        "churn_risk_revenue": churn_analysis.at_risk_revenue,
        "expansion_opportunities": 8,  # Teams ready for upgrade
        "market_size_potential": 2.4e6,  # $2.4M addressable market
        "competitive_threats": 2,  # Active competitive threats
        "growth_bottlenecks": ["onboarding_friction", "feature_discovery"]
    }
    
    return BusinessIntelligence(
        growth_metrics=growth_metrics,
        conversion_funnel=conversion_funnel,
        product_metrics=product_metrics,
        financial_metrics=financial_metrics,
        operational_metrics=operational_metrics,
        predictive_insights=predictive_insights
    )


@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(get_current_user)
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
            "acknowledged": False
        },
        {
            "id": "alert-002",
            "type": "info",
            "metric": "revenue_growth",
            "message": "Monthly revenue growth exceeded target (23% vs 20%)",
            "timestamp": datetime.utcnow() - timedelta(hours=6),
            "severity": "low",
            "acknowledged": True
        },
        {
            "id": "alert-003",
            "type": "critical",
            "metric": "system_performance",
            "message": "API response time degraded (245ms vs 150ms threshold)",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
            "severity": "high",
            "acknowledged": False
        }
    ]
    
    return active_alerts


@router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Acknowledge an alert"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In production, update alert status in database
    return {
        "success": True,
        "alert_id": alert_id,
        "acknowledged_by": current_user.email,
        "acknowledged_at": datetime.utcnow().isoformat()
    }


@router.get("/export/csv")
async def export_analytics_csv(
    report_type: str = Query(..., description="Type of report to export"),
    date_range: str = Query("30d", description="Date range for export"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export analytics data as CSV"""
    
    if not check_admin_permissions(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In production, generate actual CSV files
    export_url = f"/downloads/analytics_{report_type}_{date_range}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return {
        "success": True,
        "export_url": export_url,
        "report_type": report_type,
        "date_range": date_range,
        "generated_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }


@router.get("/real-time-metrics")
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user)
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
        "response_time_p95": 167  # 95th percentile response time in ms
    }
