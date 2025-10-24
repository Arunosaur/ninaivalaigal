#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Core API Service - Simplified version for Day 2 testing
Minimal working service to verify user signup flow
"""

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add shared to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Set required environment variables with defaults for testing
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test-secret-key-for-development-only")  # pragma: allowlist secret
os.environ.setdefault(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/ninaivalaigal"  # pragma: allowlist secret
)

# Create FastAPI app
app = FastAPI(
    title="Core API Service", version="1.0.0", description="Authentication, users, teams, and organization management"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "1.0.0",
        "endpoints": ["/health", "/auth/signup", "/auth/login"],
    }


# Simple echo endpoint for testing
@app.get("/echo")
async def echo(message: str = "hello"):
    """Echo endpoint for testing"""
    return {"echo": message, "service": "core-api"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting Core API Service on port {port}...")
    print(f"📍 Health: http://localhost:{port}/health")
    print(f"📍 Echo: http://localhost:{port}/echo?message=test")

    uvicorn.run("main_simple:app", host="0.0.0.0", port=port, reload=True)
