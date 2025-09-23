"""
Early Adopter Program API
Manages beta user onboarding, feedback collection, and program analytics
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from auth import get_current_user, get_db
from database import Team, User
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from models.standalone_teams import StandaloneTeamManager, TeamMembership
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

# Initialize router
router = APIRouter(prefix="/early-adopter", tags=["early-adopter-program"])


# Pydantic Models
class EarlyAdopterApplication(BaseModel):
    """Early adopter application form"""

    email: EmailStr
    name: str
    company: Optional[str] = None
    role: str
    team_size: int
    use_case: str
    current_tools: List[str]
    pain_points: str
    expected_value: str
    timeline: str  # "immediate", "1-2_weeks", "1-2_months"
    referral_source: Optional[str] = None
    additional_notes: Optional[str] = None


class EarlyAdopterProfile(BaseModel):
    """Early adopter profile"""

    id: UUID
    email: str
    name: str
    company: Optional[str]
    role: str
    team_size: int
    status: str  # "applied", "approved", "onboarded", "active", "churned"
    application_date: datetime
    approval_date: Optional[datetime]
    onboarding_date: Optional[datetime]
    last_activity: Optional[datetime]
    feedback_score: Optional[float]
    usage_metrics: Dict[str, Any]


class FeedbackSubmission(BaseModel):
    """Feedback submission from early adopter"""

    category: str  # "feature_request", "bug_report", "general_feedback", "improvement"
    title: str
    description: str
    priority: str  # "low", "medium", "high", "critical"
    satisfaction_score: Optional[int] = None  # 1-10 scale
    would_recommend: Optional[bool] = None
    additional_context: Optional[str] = None


class ProgramMetrics(BaseModel):
    """Early adopter program metrics"""

    total_applications: int
    approved_adopters: int
    active_adopters: int
    avg_satisfaction_score: float
    retention_rate: float
    feature_requests: int
    bug_reports: int
    success_stories: int


class OnboardingStep(BaseModel):
    """Onboarding step definition"""

    step_id: str
    title: str
    description: str
    estimated_time: str
    is_completed: bool
    completion_date: Optional[datetime]
    resources: List[Dict[str, str]]


# Mock database for early adopter data (in production, use proper database)
early_adopters_db = {}
feedback_db = {}
onboarding_progress_db = {}


def get_team_manager() -> StandaloneTeamManager:
    """Dependency to get team manager"""
    return StandaloneTeamManager()


def send_early_adopter_email(email: str, template: str, context: Dict[str, Any]):
    """Send email to early adopter (mock implementation)"""
    # In production, integrate with email service (SendGrid, Mailgun, etc.)
    print(f"Sending {template} email to {email} with context: {context}")


def calculate_usage_metrics(user_id: UUID, db: Session) -> Dict[str, Any]:
    """Calculate usage metrics for early adopter"""
    # Mock metrics - in production, gather from actual usage data
    return {
        "memories_created": 25,
        "ai_queries": 150,
        "team_invitations": 3,
        "login_frequency": "daily",
        "feature_adoption": ["memory_browser", "team_dashboard", "ai_suggestions"],
        "session_duration_avg": "15_minutes",
        "last_login": datetime.utcnow() - timedelta(hours=2),
    }


@router.post("/apply")
async def submit_early_adopter_application(
    application: EarlyAdopterApplication,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Submit application for early adopter program
    """
    # Check if user already applied
    existing_user = db.query(User).filter(User.email == application.email).first()
    if existing_user and str(existing_user.id) in early_adopters_db:
        raise HTTPException(
            status_code=400,
            detail="You have already applied to the early adopter program",
        )

    # Create early adopter profile
    adopter_id = uuid4()
    profile = EarlyAdopterProfile(
        id=adopter_id,
        email=application.email,
        name=application.name,
        company=application.company,
        role=application.role,
        team_size=application.team_size,
        status="applied",
        application_date=datetime.utcnow(),
        approval_date=None,
        onboarding_date=None,
        last_activity=datetime.utcnow(),
        feedback_score=None,
        usage_metrics={},
    )

    # Store in mock database
    early_adopters_db[str(adopter_id)] = {
        "profile": profile.dict(),
        "application": application.dict(),
    }

    # Send confirmation email
    background_tasks.add_task(
        send_early_adopter_email,
        application.email,
        "application_received",
        {
            "name": application.name,
            "application_id": str(adopter_id),
            "review_timeline": "2-3 business days",
        },
    )

    # Auto-approve based on criteria (in production, manual review process)
    auto_approve = (
        application.team_size >= 3
        and application.timeline in ["immediate", "1-2_weeks"]
        and len(application.use_case) > 50
    )

    if auto_approve:
        background_tasks.add_task(approve_early_adopter, str(adopter_id))

    return {
        "success": True,
        "application_id": str(adopter_id),
        "status": "approved" if auto_approve else "under_review",
        "message": "Application submitted successfully",
        "next_steps": "You will receive an email with next steps within 2-3 business days",
    }


