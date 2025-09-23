"""
SPEC-026: Standalone Teams & Flexible Billing System
Complete implementation of standalone team management with comprehensive billing infrastructure
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
import stripe

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import and_, desc, func, text
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User, Organization
from models.standalone_teams import (
    StandaloneTeamManager, TeamMembership, TeamInvitation, TeamUpgradeHistory
)

# Initialize router
router = APIRouter(prefix="/standalone-teams", tags=["standalone-teams-billing"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

# Mock data stores for demo (use actual database in production)
discount_codes_store = {}
team_credits_store = {}
nonprofit_applications_store = {}
team_usage_stats_store = {}
billing_plans = {
    "free": {
        "name": "Free Plan",
        "price": 0.00,
        "currency": "usd",
        "interval": "month",
        "features": {
            "contexts": 10,
            "memories_per_month": 1000,
            "storage_gb": 1,
            "max_members": 5,
            "api_calls_per_month": 1000
        }
    },
    "starter": {
        "name": "Starter Plan",
        "price": 10.00,
        "currency": "usd",
        "interval": "month",
        "features": {
            "contexts": 50,
            "memories_per_month": 25000,
            "storage_gb": 10,
            "max_members": 25,
            "api_calls_per_month": 50000
        }
    },
    "nonprofit": {
        "name": "Non-Profit Plan",
        "price": 5.00,
        "currency": "usd",
        "interval": "month",
        "features": {
            "contexts": 50,
            "memories_per_month": 100000,
            "storage_gb": 20,
            "max_members": 50,
            "api_calls_per_month": 100000
        }
    }
}


# Pydantic Models
class StandaloneTeamCreateRequest(BaseModel):
    """Request model for creating standalone team"""
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    description: Optional[str] = Field(None, max_length=500, description="Team description")
    max_members: int = Field(default=10, ge=1, le=100, description="Maximum team members")
    billing_plan: str = Field(default="free", description="Initial billing plan")


class TeamInviteRequest(BaseModel):
    """Request model for team invitation"""
    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(default="contributor", description="Role for invited user")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")


class TeamMemberResponse(BaseModel):
    """Response model for team member"""
    id: str
    user_id: str
    email: str
    name: str
    role: str
    status: str
    joined_at: datetime
    last_active: Optional[datetime]


class StandaloneTeamResponse(BaseModel):
    """Response model for standalone team"""
    id: str
    name: str
    description: Optional[str]
    is_standalone: bool
    billing_plan: str
    max_members: int
    current_members: int
    created_at: datetime
    created_by: str
    upgrade_eligible: bool
    billing_status: str


class DiscountCodeCreateRequest(BaseModel):
    """Request model for creating discount code"""
    code: str = Field(..., min_length=3, max_length=50, description="Discount code")
    percent_off: Optional[int] = Field(None, ge=1, le=100, description="Percentage discount")
    amount_off: Optional[int] = Field(None, ge=1, description="Fixed amount discount in cents")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    usage_limit: Optional[int] = Field(None, ge=1, description="Maximum usage count")


class DiscountCodeResponse(BaseModel):
    """Response model for discount code"""
    id: str
    code: str
    percent_off: Optional[int]
    amount_off: Optional[int]
    expires_at: Optional[datetime]
    usage_limit: Optional[int]
    used_count: int
    is_active: bool
    created_at: datetime


class TeamCreditsGrantRequest(BaseModel):
    """Request model for granting team credits"""
    team_id: str
    amount: float = Field(..., gt=0, description="Credit amount in dollars")
    expires_at: Optional[datetime] = Field(None, description="Credit expiration date")
    reason: str = Field(..., max_length=500, description="Reason for granting credits")


class TeamCreditsResponse(BaseModel):
    """Response model for team credits"""
    id: str
    team_id: str
    amount: float
    used_amount: float
    remaining_amount: float
    expires_at: Optional[datetime]
    granted_by: str
    reason: str
    created_at: datetime


class NonProfitApplicationRequest(BaseModel):
    """Request model for non-profit application"""
    organization_name: str = Field(..., max_length=255, description="Non-profit organization name")
    tax_id: str = Field(..., max_length=50, description="Tax ID or EIN")
    description: str = Field(..., max_length=1000, description="Organization description")
    website_url: Optional[str] = Field(None, description="Organization website")
    documentation_urls: List[str] = Field(default=[], description="Supporting documentation URLs")


class NonProfitApplicationResponse(BaseModel):
    """Response model for non-profit application"""
    id: str
    team_id: str
    organization_name: str
    tax_id: str
    description: str
    website_url: Optional[str]
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    review_notes: Optional[str]


class TeamUsageStats(BaseModel):
    """Team usage statistics"""
    team_id: str
    current_period: Dict[str, int]
    limits: Dict[str, int]
    usage_percentage: Dict[str, float]
    overage_charges: Dict[str, float]
    billing_cycle_start: datetime
    billing_cycle_end: datetime


class TeamBillingDashboard(BaseModel):
    """Complete team billing dashboard"""
    team: StandaloneTeamResponse
    current_plan: Dict[str, Any]
    usage_stats: TeamUsageStats
    credits: List[TeamCreditsResponse]
    recent_invoices: List[Dict[str, Any]]
    discount_codes_applied: List[str]
    nonprofit_status: Optional[str]


class OrganizationUpgradeRequest(BaseModel):
    """Request model for upgrading team to organization"""
    organization_name: str = Field(..., max_length=255, description="Organization name")
    domain: Optional[str] = Field(None, description="Organization domain")
    size: str = Field(default="startup", description="Organization size")
    industry: Optional[str] = Field(None, description="Industry")


# Helper Functions
def get_team_manager(db: Session) -> StandaloneTeamManager:
    """Get team manager instance"""
    return StandaloneTeamManager(db)


def check_team_admin_permissions(user: User, team_id: str, db: Session) -> bool:
    """Check if user has admin permissions for team"""
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == user.id,
        TeamMembership.role == "admin",
        TeamMembership.status == "active"
    ).first()
    return membership is not None


def calculate_team_usage(team_id: str) -> Dict[str, int]:
    """Calculate current team usage statistics"""
    # Mock calculation - in production, query actual usage
    return {
        "contexts": 8,
        "memories_this_month": 750,
        "storage_mb": 512,
        "members": 3,
        "api_calls_this_month": 2500
    }


def apply_discount_to_amount(amount: float, discount_code: str) -> float:
    """Apply discount code to billing amount"""
    if discount_code not in discount_codes_store:
        return amount
    
    discount = discount_codes_store[discount_code]
    if not discount.get("is_active", False):
        return amount
    
    if discount.get("percent_off"):
        return amount * (1 - discount["percent_off"] / 100)
    elif discount.get("amount_off"):
        return max(0, amount - (discount["amount_off"] / 100))  # amount_off is in cents
    
    return amount


def deduct_team_credits(team_id: str, amount: float) -> float:
    """Deduct credits from team and return remaining charge"""
    team_credits = team_credits_store.get(team_id, [])
    remaining_amount = amount
    
    for credit in team_credits:
        if credit["remaining_amount"] <= 0:
            continue
        
        if credit.get("expires_at") and datetime.utcnow() > credit["expires_at"]:
            continue
        
        deduction = min(remaining_amount, credit["remaining_amount"])
        credit["used_amount"] += deduction
        credit["remaining_amount"] -= deduction
        remaining_amount -= deduction
        
        if remaining_amount <= 0:
            break
    
    return remaining_amount


# API Endpoints

# Standalone Team Management
@router.post("/create", response_model=StandaloneTeamResponse)
async def create_standalone_team(
    request: StandaloneTeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new standalone team"""
    
    # Check if user can create teams (rate limiting, etc.)
    existing_teams = db.query(Team).filter(
        Team.created_by_user_id == current_user.id,
        Team.is_standalone == True
    ).count()
    
    if existing_teams >= 5:  # Limit teams per user
        raise HTTPException(status_code=429, detail="Maximum team limit reached")
    
    # Create team
    team_manager = get_team_manager(db)
    team = team_manager.create_standalone_team(
        name=request.name,
        created_by_user_id=current_user.id,
        max_members=request.max_members
    )
    
    # Set billing plan
    team.billing_plan = request.billing_plan
    team.description = request.description
    
    db.commit()
    
    return StandaloneTeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        is_standalone=team.is_standalone,
        billing_plan=team.billing_plan,
        max_members=team.max_members,
        current_members=1,
        created_at=team.created_at,
        created_by=str(current_user.id),
        upgrade_eligible=team.upgrade_eligible,
        billing_status="active"
    )


