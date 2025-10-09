"""models module."""

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    """MemoryRecord class."""

    content: str
    scope: str  # personal, team, org
    tags: list[str] | None = []


class MemoryQuery(BaseModel):
    """MemoryQuery class."""

    scope: str
    filter: str | None = None


class MemoryShare(BaseModel):
    """MemoryShare class."""

    target_scope: str
    record_id: str
