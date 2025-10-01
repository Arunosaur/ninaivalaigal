"""
API Exposure Configuration

Defines which API endpoints are exposed to different user roles.
Implements defense-in-depth by controlling documentation visibility.
"""

from rbac.permissions import Role

# Public contract - minimal endpoints safe for external/unauthenticated users
# These are the ONLY endpoints that should appear in public documentation
PUBLIC_TAGS = {
    "auth",  # signup, login, password reset (no admin scopes)
    "health",  # basic health check and status
}

# Role-based tag allowlists for documentation filtering
# Users only see endpoints they're actually allowed to call
DOCS_TAG_ALLOWLIST: dict[str, set[str]] = {
    # Anonymous/public - static docs only, no interactive Swagger
    "public": set(),  # Empty - no Swagger access without auth
    # External authenticated users (VIEWER role)
    "external": {
        "auth",
        "health",
        "memory-public",  # tokenize, recall (safe operations)
    },
    # Team members (MEMBER, MAINTAINER roles)
    "member": {
        "auth",
        "health",
        "memory-public",
        "memory",  # full memory CRUD
        "context",  # context management
        "teams",  # team operations
    },
    # Administrators (ADMIN role)
    "admin": {
        "auth",
        "health",
        "memory-public",
        "memory",
        "context",
        "teams",
        "organizations",
        "users",
        "admin",  # admin-specific operations
        "analytics",  # usage analytics
    },
    # Staff/internal (OWNER, SYSTEM roles)
    "staff": {
        "auth",
        "health",
        "memory-public",
        "memory",
        "context",
        "teams",
        "organizations",
        "users",
        "admin",
        "analytics",
        "metrics",  # system metrics
        "ops",  # operational endpoints
        "billing",  # billing and subscriptions
        "audit",  # audit logs
        "queue",  # queue management
        "preload",  # memory preloading
        "session",  # session management
    },
}


def get_allowed_tags_for_role(role: Role | None) -> set[str]:
    """
    Get the set of allowed documentation tags for a given role.

    Args:
        role: User's RBAC role, or None for unauthenticated

    Returns:
        Set of tag names the user is allowed to see in documentation
    """
    if role is None:
        return DOCS_TAG_ALLOWLIST["public"].copy()

    # Map RBAC roles to documentation access levels
    role_mapping: dict[Role, str] = {
        Role.VIEWER: "external",
        Role.MEMBER: "member",
        Role.MAINTAINER: "member",
        Role.ADMIN: "admin",
        Role.OWNER: "staff",
        Role.SYSTEM: "staff",
    }

    access_level = role_mapping.get(role, "external")
    return DOCS_TAG_ALLOWLIST[access_level].copy()


def is_public_endpoint(tags: list[str] | None) -> bool:
    """
    Check if an endpoint should be in the public contract.

    Args:
        tags: List of tags associated with the endpoint

    Returns:
        True if endpoint is part of public contract
    """
    if not tags:
        return False

    return any(tag in PUBLIC_TAGS for tag in tags)


# Validation: ensure tag sets are properly nested
def _validate_tag_hierarchy():
    """Validate that tag allowlists follow proper hierarchy."""
    levels = ["public", "external", "member", "admin", "staff"]

    for i in range(len(levels) - 1):
        current = DOCS_TAG_ALLOWLIST[levels[i]]
        next_level = DOCS_TAG_ALLOWLIST[levels[i + 1]]

        # Each level should be a subset of the next
        if not current.issubset(next_level):
            extra = current - next_level
            raise ValueError(
                f"Tag hierarchy violation: {levels[i]} has tags not in "
                f"{levels[i + 1]}: {extra}"
            )


# Run validation on import
_validate_tag_hierarchy()
