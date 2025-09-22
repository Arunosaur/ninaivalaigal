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

from routers.approvals import router as approvals_router
from routers.contexts import router as contexts_router
from routers.memory import router as memory_router
from routers.organizations import router as organizations_router
from routers.recording import router as recording_router
from routers.teams import router as teams_router
from routers.users import router as users_router

# Import routers after app initialization to avoid import-time database connections
from signup_api import router as signup_router

app.include_router(signup_router)
app.include_router(organizations_router)
app.include_router(teams_router)
app.include_router(users_router)
app.include_router(contexts_router)
app.include_router(memory_router)
app.include_router(approvals_router)
app.include_router(recording_router)

# Static file serving
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


# Health check endpoint (simple version, detailed version in health_router)
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "ninaivalaigal"}


if __name__ == "__main__":
    uvicorn.run(
        "main_modular:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
