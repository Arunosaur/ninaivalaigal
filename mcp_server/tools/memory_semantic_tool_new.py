import os
from typing import Any

from server.memory.stores.postgres_store import PGConfig, PostgresStore


async def mcp_memory_semantic_query(payload: dict[str, Any]) -> list[dict[str, Any]]:
    store = PostgresStore(
        PGConfig(
            dsn=os.getenv(
                "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
            )
        )
    )
    rows = await store.query(payload)
    return rows
