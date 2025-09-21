from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel

from memory.store_factory import get_memory_store


class WriteBody(BaseModel):
    scope: str = "personal"
    user_id: str
    team_id: str | None = None
    org_id: str | None = None
    kind: str = "note"
    text: str
    metadata: dict[str, Any] = {}


def wire_memory_store(app: FastAPI) -> None:
    app.state.memory_store = get_memory_store()
    router = APIRouter(prefix="/mem-demo", tags=["memory-factory-demo"])

    def store_dep():
        return app.state.memory_store

    @router.post("/write")
    async def write(body: WriteBody, store=Depends(store_dep)):
        row = await store.write(body.dict())
        return {"id": row.get("id"), "kind": row.get("kind"), "text": row.get("text")}

    app.include_router(router)

    @app.get("/healthz/memory")
    async def healthz_memory():
        return {"backend": type(app.state.memory_store).__name__}
