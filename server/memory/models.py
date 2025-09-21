
from pydantic import BaseModel


class MemoryRecord(BaseModel):
    content: str
    scope: str  # personal, team, org
    tags: list[str] | None = []

class MemoryQuery(BaseModel):
    scope: str
    filter: str | None = None

class MemoryShare(BaseModel):
    target_scope: str
    record_id: str
