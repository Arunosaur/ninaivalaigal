#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Graph/AI Service - SPEC-100 Compliant Microservice.

Handles graph intelligence, Apache AGE integration, and AI reasoning.
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
    logger.info("🧠 Starting Graph/AI Service...")

    # Initialize database from environment variable (REQUIRED - no fallback)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set!")
        logger.error("   Start service with: ./services/graph-service/nv-graph-service-start.sh")
        raise ValueError("DATABASE_URL is required")
    logger.info(f"📊 Database URL: {database_url[:50]}...")

    try:
        db_manager = DatabaseManager(database_url)
        app.state.db_manager = db_manager
        app.state.db = db_manager
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    logger.info("✅ Graph/AI Service started successfully")

    yield

    logger.info("👋 Graph/AI Service shutting down...")


# Initialize FastAPI app with SPEC-100 metadata
app = FastAPI(
    title="Graph/AI Service",
    description="Graph Intelligence & AI Reasoning (SPEC-100 + SPEC-062 Compliant)",
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

# Add routers with SPEC-100 compliant API prefix
app.include_router(health_router.router, prefix="/api/v1/graph", tags=["health"])
app.include_router(metrics_router.router, prefix="/api/v1/graph", tags=["metrics"])

# Import graph intelligence routers - ALL ROUTERS ENABLED
# All lib/ imports fixed, enabling full graph intelligence stack

# Import all graph routers with proper error handling and SPEC-100 prefix
try:
    from routers import graphops_integration  # noqa: E402

    app.include_router(graphops_integration.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load graphops_integration: {e}")

try:
    from routers import dashboard_widgets_api  # noqa: E402

    app.include_router(dashboard_widgets_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load dashboard_widgets_api: {e}")

try:
    from routers import ai_feedback_api  # noqa: E402

    app.include_router(ai_feedback_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load ai_feedback_api: {e}")

# NOW ENABLING: Complex graph intelligence routers
try:
    from routers import graph_intelligence_api  # noqa: E402

    app.include_router(graph_intelligence_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load graph_intelligence_api: {e}")

try:
    from routers import graph_intelligence_integration_api  # noqa: E402

    app.include_router(graph_intelligence_integration_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load graph_intelligence_integration_api: {e}")

try:
    from routers import graph_rank  # noqa: E402

    app.include_router(graph_rank.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load graph_rank: {e}")

try:
    from routers import insights_api  # noqa: E402

    app.include_router(insights_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load insights_api: {e}")

try:
    from routers import performance_api  # noqa: E402

    app.include_router(performance_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load performance_api: {e}")

try:
    from routers import agentic_api  # noqa: E402

    app.include_router(agentic_api.router, prefix="/api/v1/graph")
except Exception as e:
    print(f"⚠️  Could not load agentic_api: {e}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))  # Graph/AI Service on port 8001
    print("=" * 60)
    print("🧠 GRAPH/AI SERVICE - SPEC-100 + SPEC-062 Integration")
    print("=" * 60)
    print(f"📍 Health: http://localhost:{port}/api/v1/graph/health")
    print(f"📍 Ready:  http://localhost:{port}/api/v1/graph/ready")
    print(f"📍 Metrics: http://localhost:{port}/api/v1/graph/metrics")
    print(f"📍 API:    http://localhost:{port}/api/v1/graph/*")
    print("📊 Graph DB: Port 5433 (GraphOps)")
    print("📊 Graph Redis: Port 6380 (GraphOps)")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
