import os

from fastapi import APIRouter
from pydantic import BaseModel

from server.memory.stores.postgres_store import PGConfig, PostgresStore

router = APIRouter(prefix="/demo/memory", tags=["memory-demo"])

class DemoWrite(BaseModel):
    scope: str = "personal"
    user_id: str
    team_id: str | None = None
    org_id: str | None = None
    kind: str = "note"
    text: str
    metadata: dict = {}

class DemoSemanticQuery(BaseModel):
    scope: str = "personal"
    user_id: str | None = None
    team_id: str | None = None
    org_id: str | None = None
    semantic_query: str
    limit: int = 5

def store() -> PostgresStore:
    return PostgresStore(PGConfig(dsn=os.getenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/postgres")))

@router.post("/write")
async def demo_write(body: DemoWrite):
    s = store()
    row = await s.write(body.dict())
    return {"id": row["id"], "kind": row["kind"], "text": row["text"]}

@router.post("/semantic_search")
async def demo_semantic_search(q: DemoSemanticQuery):
    s = store()
    rows = await s.query(q.dict())
    return {"count": len(rows), "results": rows}
