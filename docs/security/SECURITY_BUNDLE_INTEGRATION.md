# Security Bundle Integration Guide

## Overview
The `SecurityBundle` provides a comprehensive, production-ready security middleware stack that addresses all P0 and P1 security requirements identified in the external code review.

## Quick Start

### Production Deployment
```python
from fastapi import FastAPI
from server.security.bundle import SecurityBundle
from server.security.idempotency.redis_store import RedisKeyStore
import redis.asyncio as redis

app = FastAPI()

# Redis-backed idempotency for multi-instance safety
redis_store = RedisKeyStore(redis.from_url("redis://localhost:6379/0"), ttl_seconds=24*3600)

SecurityBundle.apply(
    app,
    subject_ctx_provider=my_jwt_ctx_provider,  # your verified JWT resolver
    idempotency_store=redis_store,
    fail_closed_tier_threshold=3,
    enable_multipart_adapter=True,
)
```

### Development Setup
```python
from server.security.bundle import apply_development_security

app = FastAPI()
apply_development_security(app)  # Memory store, lenient policies
```

## Security Components Included

### 1. Content-Type Guard
- **Size limits**: Configurable max body size (10MB default)
- **Allowlist**: Only permitted content types (`text/*`, `application/json`, `application/x-www-form-urlencoded`)
- **Rejection policy**: 415 Unsupported Media Type for disallowed types

### 2. Compression Guard
- **Bypass prevention**: Rejects compressed requests that could bypass redaction
- **Strict mode**: No compressed encodings allowed by default
- **Response safety**: Forces chunked encoding after redaction

### 3. Idempotency Protection
- **Redis support**: Multi-instance consistency with TTL and status tracking
- **Memory fallback**: In-memory store for development
- **Replay protection**: Cached responses for duplicate requests

### 4. Request/Response Redaction
- **Unicode normalization**: NFKC + homoglyph + zero-width prevention
- **Pattern detection**: AWS keys, JWT tokens, high-entropy strings
- **Streaming support**: Memory-efficient processing with overlap handling
- **Fail-closed policy**: Tier ≥ 3 fails securely on detector errors

### 5. Multipart Security
- **Stream-aware**: Memory-efficient multipart processing
- **Text redaction**: Automatic secret detection in text parts
- **Binary policy**: Configurable binary upload handling (rejected by default)
- **Size limits**: Per-part and total size enforcement

### 6. RBAC Integration
- **Injectable context**: Custom JWT resolver via `subject_ctx_provider`
- **FastAPI integration**: Available on `app.state.subject_ctx_provider`
- **Decorator compatibility**: Works with `@require_permission` decorators

### 7. Global Log Scrubbing
- **Automatic installation**: Wraps all loggers with secret detection
- **Structured data**: Handles nested dictionaries and JSON
- **OpenTelemetry**: Span attribute scrubbing

### 8. Security Headers
- **OWASP compliance**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **Referrer policy**: Strict origin when cross-origin
- **Bundle identification**: X-Security-Bundle header for monitoring

## Configuration Options

### Core Parameters
```python
SecurityBundle.apply(
    app,
    # RBAC Integration
    subject_ctx_provider=my_jwt_resolver,           # Injectable JWT context provider

    # Content Filtering
    allowed_prefixes=("text/", "application/json"), # Permitted content types
    max_body_bytes=10 * 1024 * 1024,               # 10MB request size limit
    reject_disallowed=True,                         # Strict content-type enforcement

    # Idempotency
    idempotency_store=redis_store,                  # Redis for multi-instance safety

    # Redaction Policy
    redact_overlap=64,                              # Overlap bytes for streaming
    fail_closed_tier_threshold=3,                   # Tier ≥ 3 fails closed on errors

    # Feature Toggles
    enable_multipart_adapter=True,                  # Multipart security processing
    enable_compression_guard=True,                  # Compression bypass prevention
    enable_global_scrubbing=True,                   # Log secret scrubbing
)
```

### Tier-Based Fail-Closed Policy
- **Tier 1-2**: Best-effort redaction, continues on detector errors
- **Tier 3+**: Fail-closed, returns 4xx on detector failures
- **Configurable threshold**: Adjust `fail_closed_tier_threshold` per environment

