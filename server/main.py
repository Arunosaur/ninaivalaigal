#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Modular FastAPI Application Entry Point
Refactored from monolithic main.py for better code organization

This addresses the external code review feedback:
- Break down monolithic files (main.py 1300+ lines → focused modules)
- Consolidate configuration into single source
- Improve code organization and maintainability
- Use FastAPI lifespan events for proper startup/shutdown (SPEC-055 compliant)
"""

import os
from contextlib import asynccontextmanager

import structlog
import uvicorn
from approval_workflow import ApprovalWorkflowManager
from auto_recording import get_auto_recorder
from database import DatabaseManager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

# Middleware and security
from observability import health_router, metrics_router
from performance_monitor import get_performance_monitor, start_performance_monitoring
from redis_client import redis_client
from redis_queue import queue_manager
from security_integration import configure_security
from spec_kit import SpecKitContextManager

# Configuration and core services
from config import get_database_url, load_config

# Routers will be imported after app initialization to avoid import-time database connections

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

# Initialize logger
logger = structlog.get_logger(__name__)

# Load configuration (but don't create connections yet)
config = load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for proper startup/shutdown.

    This replaces import-time initialization to comply with SPEC-055:
    - No database connections at import time
    - Proper resource cleanup on shutdown
    - Graceful degradation if services unavailable
    """
    logger.info("🚀 Starting ninaivalaigal API server...")

    # Get configuration
    database_url = get_database_url()
    logger.info(f"📊 Database URL: {database_url[:50]}... (via PgBouncer)")

    # Initialize database connection
    try:
        db_manager = DatabaseManager(database_url)
        app.state.db_manager = db_manager
        app.state.db = db_manager  # Alias for backward compatibility
        logger.info("✅ Database connected successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Initialize dependent services
    try:
        app.state.spec_context_manager = SpecKitContextManager(app.state.db)
        app.state.auto_recorder = get_auto_recorder(app.state.db_manager)
        app.state.approval_manager = ApprovalWorkflowManager(app.state.db_manager)
        logger.info("✅ Core services initialized")
    except Exception as e:
        logger.error(f"⚠️  Service initialization warning: {e}")
        # Continue startup even if some services fail

    # Initialize performance monitoring
    try:
        app.state.performance_monitor = get_performance_monitor()
        start_performance_monitoring()
        logger.info("✅ Performance monitoring started")
    except Exception as e:
        logger.warning(f"⚠️  Performance monitoring warning: {e}")

    # Initialize Redis connection
    try:
        await redis_client.connect()
        logger.info("✅ Redis client connected")

        if hasattr(queue_manager, "connect"):
            queue_manager.connect()
            logger.info("✅ Queue manager initialized")
    except Exception as e:
        logger.warning(f"⚠️  Redis startup failed (graceful degradation): {e}")

    logger.info("🎉 API server startup complete!")

    yield  # Server is running

    # Shutdown: Clean up resources
    logger.info("🛑 Shutting down API server...")

    try:
        if hasattr(queue_manager, "disconnect"):
            queue_manager.disconnect()
        if hasattr(redis_client, "disconnect"):
            await redis_client.disconnect()
        logger.info("✅ Redis connections closed")
    except Exception as e:
        logger.warning(f"⚠️  Redis shutdown error: {e}")

    try:
        if hasattr(app.state, "db_manager") and hasattr(app.state.db_manager, "close"):
            app.state.db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.warning(f"⚠️  Database shutdown error: {e}")

    logger.info("👋 API server shutdown complete")


# Initialize FastAPI app with lifespan
# Disable default docs - we'll add protected, role-scoped docs below
app = FastAPI(
    title="ninaivalaigal Memory Management API",
    description="Enterprise-grade AI memory management platform",
    version="1.0.0",
    docs_url=None,  # Disabled - using protected endpoint
    redoc_url=None,  # Disabled - using protected endpoint
    openapi_url=None,  # Disabled - using protected endpoint
    lifespan=lifespan,  # Use modern lifespan context manager
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware - ALL DISABLED FOR DEBUGGING
# app.middleware("http")(rate_limit_middleware)
# app.middleware("http")(rbac_middleware)  # THIS WAS BLOCKING - NOT ASYNC!


# Content-Length enforcement middleware - FIXED
# Configure security
is_development = os.getenv("ENVIRONMENT", "production").lower() == "development"
configure_security(app, development_mode=is_development)


# Startup/shutdown events now handled by lifespan context manager above
# Old @app.on_event("startup") and @app.on_event("shutdown") removed


# ============================================================================
# DEPENDENCY INJECTION HELPERS
# ============================================================================
# These functions provide access to services initialized in lifespan context


def get_db_manager(request: Request) -> DatabaseManager:
    """Get database manager from app state"""
    return request.app.state.db_manager


def get_db(request: Request) -> DatabaseManager:
    """Alias for get_db_manager for backward compatibility"""
    return request.app.state.db


def get_spec_context_manager(request: Request):
    """Get SpecKit context manager from app state"""
    return request.app.state.spec_context_manager


def get_auto_recorder_instance(request: Request):
    """Get auto recorder from app state"""
    return request.app.state.auto_recorder


def get_approval_manager_instance(request: Request):
    """Get approval manager from app state"""
    return request.app.state.approval_manager


def get_performance_monitor_instance(request: Request):
    """Get performance monitor from app state"""
    return request.app.state.performance_monitor


# Module-level variables for backward compatibility with code that imports them
# These will be None at import time but available after app startup
db_manager = None
db = None
spec_context_manager = None
auto_recorder = None
approval_manager = None
performance_monitor = None


# Custom OpenAPI Fix - prevent Content-Length issues with large schema
@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    """Return OpenAPI schema as JSON response."""
    from fastapi.responses import JSONResponse

    return JSONResponse(app.openapi())


# Include routers
app.include_router(health_router)
app.include_router(metrics_router)

# Router imports placed here intentionally to avoid import-time database connections
# This prevents circular dependencies and allows proper app initialization first
from admin_analytics_api import router as admin_analytics_router  # noqa: E402
from ai_feedback_api import router as ai_feedback_router  # noqa: E402
from auth_working import router as auth_working_router  # noqa: E402
from billing_console_api import router as billing_console_router  # noqa: E402
from billing_engine_integration_api import router as billing_engine_router  # noqa: E402
from dashboard_widgets_api import router as dashboard_router  # noqa: E402
from discussion_api import router as discussion_router  # noqa: E402
from early_adopter_api import router as early_adopter_router  # noqa: E402
from enhanced_signup_api import router as enhanced_signup_router  # noqa: E402
from gamification_api import router as gamification_router  # noqa: E402
from graph_intelligence_integration_api import (  # noqa: E402
    router as graph_intelligence_integration_router,
)
from graph_rank import router as graph_router  # noqa: E402
from graph_usage_analytics import router as graph_usage_analytics_router  # noqa: E402
from graph_validation_checklist import router as graph_validation_router  # noqa: E402
from insights_api import router as insights_router  # noqa: E402
from invoice_management_api import router as invoice_management_router  # noqa: E402
from memory_health_api import router as memory_health_router  # noqa: E402
from memory_injection_api import router as memory_injection_router  # noqa: E402
from memory_suggestions_api import router as memory_suggestions_router  # noqa: E402
from memory_system import router as memory_system_router  # noqa: E402
from partner_ecosystem_api import router as partner_ecosystem_router  # noqa: E402
from protected_routes import router as protected_router  # noqa: E402

# Temporarily disabled for production stability
# from agentic_api import router as agentic_router  # noqa: E402
# from performance_api import router as performance_router  # noqa: E402
from routers.approvals import router as approvals_router  # noqa: E402
from routers.contexts import router as contexts_router  # noqa: E402
from routers.memory import router as memory_router  # noqa: E402
from routers.organizations import router as organizations_router  # noqa: E402
from routers.recording import router as recording_router  # noqa: E402
from routers.teams import router as teams_router  # noqa: E402
from routers.users import router as users_router  # noqa: E402
from signup_api import router as signup_router  # noqa: E402
from standalone_teams_api import router as standalone_teams_router  # noqa: E402
from standalone_teams_billing_api import (  # noqa: E402
    router as standalone_teams_billing_router,
)
from tag_suggester import router as tag_router  # noqa: E402
from team_api_keys_api import router as team_api_keys_router  # noqa: E402
from team_billing_portal_api import router as team_billing_portal_router  # noqa: E402
from teams_working import router as teams_working_router  # noqa: E402
from test_raw_body import router as test_raw_router  # noqa: E402
from timeline_api import router as timeline_router  # noqa: E402
from unified_macro_intelligence_api import (  # noqa: E402
    router as macro_intelligence_router,
)
from usage_analytics_api import router as usage_analytics_router  # noqa: E402
from vendor_admin_api import router as vendor_admin_router  # noqa: E402

# from teams_working_api import router as teams_router  # Temporarily disabled  # noqa: E402


app.include_router(signup_router)  # USER REGISTRATION SYSTEM
app.include_router(test_raw_router)  # TEST RAW BODY PARSING
app.include_router(auth_working_router)  # WORKING AUTH SOLUTION
app.include_router(protected_router)  # PROTECTED ROUTES WITH JWT AUTH
app.include_router(teams_working_router)  # TEAM MANAGEMENT SYSTEM
app.include_router(memory_system_router)  # MEMORY SYSTEM - THE HEART OF NINAIVALAIGAL
# app.include_router(
#     approval_workflows_router
# )  # APPROVAL WORKFLOWS - THE GOVERNANCE BRIDGE - Temporarily disabled
# app.include_router(
#     context_scoping_router
# )  # CONTEXT SCOPING - GRAPH-READY MEMORY ORGANIZATION - Temporarily disabled
app.include_router(timeline_router)  # TIMELINE API - KNOWLEDGE EVOLUTION VIEW
app.include_router(discussion_router)  # DISCUSSION API - THE PLATFORM'S VOICE
app.include_router(graph_router)  # GRAPH RANKING - PAGERANK INTELLIGENCE
app.include_router(tag_router)  # TAG SUGGESTER - GPT-POWERED AUTO-TAGGING
app.include_router(insights_router)  # INSIGHTS API - DASHBOARD INTELLIGENCE
app.include_router(dashboard_router)  # DASHBOARD WIDGETS - REAL-TIME AI INSIGHTS
app.include_router(gamification_router)  # GAMIFICATION - BADGES & LEADERBOARDS
app.include_router(organizations_router)
app.include_router(teams_router)
app.include_router(users_router)
app.include_router(contexts_router)
app.include_router(memory_router)
app.include_router(approvals_router)
app.include_router(recording_router)
app.include_router(vendor_admin_router)
app.include_router(ai_feedback_router)
app.include_router(memory_suggestions_router)
app.include_router(memory_injection_router)
app.include_router(memory_health_router)
app.include_router(standalone_teams_router)
app.include_router(enhanced_signup_router)
app.include_router(billing_console_router)
app.include_router(usage_analytics_router)
app.include_router(early_adopter_router)
app.include_router(invoice_management_router)
app.include_router(admin_analytics_router)
app.include_router(team_api_keys_router)
app.include_router(team_billing_portal_router)
app.include_router(partner_ecosystem_router)
app.include_router(standalone_teams_billing_router)
app.include_router(billing_engine_router)
app.include_router(macro_intelligence_router)
app.include_router(graph_intelligence_integration_router)
app.include_router(graph_validation_router)
app.include_router(graph_usage_analytics_router)
# app.include_router(agentic_router)  # Temporarily disabled
# app.include_router(performance_router)  # Temporarily disabled serving

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# Frontend page routes
# Custom route ID generator and OpenAPI fix
def custom_generate_unique_id(route: APIRoute):
    """Function implementation."""
    return f"{route.name}_{route.path}"


app.router.route_class.unique_id = custom_generate_unique_id


# ============================================================================
# PROTECTED DOCUMENTATION ENDPOINTS (Role-Scoped)
# ============================================================================
# These endpoints require authentication and filter docs based on user role
# Prevents API reconnaissance and enforces defense-in-depth

from fastapi.openapi.docs import get_swagger_ui_html  # noqa: E402
from openapi_filter import get_endpoint_count, get_filtered_openapi  # noqa: E402

from rbac.permissions import Role  # noqa: E402


def get_user_role_from_request(request: Request) -> Role | None:
    """
    Extract user role from request context.

    Tries multiple sources in order:
    1. RBAC context (if middleware set it)
    2. JWT token from Authorization header
    3. Development mode fallback (SYSTEM role)

    Returns:
        User's RBAC role, or None if unauthenticated
    """
    # Method 1: Check if RBAC context is available (set by middleware)
    if hasattr(request.state, "rbac_context"):
        rbac_context = request.state.rbac_context
        if hasattr(rbac_context, "role"):
            return rbac_context.role

    # Method 2: Extract from JWT token in Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            from auth import JWT_ALGORITHM, JWT_SECRET

            # Decode JWT token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

            # Extract role from token
            # Token can have either 'role' (string) or 'roles' (dict)
            if "role" in payload:
                role_str = payload["role"]
                # Convert string to Role enum
                try:
                    return Role[role_str.upper()]
                except (KeyError, AttributeError):
                    logger.warning(f"Invalid role in JWT: {role_str}")

            elif "roles" in payload:
                # Handle roles dict format: {"global": "MEMBER", "teams": {...}}
                roles_dict = payload["roles"]
                if isinstance(roles_dict, dict) and "global" in roles_dict:
                    role_str = roles_dict["global"]
                    try:
                        return Role[role_str.upper()]
                    except (KeyError, AttributeError):
                        logger.warning(f"Invalid global role in JWT: {role_str}")

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
        except Exception as e:
            logger.error(f"Error extracting role from JWT: {e}")

    # Method 3: Development mode fallback
    # In development, allow unauthenticated access with SYSTEM role for testing
    if os.getenv("ENVIRONMENT", "production").lower() == "development":
        return Role.SYSTEM

    # No authentication found
    return None


@app.get("/openapi.json", include_in_schema=False)
async def protected_openapi(request: Request):
    """
    Protected OpenAPI schema endpoint.

    Returns filtered schema based on user's role/scope.
    Unauthenticated users get empty schema.
    """
    user_role = get_user_role_from_request(request)

    # Generate filtered schema
    filtered_schema = get_filtered_openapi(
        app=app,
        role=user_role,
        title=f"ninaivalaigal API ({user_role.name if user_role else 'Public'})",
        version="1.0.0",
    )

    endpoint_count = get_endpoint_count(filtered_schema)
    logger.info(
        "OpenAPI schema requested",
        role=user_role.name if user_role else "unauthenticated",
        endpoints_visible=endpoint_count,
    )

    return JSONResponse(filtered_schema)


@app.get("/docs", include_in_schema=False)
async def protected_docs(request: Request):
    """
    Protected Swagger UI documentation.

    Requires authentication. Shows only endpoints user is allowed to call.
    """
    user_role = get_user_role_from_request(request)

    if user_role is None:
        # Unauthenticated - return 401 or redirect to login
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Authentication required to view API documentation",
                "hint": "Please sign in to access interactive API docs",
            },
        )

    # Return Swagger UI with role-filtered OpenAPI
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"ninaivalaigal API Docs ({user_role.name})",
    )


