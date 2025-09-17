from pydantic import BaseModel
from typing import Optional, List

class MemoryRecord(BaseModel):
    content: str
    scope: str  # personal, team, org
    tags: Optional[List[str]] = []

class MemoryQuery(BaseModel):
    scope: str
    filter: Optional[str] = None

class MemoryShare(BaseModel):
    target_scope: str
    record_id: str