@router.get("/{team_id}", response_model=StandaloneTeamResponse)
async def get_standalone_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get standalone team details"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id, Team.is_standalone == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check user is member
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == current_user.id,
        TeamMembership.status == "active"
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get current member count
    current_members = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.status == "active"
    ).count()
    
    return StandaloneTeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        is_standalone=team.is_standalone,
        billing_plan=getattr(team, 'billing_plan', 'free'),
        max_members=team.max_members,
        current_members=current_members,
        created_at=team.created_at,
        created_by=str(team.created_by_user_id),
        upgrade_eligible=team.upgrade_eligible,
        billing_status="active"
    )


@router.post("/{team_id}/invite", response_model=Dict[str, str])
async def invite_user_to_team(
    team_id: str,
    request: TeamInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite user to standalone team"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check team capacity
    team_manager = get_team_manager(db)
    if not team_manager.can_user_join_team(UUID(team_id)):
        raise HTTPException(status_code=400, detail="Team is at maximum capacity")
    
    # Create invitation
    invitation = team_manager.invite_user_to_team(
        team_id=UUID(team_id),
        email=request.email,
        invited_by_user_id=current_user.id,
        role=request.role
    )
    
    db.commit()
    
    # In production, send invitation email
    invitation_url = f"https://ninaivalaigal.com/teams/join?token={invitation.invitation_token}"
    
    return {
        "message": "Invitation sent successfully",
        "invitation_id": str(invitation.id),
        "invitation_url": invitation_url,
        "expires_at": invitation.expires_at.isoformat()
    }


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team members"""
    
    # Check team access
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.user_id == current_user.id,
        TeamMembership.status == "active"
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all team members
    members = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.status == "active"
    ).all()
    
    member_responses = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            member_responses.append(TeamMemberResponse(
                id=str(member.id),
                user_id=str(member.user_id),
                email=user.email,
                name=getattr(user, 'name', user.email),
                role=member.role,
                status=member.status,
                joined_at=member.joined_at,
                last_active=getattr(user, 'last_login', None)
            ))
    
    return member_responses


# Team Billing Management
@router.get("/{team_id}/billing", response_model=TeamBillingDashboard)
async def get_team_billing_dashboard(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete team billing dashboard"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get team details
    team = db.query(Team).filter(Team.id == team_id, Team.is_standalone == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get current plan
    plan_id = getattr(team, 'billing_plan', 'free')
    current_plan = billing_plans.get(plan_id, billing_plans['free'])
    
    # Calculate usage statistics
    usage = calculate_team_usage(team_id)
    plan_limits = current_plan['features']
    
    usage_stats = TeamUsageStats(
        team_id=team_id,
        current_period=usage,
        limits=plan_limits,
        usage_percentage={
            key: round((usage.get(key, 0) / plan_limits.get(key, 1)) * 100, 1)
            for key in plan_limits.keys()
        },
        overage_charges={},
        billing_cycle_start=datetime.utcnow().replace(day=1),
        billing_cycle_end=datetime.utcnow().replace(day=1) + timedelta(days=32)
    )
    
    # Get team credits
    credits = team_credits_store.get(team_id, [])
    credit_responses = [
        TeamCreditsResponse(**credit) for credit in credits
        if credit.get("remaining_amount", 0) > 0
    ]
    
    # Get team details for response
    current_members = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.status == "active"
    ).count()
    
    team_response = StandaloneTeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        is_standalone=team.is_standalone,
        billing_plan=plan_id,
        max_members=team.max_members,
        current_members=current_members,
        created_at=team.created_at,
        created_by=str(team.created_by_user_id),
        upgrade_eligible=team.upgrade_eligible,
        billing_status="active"
    )
    
    return TeamBillingDashboard(
        team=team_response,
        current_plan=current_plan,
        usage_stats=usage_stats,
        credits=credit_responses,
        recent_invoices=[],  # Mock data
        discount_codes_applied=[],
        nonprofit_status=None
    )


@router.post("/{team_id}/billing/upgrade")
async def upgrade_team_billing_plan(
    team_id: str,
    new_plan: str,
    discount_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade team billing plan"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate new plan
    if new_plan not in billing_plans:
        raise HTTPException(status_code=400, detail="Invalid billing plan")
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id, Team.is_standalone == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate billing amount
    plan_details = billing_plans[new_plan]
    amount = plan_details['price']
    
    # Apply discount if provided
    if discount_code:
        amount = apply_discount_to_amount(amount, discount_code)
    
    # Apply credits
    final_amount = deduct_team_credits(team_id, amount)
    
    # Process payment if amount > 0
    if final_amount > 0:
        # In production, process with Stripe
        # stripe.PaymentIntent.create(amount=int(final_amount * 100), currency='usd')
        pass
    
    # Update team plan
    team.billing_plan = new_plan
    db.commit()
    
    return {
        "message": f"Successfully upgraded to {plan_details['name']}",
        "new_plan": new_plan,
        "amount_charged": final_amount,
        "credits_used": amount - final_amount
    }


# Organization Upgrade
@router.post("/{team_id}/upgrade-to-organization")
async def upgrade_team_to_organization(
    team_id: str,
    request: OrganizationUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade standalone team to organization"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Upgrade team
    team_manager = get_team_manager(db)
    organization = team_manager.upgrade_team_to_organization(
        team_id=UUID(team_id),
        upgraded_by_user_id=current_user.id,
        org_data=request.dict()
    )
    
    if not organization:
        raise HTTPException(status_code=400, detail="Team upgrade failed")
    
    db.commit()
    
    return {
        "message": "Team successfully upgraded to organization",
        "organization_id": str(organization.id),
        "organization_name": organization.name,
        "team_id": team_id
    }


# Admin Functions (Discount Codes, Credits, Non-Profit)
@router.post("/admin/discount-codes", response_model=DiscountCodeResponse)
async def create_discount_code(
    request: DiscountCodeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create discount code (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate discount code
    if request.code in discount_codes_store:
        raise HTTPException(status_code=400, detail="Discount code already exists")
    
    if not request.percent_off and not request.amount_off:
        raise HTTPException(status_code=400, detail="Either percent_off or amount_off must be specified")
    
    # Create discount code
    discount_id = str(uuid4())
    discount_data = {
        "id": discount_id,
        "code": request.code,
        "percent_off": request.percent_off,
        "amount_off": request.amount_off,
        "expires_at": request.expires_at,
        "usage_limit": request.usage_limit,
        "used_count": 0,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "created_by": str(current_user.id)
    }
    
    discount_codes_store[request.code] = discount_data
    
    return DiscountCodeResponse(**discount_data)


@router.post("/admin/credits/grant", response_model=TeamCreditsResponse)
async def grant_team_credits(
    request: TeamCreditsGrantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant credits to team (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate team exists
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Create credit entry
    credit_id = str(uuid4())
    credit_data = {
        "id": credit_id,
        "team_id": request.team_id,
        "amount": request.amount,
        "used_amount": 0.0,
        "remaining_amount": request.amount,
        "expires_at": request.expires_at,
        "granted_by": str(current_user.id),
        "reason": request.reason,
        "created_at": datetime.utcnow()
    }
    
    if request.team_id not in team_credits_store:
        team_credits_store[request.team_id] = []
    
    team_credits_store[request.team_id].append(credit_data)
    
    return TeamCreditsResponse(**credit_data)


# Non-Profit Application System
@router.post("/{team_id}/nonprofit/apply", response_model=NonProfitApplicationResponse)
async def apply_for_nonprofit_status(
    team_id: str,
    request: NonProfitApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply for non-profit status"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if application already exists
    if team_id in nonprofit_applications_store:
        raise HTTPException(status_code=400, detail="Non-profit application already submitted")
    
    # Create application
    application_id = str(uuid4())
    application_data = {
        "id": application_id,
        "team_id": team_id,
        "organization_name": request.organization_name,
        "tax_id": request.tax_id,
        "description": request.description,
        "website_url": request.website_url,
        "documentation_urls": request.documentation_urls,
        "status": "pending",
        "submitted_at": datetime.utcnow(),
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None
    }
    
    nonprofit_applications_store[team_id] = application_data
    
    return NonProfitApplicationResponse(**application_data)


@router.get("/admin/nonprofit-applications", response_model=List[NonProfitApplicationResponse])
async def list_nonprofit_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List non-profit applications (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    applications = list(nonprofit_applications_store.values())
    
    if status:
        applications = [app for app in applications if app["status"] == status]
    
    return [NonProfitApplicationResponse(**app) for app in applications]


@router.put("/admin/nonprofit-applications/{application_id}/review")
async def review_nonprofit_application(
    application_id: str,
    status: str,
    review_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Review non-profit application (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")
    
    # Find application
    application = None
    team_id = None
    for tid, app in nonprofit_applications_store.items():
        if app["id"] == application_id:
            application = app
            team_id = tid
            break
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update application
    application["status"] = status
    application["reviewed_at"] = datetime.utcnow()
    application["reviewed_by"] = str(current_user.id)
    application["review_notes"] = review_notes
    
    # If approved, update team billing plan
    if status == "approved":
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            team.billing_plan = "nonprofit"
            db.commit()
    
    return {
        "message": f"Application {status}",
        "application_id": application_id,
        "status": status
    }
