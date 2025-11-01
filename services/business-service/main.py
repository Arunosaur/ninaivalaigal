#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Business Service - SPEC-100 Compliant Microservice.

Handles billing, invoicing, usage analytics, and admin intelligence.
Part of SPEC-100 API Container Modularization & Runtime-Agnostic Federation.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add directories to path (order matters: current first, then lib, then shared)
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
lib_dir = current_dir / "lib"
sys.path.insert(0, str(current_dir))  # Current directory first for our routers
sys.path.insert(1, str(lib_dir))  # Then lib for server dependencies
sys.path.insert(2, str(shared_dir))  # Finally shared utilities

# Set environment defaults (from .env.dev or start script)
os.environ.setdefault("NINA_ENV", "dev")

from database import DatabaseManager  # noqa: E402

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan for proper startup/shutdown"""
    logger.info("🚀 Starting Business Service...")

    skip_db = os.getenv("BUSINESS_SERVICE_SKIP_DB", "false").lower() in {"true", "1", "yes"}
    db_manager = None

    if skip_db:
        logger.warning("BUSINESS_SERVICE_SKIP_DB enabled; skipping database initialization")
    else:
        # Initialize database from environment variable (REQUIRED when skip flag is false)
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not set!")
            logger.error("   Start service with: ./scripts/nv-business-service-start.sh or export DATABASE_URL")
            raise ValueError("DATABASE_URL is required when BUSINESS_SERVICE_SKIP_DB is false")
        logger.info(f"📊 Database URL: {database_url[:50]}...")

        try:
            db_manager = DatabaseManager(database_url)
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    app.state.db_manager = db_manager
    app.state.db = db_manager

    logger.info("✅ Business Service started successfully")

    yield

    logger.info("👋 Business Service shutting down...")


# Initialize FastAPI app with SPEC-100 metadata
app = FastAPI(
    title="Business Service",
    description="Billing, Usage Analytics, and Admin Intelligence (SPEC-100 Compliant)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include SPEC-100 routers
from routers import health as health_router  # noqa: E402
from routers import metrics as metrics_router  # noqa: E402

app.include_router(health_router.router)
app.include_router(metrics_router.router)

# Import engagement routers
# Import business routers
from routers import admin_analytics_api  # noqa: E402
from routers import billing_console_api  # noqa: E402
from routers import billing_engine_integration_api  # noqa: E402
from routers import discussion_api  # noqa: E402
from routers import early_adopter_api  # noqa: E402
from routers import feedback_api  # noqa: E402
from routers import gamification_api  # noqa: E402
from routers import invoice_management_api  # noqa: E402
from routers import partner_ecosystem_api  # noqa: E402
from routers import team_billing_portal_api  # noqa: E402
from routers import timeline_api  # noqa: E402
from routers import usage_analytics_api  # noqa: E402

# Include business routers
app.include_router(billing_console_api.router)
app.include_router(invoice_management_api.router)
app.include_router(usage_analytics_api.router)
app.include_router(admin_analytics_api.router)
app.include_router(billing_engine_integration_api.router)
app.include_router(team_billing_portal_api.router)

# Include engagement routers
app.include_router(early_adopter_api.router)
app.include_router(gamification_api.router)
app.include_router(feedback_api.router)
app.include_router(partner_ecosystem_api.router)
app.include_router(discussion_api.router)
app.include_router(timeline_api.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "13391"))  # Business Service canonical port
    print("=" * 60)
    print("🏢 BUSINESS SERVICE - SPEC-100 Modularization")
    print("=" * 60)
    print(f"📍 Health:  http://localhost:{port}/health")
    print(f"📍 Ready:   http://localhost:{port}/ready")
    print(f"📍 Metrics: http://localhost:{port}/metrics")
    print("📋 Phase 1: Health and metrics endpoints only")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
