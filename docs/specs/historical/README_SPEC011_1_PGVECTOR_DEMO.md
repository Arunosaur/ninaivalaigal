# Spec 011.1 — Postgres + pgvector (with semantic demo)

This bundle adds a Postgres store with pgvector and a **demo semantic search endpoint**
for end-to-end validation (FastAPI + MCP).

## Files
- `server/memory/stores/postgres_store.py` — async psycopg3 store, vector search
- `server/memory/db/migrations/0111_memory_pgvector.sql` — migration (creates table + vector ext)
- `server/memory/api_demo/semantic.py` — FastAPI demo endpoints:
  - `POST /demo/memory/write`
  - `POST /demo/memory/semantic_search`
- `mcp_server/tools/memory_semantic_tool.py` — MCP demo function `mcp_memory_semantic_query()`
- `server/memory/tests/test_postgres_semantic_demo.py` — opt-in test (requires `DATABASE_URL`)

## Run
1) Create schema/extensions:
```bash
psql "$DATABASE_URL" -f server/memory/db/migrations/0111_memory_pgvector.sql
```

2) Start your FastAPI app and include the router:
```python
from fastapi import FastAPI
from server.memory.api_demo.semantic import router as memory_demo_router

app = FastAPI()
app.include_router(memory_demo_router)
```

3) Try the demo:
```bash
curl -X POST $HOST/demo/memory/write -H 'Content-Type: application/json' -d '{"scope":"personal","user_id":"u1","kind":"note","text":"We prefer async daily standups"}'
curl -X POST $HOST/demo/memory/semantic_search -H 'Content-Type: application/json' -d '{"scope":"personal","user_id":"u1","semantic_query":"standups","limit":5}'
```

4) MCP (pseudo):
```python
from mcp_server.tools.memory_semantic_tool import mcp_memory_semantic_query
rows = await mcp_memory_semantic_query({"scope":"personal","user_id":"u1","semantic_query":"standups","limit":5})
```

> Replace the tiny `embed(text)` with your real embeddings service and update dimension.