## Integration with Existing Code

### FastAPI Dependencies
```python
from fastapi import Depends, Request

def get_subject_context(request: Request):
    """Extract subject context using injected provider."""
    provider = request.app.state.subject_ctx_provider
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    return provider(token)

@app.get("/memories")
async def get_memories(ctx: dict = Depends(get_subject_context)):
    # ctx contains user_id, role, org_id, etc.
    pass
```

### RBAC Decorators
```python
from server.security import require_permission, Permission, Resource

@require_permission(Permission.READ, Resource.MEMORY)
async def read_memory(user_role: str, user_id: str):
    # Automatically enforced by decorator
    pass
```

### Multipart Processing
```python
@app.post("/upload")
async def upload_file(request: Request):
    # Processed multipart data available on request.state
    if hasattr(request.state, 'processed_multipart'):
        safe_data = request.state.processed_multipart
        # All text parts have been redacted, binary parts rejected
```

## Monitoring and Observability

### Security Headers
All responses include security bundle identification:
```
X-Security-Bundle: ninaivalaigal-v1.0
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

### Audit Logging
- **RBAC decisions**: All access grants/denials logged
- **Redaction events**: Secret detection and redaction logged
- **Policy violations**: Content-type, size limit violations logged
- **Detector failures**: Tier-based failure handling logged

### Metrics Integration
```python
# Add custom metrics middleware after SecurityBundle
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Track security events, redaction counts, etc.
    response = await call_next(request)
    return response
```

## Performance Considerations

### Memory Usage
- **Streaming processing**: Large payloads handled efficiently
- **Overlap buffering**: Configurable overlap size (64 bytes default)
- **Redis connection pooling**: Async Redis client with connection reuse

### Latency Impact
- **Content-type check**: ~0.1ms overhead
- **Unicode normalization**: ~1-2ms for typical payloads
- **Pattern matching**: ~2-5ms depending on content size
- **Redis roundtrip**: ~1-3ms for idempotency checks

### Throughput
- **Concurrent processing**: Async middleware stack
- **Non-blocking I/O**: Redis operations don't block request processing
- **Configurable limits**: Tune size limits based on infrastructure

## Security Compliance

### OWASP Alignment
- ✅ **Input Validation**: Content-type and size limits
- ✅ **Authentication**: Injectable JWT context provider
- ✅ **Authorization**: RBAC decorator integration
- ✅ **Data Protection**: Comprehensive secret redaction
- ✅ **Logging**: Audit trail with secret scrubbing
- ✅ **Error Handling**: Fail-closed policies for high tiers

### Enterprise Requirements
- ✅ **Multi-tenant isolation**: ORM tenancy guard integration
- ✅ **Audit compliance**: Comprehensive logging and monitoring
- ✅ **Secret management**: Detection and redaction across all layers
- ✅ **Performance**: Production-ready with configurable limits

## Deployment Checklist

### Pre-deployment
- [ ] Configure Redis URL for idempotency store
- [ ] Set up JWT secret and verification
- [ ] Configure content-type allowlist for your APIs
- [ ] Set appropriate tier thresholds
- [ ] Test multipart upload policies

### Post-deployment
- [ ] Monitor security headers in responses
- [ ] Verify RBAC audit logs
- [ ] Check redaction effectiveness in logs
- [ ] Monitor Redis idempotency metrics
- [ ] Validate fail-closed behavior for high tiers

## Troubleshooting

### Common Issues
1. **JWT verification failures**: Check `NINAIVALAIGAL_JWT_SECRET` environment variable
2. **Redis connection errors**: Verify Redis URL and connectivity
3. **Content-type rejections**: Review allowlist configuration
4. **Multipart processing failures**: Check size limits and binary policies
5. **Detector failures**: Monitor tier-based fail-closed behavior

### Debug Mode
```python
import logging
logging.getLogger("security.bundle").setLevel(logging.DEBUG)
logging.getLogger("rbac.audit").setLevel(logging.DEBUG)
```

The SecurityBundle provides enterprise-grade security with minimal configuration while maintaining flexibility for different deployment environments.
