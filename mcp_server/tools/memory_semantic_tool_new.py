from typing import Any, Dict, List
import os, asyncio
from server.memory.stores.postgres_store import PostgresStore, PGConfig

async def mcp_memory_semantic_query(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    store = PostgresStore(PGConfig(dsn=os.getenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/postgres")))
    rows = await store.query(payload)
    return rows
