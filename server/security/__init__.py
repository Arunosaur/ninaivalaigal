"""
Ninaivalaigal Security Middleware Package

Comprehensive security middleware suite for the Ninaivalaigal platform
including Unicode normalization, compression handling, global log scrubbing,
RBAC enforcement, idempotency protection, and multipart redaction.
"""

from .utils.unicode_normalizer import normalize_unicode_for_detection, detect_evasion_attempt
from .middleware.compression_guard import CompressionGuardMiddleware, strict_compression_guard
from .logging.global_scrubber import GlobalLogScrubber, scrub_text, scrub_dict, install_global_scrubber
from .rbac.decorators import (
    require_permission, require_role, admin_required, authenticated_required,
    memory_read_required, memory_write_required, context_read_required, context_write_required
)
from .rbac.context import get_subject_ctx, resolve_jwt_claims, SubjectContext, Role
from .idempotency.middleware import IdempotencyMiddleware, memory_idempotency_middleware
from .multipart.starlette_adapter import scan_with_starlette
from .orm.tenancy_guard import (
    set_tenant_context, get_tenant_context, tenant_context, require_tenant_context,
    install_tenancy_guard, validate_tenant_access
)

__version__ = "1.0.0"
__all__ = [
    # Unicode normalization
    "normalize_unicode_for_detection",
    "detect_evasion_attempt",
    
    # Compression guard
    "CompressionGuardMiddleware",
    "strict_compression_guard",
    
    # Global log scrubbing
    "GlobalLogScrubber",
    "scrub_text",
    "scrub_dict",
    "install_global_scrubber",
    
    # RBAC
    "require_permission",
    "require_role",
    "admin_required",
    "authenticated_required",
    "memory_read_required",
    "memory_write_required",
    "context_read_required",
    "context_write_required",
    "get_subject_ctx",
    "resolve_jwt_claims",
    "SubjectContext",
    "Role",
    
    # Idempotency
    "IdempotencyMiddleware",
    "memory_idempotency_middleware",
    
    # Multipart processing
    "process_multipart_securely",
    "SecurityMultipartHandler",
    
    # ORM tenancy
    "set_tenant_context",
    "get_tenant_context",
    "tenant_context",
    "require_tenant_context",
    "install_tenancy_guard",
    "validate_tenant_access",
]
