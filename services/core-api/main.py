#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
"""
Core API - SPEC-100 Compliant Microservice.

Handles authentication, users, teams, and RBAC functionality.
Part of SPEC-100 API Container Modularization & Runtime-Agnostic Federation.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI, Request
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
        structlog.processors.UnicodeDecoder(),
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
    logger.info("🚀 Starting Core API Service...")

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

    # Initialize event publisher
    try:
        from events import get_event_publisher

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")
        event_publisher = await get_event_publisher(redis_url)
        app.state.event_publisher = event_publisher
        logger.info("✅ Event publisher connected")
    except Exception as e:
        logger.warning(f"⚠️  Event publisher connection failed: {e}")
        logger.warning("Events will not be published")
        app.state.event_publisher = None

    logger.info("✅ Core API Service started successfully")

    yield

    # Cleanup
    logger.info("🛑 Shutting down Core API Service...")
    if hasattr(app.state, "event_publisher") and app.state.event_publisher:
        await app.state.event_publisher.disconnect()
        logger.info("Event publisher disconnected")


# Create FastAPI app
app = FastAPI(
    title="Core API Service",
    version="1.0.0",
    description="Authentication, users, teams, and organization management",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_db(request: Request) -> DatabaseManager:
    """Get database manager from app state"""
    return request.app.state.db_manager


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "core-api", "version": "1.0.0"}


# Import and include SPEC-100 routers
from routers import health as health_router  # noqa: E402
from routers import metrics as metrics_router  # noqa: E402

app.include_router(health_router.router)
app.include_router(metrics_router.router)

# Import team management routers
# Import memory & session routers
# Import business logic routers
from routers import memory_acl_api  # noqa: E402
from routers import memory_api  # noqa: E402
from routers import memory_drift_api  # noqa: E402
from routers import memory_health_api  # noqa: E402
from routers import memory_injection_api  # noqa: E402
from routers import memory_suggestions_api  # noqa: E402
from routers import organizations  # noqa: E402
from routers import preload_api  # noqa: E402
from routers import queue_api  # noqa: E402
from routers import rbac_api  # noqa: E402
from routers import session_api  # noqa: E402
from routers import signup_api  # noqa: E402
from routers import team_api_keys_api  # noqa: E402
from routers import team_invitations_api  # noqa: E402
from routers import teams  # noqa: E402
from routers import token_api  # noqa: E402
from routers import users  # noqa: E402

# Include business logic routers
app.include_router(signup_api.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(organizations.router)
app.include_router(rbac_api.rbac_router)  # Note: rbac_api uses 'rbac_router' not 'router'
app.include_router(token_api.router)

# Include memory & session routers
app.include_router(memory_api.router)
app.include_router(memory_acl_api.router)
app.include_router(memory_drift_api.router)
app.include_router(memory_health_api.router)
app.include_router(memory_injection_api.router)
app.include_router(memory_suggestions_api.router)
app.include_router(session_api.router)
app.include_router(queue_api.router)
app.include_router(preload_api.router)

# Include team management routers
app.include_router(team_api_keys_api.router)
app.include_router(team_invitations_api.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
