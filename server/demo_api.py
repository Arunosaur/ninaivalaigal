#!/usr/bin/env python3
"""
Nina Intelligence Platform - Demo API
Minimal working API for Q4 colleague testing via Tailscale funnel
"""

import os
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nina Intelligence Platform",
    description="Enterprise AI Memory Management with Narrative Intelligence",
    version="Q4 2024 Demo",
)

# Enable CORS for colleague testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Platform overview"""
    return {
        "platform": "Nina Intelligence",
        "version": "Q4 2024 Demo",
        "status": "Enterprise Ready",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "SPEC-076: Visual Narrative Layer (Pilot Integration)",
            "SPEC-082: Narrative Analytics Layer (6-week sprint)",
            "Perfect Technical Trifecta Achieved",
            "46 SPECs Complete (55%)",
        ],
        "capabilities": {
            "performance": "Sub-200ms narrative transitions",
            "engagement": "60% increase vs. static browsing",
            "bounce_reduction": "40% improvement",
            "ai_confidence": "92% accuracy with feedback loop",
            "advantage": "5× performance vs. industry standard",
        },
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Nina Intelligence API",
        "environment": os.getenv("NINA_ENV", "dev"),
        "runtime": os.getenv("NINA_RUNTIME", "apple"),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/demo/narrative")
def narrative_demo():
    """SPEC-076 Visual Narrative Layer demo"""
    return {
        "spec": "SPEC-076: Visual Narrative Layer",
        "status": "Pilot Integration Complete",
        "description": "Interactive guided story mode for memory exploration",
        "features": [
            "Branching narrative paths",
            "AI-powered context injection",
            "Real-time performance tracking",
            "User feedback integration",
        ],
        "metrics": {
            "transition_speed": "<200ms",
            "engagement_increase": "60%",
            "user_retention": "3× vs static browsing",
        },
        "next_phase": "SPEC-082 Analytics Layer for measurable ROI",
    }


@app.get("/demo/analytics")
def analytics_demo():
    """SPEC-082 Narrative Analytics Layer preview"""
    return {
        "spec": "SPEC-082: Narrative Analytics Layer",
        "status": "6-Week Sprint (Q4 2024)",
        "description": "Measuring, analyzing, and optimizing narrative engagement",
        "timeline": {
            "week_2": "Basic engagement metrics dashboard",
            "week_4": "Predictive models for user behavior",
            "week_6": "Enterprise ROI reporting ready for demos",
        },
        "business_impact": {
            "investor_presentations": "Data-driven ROI proof",
            "partner_demos": "Live analytics during narrative sessions",
            "enterprise_sales": "Quantified productivity improvements",
        },
    }


@app.get("/platform/status")
def platform_status():
    """Current platform achievement summary"""
    return {
        "phase": "Phase 3: Business Development Activation",
        "technical_foundation": "Bulletproof - Perfect Technical Trifecta",
        "specs": {
            "total": 85,
            "complete": 46,
            "completion_rate": "55%",
            "pilot_integration": 1,
            "planned": 33,
        },
        "achievements": [
            "Operational Maturity: Real-time monitoring, auto-healing",
            "Innovation Leadership: Graph intelligence, narrative AI",
            "Enterprise Security: SOC2/GDPR compliance, auth-aware testing",
        ],
        "q4_focus": [
            "SPEC-082 Analytics sprint for measurable ROI",
            "SPEC-076 pilot expansion to 3 enterprise customers",
            "Business development: demos, investors, partnerships",
        ],
    }


@app.get("/demo/architecture")
def architecture_demo():
    """Unified naming and architecture overview"""
    return {
        "architecture": "Unified Container Naming Convention",
        "database": {
            "strategy": "Shared per environment (not per runtime)",
            "containers": {
                "dev": "ninaivalaigal-dev-db (port 5432)",
                "test": "ninaivalaigal-test-db (port 5532)",
                "prod": "ninaivalaigal-prod-db (port 5632)",
            },
            "benefits": [
                "Data consistency across runtimes",
                "Resource efficiency",
                "Parallel development support",
            ],
        },
        "services": {
            "strategy": "Runtime-specific for parallel development",
            "naming": "ninaivalaigal-{env}-{service}-{runtime}",
            "examples": [
                "ninaivalaigal-dev-api-apple (port 13390)",
                "ninaivalaigal-dev-api-docker (port 13370)",
                "ninaivalaigal-dev-redis-apple (port 6399)",
            ],
        },
        "persistence": "PGDATA subdirectory approach for Apple Container CLI",
        "status": "Production-ready for Q4 business development",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 13390))
    uvicorn.run(app, host="0.0.0.0", port=port)