# Root endpoint handled by API routers
# @app.get("/")
# def serve_signup():
#     """Serve signup page as default"""
#     return FileResponse(os.path.join(frontend_dir, "signup.html"))


@app.get("/signup")
def serve_signup_page():
    """Serve signup page"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))


@app.get("/signup.html")
def serve_signup_page_html():
    """Serve signup page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))


@app.get("/enhanced-signup")
def serve_enhanced_signup():
    """Serve enhanced signup page with team options"""
    return FileResponse(os.path.join(frontend_dir, "enhanced-signup.html"))


@app.get("/enhanced-signup.html")
def serve_enhanced_signup_html():
    """Serve enhanced signup page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "enhanced-signup.html"))


@app.get("/team-dashboard")
def serve_team_dashboard():
    """Serve team dashboard page"""
    return FileResponse(os.path.join(frontend_dir, "team-dashboard.html"))


@app.get("/team-dashboard.html")
def serve_team_dashboard_html():
    """Serve team dashboard page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "team-dashboard.html"))


@app.get("/billing-console")
def serve_billing_console():
    """Serve billing console page"""
    return FileResponse(os.path.join(frontend_dir, "billing-console.html"))


@app.get("/billing-console.html")
def serve_billing_console_html():
    """Serve billing console page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "billing-console.html"))


@app.get("/usage-analytics")
def serve_usage_analytics():
    """Serve usage analytics dashboard"""
    return FileResponse(os.path.join(frontend_dir, "usage-analytics.html"))


@app.get("/usage-analytics.html")
def serve_usage_analytics_html():
    """Serve usage analytics dashboard with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "usage-analytics.html"))


