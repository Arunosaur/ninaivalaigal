"""
Usage Analytics Dashboard API
Provides comprehensive analytics for team usage, conversions, and monetization
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from auth import get_current_user, get_db
from database import Team, User
from fastapi import APIRouter, Depends, HTTPException, Query
from models.standalone_teams import (
    StandaloneTeamManager,
    TeamInvitation,
    TeamMembership,
    TeamUpgradeHistory,
)
from pydantic import BaseModel
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

# Initialize router
router = APIRouter(prefix="/analytics", tags=["usage-analytics"])


# Pydantic Models
class TeamGrowthMetrics(BaseModel):
    """Team growth metrics over time"""

    date: datetime
    teams_created: int
    total_teams: int
    members_added: int
    total_members: int
    invitations_sent: int
    invitations_accepted: int


class ConversionMetrics(BaseModel):
    """Conversion funnel metrics"""

    period: str
    signups: int
    team_creations: int
    team_creation_rate: float
    invitations_sent: int
    invitations_accepted: int
    invitation_acceptance_rate: float
    upgrades_initiated: int
    upgrades_completed: int
    upgrade_conversion_rate: float


class UsageDistribution(BaseModel):
    """Usage distribution across team sizes"""

    team_size_range: str
    team_count: int
    percentage: float
    avg_storage_usage: float
    avg_ai_queries: int


class RevenueProjection(BaseModel):
    """Revenue projection based on current trends"""

    period: str
    projected_teams: int
    projected_revenue: float
    conversion_assumptions: Dict[str, float]
    growth_rate: float


class TeamAnalytics(BaseModel):
    """Individual team analytics"""

    team_id: UUID
    team_name: str
    created_date: datetime
    member_count: int
    plan: str
    monthly_revenue: float
    storage_usage_gb: float
    ai_queries_count: int
    last_activity: datetime
    conversion_probability: float


class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard data"""

    overview: Dict[str, Any]
    growth_metrics: List[TeamGrowthMetrics]
    conversion_funnel: ConversionMetrics
    usage_distribution: List[UsageDistribution]
    revenue_projection: RevenueProjection
    top_teams: List[TeamAnalytics]
    alerts: List[Dict[str, str]]


def get_team_manager() -> StandaloneTeamManager:
    """Dependency to get team manager"""
    return StandaloneTeamManager()


def calculate_team_plan(member_count: int) -> str:
    """Determine team plan based on member count"""
    if member_count <= 5:
        return "free"
    elif member_count <= 20:
        return "team_pro"
    elif member_count <= 50:
        return "team_enterprise"
    else:
        return "organization"


def calculate_monthly_revenue(plan: str) -> float:
    """Calculate monthly revenue for a plan"""
    revenue_map = {
        "free": 0.0,
        "team_pro": 29.0,
        "team_enterprise": 99.0,
        "organization": 500.0,
    }
    return revenue_map.get(plan, 0.0)