async def approve_early_adopter(adopter_id: str):
    """Approve early adopter and start onboarding process"""
    if adopter_id not in early_adopters_db:
        return

    # Update status
    early_adopters_db[adopter_id]["profile"]["status"] = "approved"
    early_adopters_db[adopter_id]["profile"][
        "approval_date"
    ] = datetime.utcnow().isoformat()

    # Create onboarding checklist
    onboarding_steps = [
        OnboardingStep(
            step_id="welcome_call",
            title="Welcome Call",
            description="30-minute onboarding call with our team",
            estimated_time="30 minutes",
            is_completed=False,
            completion_date=None,
            resources=[
                {
                    "type": "calendar_link",
                    "url": "https://calendly.com/ninaivalaigal/onboarding",
                },
                {"type": "preparation_guide", "url": "/docs/onboarding-prep"},
            ],
        ),
        OnboardingStep(
            step_id="account_setup",
            title="Account Setup",
            description="Create your team account and invite initial members",
            estimated_time="15 minutes",
            is_completed=False,
            completion_date=None,
            resources=[
                {"type": "setup_guide", "url": "/docs/team-setup"},
                {"type": "video_tutorial", "url": "/videos/account-setup"},
            ],
        ),
        OnboardingStep(
            step_id="first_memories",
            title="Create First Memories",
            description="Add your first 10 memories to the system",
            estimated_time="20 minutes",
            is_completed=False,
            completion_date=None,
            resources=[
                {"type": "quick_start", "url": "/docs/quick-start"},
                {"type": "best_practices", "url": "/docs/memory-best-practices"},
            ],
        ),
        OnboardingStep(
            step_id="team_collaboration",
            title="Team Collaboration",
            description="Invite team members and set up collaboration workflows",
            estimated_time="25 minutes",
            is_completed=False,
            completion_date=None,
            resources=[
                {"type": "collaboration_guide", "url": "/docs/team-collaboration"},
                {"type": "permission_setup", "url": "/docs/permissions"},
            ],
        ),
        OnboardingStep(
            step_id="feedback_session",
            title="Feedback Session",
            description="Share your initial experience and suggestions",
            estimated_time="20 minutes",
            is_completed=False,
            completion_date=None,
            resources=[
                {"type": "feedback_form", "url": "/early-adopter/feedback"},
                {"type": "feature_roadmap", "url": "/roadmap"},
            ],
        ),
    ]

    onboarding_progress_db[adopter_id] = {
        "steps": [step.dict() for step in onboarding_steps],
        "started_date": datetime.utcnow().isoformat(),
        "completion_percentage": 0,
    }

    # Send approval email
    profile = early_adopters_db[adopter_id]["profile"]
    send_early_adopter_email(
        profile["email"],
        "application_approved",
        {
            "name": profile["name"],
            "onboarding_link": f"/early-adopter/onboarding/{adopter_id}",
            "calendar_link": "https://calendly.com/ninaivalaigal/onboarding",
        },
    )


