import os

import pytest

from server.memory.stores.postgres_store import PGConfig, PostgresStore

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="set DATABASE_URL to run PG tests"
)


@pytest.mark.asyncio
async def test_write_query_semantic():
    s = PostgresStore(PGConfig(dsn=os.getenv("DATABASE_URL")))
    await s.ensure_schema()
    row = await s.write(
        {
            "scope": "personal",
            "user_id": "u1",
            "team_id": "t1",
            "org_id": "o1",
            "kind": "note",
            "text": "ai context about standups",
        }
    )
    rows = await s.query(
        {"scope": "personal", "user_id": "u1", "semantic_query": "standups", "limit": 3}
    )
    assert rows