@app.get("/invoice-management")
def serve_invoice_management():
    """Serve invoice management dashboard"""
    return FileResponse(os.path.join(frontend_dir, "invoice-management.html"))


@app.get("/invoice-management.html")
def serve_invoice_management_html():
    """Serve invoice management dashboard with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "invoice-management.html"))


@app.get("/admin-analytics")
def serve_admin_analytics():
    """Serve admin analytics console"""
    return FileResponse(os.path.join(frontend_dir, "admin-analytics.html"))


@app.get("/admin-analytics.html")
def serve_admin_analytics_html():
    """Serve admin analytics console with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "admin-analytics.html"))


@app.get("/login")
def serve_login_page():
    """Serve login page"""
    return FileResponse(os.path.join(frontend_dir, "login.html"))


@app.get("/login.html")
def serve_login_page_html():
    """Serve login page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "login.html"))


@app.get("/dashboard")
def serve_dashboard_page():
    """Serve dashboard page"""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))


@app.get("/dashboard.html")
def serve_dashboard_page_html():
    """Serve dashboard page with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))


@app.get("/team-api-keys")
def serve_team_api_keys():
    """Serve team API keys management"""
    return FileResponse(os.path.join(frontend_dir, "team-api-keys.html"))


@app.get("/team-api-keys.html")
def serve_team_api_keys_html():
    """Serve team API keys management with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "team-api-keys.html"))


@app.get("/team-billing-portal")
def serve_team_billing_portal():
    """Serve team billing portal"""
    return FileResponse(os.path.join(frontend_dir, "team-billing-portal.html"))


@app.get("/team-billing-portal.html")
def serve_team_billing_portal_html():
    """Serve team billing portal with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "team-billing-portal.html"))


@app.get("/partner-dashboard")
def serve_partner_dashboard():
    """Serve partner dashboard"""
    return FileResponse(os.path.join(frontend_dir, "partner-dashboard.html"))


@app.get("/partner-dashboard.html")
def serve_partner_dashboard_html():
    """Serve partner dashboard with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "partner-dashboard.html"))


@app.get("/standalone-teams-billing")
def serve_standalone_teams_billing():
    """Serve standalone teams billing interface"""
    return FileResponse(os.path.join(frontend_dir, "standalone-teams-billing.html"))


@app.get("/standalone-teams-billing.html")
def serve_standalone_teams_billing_html():
    """Serve standalone teams billing interface with .html extension"""
    return FileResponse(os.path.join(frontend_dir, "standalone-teams-billing.html"))


# Health check endpoint (simple version, detailed version in health_router)
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "ninaivalaigal"}


if __name__ == "__main__":
    uvicorn.run("main_modular:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
