#!/usr/bin/env python3
"""
Core API Service - Authentication, Users, Teams, Organizations
Extracted from monolithic server for SPEC-100 Stage 3 microservices architecture
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add shared and parent directories to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))
sys.path.insert(0, str(current_dir.parent.parent / "server"))

from database.database import DatabaseManager
from utils.config import load_config

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

# Load configuration
config = load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan for proper startup/shutdown"""
    logger.info("🚀 Starting Core API Service...")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL") or load_config()
    if isinstance(database_url, dict):
        database_url = database_url.get('storage', {}).get('database_url', 'postgresql://user:password@localhost:5432/ninaivalaigal')
    logger.info(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        db_manager = DatabaseManager(database_url)
        app.state.db_manager = db_manager
        app.state.db = db_manager
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    logger.info("✅ Core API Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Core API Service...")


# Create FastAPI app
app = FastAPI(
    title="Core API Service",
    version="1.0.0",
    description="Authentication, users, teams, and organization management",
    lifespan=lifespan
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
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "1.0.0"
    }


# Import and include routers
from routers.auth import router as auth_router
from routers.signup_api import router as signup_router
from routers.protected_routes import router as protected_router
from routers.users import router as users_router
from routers.teams import router as teams_router
from routers.organizations import router as organizations_router

app.include_router(signup_router, prefix="/auth", tags=["auth"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(protected_router, tags=["protected"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(teams_router, prefix="/teams", tags=["teams"])
app.include_router(organizations_router, prefix="/organizations", tags=["organizations"])


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
