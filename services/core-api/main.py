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
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add directories to path (order matters: current first, then lib, then shared)
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
lib_dir = current_dir / "lib"
sys.path.insert(0, str(current_dir))  # Current directory first for our routers
sys.path.insert(1, str(lib_dir))  # Then lib for server dependencies
sys.path.insert(2, str(shared_dir))  # Finally shared utilities

from database import DatabaseManager  # noqa: E402
from rbac_middleware import rbac_middleware  # noqa: E402

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

    # Initialize database from environment variable (required)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        raise ValueError("DATABASE_URL must be set in environment")
    logger.info(f"📊 Database URL: {database_url[:50]}...")

    try:
        db_manager = DatabaseManager(database_url)
        app.state.db_manager = db_manager
        app.state.db = db_manager
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Initialize event publisher (optional)
    try:
        from events import get_event_publisher

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("⚠️  REDIS_URL not configured - events will not be published")
            app.state.event_publisher = None
        else:
            event_publisher = await get_event_publisher(redis_url)
            app.state.event_publisher = event_publisher
            logger.info("✅ Event publisher connected")
    except Exception as e:
        logger.warning(f"⚠️  Event publisher connection failed: {e}")
        logger.warning("Events will not be published")
        app.state.event_publisher = None

    # Initialize container health monitoring (SPEC-051)
    try:
        from lib.observability.circuit_breaker import (
            initialize_service_circuit_breakers,
        )
        from lib.observability.container_health import initialize_container_monitoring
        from lib.observability.platform_alerting import (
            initialize_platform_stability_alerting,
        )

        # Initialize circuit breakers for all services
        circuit_breaker_registry = initialize_service_circuit_breakers()
        app.state.circuit_breaker_registry = circuit_breaker_registry
        logger.info("✅ Circuit breakers initialized")

        # Start container health monitoring
        container_monitor = await initialize_container_monitoring()
        app.state.container_monitor = container_monitor
        logger.info("✅ Container health monitoring started")

        # Start platform stability alerting
        platform_alerter = await initialize_platform_stability_alerting()
        app.state.platform_alerter = platform_alerter
        logger.info("✅ Platform stability alerting started")
    except Exception as e:
        logger.warning(f"⚠️  Container health monitoring initialization failed: {e}")
        logger.warning("Platform stability monitoring will be limited")
        app.state.container_monitor = None
        app.state.circuit_breaker_registry = None
        app.state.platform_alerter = None

    logger.info("✅ Core API Service started successfully")

    yield

    # Cleanup
    logger.info("🛑 Shutting down Core API Service...")
    if hasattr(app.state, "event_publisher") and app.state.event_publisher:
        await app.state.event_publisher.disconnect()
        logger.info("Event publisher disconnected")

    if hasattr(app.state, "container_monitor") and app.state.container_monitor:
        await app.state.container_monitor.stop_monitoring()
        logger.info("Container health monitoring stopped")

    if hasattr(app.state, "platform_alerter") and app.state.platform_alerter:
        await app.state.platform_alerter.stop_monitoring()
        logger.info("Platform stability alerting stopped")


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

# Add Prometheus metrics middleware (must be before other middleware to track all requests)
from lib.observability.metrics import MetricsMiddleware

app.add_middleware(MetricsMiddleware)

# Enforce JWT authentication + RBAC context extraction for protected routes
app.middleware("http")(rbac_middleware)


# Exception handlers for proper status codes
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper status codes"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


import json

# Add JSON parsing error handler (catches malformed JSON before route handlers)
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.middleware("http")
async def catch_json_errors(request: Request, call_next):
    """Catch JSON parsing errors and return 400"""
    # Only process JSON requests
    if request.headers.get("content-type") == "application/json":
        try:
            # Try to read and parse the body
            body = await request.body()
            if body:
                try:
                    json.loads(body)
                except json.JSONDecodeError:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Malformed JSON payload"}
                    )

            # Reset body for route handlers
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive
        except Exception:
            pass

    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors

    For JSON parsing errors, return 400 (Bad Request)
    For field validation errors, return 422 (Unprocessable Entity)
    """
    errors = exc.errors()

    # Check if it's a JSON parsing error
    for error in errors:
        if error.get("type") in ["json_invalid", "json_type_error"]:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid JSON format"})

    # Otherwise, return 422 for field validation errors
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errors})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError as 400 Bad Request"""
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


# Dependency injection
def get_db(request: Request) -> DatabaseManager:
    """Get database manager from app state"""
    return request.app.state.db_manager


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "core-api", "version": "1.0.0"}


# SPEC-030: US-262 Security Monitoring Dashboard
# Import and include SPEC-100 routers
from routers import admin_analytics_security  # noqa: E402
from routers import health as health_router  # noqa: E402

from lib.api import container_health_api  # noqa: E402
from lib.api import monitoring_api  # noqa: E402
from lib.observability import memory_health  # noqa: E402
from lib.observability import metrics as metrics_module  # noqa: E402

app.include_router(health_router.router)
app.include_router(metrics_module.router)
app.include_router(memory_health.router)
app.include_router(monitoring_api.router)
app.include_router(container_health_api.router)  # SPEC-051 Platform Stability
app.include_router(admin_analytics_security.router)  # SPEC-030: US-262 Security Analytics

