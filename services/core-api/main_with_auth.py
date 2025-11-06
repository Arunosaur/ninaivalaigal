#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Core API Service - Day 2: User Signup Working!
Includes database connection and user registration
"""

import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from starlette.middleware.base import BaseHTTPMiddleware

# Import models from shared contracts (SPEC-100 Task #79)
from auth.v1.models import UserLogin

# Add shared to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Set environment defaults ONLY if not already set (for local dev)
# In container, these come from docker-compose environment variables
os.environ.setdefault("NINA_ENV", "dev")
os.environ.setdefault("NINA_DB_USER", "nina")
os.environ.setdefault("NINA_DB_PASSWORD", "dev_password_change_in_production")
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "dev_jwt_secret_change_in_production")
os.environ.setdefault("NINA_JWT_SECRET", "dev_jwt_secret_change_in_production")

from database import DatabaseManager  # noqa: E402
from lib.auth_audit import (  # noqa: E402
    log_login_attempt,
    log_rate_limit_exceeded,
    log_signup_attempt,
)
from routers import health as health_router  # noqa: E402
from routers import metrics as metrics_router  # noqa: E402
from sqlalchemy import text  # noqa: E402

from utils.auth import hash_password, verify_password  # noqa: E402
from utils.config import get_dynamic_database_url  # noqa: E402
from utils.login_security import (  # noqa: E402
    clear_failed_attempts,
    is_account_locked,
    record_failed_attempt,
)

# Get database URL dynamically (resolves PgBouncer IP automatically)
DATABASE_URL = get_dynamic_database_url()

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


from utils.rate_limiting import AuthRateLimiter  # noqa: E402

# Global rate limiter instance
auth_rate_limiter = AuthRateLimiter()


# Pydantic models
class UserSignup(BaseModel):
    """User signup request"""

    email: EmailStr
    password: str
    name: str
    """User login request"""

    email: EmailStr
    password: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan for database connection"""
    logger.info("🚀 Starting Core API Service with Database...")

    try:
        db_manager = DatabaseManager(DATABASE_URL)
        app.state.db = db_manager
        logger.info(f"✅ Database connected: {DATABASE_URL[:50]}...")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning("⚠️  Running without database (health checks only)")
        app.state.db = None

    yield

    logger.info("🛑 Shutting down Core API Service...")


