import pytest
from rbac.permissions import (
    Action,
    Resource,
    Role,
    SubjectContext,
    authorize,
    effective_role,
    is_allowed,
)


def make_ctx(org_role=None, team_roles=None):
    team_roles = team_roles or {}
    roles = {}
    if org_role:
        roles["org"] = org_role
    team_ids = set()
    for tid, r in team_roles.items():
        roles[f"team:{tid}"] = r
        team_ids.add(tid)
    return SubjectContext(org_id="org1", team_ids=team_ids, roles=roles)


def test_precedence_org_over_team():
    ctx = make_ctx(org_role=Role.ADMIN, team_roles={"alpha": Role.MEMBER})
    assert effective_role(ctx, team_id="alpha") == Role.ADMIN


def test_precedence_best_team_if_no_org():
    ctx = make_ctx(team_roles={"alpha": Role.MEMBER, "beta": Role.MAINTAINER})
    assert effective_role(ctx, team_id="beta") == Role.MAINTAINER


@pytest.mark.parametrize(
    "role,resource,action,expected",
    [
        (Role.VIEWER, Resource.MEMORY, Action.READ, True),
        (Role.VIEWER, Resource.MEMORY, Action.UPDATE, False),
        (Role.MEMBER, Resource.CONTEXT, Action.CREATE, True),
        (Role.MEMBER, Resource.CONTEXT, Action.DELETE, False),
        (Role.MAINTAINER, Resource.CONTEXT, Action.SHARE, True),
        (Role.ADMIN, Resource.ORG, Action.ADMINISTER, True),
        (Role.ADMIN, Resource.AUDIT, Action.READ, True),
        (Role.MEMBER, Resource.AUDIT, Action.READ, False),
    ],
)
def test_policy_matrix(role, resource, action, expected):
    assert is_allowed(role, resource, action) is expected


def test_authorize_positive():
    ctx = make_ctx(org_role=Role.MAINTAINER)
    assert authorize(ctx, Resource.MEMORY, Action.CREATE)


def test_authorize_negative():
    ctx = make_ctx(org_role=Role.VIEWER)
    assert not authorize(ctx, Resource.CONTEXT, Action.UPDATE)
