from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Role(Enum):
    OWNER = auto()
    ADMIN = auto()
    MAINTAINER = auto()
    MEMBER = auto()
    VIEWER = auto()


class Action(Enum):
    READ = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    SHARE = auto()
    EXPORT = auto()
    ADMINISTER = auto()


class Resource(Enum):
    MEMORY = auto()
    CONTEXT = auto()
    TEAM = auto()
    ORG = auto()
    AUDIT = auto()


ROLE_PRECEDENCE = [Role.VIEWER, Role.MEMBER, Role.MAINTAINER, Role.ADMIN, Role.OWNER]

POLICY: dict[tuple[Role, Resource], set[Action]] = {}


def allow(role: Role, res: Resource, *actions: Action):
    POLICY.setdefault((role, res), set()).update(actions)


for r in Resource:
    allow(Role.OWNER, r, *list(Action))

allow(Role.ADMIN, Resource.ORG, Action.READ, Action.UPDATE, Action.ADMINISTER)
allow(
    Role.ADMIN,
    Resource.TEAM,
    Action.READ,
    Action.CREATE,
    Action.UPDATE,
    Action.DELETE,
    Action.ADMINISTER,
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
allow(Role.ADMIN, Resource.AUDIT, Action.READ)

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
allow(Role.MAINTAINER, Resource.TEAM, Action.READ, Action.UPDATE)
allow(Role.MAINTAINER, Resource.AUDIT, Action.READ)

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

allow(Role.VIEWER, Resource.CONTEXT, Action.READ, Action.EXPORT)
allow(Role.VIEWER, Resource.MEMORY, Action.READ, Action.EXPORT)


@dataclass(frozen=True)
class SubjectContext:
    org_id: str
    team_ids: set[str]
    roles: dict[str, Role]


def _resolve_effective_role(ctx: SubjectContext, scope: str) -> Role | None:
    role = ctx.roles.get(scope)
    return role


def _max_role(roles: set[Role]) -> Role | None:
    if not roles:
        return None
    return sorted(roles, key=lambda r: ROLE_PRECEDENCE.index(r))[-1]


def effective_role(ctx: SubjectContext, team_id: str | None = None) -> Role | None:
    roles: set[Role] = set()
    org_role = _resolve_effective_role(ctx, "org")
    if org_role:
        roles.add(org_role)
    if team_id:
        tr = _resolve_effective_role(ctx, f"team:{team_id}")
        if tr:
            roles.add(tr)
    else:
        for tid in ctx.team_ids:
            tr = _resolve_effective_role(ctx, f"team:{tid}")
            if tr:
                roles.add(tr)
    return _max_role(roles)


def is_allowed(role: Role, resource: Resource, action: Action) -> bool:
    return action in POLICY.get((role, resource), set())


def authorize(
    ctx: SubjectContext, resource: Resource, action: Action, team_id: str | None = None
) -> bool:
    role = effective_role(ctx, team_id=team_id)
    if role is None:
        return False
    return is_allowed(role, resource, action)


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