@router.get("/status/{adopter_id}")
async def get_adopter_status(
    adopter_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get early adopter status and progress"""

    if adopter_id not in early_adopters_db:
        raise HTTPException(status_code=404, detail="Early adopter not found")

    adopter_data = early_adopters_db[adopter_id]
    profile = adopter_data["profile"]

    # Check if current user has access (either the adopter or admin)
    if current_user.email != profile["email"]:
        # In production, check for admin permissions
        pass

    # Get onboarding progress
    onboarding_progress = onboarding_progress_db.get(adopter_id, {})

    return {
        "profile": profile,
        "onboarding_progress": onboarding_progress,
        "program_benefits": [
            "Priority support and direct access to our team",
            "Early access to new features and beta releases",
            "Influence on product roadmap and feature prioritization",
            "Special pricing and extended trial periods",
            "Exclusive early adopter community access",
        ],
    }


@router.get("/onboarding/{adopter_id}")
async def get_onboarding_checklist(
    adopter_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get onboarding checklist for early adopter"""

    if adopter_id not in early_adopters_db:
        raise HTTPException(status_code=404, detail="Early adopter not found")

    if adopter_id not in onboarding_progress_db:
        raise HTTPException(status_code=404, detail="Onboarding not started")

    progress = onboarding_progress_db[adopter_id]
    completed_steps = sum(1 for step in progress["steps"] if step["is_completed"])
    total_steps = len(progress["steps"])
    completion_percentage = (completed_steps / total_steps) * 100

    return {
        "adopter_id": adopter_id,
        "steps": progress["steps"],
        "completion_percentage": completion_percentage,
        "started_date": progress["started_date"],
        "estimated_completion": "3-5 business days",
        "support_contact": "early-adopters@ninaivalaigal.com",
    }


@router.post("/onboarding/{adopter_id}/complete-step")
async def complete_onboarding_step(
    adopter_id: str, step_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark onboarding step as completed"""

    if adopter_id not in onboarding_progress_db:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    progress = onboarding_progress_db[adopter_id]

    # Find and update step
    step_found = False
    for step in progress["steps"]:
        if step["step_id"] == step_id:
            step["is_completed"] = True
            step["completion_date"] = datetime.utcnow().isoformat()
            step_found = True
            break

    if not step_found:
        raise HTTPException(status_code=404, detail="Onboarding step not found")

    # Update completion percentage
    completed_steps = sum(1 for step in progress["steps"] if step["is_completed"])
    total_steps = len(progress["steps"])
    completion_percentage = (completed_steps / total_steps) * 100

    # Check if onboarding is complete
    if completion_percentage == 100:
        # Update adopter status to onboarded
        early_adopters_db[adopter_id]["profile"]["status"] = "onboarded"
        early_adopters_db[adopter_id]["profile"][
            "onboarding_date"
        ] = datetime.utcnow().isoformat()

        # Send completion email
        profile = early_adopters_db[adopter_id]["profile"]
        send_early_adopter_email(
            profile["email"],
            "onboarding_complete",
            {
                "name": profile["name"],
                "dashboard_link": "/team-dashboard",
                "community_link": "/early-adopter/community",
            },
        )

    return {
        "success": True,
        "step_completed": step_id,
        "completion_percentage": completion_percentage,
        "is_onboarding_complete": completion_percentage == 100,
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackSubmission,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Submit feedback from early adopter"""

    feedback_id = str(uuid4())
    feedback_entry = {
        "id": feedback_id,
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "submission_date": datetime.utcnow().isoformat(),
        "status": "new",
        **feedback.dict(),
    }

    feedback_db[feedback_id] = feedback_entry

    # Send notification to team
    background_tasks.add_task(
        send_early_adopter_email,
        "team@ninaivalaigal.com",
        "new_feedback",
        {
            "feedback_id": feedback_id,
            "category": feedback.category,
            "title": feedback.title,
            "user_email": current_user.email,
            "priority": feedback.priority,
        },
    )

    return {
        "success": True,
        "feedback_id": feedback_id,
        "message": "Thank you for your feedback! Our team will review it shortly.",
        "response_timeline": "2-3 business days for high priority items",
    }


@router.get("/metrics")
async def get_program_metrics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProgramMetrics:
    """Get early adopter program metrics (admin only)"""

    # In production, check admin permissions

    total_applications = len(early_adopters_db)
    approved_adopters = sum(
        1
        for data in early_adopters_db.values()
        if data["profile"]["status"] in ["approved", "onboarded", "active"]
    )
    active_adopters = sum(
        1
        for data in early_adopters_db.values()
        if data["profile"]["status"] == "active"
    )

    # Calculate satisfaction score
    feedback_scores = [
        entry["satisfaction_score"]
        for entry in feedback_db.values()
        if entry.get("satisfaction_score")
    ]
    avg_satisfaction_score = (
        sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0
    )

    # Calculate retention rate (simplified)
    retention_rate = (active_adopters / max(approved_adopters, 1)) * 100

    # Count feedback categories
    feature_requests = sum(
        1 for entry in feedback_db.values() if entry["category"] == "feature_request"
    )
    bug_reports = sum(
        1 for entry in feedback_db.values() if entry["category"] == "bug_report"
    )

    return ProgramMetrics(
        total_applications=total_applications,
        approved_adopters=approved_adopters,
        active_adopters=active_adopters,
        avg_satisfaction_score=avg_satisfaction_score,
        retention_rate=retention_rate,
        feature_requests=feature_requests,
        bug_reports=bug_reports,
        success_stories=3,  # Mock data
    )


@router.get("/community")
async def get_community_info(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get early adopter community information"""

    return {
        "community_stats": {
            "total_members": len(
                [
                    data
                    for data in early_adopters_db.values()
                    if data["profile"]["status"] in ["onboarded", "active"]
                ]
            ),
            "active_this_week": 15,
            "feature_requests_submitted": len(
                [
                    entry
                    for entry in feedback_db.values()
                    if entry["category"] == "feature_request"
                ]
            ),
            "features_shipped": 8,
        },
        "recent_updates": [
            {
                "date": "2024-09-20",
                "title": "New Team Dashboard Released",
                "description": "Based on your feedback, we've launched an improved team dashboard with real-time analytics.",
                "requested_by": "early_adopter_community",
            },
            {
                "date": "2024-09-18",
                "title": "Enhanced Memory Search",
                "description": "Advanced search capabilities now available with filtering and highlighting.",
                "requested_by": "sarah@techstartup.com",
            },
        ],
        "upcoming_features": [
            {
                "title": "AI-Powered Memory Suggestions",
                "description": "Intelligent memory recommendations based on your usage patterns",
                "eta": "October 2024",
                "votes": 12,
            },
            {
                "title": "Advanced Team Analytics",
                "description": "Comprehensive usage analytics and team performance insights",
                "eta": "November 2024",
                "votes": 8,
            },
        ],
        "resources": [
            {
                "title": "Early Adopter Slack Channel",
                "url": "https://ninaivalaigal.slack.com/channels/early-adopters",
            },
            {
                "title": "Monthly Feedback Sessions",
                "url": "/calendar/feedback-sessions",
            },
            {"title": "Product Roadmap", "url": "/roadmap"},
            {"title": "Feature Request Portal", "url": "/early-adopter/feedback"},
        ],
    }


@router.get("/success-stories")
async def get_success_stories() -> List[Dict[str, Any]]:
    """Get early adopter success stories"""

    return [
        {
            "company": "TechStartup Inc",
            "user": "Sarah Chen",
            "role": "Engineering Manager",
            "team_size": 12,
            "use_case": "Engineering knowledge management",
            "results": {
                "time_saved": "8 hours per week",
                "knowledge_retention": "85% improvement",
                "onboarding_speed": "50% faster",
            },
            "quote": "Ninaivalaigal transformed how our engineering team shares and retains knowledge. New team members are productive 50% faster.",
            "metrics": {
                "memories_created": 450,
                "team_adoption": "100%",
                "satisfaction_score": 9.2,
            },
        },
        {
            "company": "Design Agency Pro",
            "user": "Mike Rodriguez",
            "role": "Creative Director",
            "team_size": 8,
            "use_case": "Creative project management",
            "results": {
                "project_efficiency": "30% improvement",
                "client_satisfaction": "95% rating",
                "idea_retention": "90% better",
            },
            "quote": "We never lose great ideas anymore. Every brainstorm session and client feedback is captured and easily accessible.",
            "metrics": {
                "memories_created": 320,
                "team_adoption": "87%",
                "satisfaction_score": 8.8,
            },
        },
    ]
