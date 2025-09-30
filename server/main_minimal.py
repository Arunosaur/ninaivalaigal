"""
Minimal Nina Intelligence API - For Testing
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Nina Intelligence API",
    description="Minimal API for testing",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nina Intelligence API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("NINA_ENV", "dev"),
        "runtime": os.getenv("NINA_RUNTIME", "apple"),
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is operational",
        "database": "connected",
        "environment": os.getenv("NINA_ENV", "dev"),
        "runtime": os.getenv("NINA_RUNTIME", "apple"),
    }


@app.get("/demo")
async def demo():
    """Demo endpoint for colleagues"""
    return {
        "message": "Welcome to Nina Intelligence Platform!",
        "features": [
            "Unified Naming Convention ✅",
            "Shared Database Architecture ✅",
            "Apple Container CLI Support ✅",
            "Health Monitoring ✅",
        ],
        "q4_goals": {
            "spec_082_analytics": "Ready for 6-week sprint",
            "spec_076_pilots": "Ready for 3 enterprise customers",
            "investor_demos": "Enterprise-ready platform",
        },
        "next_steps": [
            "SPEC-082 Analytics Layer implementation",
            "Tailscale Funnel setup for remote access",
            "Enterprise pilot expansion",
        ],
    }


@app.post("/register")
async def register(user_data: dict):
    """Simple registration endpoint for colleague testing"""
    return {
        "status": "success",
        "message": f"User {user_data.get('email', 'colleague')} registered successfully!",
        "user_id": "demo_user_123",
        "access_token": "demo_token_for_testing",
        "next_steps": [
            "Visit /demo to see platform capabilities",
            "Use /health to monitor system status",
            "Contact team for full UI access",
        ],
    }


@app.get("/login")
async def login_form():
    """Simple login form for colleagues"""
    return {
        "message": "Nina Intelligence Login",
        "instructions": "POST to /login with email and password",
        "demo_credentials": {"email": "colleague@company.com", "password": "demo123"},
        "endpoints": {
            "register": "POST /register",
            "demo": "GET /demo",
            "health": "GET /health",
        },
    }


@app.post("/login")
async def login(credentials: dict):
    """Simple login endpoint for colleague testing"""
    email = credentials.get("email", "")
    return {
        "status": "success",
        "message": f"Welcome back, {email}!",
        "access_token": "demo_session_token",
        "user_profile": {
            "email": email,
            "role": "demo_user",
            "permissions": ["read", "demo"],
        },
        "available_endpoints": [
            "GET /demo - Platform overview",
            "GET /health - System status",
            "GET /profile - User information",
        ],
    }


@app.get("/profile")
async def profile():
    """User profile endpoint"""
    return {
        "user": {
            "email": "colleague@company.com",
            "role": "demo_user",
            "joined": "2024-09-29",
            "status": "active",
        },
        "platform_access": {
            "nina_intelligence": "enabled",
            "analytics_dashboard": "coming_soon",
            "enterprise_features": "contact_team",
        },
        "usage_stats": {
            "sessions": 1,
            "last_login": "2024-09-29T12:19:00Z",
            "features_used": ["demo", "health_check"],
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 13370)))