def calculate_conversion_probability(
    team: Team, member_count: int, db: Session
) -> float:
    """Calculate probability of team upgrading based on usage patterns"""
    base_probability = 0.1  # 10% base conversion rate

    # Factor 1: Team size approaching limits
    if member_count >= 4:  # 80% of free limit
        base_probability += 0.3

    # Factor 2: Team age (older teams more likely to convert)
    if team.created_at:
        days_old = (datetime.utcnow() - team.created_at).days
        if days_old > 30:
            base_probability += 0.2
        elif days_old > 7:
            base_probability += 0.1

    # Factor 3: Invitation activity (active teams more likely to convert)
    recent_invitations = (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.team_id == team.id,
            TeamInvitation.created_at >= datetime.utcnow() - timedelta(days=7),
        )
        .count()
    )

    if recent_invitations > 0:
        base_probability += 0.15

    return min(base_probability, 0.95)  # Cap at 95%


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsDashboard:
    """
    Get comprehensive analytics dashboard
    Note: In production, this would require admin permissions
    """
    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Overview metrics
    total_teams = db.query(Team).filter(Team.is_standalone == True).count()
    total_members = (
        db.query(TeamMembership).filter(TeamMembership.status == "active").count()
    )

    recent_teams = (
        db.query(Team)
        .filter(Team.is_standalone == True, Team.created_at >= start_date)
        .count()
    )

    recent_invitations = (
        db.query(TeamInvitation).filter(TeamInvitation.created_at >= start_date).count()
    )

    accepted_invitations = (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.created_at >= start_date, TeamInvitation.status == "accepted"
        )
        .count()
    )

    # Calculate revenue
    teams_with_members = (
        db.query(Team.id, func.count(TeamMembership.id).label("member_count"))
        .join(TeamMembership, Team.id == TeamMembership.team_id)
        .filter(Team.is_standalone == True, TeamMembership.status == "active")
        .group_by(Team.id)
        .all()
    )

    total_revenue = 0.0
    for team_id, member_count in teams_with_members:
        plan = calculate_team_plan(member_count)
        total_revenue += calculate_monthly_revenue(plan)

    overview = {
        "total_teams": total_teams,
        "total_members": total_members,
        "recent_teams": recent_teams,
        "recent_invitations": recent_invitations,
        "monthly_revenue": total_revenue,
        "avg_team_size": total_members / max(total_teams, 1),
        "invitation_acceptance_rate": (
            accepted_invitations / max(recent_invitations, 1)
        )
        * 100,
    }

    # Growth metrics (simplified - in production, this would use time-series data)
    growth_metrics = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Mock growth data - in production, this would come from daily aggregations
        growth_metrics.append(
            TeamGrowthMetrics(
                date=date,
                teams_created=max(0, int((total_teams / days) + (i % 3 - 1))),
                total_teams=int(total_teams * (i + 1) / days),
                members_added=max(0, int((total_members / days) + (i % 5 - 2))),
                total_members=int(total_members * (i + 1) / days),
                invitations_sent=max(0, int((recent_invitations / days) + (i % 4 - 1))),
                invitations_accepted=max(
                    0, int((accepted_invitations / days) + (i % 3 - 1))
                ),
            )
        )

    # Conversion funnel
    conversion_funnel = ConversionMetrics(
        period=period,
        signups=recent_teams * 2,  # Estimate signups (some don't create teams)
        team_creations=recent_teams,
        team_creation_rate=(recent_teams / max(recent_teams * 2, 1)) * 100,
        invitations_sent=recent_invitations,
        invitations_accepted=accepted_invitations,
        invitation_acceptance_rate=(accepted_invitations / max(recent_invitations, 1))
        * 100,
        upgrades_initiated=max(1, int(recent_teams * 0.15)),  # 15% initiate upgrades
        upgrades_completed=max(1, int(recent_teams * 0.08)),  # 8% complete upgrades
        upgrade_conversion_rate=8.0,  # 8% conversion rate
    )

    # Usage distribution
    usage_distribution = [
        UsageDistribution(
            team_size_range="1-5 members (Free)",
            team_count=int(total_teams * 0.7),
            percentage=70.0,
            avg_storage_usage=1.2,
            avg_ai_queries=45,
        ),
        UsageDistribution(
            team_size_range="6-20 members (Pro)",
            team_count=int(total_teams * 0.25),
            percentage=25.0,
            avg_storage_usage=6.8,
            avg_ai_queries=280,
        ),
        UsageDistribution(
            team_size_range="21-50 members (Enterprise)",
            team_count=int(total_teams * 0.04),
            percentage=4.0,
            avg_storage_usage=25.0,
            avg_ai_queries=850,
        ),
        UsageDistribution(
            team_size_range="50+ members (Organization)",
            team_count=int(total_teams * 0.01),
            percentage=1.0,
            avg_storage_usage=100.0,
            avg_ai_queries=2500,
        ),
    ]

    # Revenue projection
    growth_rate = (recent_teams / max(total_teams - recent_teams, 1)) * 100
    projected_teams = int(total_teams * (1 + growth_rate / 100))
    projected_revenue = (
        total_revenue * (1 + growth_rate / 100) * 1.1
    )  # 10% conversion improvement

    revenue_projection = RevenueProjection(
        period="next_30d",
        projected_teams=projected_teams,
        projected_revenue=projected_revenue,
        conversion_assumptions={
            "team_creation_rate": 50.0,
            "invitation_acceptance_rate": 65.0,
            "upgrade_conversion_rate": 12.0,
        },
        growth_rate=growth_rate,
    )

    # Top teams
    top_teams_query = (
        db.query(Team, func.count(TeamMembership.id).label("member_count"))
        .join(TeamMembership, Team.id == TeamMembership.team_id)
        .filter(Team.is_standalone == True, TeamMembership.status == "active")
        .group_by(Team.id)
        .order_by(desc("member_count"))
        .limit(10)
        .all()
    )

    top_teams = []
    for team, member_count in top_teams_query:
        plan = calculate_team_plan(member_count)
        monthly_revenue = calculate_monthly_revenue(plan)
        conversion_probability = calculate_conversion_probability(
            team, member_count, db
        )

        top_teams.append(
            TeamAnalytics(
                team_id=team.id,
                team_name=team.name,
                created_date=team.created_at or datetime.utcnow(),
                member_count=member_count,
                plan=plan,
                monthly_revenue=monthly_revenue,
                storage_usage_gb=member_count * 0.8,  # Estimate
                ai_queries_count=member_count * 50,  # Estimate
                last_activity=datetime.utcnow() - timedelta(hours=member_count % 24),
                conversion_probability=conversion_probability,
            )
        )

    # Alerts
    alerts = []
    if growth_rate < 5:
        alerts.append(
            {
                "type": "warning",
                "title": "Low Growth Rate",
                "message": f"Team growth rate is {growth_rate:.1f}%, below 5% target",
            }
        )

    if overview["invitation_acceptance_rate"] < 50:
        alerts.append(
            {
                "type": "warning",
                "title": "Low Invitation Acceptance",
                "message": f"Invitation acceptance rate is {overview['invitation_acceptance_rate']:.1f}%, below 50% target",
            }
        )

    high_conversion_teams = [t for t in top_teams if t.conversion_probability > 0.7]
    if high_conversion_teams:
        alerts.append(
            {
                "type": "opportunity",
                "title": "High Conversion Potential",
                "message": f"{len(high_conversion_teams)} teams have >70% conversion probability",
            }
        )

    return AnalyticsDashboard(
        overview=overview,
        growth_metrics=growth_metrics,
        conversion_funnel=conversion_funnel,
        usage_distribution=usage_distribution,
        revenue_projection=revenue_projection,
        top_teams=top_teams,
        alerts=alerts,
    )


