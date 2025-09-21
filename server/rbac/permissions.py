from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Role(Enum):
    VIEWER = auto()  # Read-only access
    MEMBER = auto()  # Basic user permissions
    MAINTAINER = auto()  # Advanced user permissions
    ADMIN = auto()  # Administrative permissions
    OWNER = auto()  # Full access
    SYSTEM = auto()  # System-level operations


class Action(Enum):
    READ = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    SHARE = auto()
    EXPORT = auto()
    ADMINISTER = auto()
    # New actions for enhanced RBAC
    INVITE = auto()  # Invite users
    APPROVE = auto()  # Approve requests
    BACKUP = auto()  # Create backups
    RESTORE = auto()  # Restore data
    CONFIGURE = auto()  # System configuration
    AUDIT = auto()  # Access audit logs


class Resource(Enum):
    MEMORY = auto()
    CONTEXT = auto()
    TEAM = auto()
    ORG = auto()
    AUDIT = auto()
    # New resources for enhanced RBAC
    USER = auto()  # User management
    INVITATION = auto()  # Invitation management
    BACKUP = auto()  # Backup operations
    SYSTEM = auto()  # System administration
    API = auto()  # API access control


ROLE_PRECEDENCE = [
    Role.VIEWER,
    Role.MEMBER,
    Role.MAINTAINER,
    Role.ADMIN,
    Role.OWNER,
    Role.SYSTEM,
]

POLICY: dict[tuple[Role, Resource], set[Action]] = {}


def allow(role: Role, res: Resource, *actions: Action):
    POLICY.setdefault((role, res), set()).update(actions)


# SYSTEM role has all permissions (for automated processes)
for r in Resource:
    allow(Role.SYSTEM, r, *list(Action))

# OWNER has all permissions except system-level operations
for r in Resource:
    if r != Resource.SYSTEM:
        allow(Role.OWNER, r, *list(Action))
    else:
        allow(Role.OWNER, r, Action.READ, Action.CONFIGURE)

# ADMIN permissions - comprehensive administrative access
allow(
    Role.ADMIN,
    Resource.ORG,
    Action.READ,
    Action.UPDATE,
    Action.ADMINISTER,
    Action.INVITE,
    Action.CONFIGURE,
)
allow(
    Role.ADMIN,
    Resource.TEAM,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.ADMINISTER,
    Action.INVITE,
)
allow(
    Role.ADMIN,
    Resource.CONTEXT,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.SHARE,
    Action.EXPORT,
)
allow(
    Role.ADMIN,
    Resource.MEMORY,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.EXPORT,
)
allow(
    Role.ADMIN,
    Resource.USER,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.ADMINISTER,
    Action.INVITE,
)
allow(
    Role.ADMIN,
    Resource.INVITATION,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.APPROVE,
)
allow(Role.ADMIN, Resource.BACKUP, Action.READ, Action.CREATE, Action.RESTORE)
allow(Role.ADMIN, Resource.AUDIT, Action.READ, Action.AUDIT)
allow(Role.ADMIN, Resource.API, Action.READ, Action.ADMINISTER)

# MAINTAINER permissions - advanced user operations
allow(
    Role.MAINTAINER,
    Resource.CONTEXT,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.SHARE,
    Action.EXPORT,
)
allow(
    Role.MAINTAINER,
    Resource.MEMORY,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.EXPORT,
)
allow(Role.MAINTAINER, Resource.TEAM, Action.READ, Action.UPDATE, Action.INVITE)
allow(Role.MAINTAINER, Resource.USER, Action.READ, Action.INVITE)
allow(Role.MAINTAINER, Resource.INVITATION, Action.READ, Action.CREATE)
allow(Role.MAINTAINER, Resource.BACKUP, Action.READ, Action.CREATE)
allow(Role.MAINTAINER, Resource.AUDIT, Action.READ)
allow(Role.MAINTAINER, Resource.API, Action.READ)

# MEMBER permissions - standard user operations
allow(
    Role.MEMBER,
    Resource.CONTEXT,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.SHARE,
    Action.EXPORT,
)
allow(
    Role.MEMBER,
    Resource.MEMORY,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.EXPORT,
)
allow(Role.MEMBER, Resource.TEAM, Action.READ)
allow(Role.MEMBER, Resource.USER, Action.READ)
allow(Role.MEMBER, Resource.BACKUP, Action.READ)
allow(Role.MEMBER, Resource.API, Action.READ)

# VIEWER permissions - read-only access
allow(Role.VIEWER, Resource.CONTEXT, Action.READ, Action.EXPORT)
allow(Role.VIEWER, Resource.MEMORY, Action.READ, Action.EXPORT)
allow(Role.VIEWER, Resource.TEAM, Action.READ)
allow(Role.VIEWER, Resource.USER, Action.READ)
allow(Role.VIEWER, Resource.API, Action.READ)


@dataclass(frozen=True)
class SubjectContext:
    org_id: str
    team_ids: set[str]
    roles: dict[str, Role]


def _resolve_effective_role(ctx: SubjectContext, scope: str) -> Role | None:
    role = ctx.roles.get(scope)
    return role


def effective_role(ctx: SubjectContext, team_id: str | None = None) -> Role | None:
    """Get the effective role for a user in a given context"""
    # Priority: team-specific role > org role > global role
    if team_id and team_id in ctx.roles:
        return ctx.roles[team_id]

    if ctx.org_id in ctx.roles:
        return ctx.roles[ctx.org_id]

    # Check for global role
    if "global" in ctx.roles:
        return ctx.roles["global"]

    # Default to highest precedence role if no specific scope
    if ctx.roles:
        return max(ctx.roles.values(), key=lambda r: ROLE_PRECEDENCE.index(r))

    return None


def authorize(
    ctx: SubjectContext, res: Resource, action: Action, team_id: str | None = None
) -> bool:
    """Check if a user is authorized to perform an action on a resource"""
    role = effective_role(ctx, team_id)
    if not role:
        return False

    # Check if the role has permission for this action on this resource
    allowed_actions = POLICY.get((role, res), set())
    return action in allowed_actions


def has_role_precedence(role1: Role, role2: Role) -> bool:
    """Check if role1 has higher or equal precedence than role2"""
    try:
        return ROLE_PRECEDENCE.index(role1) >= ROLE_PRECEDENCE.index(role2)
    except ValueError:
        return False


def get_user_permissions(role: Role) -> dict[Resource, set[Action]]:
    """Get all permissions for a given role"""
    permissions = {}
    for (r, resource), actions in POLICY.items():
        if r == role:
            if resource not in permissions:
                permissions[resource] = set()
            permissions[resource].update(actions)
    return permissions


def can_delegate_permission(
    delegator_role: Role, action: Action, resource: Resource
) -> bool:
    """Check if a role can delegate a specific permission to another user"""
    # Only roles with the permission can delegate it
    allowed_actions = POLICY.get((delegator_role, resource), set())
    if action not in allowed_actions:
        return False

    # Additional restrictions: only ADMIN and above can delegate administrative actions
    admin_actions = {Action.ADMINISTER, Action.CONFIGURE, Action.APPROVE}
    if action in admin_actions:
        return has_role_precedence(delegator_role, Role.ADMIN)

    return True


def require_permission(resource: Resource, action: Action):
    def decorator(func):
        def wrapper(subject_ctx: SubjectContext, *args, **kwargs):
            if not authorize(
                subject_ctx, resource, action, team_id=kwargs.get("team_id")
            ):
                raise PermissionError(
                    f"Forbidden: need {action.name} on {resource.name}"
                )
            return func(subject_ctx, *args, **kwargs)

        return wrapper

    return decorator
