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

# Make tracing imports optional for tests
try:
    from observability.tracing import TracingConfig, init_tracing

    TRACING_AVAILABLE = True
except ImportError:
    # Gracefully handle missing opentelemetry dependencies (common in test environments)
    TracingConfig = None
    init_tracing = None
    TRACING_AVAILABLE = False

from performance_monitor import get_performance_monitor, start_performance_monitoring
from redis_client import redis_client
from redis_queue import queue_manager
from security_integration import configure_security
from spec_kit import SpecKitContextManager
from server.middleware import AdminSessionMiddleware

# Configuration and core services
from server.config import get_database_url, load_config

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
    """Lifespan context manager for proper FastAPI startup/shutdown.

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

# Initialize OpenTelemetry Distributed Tracing (Task #84)
# Skip tracing if dependencies are unavailable or explicitly disabled for tests
tracing_enabled_env = os.getenv("OTEL_TRACING_ENABLED", "true").lower() == "true"
is_testing = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TESTING") == "true"

if TRACING_AVAILABLE and tracing_enabled_env and not is_testing:
    try:
        service_name = os.getenv("OTEL_SERVICE_NAME", "ninaivalaigal-core-api")
        jaeger_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        is_dev = os.getenv("ENVIRONMENT", "production").lower() == "development"

        tracing_config = TracingConfig(
            service_name=service_name,
            service_version="1.0.0",
            jaeger_endpoint=jaeger_endpoint,
            enable_console_export=is_dev,
        )
        tracer = init_tracing(app, tracing_config)
        logger.info(f"✅ Distributed tracing enabled: {service_name} -> {jaeger_endpoint}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize tracing: {e}")
        logger.info("Continuing without distributed tracing")
elif is_testing:
    logger.debug("⏭️  Distributed tracing disabled in test environment")
elif not TRACING_AVAILABLE:
    logger.debug("⏭️  Distributed tracing dependencies not available")
elif not tracing_enabled_env:
    logger.info("⏭️  Distributed tracing disabled via OTEL_TRACING_ENABLED=false")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bridge admin session cookies to legacy authorization dependencies
app.add_middleware(AdminSessionMiddleware)

# Add tenant isolation middleware (US#117: ORM Guardrails)
try:
    from server.security.orm.tenancy_guard import create_tenant_middleware

    tenant_middleware = create_tenant_middleware()
    app.middleware("http")(tenant_middleware)
    logger.info("✅ Tenant isolation middleware installed")
except Exception as e:
    logger.warning(f"⚠️  Could not install tenant middleware: {e}")

# SPEC-147: Usage Metering Middleware (BILL-002)
# Add after tenant middleware to ensure billing account context is available
try:
    from server.billing.usage_middleware import UsageMeteringMiddleware

    # Enable middleware with configuration
    usage_metering_enabled = os.getenv("BILLING_USAGE_METERING_ENABLED", "true").lower() == "true"
    if usage_metering_enabled:
        app.add_middleware(
            UsageMeteringMiddleware,
            enabled=True,
            track_storage=True,
            track_retrievals=True,
            track_tokens=True,
        )
        logger.info("✅ SPEC-147 usage metering middleware installed")
    else:
        logger.info("⏭️  SPEC-147 usage metering middleware disabled via BILLING_USAGE_METERING_ENABLED=false")
except ImportError as e:
    logger.warning(f"⚠️  Could not install SPEC-147 usage metering middleware: {e}")
except Exception as e:
    logger.warning(f"⚠️  Error installing SPEC-147 usage metering middleware: {e}")

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

# TRACE-006: Trace Analytics & Service Dependency Graphs (US#977)
try:
    from routers.trace_analytics_api import router as trace_analytics_router

    app.include_router(trace_analytics_router)
    logger.info("✅ Trace Analytics API router registered (US#977: TRACE-006)")
except ImportError as e:
    logger.warning(f"⚠️  Trace Analytics API not available: {e}")

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
from graphops_integration import router as graphops_router  # noqa: E402
from insights_api import router as insights_router  # noqa: E402
from invoice_management_api import router as invoice_management_router  # noqa: E402
from memory_health_api import router as memory_health_router  # noqa: E402

# REMOVED: memory_injection_api router (Python)
# Migrated to Rust endpoint: http://localhost:13393/memory/injection/*
# Migration Date: 2025-01-31
# Removal Date: 2025-01-31 (US#857: SPEC-131 Phase 3)
# from memory_injection_api import router as memory_injection_router  # noqa: E402
from memory_suggestions_api import router as memory_suggestions_router  # noqa: E402
from memory_system import router as memory_system_router  # noqa: E402
from partner_ecosystem_api import router as partner_ecosystem_router  # noqa: E402
from protected_routes import router as protected_router  # noqa: E402

# Temporarily disabled for production stability
# from agentic_api import router as agentic_router  # noqa: E402
# from performance_api import router as performance_router  # noqa: E402
from routers.admin_activity import router as admin_activity_router  # noqa: E402
from routers.admin_dashboard import router as admin_dashboard_router  # noqa: E402
from routers.admin_organizations import (  # noqa: E402
    router as admin_organizations_router,
)
from routers.approvals import router as approvals_router  # noqa: E402
from routers.contexts import router as contexts_router  # noqa: E402
from routers.memory import router as memory_router  # noqa: E402

# NOTE: substrate_router moved to services/core-api/main.py per SPEC-100 router mapping
# from routers.substrate import router as substrate_router  # noqa: E402  # SPEC-012: Memory Substrate Management
from routers.memory_browser_api import router as memory_browser_router  # noqa: E402
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

# from teams_working import router as teams_working_router  # noqa: E402  # Disabled: conflicts with routers/teams.py
from test_raw_body import router as test_raw_router  # noqa: E402
from timeline_api import router as timeline_router  # noqa: E402
from unified_macro_intelligence_api import (  # noqa: E402
    router as macro_intelligence_router,
)
from usage_analytics_api import router as usage_analytics_router  # noqa: E402
from vendor_admin_api import router as vendor_admin_router  # noqa: E402

from server.macro.context_linking_api import (  # noqa: E402
    router as macro_context_linking_router,
)
from server.macro.execution_api import router as macro_execution_router  # noqa: E402
from server.macro.plugin_api import router as macro_plugin_router  # noqa: E402
from server.macro.visual_recording_api import (  # noqa: E402
    router as macro_visual_recording_router,
)
from server.macro.implicit_detection_api import (  # noqa: E402
    router as macro_implicit_detection_router,
)
from server.notifications.in_app_api import (  # noqa: E402
    router as in_app_notifications_router,
)

# from teams_working_api import router as teams_router  # Temporarily disabled  # noqa: E402


app.include_router(signup_router)  # USER REGISTRATION SYSTEM
app.include_router(test_raw_router)  # TEST RAW BODY PARSING
app.include_router(auth_working_router)  # WORKING AUTH SOLUTION
app.include_router(protected_router)  # PROTECTED ROUTES WITH JWT AUTH
# app.include_router(teams_working_router)  # TEAM MANAGEMENT SYSTEM - Disabled: conflicts with routers/teams.py
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
app.include_router(graphops_router)  # Mock GraphOps Client
app.include_router(tag_router)  # TAG SUGGESTER - GPT-POWERED AUTO-TAGGING
app.include_router(insights_router)  # INSIGHTS API - DASHBOARD INTELLIGENCE
app.include_router(dashboard_router)  # DASHBOARD WIDGETS - REAL-TIME AI INSIGHTS
app.include_router(gamification_router)  # GAMIFICATION - BADGES & LEADERBOARDS
app.include_router(in_app_notifications_router)  # IN-APP NOTIFICATIONS (US#938, SPEC-148)
app.include_router(organizations_router)
app.include_router(teams_router)
app.include_router(users_router)
app.include_router(contexts_router)
app.include_router(memory_router)
# NOTE: substrate_router moved to services/core-api/main.py per SPEC-100 router mapping
# app.include_router(substrate_router)  # SPEC-012: Memory Substrate Management
app.include_router(memory_browser_router)  # MEMORY BROWSER API - /api/v1/memory/memories
app.include_router(approvals_router)
app.include_router(recording_router)

# SPEC-035: Memory Versioning API
try:
    from memory_versioning_api import router as memory_versioning_router
    app.include_router(memory_versioning_router)
    logger.info("✅ Memory Versioning API router registered (SPEC-035)")
except ImportError as e:
    logger.warning(f"⚠️  Memory Versioning API not available: {e}")

# SPEC-166: Offline Memory Capture API
try:
    from routers.offline_capture_api import router as offline_capture_router
    app.include_router(offline_capture_router)
    logger.info("✅ Offline Memory Capture API router registered (SPEC-166)")
except ImportError as e:
    logger.warning(f"⚠️  Offline Memory Capture API not available: {e}")
app.include_router(vendor_admin_router)
app.include_router(admin_dashboard_router)  # US#114: System Dashboard & Monitoring
app.include_router(ai_feedback_router)
app.include_router(memory_suggestions_router)
# REMOVED: memory_injection_router registration
# Migrated to Rust endpoint: http://localhost:13393/memory/injection/*
# app.include_router(memory_injection_router)
app.include_router(memory_health_router)
app.include_router(standalone_teams_router)
app.include_router(enhanced_signup_router)
app.include_router(billing_console_router)
app.include_router(usage_analytics_router)
app.include_router(early_adopter_router)
app.include_router(invoice_management_router)
app.include_router(admin_analytics_router)
app.include_router(admin_activity_router)
app.include_router(admin_organizations_router)  # SPEC-005: Organization Admin Management API (US#663)
app.include_router(team_api_keys_router)
app.include_router(team_billing_portal_router)
app.include_router(partner_ecosystem_router)
app.include_router(standalone_teams_billing_router)
app.include_router(billing_engine_router)

# SPEC-147: Billing API (BILL-001, BILL-002, BILL-003)
try:
    from server.billing.api import router as spec147_billing_router  # noqa: E402

    app.include_router(spec147_billing_router)
    logger.info("✅ SPEC-147 billing API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 billing API router: {e}")

# SPEC-147: Stripe Integration API (BILL-004)
try:
    from server.billing.stripe_api import router as stripe_billing_router  # noqa: E402

    app.include_router(stripe_billing_router)
    logger.info("✅ SPEC-147 Stripe billing API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 Stripe billing API router: {e}")

# SPEC-147: Invoice Generation API (BILL-005)
try:
    from server.billing.invoice_api import (  # noqa: E402
        router as invoice_billing_router,
    )

    app.include_router(invoice_billing_router)

    # US#187: Advanced Tax Configuration API
    try:
        from server.billing.tax_config_api import (  # noqa: E402
            router as tax_config_router,
        )

        app.include_router(tax_config_router)
    except ImportError:
        logger.warning("Tax configuration API not available (optional feature)")
    logger.info("✅ SPEC-147 invoice generation API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 invoice generation API router: {e}")

# US-228: Customer Invoice Portal API (SPEC-028)
try:
    from server.billing.invoice_portal_api import (  # noqa: E402
        router as invoice_portal_router,
    )

    app.include_router(invoice_portal_router)
    logger.info("✅ US-228 Customer Invoice Portal API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register Customer Invoice Portal API router: {e}")

# US-231: Accounting System Export & Integration API (SPEC-028)
try:
    from server.billing.accounting_export_api import (  # noqa: E402
        router as accounting_export_router,
    )

    app.include_router(accounting_export_router)
    logger.info("✅ US-231 Accounting Export API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register Accounting Export API router: {e}")

# US-233: Custom Invoice Branding & Styling API (SPEC-028)
try:
    from server.billing.invoice_branding_api import (  # noqa: E402
        router as invoice_branding_router,
    )

    app.include_router(invoice_branding_router)
    logger.info("✅ US-233 Invoice Branding API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register Invoice Branding API router: {e}")

# SPEC-147: Billing Management API (BILL-015)
try:
    from server.billing.admin_api import router as billing_admin_router  # noqa: E402

    app.include_router(billing_admin_router)
    logger.info("✅ SPEC-147 billing management API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 billing management API router: {e}")

# SPEC-147: Payment Transfer API (BILL-006)
try:
    from server.billing.payment_transfer_api import (  # noqa: E402
        router as payment_transfer_router,
    )

    app.include_router(payment_transfer_router)
    logger.info("✅ SPEC-147 payment transfer API router registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 payment transfer API router: {e}")

# SPEC-147: Cost Tracking API (BILL-002)
try:
    from server.billing.cost_tracking_api import (  # noqa: E402
        router as cost_tracking_router,
    )

    app.include_router(cost_tracking_router)
    logger.info("✅ SPEC-147 cost tracking API router registered (BILL-002)")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-147 cost tracking API router: {e}")

# US#204: Team Billing APIs (SPEC-026 Phase 2)
from team_billing_api import router as team_billing_router  # noqa: E402

app.include_router(team_billing_router)

# SPEC-074: GDPR Compliance APIs (US#558)
# SPEC-011/US-121: HIPAA Compliance APIs
# Skip importing compliance routers in test mode to avoid model import conflicts
# Tests import routers directly and don't need them registered in main app
if not is_testing:
    from compliance.api import router as compliance_router  # noqa: E402

    app.include_router(compliance_router)

    from compliance.api_hipaa import router as hipaa_router  # noqa: E402

    app.include_router(hipaa_router)
app.include_router(macro_intelligence_router)
app.include_router(macro_context_linking_router)  # US#376: Macro-to-Memory Context Linking
app.include_router(macro_execution_router)  # US#375: Macro Replay System and Execution Engine
app.include_router(macro_plugin_router)  # US#374: Browser/IDE Plugin for Scoped Macro Capture
app.include_router(macro_visual_recording_router)  # US#1032: Visual/Replay-based Macro Recording
app.include_router(macro_implicit_detection_router)  # US#1033: Implicit Detection Macro Recording
app.include_router(graph_intelligence_integration_router)
app.include_router(graph_validation_router)
app.include_router(graph_usage_analytics_router)

# GRAPH-FED-001: Graph Schema Registry (US#984)
try:
    from routers.schema_registry_api import router as schema_registry_router

    app.include_router(schema_registry_router)
    logger.info("✅ Graph Schema Registry API router registered (US#984: GRAPH-FED-001)")
except ImportError as e:
    logger.warning(f"⚠️  Graph Schema Registry API not available: {e}")

# GRAPH-FED-003: Graph Query Router (US#988)
try:
    import sys
    from pathlib import Path

    federation_path = Path(__file__).parent.parent / "services" / "graph-federation" / "api"
    if str(federation_path) not in sys.path:
        sys.path.insert(0, str(federation_path.parent))
    from api.router import router as graph_query_router

    app.include_router(graph_query_router)
    logger.info("✅ Graph Query Router API registered (US#988: GRAPH-FED-003)")
except ImportError as e:
    logger.warning(f"⚠️  Graph Query Router API not available: {e}")

# GRAPH-FED-004: Graph Result Aggregator (US#989)
try:
    import sys
    from pathlib import Path

    federation_path = Path(__file__).parent.parent / "services" / "graph-federation" / "api"
    if str(federation_path) not in sys.path:
        sys.path.insert(0, str(federation_path.parent))
    from api.aggregator import router as graph_aggregator_router

    app.include_router(graph_aggregator_router)
    logger.info("✅ Graph Result Aggregator API registered (US#989: GRAPH-FED-004)")
except ImportError as e:
    logger.warning(f"⚠️  Graph Result Aggregator API not available: {e}")

# GRAPH-FED-005: Graph Federation Cache (US#990)
try:
    import sys
    from pathlib import Path

    federation_path = Path(__file__).parent.parent / "services" / "graph-federation" / "api"
    if str(federation_path) not in sys.path:
        sys.path.insert(0, str(federation_path.parent))
    from api.cache import router as graph_cache_router

    app.include_router(graph_cache_router)
    logger.info("✅ Graph Federation Cache API registered (US#990: GRAPH-FED-005)")
except ImportError as e:
    logger.warning(f"⚠️  Graph Federation Cache API not available: {e}")

# GRAPH-FED-002: Federation Query Engine (US#1006)
try:
    import sys
    from pathlib import Path

    federation_path = Path(__file__).parent.parent / "services" / "graph-federation" / "api"
    if str(federation_path) not in sys.path:
        sys.path.insert(0, str(federation_path.parent))
    from api.engine import router as graph_engine_router

    app.include_router(graph_engine_router)
    logger.info("✅ Federation Query Engine API registered (US#1006: GRAPH-FED-002)")
except ImportError as e:
    logger.warning(f"⚠️  Federation Query Engine API not available: {e}")

# GRAPH-FED-006: Context Bridge Integration (US#991)
try:
    import sys
    from pathlib import Path

    federation_path = Path(__file__).parent.parent / "services" / "graph-federation" / "api"
    if str(federation_path) not in sys.path:
        sys.path.insert(0, str(federation_path.parent))
    from api.context_bridge import router as context_bridge_router

    app.include_router(context_bridge_router)
    logger.info("✅ Context Bridge Integration API registered (US#991: GRAPH-FED-006)")
except ImportError as e:
    logger.warning(f"⚠️  Context Bridge Integration API not available: {e}")

# SPEC-127: Context Bridge System (US#841)
try:
    from routers.context_bridge_api import router as spec127_context_bridge_router

    app.include_router(spec127_context_bridge_router)
    logger.info("✅ SPEC-127 Context Bridge API registered (US#841: Phase 1)")
except ImportError as e:
    logger.warning(f"⚠️  SPEC-127 Context Bridge API not available: {e}")

# SPEC-128: Memory Transfer & Copy (US#846)
try:
    from routers.memory_transfer_api import router as spec128_memory_transfer_router

    app.include_router(spec128_memory_transfer_router)
    logger.info("✅ SPEC-128 Memory Transfer & Copy API registered (US#846: Phase 1)")
except ImportError as e:
    logger.warning(f"⚠️  SPEC-128 Memory Transfer & Copy API not available: {e}")

# SPEC-137: Agent Plan-Reflection Loop (DPPM Framework)
try:
    from server.routers.dppm_api import router as dppm_router  # noqa: E402

    app.include_router(dppm_router)
    logger.info("✅ SPEC-137 DPPM API registered (US#877: Phase 1 - Decomposition)")
except ImportError as e:
    logger.warning(f"⚠️  SPEC-137 DPPM API not available: {e}")

# SPEC-142: Offline Mode (Phase 1.1: Database Setup & Basic Operations)
try:
    from server.routers.offline_storage_api import (  # noqa: E402
        router as offline_storage_router,
    )

    app.include_router(offline_storage_router)
    logger.info("✅ SPEC-142 Offline Storage API registered (US#882: Phase 1.1)")
except ImportError as e:
    logger.warning(f"⚠️  SPEC-142 Offline Storage API not available: {e}")

# app.include_router(agentic_router)  # Temporarily disabled
# app.include_router(performance_router)  # Temporarily disabled serving

# SPEC-085: Staff Management System
try:
    from staff_auth_api import router as staff_auth_router  # noqa: E402
    from staff_management_api import router as staff_management_router  # noqa: E402

    app.include_router(staff_management_router)
    app.include_router(staff_auth_router)
    logger.info("✅ SPEC-085 staff management API routers registered")
except ImportError as e:
    logger.warning(f"⚠️  Could not register SPEC-085 staff management API routers: {e}")

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
