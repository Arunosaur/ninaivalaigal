#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Graph/AI Service - SPEC-100 Modularization

Handles:
- Graph intelligence and reasoning (Apache AGE)
- AI-powered suggestions and relevance
- Memory graph analysis
- Heavy compute isolation

Integrates with:
- GraphOps Stack (ninaivalaigal-graph-db on port 5433)
- Graph Redis Cache (ninaivalaigal-graph-redis on port 6380)

Part of SPEC-100 API Container Modularization & Runtime-Agnostic Federation
SPEC-062: GraphOps Stack Deployment Architecture
SPEC-064: Graph Intelligence Architecture
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

# Set environment defaults for GraphOps
os.environ.setdefault("NINA_ENV", "dev")
os.environ.setdefault("GRAPH_DB_HOST", "localhost")
os.environ.setdefault("GRAPH_DB_PORT", "5433")  # GraphOps port
os.environ.setdefault("GRAPH_DB_NAME", "graph_db")
os.environ.setdefault("GRAPH_DB_USER", "graphops")
os.environ.setdefault("GRAPH_DB_PASSWORD", "graphops_password")
os.environ.setdefault("GRAPH_REDIS_HOST", "localhost")
os.environ.setdefault("GRAPH_REDIS_PORT", "6380")  # GraphOps Redis port

from routers import health as health_router  # noqa: E402
from routers import metrics as metrics_router  # noqa: E402

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
    """Lifecycle management for Graph/AI Service"""
    logger.info("🧠 Graph/AI Service starting up...")

    # GraphOps connection details
    graph_db_url = (
        f"postgresql://{os.getenv('GRAPH_DB_USER')}:{os.getenv('GRAPH_DB_PASSWORD')}"
        f"@{os.getenv('GRAPH_DB_HOST')}:{os.getenv('GRAPH_DB_PORT')}/{os.getenv('GRAPH_DB_NAME')}"
    )
    graph_redis_url = f"redis://{os.getenv('GRAPH_REDIS_HOST')}:{os.getenv('GRAPH_REDIS_PORT')}"

    logger.info(f"📊 Graph DB: {graph_db_url[:60]}...")
    logger.info(f"📊 Graph Redis: {graph_redis_url}")

    # Initialize connections
    try:
        # TODO: Initialize Apache AGE client
        # app.state.age_client = AGEClient(graph_db_url)
        logger.info("✅ Apache AGE client ready (placeholder)")

        # TODO: Initialize Graph Redis client
        # app.state.graph_redis = redis.from_url(graph_redis_url)
        logger.info("✅ Graph Redis client ready (placeholder)")

        # TODO: Initialize GraphReasoner
        # app.state.graph_reasoner = GraphReasoner(app.state.age_client, app.state.graph_redis)
        logger.info("✅ GraphReasoner ready (placeholder)")

        app.state.graphops_available = False  # Set to True when connected
    except Exception as e:
        logger.error(f"❌ GraphOps connection failed: {e}")
        app.state.graphops_available = False

    yield

    # Cleanup
    logger.info("👋 Graph/AI Service shutting down...")
    if hasattr(app.state, "age_client"):
        # Close Apache AGE connections
        logger.info("✅ Apache AGE connections closed")
    if hasattr(app.state, "graph_redis"):
        # Close Redis connections
        logger.info("✅ Graph Redis connections closed")


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

# Include SPEC-100 compliant routers
app.include_router(health_router.router)
app.include_router(metrics_router.router)

# Include graph intelligence routers
from routers import graph as graph_router  # noqa: E402

app.include_router(graph_router.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))  # Graph/AI Service on port 8001
    print("=" * 60)
    print("🧠 GRAPH/AI SERVICE - SPEC-100 + SPEC-062 Integration")
    print("=" * 60)
    print(f"📍 Health: http://localhost:{port}/health")
    print(f"📍 Ready:  http://localhost:{port}/ready")
    print(f"📍 Metrics: http://localhost:{port}/metrics")
    print(f"📍 Graph:  http://localhost:{port}/graph/*")
    print("📊 Graph DB: Port 5433 (GraphOps)")
    print("📊 Graph Redis: Port 6380 (GraphOps)")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
