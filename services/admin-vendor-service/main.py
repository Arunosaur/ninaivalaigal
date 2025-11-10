#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Admin/Vendor Service - SPEC-100 Compliant Microservice.

Handles vendor administration, staff management, and platform operations.
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

from database import DatabaseManager  # noqa: E402

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan for proper startup/shutdown"""
    logger.info("🏢 Starting Admin/Vendor Service...")

    # Initialize database from environment variable
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://nina:dev_password_change_in_production@localhost:5432/ninaivalaigal_dev"
    )  # pragma: allowlist secret
    logger.info(f"📊 Database URL: {database_url[:50]}...")

    try:
        db_manager = DatabaseManager(database_url)
        app.state.db_manager = db_manager
        app.state.db = db_manager
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    logger.info("✅ Admin/Vendor Service started successfully")

    yield

    logger.info("👋 Admin/Vendor Service shutting down...")


# Initialize FastAPI app with SPEC-100 metadata
app = FastAPI(
    title="Admin/Vendor Service",
    description="Vendor Administration & Staff Management (SPEC-100 Compliant)",
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

# Import admin/vendor routers
from routers import staff_auth_api  # noqa: E402
from routers import staff_management_api  # noqa: E402
from routers import vendor_admin_api  # noqa: E402
from routers import vendor_admin_billing_api  # noqa: E402
from routers import vendor_admin_ui  # noqa: E402

# Include admin/vendor routers
app.include_router(vendor_admin_api.router)
app.include_router(vendor_admin_ui.router)  # Vendor Admin UI (SPEC-025)
app.include_router(vendor_admin_billing_api.router)  # Vendor Admin Billing APIs (US#162, SPEC-026 Phase 2)
app.include_router(staff_management_api.router)
app.include_router(staff_auth_api.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("=" * 60)
    print("🏢 ADMIN/VENDOR SERVICE - SPEC-100 Modularization")
    print("=" * 60)
    print(f"📍 Health: http://localhost:{port}/health")
    print(f"📍 Ready:  http://localhost:{port}/ready")
    print(f"📍 Metrics: http://localhost:{port}/metrics")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
