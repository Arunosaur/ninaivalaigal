#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Business Service - SPEC-100 Modularization

Handles:
- Billing management (Stripe integration)
- Usage analytics and metrics
- Admin analytics dashboard
- Team billing portals

Part of SPEC-100 API Container Modularization & Runtime-Agnostic Federation
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add shared to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Set environment defaults
os.environ.setdefault("NINA_ENV", "dev")
os.environ.setdefault("NINA_DB_USER", "nina")
os.environ.setdefault("NINA_DB_PASSWORD", "dev_password_change_in_production")

from database import DatabaseManager  # noqa: E402
from routers import health as health_router  # noqa: E402
from routers import metrics as metrics_router  # noqa: E402

from utils.config import get_dynamic_database_url  # noqa: E402

# Get database URL dynamically
DATABASE_URL = get_dynamic_database_url()

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
    """Lifecycle management for Business Service"""
    logger.info("🚀 Business Service starting up...")
    logger.info(f"📊 Database: {DATABASE_URL[:50]}...")

    # Initialize database connection
    try:
        app.state.db = DatabaseManager(DATABASE_URL)
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        app.state.db = None

    yield

    # Cleanup
    logger.info("👋 Business Service shutting down...")
    if hasattr(app.state, "db") and app.state.db:
        # Close database connections if needed
        logger.info("✅ Database connections closed")


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

# Include SPEC-100 compliant routers
app.include_router(health_router.router)
app.include_router(metrics_router.router)

# Include business routers
from routers import analytics as analytics_router  # noqa: E402
from routers import billing as billing_router  # noqa: E402

app.include_router(billing_router.router)
app.include_router(analytics_router.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))  # Business Service on port 8002
    print("=" * 60)
    print("🏢 BUSINESS SERVICE - SPEC-100 Modularization")
    print("=" * 60)
    print(f"📍 Health: http://localhost:{port}/health")
    print(f"📍 Ready:  http://localhost:{port}/ready")
    print(f"📍 Metrics: http://localhost:{port}/metrics")
    print(f"📊 Database: {DATABASE_URL[:50]}...")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