from lib.memory_attachments_api import router as memory_attachments_router  # noqa: E402
from lib.memory_capture_api import router as memory_capture_router  # noqa: E402
from lib.routers.substrate import (  # noqa: E402  # SPEC-012: Memory Substrate Management
    router as substrate_router,
)

# ⚠️  REMOVED: queue_api migrated to Rust Memory Service (port 13393)
# Phase 3: Router registration removed per SPEC-131 deprecation plan
# See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md
# New Endpoint: http://localhost:13393/queue/*
# from routers import queue_api  # REMOVED - Use Rust service
# ⚠️  REMOVED: memory_injection_api migrated to Rust Memory Service (port 13393)
# Phase 3: Router registration removed per SPEC-131 deprecation plan
# See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md
# New Endpoint: http://localhost:13393/memory/injection/*
# from routers import memory_injection_api  # REMOVED - Use Rust service
# from routers import memory_api  # noqa: E402  # REMOVED - redundant with Rust
# Import team management routers
# Import memory & session routers
# Import business logic routers
from routers import dev_tools  # noqa: E402
from routers import memory_acl_api  # noqa: E402
from routers import memory_browser_api  # noqa: E402
from routers import memory_drift_api  # noqa: E402
from routers import memory_health_api  # noqa: E402
from routers import memory_suggestions_api  # noqa: E402
from routers import organizations  # noqa: E402
from routers import preload_api  # noqa: E402
from routers import rbac_api  # noqa: E402
from routers import session_api  # noqa: E402
from routers import signup_api  # noqa: E402
from routers import team_api_keys_api  # noqa: E402
from routers import team_invitations_api  # noqa: E402
from routers import teams  # noqa: E402
from routers import token_api  # noqa: E402
from routers import users  # noqa: E402
from routers import (  # noqa: E402  # Basic protected memory endpoints for auth testing
    memory_basic,
)

# Include business logic routers
app.include_router(signup_api.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(organizations.router)
app.include_router(rbac_api.rbac_router)  # Note: rbac_api uses 'rbac_router' not 'router'
app.include_router(token_api.router)

# Include memory & session routers
# memory_api.router REMOVED - redundant with Rust Memory Service (port 13393)
# Basic CRUD (remember, recall, list, delete) now handled by Rust
# app.include_router(memory_api.router)
app.include_router(memory_basic.router)  # Protected endpoints for auth testing
app.include_router(memory_acl_api.router)
app.include_router(memory_browser_api.router)
app.include_router(memory_drift_api.router)
app.include_router(memory_health_api.router)
# ⚠️  REMOVED: memory_injection_api router registration removed (Phase 3)
# Migrated to Rust Memory Service at http://localhost:13393/memory/injection/*
# See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md
# app.include_router(memory_injection_api.router)  # REMOVED - Use Rust service
app.include_router(memory_suggestions_api.router)
app.include_router(memory_attachments_router)  # SPEC-032: Memory Attachment Endpoints
app.include_router(memory_capture_router)  # SPEC-077: Multimodal Memory Capture Endpoints
app.include_router(substrate_router)  # SPEC-012: Memory Substrate Management
app.include_router(session_api.router)
# ⚠️  REMOVED: queue_api router registration removed (Phase 3)
# Migrated to Rust Memory Service at http://localhost:13393/queue/*
# See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md
# app.include_router(queue_api.router)  # REMOVED - Use Rust service
app.include_router(preload_api.router)

# Include team management routers
app.include_router(team_api_keys_api.router)
app.include_router(team_invitations_api.router)

# Include development tools router
app.include_router(dev_tools.router)

# Include macro management router (SPEC-046)
from routers import macro_audit_api, macro_management_api

app.include_router(macro_management_api.router)
app.include_router(macro_audit_api.router)

# Include demo management router (SPEC-047)
from routers import demo_management_api

app.include_router(demo_management_api.router)

# Include classification router (SPEC-048)
from routers import (
    classification_api,
    classification_audit_api,
    classification_search_api,
    reclassification_api,
)

app.include_router(classification_api.router)
app.include_router(classification_search_api.router)
app.include_router(classification_audit_api.router)
app.include_router(reclassification_api.router)

# Include admin SPEC-005 status router
from routers import admin_spec005_status, personalization_api

app.include_router(admin_spec005_status.router)

# Include admin user management API (US#110)
from lib.routers.admin_user_management import router as admin_user_management_router

app.include_router(admin_user_management_router)

# Include admin context management API (US#113)
from lib.routers.admin_context_management import (
    router as admin_context_management_router,
)

app.include_router(admin_context_management_router)

# Include policy visualization API (US#116)
from lib.routers.policy_visualization import router as policy_visualization_router

app.include_router(policy_visualization_router)

# Include permission inheritance API (US#119)
from lib.routers.permission_inheritance import router as permission_inheritance_router

app.include_router(permission_inheritance_router)

# Include tag ACL API (US#339)
from lib.routers.tag_acl import router as tag_acl_router

app.include_router(tag_acl_router)

# Include snapshot restore API (US#343)
from lib.routers.snapshot_restore import router as snapshot_restore_router

app.include_router(snapshot_restore_router)

# Include personalization engine router (SPEC-079)
app.include_router(personalization_api.router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
