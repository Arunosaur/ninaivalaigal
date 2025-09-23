"""
SPEC-069: Partner Ecosystem & Referral Program
Third-party ecosystem with referral tracking, attribution, and revenue sharing
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User

# Initialize router
router = APIRouter(prefix="/partners", tags=["partner-ecosystem"])

# Mock data stores (use actual database in production)
partners_store = {}
referral_codes_store = {}
referral_tracking_store = {}
revenue_share_store = {}
partner_performance_store = {}


# Enums
class PartnerTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class ReferralStatus(str, Enum):
    PENDING = "pending"
    CONVERTED = "converted"
    PAID = "paid"
    EXPIRED = "expired"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"


# Pydantic Models
class PartnerRegistrationRequest(BaseModel):
    """Partner registration request"""
    company_name: str = Field(..., description="Company or organization name")
    contact_email: EmailStr = Field(..., description="Primary contact email")
    contact_name: str = Field(..., description="Primary contact person")
    website_url: Optional[str] = Field(None, description="Company website")
    description: str = Field(..., description="Description of services/expertise")
    target_market: str = Field(..., description="Target market or industry")
    expected_referrals_per_month: int = Field(..., description="Expected monthly referrals")
    integration_type: List[str] = Field(..., description="Types of integrations planned")


class Partner(BaseModel):
    """Partner information"""
    id: str
    company_name: str
    contact_email: str
    contact_name: str
    website_url: Optional[str]
    description: str
    tier: PartnerTier
    status: str  # active, pending, suspended
    created_at: datetime
    approved_at: Optional[datetime]
    total_referrals: int
    successful_conversions: int
    total_revenue_generated: float
    commission_rate: float
    integration_readiness_score: int


class ReferralCode(BaseModel):
    """Referral code information"""
    id: str
    code: str
    partner_id: str
    name: str
    description: Optional[str]
    commission_rate: float
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    current_uses: int
    is_active: bool
    created_at: datetime


class ReferralTracking(BaseModel):
    """Referral tracking entry"""
    id: str
    referral_code: str
    partner_id: str
    referred_user_email: str
    referred_team_id: Optional[str]
    status: ReferralStatus
    conversion_value: Optional[float]
    commission_amount: Optional[float]
    created_at: datetime
    converted_at: Optional[datetime]
    ip_address: str
    user_agent: str
    utm_source: Optional[str]
    utm_medium: Optional[str]
    utm_campaign: Optional[str]


class PartnerPerformanceDashboard(BaseModel):
    """Partner performance dashboard"""
    partner_id: str
    partner_name: str
    tier: PartnerTier
    performance_period: Dict[str, datetime]
    metrics: Dict[str, Any]
    referral_summary: Dict[str, int]
    revenue_summary: Dict[str, float]
    top_performing_codes: List[Dict[str, Any]]
    conversion_funnel: Dict[str, int]
    payout_summary: Dict[str, float]


class RevenueShareCalculation(BaseModel):
    """Revenue share calculation"""
    partner_id: str
    calculation_period: Dict[str, datetime]
    total_revenue_generated: float
    commission_rate: float
    gross_commission: float
    deductions: Dict[str, float]
    net_commission: float
    payout_status: PayoutStatus
    payout_date: Optional[datetime]


class PartnerPayoutRequest(BaseModel):
    """Partner payout request"""
    partner_id: str
    amount: float
    currency: str = "usd"
    payment_method: str  # stripe, paypal, bank_transfer
    payment_details: Dict[str, Any]


# Helper Functions
def generate_referral_code(partner_id: str, custom_suffix: Optional[str] = None) -> str:
    """Generate unique referral code"""
    partner_prefix = partner_id[:8].upper()
    if custom_suffix:
        return f"{partner_prefix}_{custom_suffix.upper()}"
    else:
        random_suffix = secrets.token_hex(4).upper()
        return f"{partner_prefix}_{random_suffix}"


def calculate_partner_tier(partner_id: str) -> PartnerTier:
    """Calculate partner tier based on performance"""
    partner = partners_store.get(partner_id)
    if not partner:
        return PartnerTier.BRONZE
    
    total_revenue = partner.get("total_revenue_generated", 0)
    successful_conversions = partner.get("successful_conversions", 0)
    
    if total_revenue >= 50000 and successful_conversions >= 100:
        return PartnerTier.PLATINUM
    elif total_revenue >= 20000 and successful_conversions >= 50:
        return PartnerTier.GOLD
    elif total_revenue >= 5000 and successful_conversions >= 20:
        return PartnerTier.SILVER
    else:
        return PartnerTier.BRONZE


def get_commission_rate_for_tier(tier: PartnerTier) -> float:
    """Get commission rate based on partner tier"""
    rates = {
        PartnerTier.BRONZE: 0.10,  # 10%
        PartnerTier.SILVER: 0.15,  # 15%
        PartnerTier.GOLD: 0.20,    # 20%
        PartnerTier.PLATINUM: 0.25  # 25%
    }
    return rates.get(tier, 0.10)


def calculate_integration_readiness_score(partner_id: str) -> int:
    """Calculate integration readiness score (0-100)"""
    # Mock calculation - in production, check actual integrations
    partner = partners_store.get(partner_id, {})
    
    score = 0
    
    # Website presence
    if partner.get("website_url"):
        score += 20
    
    # Documentation completeness
    score += 25  # Mock: assume good documentation
    
    # API health checks
    score += 20  # Mock: assume healthy API
    
    # Support responsiveness
    score += 15  # Mock: assume good support
    
    # Integration examples
    score += 20  # Mock: assume good examples
    
    return min(score, 100)


def track_referral_conversion(referral_id: str, team_id: str, conversion_value: float):
    """Track referral conversion and calculate commission"""
    if referral_id not in referral_tracking_store:
        return
    
    referral = referral_tracking_store[referral_id]
    partner_id = referral["partner_id"]
    
    # Update referral status
    referral["status"] = ReferralStatus.CONVERTED
    referral["converted_at"] = datetime.utcnow()
    referral["referred_team_id"] = team_id
    referral["conversion_value"] = conversion_value
    
    # Calculate commission
    partner = partners_store.get(partner_id, {})
    commission_rate = partner.get("commission_rate", 0.10)
    commission_amount = conversion_value * commission_rate
    
    referral["commission_amount"] = commission_amount
    
    # Update partner stats
    partner["successful_conversions"] = partner.get("successful_conversions", 0) + 1
    partner["total_revenue_generated"] = partner.get("total_revenue_generated", 0) + conversion_value
    
    # Update tier if needed
    new_tier = calculate_partner_tier(partner_id)
    if new_tier != partner.get("tier"):
        partner["tier"] = new_tier
        partner["commission_rate"] = get_commission_rate_for_tier(new_tier)


# API Endpoints
@router.post("/register", response_model=Dict[str, Any])
async def register_partner(
    request: PartnerRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register new partner"""
    
    partner_id = str(uuid4())
    
    # Create partner record
    partner_data = {
        "id": partner_id,
        "company_name": request.company_name,
        "contact_email": request.contact_email,
        "contact_name": request.contact_name,
        "website_url": request.website_url,
        "description": request.description,
        "target_market": request.target_market,
        "expected_referrals_per_month": request.expected_referrals_per_month,
        "integration_type": request.integration_type,
        "tier": PartnerTier.BRONZE,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "approved_at": None,
        "total_referrals": 0,
        "successful_conversions": 0,
        "total_revenue_generated": 0.0,
        "commission_rate": get_commission_rate_for_tier(PartnerTier.BRONZE),
        "integration_readiness_score": 0,
        "registered_by_user_id": current_user.id
    }
    
    partners_store[partner_id] = partner_data
    
    return {
        "message": "Partner registration submitted successfully",
        "partner_id": partner_id,
        "status": "pending_approval",
        "next_steps": [
            "Wait for admin approval",
            "Complete integration documentation",
            "Set up referral tracking"
        ]
    }