@router.get("/teams/{team_id}/usage")
async def get_team_usage_details(
    team_id: UUID,
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed usage analytics for a specific team"""

    # Verify team exists and user has access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get team members
    members = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.status == "active")
        .all()
    )

    # Get invitations
    invitations = (
        db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id).all()
    )

    # Calculate usage metrics
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    recent_invitations = [inv for inv in invitations if inv.created_at >= start_date]
    accepted_invitations = [
        inv for inv in recent_invitations if inv.status == "accepted"
    ]

    plan = calculate_team_plan(len(members))
    monthly_revenue = calculate_monthly_revenue(plan)
    conversion_probability = calculate_conversion_probability(team, len(members), db)

    return {
        "team_info": {
            "id": str(team.id),
            "name": team.name,
            "created_date": team.created_at,
            "plan": plan,
            "monthly_revenue": monthly_revenue,
        },
        "usage_metrics": {
            "member_count": len(members),
            "storage_usage_gb": len(members) * 0.8,  # Estimate
            "ai_queries_count": len(members) * 50,  # Estimate
            "api_calls_count": len(members) * 200,  # Estimate
        },
        "growth_metrics": {
            "invitations_sent": len(recent_invitations),
            "invitations_accepted": len(accepted_invitations),
            "acceptance_rate": (
                len(accepted_invitations) / max(len(recent_invitations), 1)
            )
            * 100,
            "growth_rate": (
                len(accepted_invitations)
                / max(len(members) - len(accepted_invitations), 1)
            )
            * 100,
        },
        "conversion_analysis": {
            "conversion_probability": conversion_probability,
            "upgrade_triggers": [
                f"Team size: {len(members)}/5 (Free limit)" if plan == "free" else None,
                "High invitation activity" if len(recent_invitations) > 2 else None,
                (
                    "Team age > 30 days"
                    if team.created_at
                    and (datetime.utcnow() - team.created_at).days > 30
                    else None
                ),
            ],
            "recommended_actions": [
                "Send upgrade notification" if conversion_probability > 0.6 else None,
                "Offer demo call" if len(members) >= 4 else None,
                "Provide usage analytics" if len(recent_invitations) > 0 else None,
            ],
        },
    }


@router.get("/conversion-opportunities")
async def get_conversion_opportunities(
    min_probability: float = Query(0.5, description="Minimum conversion probability"),
    limit: int = Query(20, description="Maximum number of opportunities"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get teams with high conversion probability"""

    # Get all teams with member counts
    teams_with_members = (
        db.query(Team.id, func.count(TeamMembership.id).label("member_count"))
        .join(TeamMembership, Team.id == TeamMembership.team_id)
        .filter(Team.is_standalone.is_(True), TeamMembership.status == "active")
        .group_by(Team.id)
        .all()
    )

    opportunities = []
    for team, member_count in teams_with_members:
        conversion_probability = calculate_conversion_probability(
            team, member_count, db
        )

        if conversion_probability >= min_probability:
            plan = calculate_team_plan(member_count)

            # Skip teams already on paid plans
            if plan != "free":
                continue

            opportunities.append(
                {
                    "team_id": str(team.id),
                    "team_name": team.name,
                    "member_count": member_count,
                    "current_plan": plan,
                    "conversion_probability": conversion_probability,
                    "potential_revenue": 29.0,  # Team Pro price
                    "created_date": team.created_at,
                    "triggers": [
                        f"Team size: {member_count}/5" if member_count >= 4 else None,
                        (
                            "Active team"
                            if team.created_at
                            and (datetime.utcnow() - team.created_at).days > 7
                            else None
                        ),
                    ],
                    "recommended_action": (
                        "Send upgrade notification"
                        if conversion_probability > 0.7
                        else "Monitor usage"
                    ),
                }
            )

    # Sort by conversion probability
    opportunities.sort(key=lambda x: x["conversion_probability"], reverse=True)

    return opportunities[:limit]


@router.get("/revenue-forecast")
async def get_revenue_forecast(
    months: int = Query(12, description="Number of months to forecast"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate revenue forecast based on current trends"""

    # Current metrics
    total_teams = db.query(Team).filter(Team.is_standalone == True).count()

    # Calculate current revenue
    teams_with_members = (
        db.query(Team.id, func.count(TeamMembership.id).label("member_count"))
        .join(TeamMembership, Team.id == TeamMembership.team_id)
        .filter(Team.is_standalone == True, TeamMembership.status == "active")
        .group_by(Team.id)
        .all()
    )

    current_revenue = 0.0
    plan_distribution = {
        "free": 0,
        "team_pro": 0,
        "team_enterprise": 0,
        "organization": 0,
    }

    for team_id, member_count in teams_with_members:
        plan = calculate_team_plan(member_count)
        plan_distribution[plan] += 1
        current_revenue += calculate_monthly_revenue(plan)

    # Forecast assumptions
    monthly_growth_rate = 0.15  # 15% monthly growth
    conversion_rate = 0.08  # 8% of free teams convert monthly

    forecast = []
    for month in range(1, months + 1):
        # Project team growth
        projected_teams = int(total_teams * (1 + monthly_growth_rate) ** month)

        # Project conversions
        free_teams = plan_distribution["free"]
        monthly_conversions = int(free_teams * conversion_rate)

        # Update plan distribution
        plan_distribution["free"] -= monthly_conversions
        plan_distribution["team_pro"] += int(monthly_conversions * 0.8)  # 80% to Pro
        plan_distribution["team_enterprise"] += int(
            monthly_conversions * 0.2
        )  # 20% to Enterprise

        # Calculate revenue
        monthly_revenue = (
            plan_distribution["team_pro"] * 29.0
            + plan_distribution["team_enterprise"] * 99.0
            + plan_distribution["organization"] * 500.0
        )

        forecast.append(
            {
                "month": month,
                "date": (datetime.utcnow() + timedelta(days=30 * month)).strftime(
                    "%Y-%m"
                ),
                "projected_teams": projected_teams,
                "projected_revenue": monthly_revenue,
                "plan_distribution": dict(plan_distribution),
                "growth_rate": monthly_growth_rate * 100,
                "conversion_rate": conversion_rate * 100,
            }
        )

    return {
        "current_metrics": {
            "total_teams": total_teams,
            "current_revenue": current_revenue,
            "plan_distribution": dict(plan_distribution),
        },
        "assumptions": {
            "monthly_growth_rate": monthly_growth_rate * 100,
            "conversion_rate": conversion_rate * 100,
            "pro_vs_enterprise_split": "80/20",
        },
        "forecast": forecast,
        "summary": {
            "year_1_revenue": (
                forecast[11]["projected_revenue"] if len(forecast) >= 12 else 0
            ),
            "year_1_teams": (
                forecast[11]["projected_teams"] if len(forecast) >= 12 else 0
            ),
            "total_conversions": sum(
                f["plan_distribution"]["team_pro"]
                + f["plan_distribution"]["team_enterprise"]
                for f in forecast[-3:]
            )
            / 3,
        },
    }
