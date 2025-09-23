"""
Modular FastAPI Application Entry Point
Refactored from monolithic main.py for better code organization

This addresses the external code review feedback:
- Break down monolithic files (main.py 1300+ lines → focused modules)
- Consolidate configuration into single source
- Improve code organization and maintainability
"""

import os

import structlog
import uvicorn
from approval_workflow import ApprovalWorkflowManager
from auto_recording import get_auto_recorder

# Configuration and core services
from config import get_database_url, load_config
from database import DatabaseManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Middleware and security
from observability import MetricsMiddleware, health_router, metrics_router
from performance_monitor import get_performance_monitor, start_performance_monitoring
from rate_limiting import rate_limit_middleware
from rbac_middleware import rbac_middleware
from redis_client import redis_client
from redis_queue import queue_manager
from security_integration import configure_security
from spec_kit import SpecKitContextManager

# Routers will be imported after app initialization to avoid import-time database connections

# Initialize logger
logger = structlog.get_logger(__name__)

# Load configuration
config = load_config()
database_url = get_database_url()

# Initialize core services
db_manager = DatabaseManager(database_url)
db = db_manager  # Alias for backward compatibility
spec_context_manager = SpecKitContextManager(db)
auto_recorder = get_auto_recorder(db_manager)
approval_manager = ApprovalWorkflowManager(db_manager)

# Performance monitoring
performance_monitor = get_performance_monitor()
start_performance_monitoring()

# Initialize FastAPI app
app = FastAPI(
    title="ninaivalaigal Memory Management API",
    description="Enterprise-grade AI memory management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(rbac_middleware)
app.add_middleware(MetricsMiddleware)

# Configure security
configure_security(app)


# Redis startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection and queue manager on startup"""
    try:
        await redis_client.ping()
        logger.info("Redis connection established")

        # Initialize queue manager
        await queue_manager.initialize()
        logger.info("Queue manager initialized")

    except Exception as e:
        logger.warning(f"Redis startup failed: {e}")
        # Don't fail startup if Redis is unavailable - graceful degradation


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection and queue manager on shutdown"""
    try:
        await queue_manager.close()
        await redis_client.close()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.warning(f"Redis shutdown error: {e}")


# Include routers
app.include_router(health_router)
app.include_router(metrics_router)

from ai_feedback_api import router as ai_feedback_router
from billing_console_api import router as billing_console_router
from early_adopter_api import router as early_adopter_router
from invoice_management_api import router as invoice_management_router
from admin_analytics_api import router as admin_analytics_router
from enhanced_signup_api import router as enhanced_signup_router
from memory_injection_api import router as memory_injection_router
from memory_suggestions_api import router as memory_suggestions_router
from team_api_keys_api import router as team_api_keys_router
from team_billing_portal_api import router as team_billing_portal_router
from partner_ecosystem_api import router as partner_ecosystem_router
from standalone_teams_billing_api import router as standalone_teams_billing_router
from billing_engine_integration_api import router as billing_engine_router
from unified_macro_intelligence_api import router as macro_intelligence_router
from graph_intelligence_integration_api import router as graph_intelligence_integration_router
from graph_validation_checklist import router as graph_validation_router
from graph_usage_analytics import router as graph_usage_analytics_router

# Temporarily disabled for production stability
# from agentic_api import router as agentic_router
# from performance_api import router as performance_router
from routers.approvals import router as approvals_router
from routers.contexts import router as contexts_router
from routers.memory import router as memory_router
from routers.organizations import router as organizations_router
from routers.recording import router as recording_router
from routers.teams import router as teams_router
from routers.users import router as users_router

# Import routers after app initialization to avoid import-time database connections
from signup_api import router as signup_router
from standalone_teams_api import router as standalone_teams_router
from usage_analytics_api import router as usage_analytics_router
from vendor_admin_api import router as vendor_admin_router

app.include_router(signup_router)
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
@app.get("/")
def serve_signup():
    """Serve signup page as default"""
    return FileResponse(os.path.join(frontend_dir, "signup.html"))


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
    uvicorn.run(
        "main_modular:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
