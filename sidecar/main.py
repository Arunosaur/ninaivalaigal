import hashlib
import hmac
import logging
import os
import time
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    # example; adapt to your actual mem0 usage
    from mem0 import MemoryClient  # or MemoryStore depending on API
except Exception:  # pragma: no cover
    MemoryClient = object  # stub to avoid import errors during scaffolding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="mem0 Sidecar API",
    description="Authenticated mem0 memory service sidecar",
    version="1.0.0"
)

# Authentication configuration
MEMORY_SHARED_SECRET = os.getenv("MEMORY_SHARED_SECRET")
if not MEMORY_SHARED_SECRET:
    logger.warning("MEMORY_SHARED_SECRET not set - authentication disabled")

security = HTTPBearer(auto_error=False)

def verify_shared_secret(authorization: HTTPAuthorizationCredentials | None = Depends(security)):
    """Verify shared secret authentication"""
    if not MEMORY_SHARED_SECRET:
        # Authentication disabled if no secret configured
        return True

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.credentials

    # Simple shared secret verification
    if token == MEMORY_SHARED_SECRET:
        return True

    # HMAC-based verification (more secure)
    try:
        # Expected format: timestamp:signature
        if ":" in token:
            timestamp_str, signature = token.split(":", 1)
            timestamp = int(timestamp_str)

            # Check timestamp (5 minute window)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:  # 5 minutes
                raise HTTPException(
                    status_code=401,
                    detail="Token expired"
                )

            # Verify HMAC signature
            expected_signature = hmac.new(
                MEMORY_SHARED_SECRET.encode(),
                timestamp_str.encode(),
                hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                return True
    except (ValueError, TypeError):
        pass

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

def get_user_context(
    x_user_id: str | None = Header(None),
    x_team_id: str | None = Header(None),
    x_org_id: str | None = Header(None)
) -> dict[str, Any]:
    """Extract user context from headers"""
    return {
        "user_id": x_user_id,
        "team_id": x_team_id,
        "org_id": x_org_id
    }

client = MemoryClient() if isinstance(MemoryClient, type) else None

@app.get("/health")
def health():
    """Health check endpoint - no authentication required"""
    auth_status = "enabled" if MEMORY_SHARED_SECRET else "disabled"
    return {
        "status": "ok",
        "authentication": auth_status,
        "version": "1.0.0"
    }

@app.post("/remember")
def remember(
    text: str = Body(..., embed=True),
    metadata: dict[str, Any] | None = None,
    auth: bool = Depends(verify_shared_secret),
    context: dict[str, Any] = Depends(get_user_context)
):
    """Store memory with authentication and user context"""
    logger.info(f"Remember request from user_id={context.get('user_id')}")

    # Add context to metadata
    if metadata is None:
        metadata = {}

    metadata.update({
        "user_id": context.get("user_id"),
        "team_id": context.get("team_id"),
        "org_id": context.get("org_id"),
        "timestamp": int(time.time())
    })

    # TODO: wire org/team/user scoping in headers or body as you choose
    # return client.add(text=text, metadata=metadata)
    return {
        "ok": True,
        "id": f"mem_{int(time.time())}",
        "context": context,
        "metadata": metadata
    }

@app.get("/recall")
def recall(
    q: str,
    k: int = 5,
    auth: bool = Depends(verify_shared_secret),
    context: dict[str, Any] = Depends(get_user_context)
):
    """Recall memories with authentication and user context filtering"""
    logger.info(f"Recall request from user_id={context.get('user_id')}, query='{q}'")

    # TODO: Filter by user context in actual implementation
    # return client.search(query=q, k=k, filters={"user_id": context.get("user_id")})
    return {
        "ok": True,
        "query": q,
        "context": context,
        "items": []  # stub until wired
    }

@app.delete("/memories/{mid}")
def delete(
    mid: str,
    auth: bool = Depends(verify_shared_secret),
    context: dict[str, Any] = Depends(get_user_context)
):
    """Delete memory with authentication and ownership verification"""
    logger.info(f"Delete request from user_id={context.get('user_id')}, memory_id={mid}")

    # TODO: Verify ownership before deletion in actual implementation
    # memory = client.get(id=mid)
    # if memory.metadata.get("user_id") != context.get("user_id"):
    #     raise HTTPException(403, "Not authorized to delete this memory")
    # client.delete(id=mid)

    return {
        "ok": True,
        "deleted": mid,
        "context": context
    }

@app.get("/memories")
def list_memories(
    limit: int = 10,
    offset: int = 0,
    auth: bool = Depends(verify_shared_secret),
    context: dict[str, Any] = Depends(get_user_context)
):
    """List user's memories with pagination"""
    logger.info(f"List memories request from user_id={context.get('user_id')}")

    # TODO: Implement actual memory listing with user filtering
    return {
        "ok": True,
        "context": context,
        "memories": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }

@app.get("/auth/test")
def test_auth(
    auth: bool = Depends(verify_shared_secret),
    context: dict[str, Any] = Depends(get_user_context)
):
    """Test authentication endpoint"""
    return {
        "authenticated": True,
        "context": context,
        "message": "Authentication successful"
    }