@router.get("/dashboard", response_model=PartnerPerformanceDashboard)
async def get_partner_dashboard(
    partner_id: Optional[str] = Query(None, description="Partner ID (admin only)"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get partner performance dashboard"""
    
    # Determine which partner to show
    if partner_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required to view other partners")
    
    if not partner_id:
        # Find partner by user (assuming user is associated with partner)
        user_partners = [p for p in partners_store.values() if p.get("registered_by_user_id") == current_user.id]
        if not user_partners:
            raise HTTPException(status_code=404, detail="No partner account found")
        partner_data = user_partners[0]
        partner_id = partner_data["id"]
    else:
        partner_data = partners_store.get(partner_id)
        if not partner_data:
            raise HTTPException(status_code=404, detail="Partner not found")
    
    # Calculate performance metrics
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get referrals in period
    period_referrals = [
        r for r in referral_tracking_store.values()
        if r["partner_id"] == partner_id and start_date <= datetime.fromisoformat(r["created_at"]) <= end_date
    ]
    
    # Calculate metrics
    total_referrals = len(period_referrals)
    conversions = len([r for r in period_referrals if r["status"] == ReferralStatus.CONVERTED])
    pending_referrals = len([r for r in period_referrals if r["status"] == ReferralStatus.PENDING])
    
    total_revenue = sum(r.get("conversion_value", 0) for r in period_referrals if r["status"] == ReferralStatus.CONVERTED)
    total_commission = sum(r.get("commission_amount", 0) for r in period_referrals if r["status"] == ReferralStatus.CONVERTED)
    
    # Top performing codes
    code_performance = {}
    for referral in period_referrals:
        code = referral["referral_code"]
        if code not in code_performance:
            code_performance[code] = {"uses": 0, "conversions": 0, "revenue": 0}
        
        code_performance[code]["uses"] += 1
        if referral["status"] == ReferralStatus.CONVERTED:
            code_performance[code]["conversions"] += 1
            code_performance[code]["revenue"] += referral.get("conversion_value", 0)
    
    top_codes = sorted(
        [{"code": code, **stats} for code, stats in code_performance.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:5]
    
    return PartnerPerformanceDashboard(
        partner_id=partner_id,
        partner_name=partner_data["company_name"],
        tier=PartnerTier(partner_data["tier"]),
        performance_period={
            "start_date": start_date,
            "end_date": end_date
        },
        metrics={
            "total_referrals": total_referrals,
            "conversion_rate": round((conversions / total_referrals) * 100, 2) if total_referrals > 0 else 0,
            "average_conversion_value": round(total_revenue / conversions, 2) if conversions > 0 else 0,
            "integration_readiness_score": calculate_integration_readiness_score(partner_id)
        },
        referral_summary={
            "total": total_referrals,
            "converted": conversions,
            "pending": pending_referrals,
            "expired": total_referrals - conversions - pending_referrals
        },
        revenue_summary={
            "total_generated": total_revenue,
            "commission_earned": total_commission,
            "commission_rate": partner_data["commission_rate"]
        },
        top_performing_codes=top_codes,
        conversion_funnel={
            "referrals": total_referrals,
            "signups": conversions,  # Simplified funnel
            "activations": conversions,
            "conversions": conversions
        },
        payout_summary={
            "pending_payout": total_commission,
            "paid_this_month": 0,  # Mock data
            "total_lifetime_payouts": 0  # Mock data
        }
    )


@router.post("/{partner_id}/referral-codes", response_model=ReferralCode)
async def create_referral_code(
    partner_id: str,
    name: str,
    description: Optional[str] = None,
    custom_suffix: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    max_uses: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Create new referral code for partner"""
    
    # Check partner exists and user has access
    partner = partners_store.get(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    if current_user.role != "admin" and partner.get("registered_by_user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate referral code
    code = generate_referral_code(partner_id, custom_suffix)
    code_id = str(uuid4())
    
    # Check if code already exists
    existing_codes = [c for c in referral_codes_store.values() if c["code"] == code]
    if existing_codes:
        raise HTTPException(status_code=400, detail="Referral code already exists")
    
    # Create referral code
    referral_code_data = {
        "id": code_id,
        "code": code,
        "partner_id": partner_id,
        "name": name,
        "description": description,
        "commission_rate": partner["commission_rate"],
        "expires_at": expires_at,
        "max_uses": max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "created_by": current_user.id
    }
    
    referral_codes_store[code_id] = referral_code_data
    
    return ReferralCode(**referral_code_data)


@router.get("/{partner_id}/referral-codes", response_model=List[ReferralCode])
async def list_partner_referral_codes(
    partner_id: str,
    include_inactive: bool = Query(False, description="Include inactive codes"),
    current_user: User = Depends(get_current_user)
):
    """List referral codes for partner"""
    
    # Check partner access
    partner = partners_store.get(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    if current_user.role != "admin" and partner.get("registered_by_user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get partner's referral codes
    partner_codes = []
    for code_data in referral_codes_store.values():
        if code_data["partner_id"] != partner_id:
            continue
            
        if not include_inactive and not code_data["is_active"]:
            continue
            
        # Check if expired
        if code_data.get("expires_at") and datetime.utcnow() > code_data["expires_at"]:
            code_data["is_active"] = False
            
        partner_codes.append(ReferralCode(**code_data))
    
    return sorted(partner_codes, key=lambda x: x.created_at, reverse=True)


@router.post("/track-referral")
async def track_referral_signup(
    referral_code: str,
    user_email: str,
    request: Request,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None
):
    """Track referral signup (called during user registration)"""
    
    # Find referral code
    code_data = None
    for code in referral_codes_store.values():
        if code["code"] == referral_code and code["is_active"]:
            code_data = code
            break
    
    if not code_data:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Check if code is expired or at max uses
    if code_data.get("expires_at") and datetime.utcnow() > code_data["expires_at"]:
        raise HTTPException(status_code=400, detail="Referral code has expired")
    
    if code_data.get("max_uses") and code_data["current_uses"] >= code_data["max_uses"]:
        raise HTTPException(status_code=400, detail="Referral code usage limit reached")
    
    # Create referral tracking entry
    tracking_id = str(uuid4())
    tracking_data = {
        "id": tracking_id,
        "referral_code": referral_code,
        "partner_id": code_data["partner_id"],
        "referred_user_email": user_email,
        "referred_team_id": None,  # Will be set when team is created
        "status": ReferralStatus.PENDING,
        "conversion_value": None,
        "commission_amount": None,
        "created_at": datetime.utcnow().isoformat(),
        "converted_at": None,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign
    }
    
    referral_tracking_store[tracking_id] = tracking_data
    
    # Update code usage
    code_data["current_uses"] += 1
    
    # Update partner stats
    partner = partners_store[code_data["partner_id"]]
    partner["total_referrals"] = partner.get("total_referrals", 0) + 1
    
    return {
        "message": "Referral tracked successfully",
        "tracking_id": tracking_id,
        "partner_id": code_data["partner_id"],
        "referral_code": referral_code
    }


@router.post("/admin/approve-partner/{partner_id}")
async def approve_partner(
    partner_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve partner registration (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    partner = partners_store.get(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    if partner["status"] != "pending":
        raise HTTPException(status_code=400, detail="Partner is not pending approval")
    
    # Approve partner
    partner["status"] = "active"
    partner["approved_at"] = datetime.utcnow()
    partner["integration_readiness_score"] = calculate_integration_readiness_score(partner_id)
    
    return {
        "message": "Partner approved successfully",
        "partner_id": partner_id,
        "status": "active"
    }


@router.get("/admin/revenue-share/{partner_id}", response_model=RevenueShareCalculation)
async def calculate_partner_revenue_share(
    partner_id: str,
    start_date: datetime = Query(..., description="Start date for calculation"),
    end_date: datetime = Query(..., description="End date for calculation"),
    current_user: User = Depends(get_current_user)
):
    """Calculate revenue share for partner (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    partner = partners_store.get(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # Get conversions in period
    period_conversions = [
        r for r in referral_tracking_store.values()
        if (r["partner_id"] == partner_id and 
            r["status"] == ReferralStatus.CONVERTED and
            r.get("converted_at") and
            start_date <= datetime.fromisoformat(r["converted_at"]) <= end_date)
    ]
    
    # Calculate revenue share
    total_revenue = sum(r.get("conversion_value", 0) for r in period_conversions)
    commission_rate = partner["commission_rate"]
    gross_commission = total_revenue * commission_rate
    
    # Calculate deductions (fees, taxes, etc.)
    deductions = {
        "platform_fee": gross_commission * 0.03,  # 3% platform fee
        "processing_fee": gross_commission * 0.029,  # 2.9% processing fee
        "tax_withholding": 0  # Depends on jurisdiction
    }
    
    total_deductions = sum(deductions.values())
    net_commission = gross_commission - total_deductions
    
    return RevenueShareCalculation(
        partner_id=partner_id,
        calculation_period={
            "start_date": start_date,
            "end_date": end_date
        },
        total_revenue_generated=total_revenue,
        commission_rate=commission_rate,
        gross_commission=gross_commission,
        deductions=deductions,
        net_commission=net_commission,
        payout_status=PayoutStatus.PENDING,
        payout_date=None
    )
