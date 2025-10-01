#!/usr/bin/env python3
"""
Minimal FastAPI server for ninaivalaigal development
Tests Redis connectivity and provides basic health endpoints
"""

import os
import sys
from typing import Any, Dict

import redis
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
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

# Initialize FastAPI
app = FastAPI(
    title="ninaivalaigal Minimal API",
    description="Minimal API for testing Redis connectivity and basic health",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Redis configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", "secure_nina_password"),
    "db": int(os.getenv("REDIS_DB", "0")),
    "decode_responses": True,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
}

# Global Redis client
redis_client = None


class HealthResponse(BaseModel):
    status: str
    redis: Dict[str, Any]
    environment: Dict[str, str]


def get_redis_client() -> redis.Redis:
    """Get Redis client with unified password authentication."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(**REDIS_CONFIG)
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established", config=REDIS_CONFIG)
        except Exception as e:
            logger.error(
                "Failed to connect to Redis", error=str(e), config=REDIS_CONFIG
            )
            raise HTTPException(status_code=503, detail=f"Redis connection failed: {e}")
    return redis_client


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting ninaivalaigal minimal API")
    try:
        # Test Redis connection
        client = get_redis_client()
        client.set("startup_test", "success")
        result = client.get("startup_test")
        client.delete("startup_test")
        logger.info("Redis startup test successful", result=result)
    except Exception as e:
        logger.error("Startup Redis test failed", error=str(e))
        # Don't fail startup, but log the issue


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ninaivalaigal minimal API", "status": "running"}


@app.get("/health")
async def health():
    """Basic health check."""
    return {"status": "ok"}


@app.get("/health/detailed", response_model=HealthResponse)
async def detailed_health():
    """Detailed health check including Redis."""
    redis_status = {"status": "unknown", "error": None}

    try:
        client = get_redis_client()

        # Test basic operations
        client.ping()
        client.set("health_test", "working")
        test_value = client.get("health_test")
        client.delete("health_test")

        # Get Redis info
        info = client.info()

        redis_status = {
            "status": "healthy",
            "ping": "PONG",
            "test_value": test_value,
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
        }

    except Exception as e:
        redis_status = {"status": "unhealthy", "error": str(e)}
        logger.error("Redis health check failed", error=str(e))

    return HealthResponse(
        status="ok" if redis_status["status"] == "healthy" else "degraded",
        redis=redis_status,
        environment={
            "redis_host": REDIS_CONFIG["host"],
            "redis_port": str(REDIS_CONFIG["port"]),
            "redis_db": str(REDIS_CONFIG["db"]),
        },
    )


@app.get("/redis/test")
async def redis_test():
    """Test Redis operations."""
    try:
        client = get_redis_client()

        # Test various operations
        operations = {}

        # String operations
        client.set("test:string", "hello_world")
        operations["string_set_get"] = client.get("test:string")
        client.delete("test:string")

        # Hash operations
        client.hset("test:hash", "field1", "value1")
        client.hset("test:hash", "field2", "value2")
        operations["hash_operations"] = client.hgetall("test:hash")
        client.delete("test:hash")

        # List operations
        client.lpush("test:list", "item1", "item2", "item3")
        operations["list_operations"] = client.lrange("test:list", 0, -1)
        client.delete("test:list")

        # Set operations
        client.sadd("test:set", "member1", "member2", "member3")
        operations["set_operations"] = list(client.smembers("test:set"))
        client.delete("test:set")

        return {
            "status": "success",
            "operations": operations,
            "message": "All Redis operations completed successfully",
        }

    except Exception as e:
        logger.error("Redis test failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Redis test failed: {e}")


if __name__ == "__main__":
    logger.info("Starting minimal server", config=REDIS_CONFIG)
    uvicorn.run(
        "run_server_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
