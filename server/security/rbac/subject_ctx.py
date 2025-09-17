from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass(frozen=True)
class SubjectContext:
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    team_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    claims: Dict[str, object] = field(default_factory=dict)