# Create FastAPI app
app = FastAPI(
    title="Core API Service", version="1.0.0", description="User authentication and management", lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# US-91: API Rate Limiting Middleware
try:
    from middleware.api_rate_limit_middleware import APIRateLimitMiddleware

    app.add_middleware(APIRateLimitMiddleware)
    logger.info("✅ API Rate Limiting Middleware enabled (US-91)")
except Exception as e:
    logger.warning(f"⚠️  Could not enable API Rate Limiting Middleware: {e}")

# Include SPEC-100 compliant routers
app.include_router(health_router.router)
app.include_router(metrics_router.router)


@app.post("/auth/signup")
async def signup(user_data: UserSignup, request: Request) -> dict[str, Any]:
    """
    User signup endpoint - Day 2 Goal!
    Creates a new user account

    SPEC-114: Rate limited to 3 attempts per 10 minutes per IP
    """
    logger.info(f"📝 Signup request for: {user_data.email}")

    if not app.state.db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Rate limiting check (SPEC-114: 3 attempts per 10 minutes)
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or (request.client.host if request.client else "unknown")
    )
    rate_limit_key = f"{client_ip}:{user_data.email}"
    is_allowed, error_msg, rate_info = auth_rate_limiter.is_allowed(rate_limit_key, endpoint="signup")

    if not is_allowed:
        logger.warning(f"❌ Signup rate limit exceeded: {user_data.email} from {client_ip}")
        await log_rate_limit_exceeded(request, "signup", rate_limit_key)
        raise HTTPException(
            status_code=429,
            detail=error_msg or "Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                "Retry-After": str(rate_info["retry_after"]),
            },
        )

    try:
        session = app.state.db.get_session()

        # Check if user exists
        existing_user = session.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": user_data.email}
        ).fetchone()

        if existing_user:
            await log_signup_attempt(request, user_data.email, success=False, error_reason="user_already_exists")
            raise HTTPException(status_code=400, detail="User already exists")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Insert user
        result = session.execute(
            text(
                """
            INSERT INTO users (email, password_hash, name, account_type, created_at)
            VALUES (:email, :password_hash, :name, :account_type, :created_at)
            RETURNING id, email, name, account_type, created_at
            """
            ),
            {
                "email": user_data.email,
                "password_hash": password_hash,
                "name": user_data.name,
                "account_type": user_data.account_type,
                "created_at": datetime.utcnow(),
            },
        )
        session.commit()

        user = result.fetchone()
        session.close()

        # Generate JWT token
        token_data = {"user_id": str(user.id), "email": user.email, "exp": datetime.utcnow() + timedelta(hours=168)}
        jwt_token = jwt.encode(token_data, os.getenv("NINAIVALAIGAL_JWT_SECRET"), algorithm="HS256")

        logger.info(f"✅ User created: {user.email}")

        # Audit log successful signup
        await log_signup_attempt(request, user_data.email, success=True, user_id=str(user.id))

        return {
            "success": True,
            "message": "User created successfully!",
            "user": {"id": str(user.id), "email": user.email, "name": user.name, "account_type": user.account_type},
            "jwt_token": jwt_token,
            "token_type": "Bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Signup failed: {e}")
        await log_signup_attempt(request, user_data.email, success=False, error_reason=str(e))
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@app.post("/auth/login")
async def login(login_data: UserLogin, request: Request) -> dict[str, Any]:
    """
    User login endpoint with enhanced security features
    - Password verification with bcrypt
    - Account lockout after failed attempts
    - Failed attempt tracking and audit logging
    - JWT token generation on success
    - SPEC-114: Rate limited to 5 attempts per 15 minutes
    """
    logger.info(f"🔐 Login request for: {login_data.email}")

    if not app.state.db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Rate limiting check (SPEC-114: 5 attempts per 15 minutes)
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or (request.client.host if request.client else "unknown")
    )
    rate_limit_key = f"{client_ip}:{login_data.email}"
    is_allowed, error_msg, rate_info = auth_rate_limiter.is_allowed(rate_limit_key, endpoint="login")

    if not is_allowed:
        logger.warning(f"❌ Login rate limit exceeded: {login_data.email} from {client_ip}")
        await log_rate_limit_exceeded(request, "login", rate_limit_key)
        raise HTTPException(
            status_code=429,
            detail=error_msg or "Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                "Retry-After": str(rate_info["retry_after"]),
            },
        )

    # Check if account is locked
    is_locked, lock_until = is_account_locked(login_data.email)
    if is_locked:
        logger.warning(f"❌ Login blocked: account locked for {login_data.email}", lock_until=lock_until)
        raise HTTPException(
            status_code=423,
            detail=f"Account temporarily locked due to multiple failed login attempts. Please try again later.",
        )

    try:
        session = app.state.db.get_session()

        # Get user
        user = session.execute(
            text("SELECT id, email, name, password_hash, account_type FROM users WHERE email = :email"),
            {"email": login_data.email},
        ).fetchone()

        if not user:
            # Record failed attempt (even for non-existent users to prevent enumeration)
            record_failed_attempt(login_data.email)
            logger.warning(f"❌ Login failed: user not found: {login_data.email}")
            await log_login_attempt(request, login_data.email, success=False, error_reason="user_not_found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password with bcrypt
        if not verify_password(login_data.password, user.password_hash):
            # Record failed attempt
            record_failed_attempt(login_data.email)
            logger.warning(f"❌ Login failed: invalid password: {login_data.email}", user_id=str(user.id))
            await log_login_attempt(
                request, login_data.email, success=False, user_id=str(user.id), error_reason="invalid_password"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Successful login - clear failed attempts
        clear_failed_attempts(login_data.email)
        logger.info(f"✅ Password verified for: {login_data.email}")

        # Generate JWT token
        token_data = {"user_id": str(user.id), "email": user.email, "exp": datetime.utcnow() + timedelta(hours=168)}
        jwt_token = jwt.encode(token_data, os.getenv("NINAIVALAIGAL_JWT_SECRET"), algorithm="HS256")

        logger.info(f"✅ Login successful: {user.email}", user_id=str(user.id), account_type=user.account_type)

        # Audit log successful login
        await log_login_attempt(request, login_data.email, success=True, user_id=str(user.id))

        return {
            "success": True,
            "message": "Login successful!",
            "user": {"id": str(user.id), "email": user.email, "name": user.name},
            "jwt_token": jwt_token,
            "token_type": "Bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}", email=login_data.email, error=str(e))
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))  # Use 8001 to avoid conflict
    print("=" * 60)
    print("🚀 CORE API SERVICE - DAY 2: USER SIGNUP!")
    print("=" * 60)
    print(f"📍 Health: http://localhost:{port}/health")
    print(f"📍 Ready:  http://localhost:{port}/ready")
    print(f"📍 Metrics: http://localhost:{port}/metrics")
    print(f"📍 Signup: http://localhost:{port}/auth/signup")
    print(f"📍 Login:  http://localhost:{port}/auth/login")
    print(f"📊 Database: {DATABASE_URL[:50]}...")
    print("=" * 60)

    uvicorn.run("main_with_auth:app", host="0.0.0.0", port=port, reload=True)
