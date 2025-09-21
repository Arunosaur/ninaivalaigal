from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubjectContext:
    user_id: str | None = None
    org_id: str | None = None
    team_id: str | None = None
    roles: list[str] = field(default_factory=list)
    claims: dict[str, object] = field(default_factory=dict)
