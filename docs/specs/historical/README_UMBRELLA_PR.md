# Umbrella PR: Spec 011.1 Memory Substrate (Prod)

This PR bundles:
- Postgres + pgvector store + migration
- Factory switch (Postgres in prod / InMemory in dev)
- FastAPI wiring + /mem-demo + /healthz/memory
- Semantic search demo API
- CI v3 (lint, matrix, nightly, DB snapshot/restore)
- DevEx (pre-commit, Makefile, requirements-dev)

## Merge steps
1) Drop these files at repo root (preserve paths).
2) `pip install -r requirements-dev.txt`
3) `pre-commit install`
4) `docker compose -f docker-compose.ci.yml up -d pgvector`
5) `export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres`
6) `alembic upgrade head` (or apply SQL migration)
7) `pytest -q tests/test_factory_switch_smoke.py`
8) Push branch → CI should pass.

## App integration
```python
from fastapi import FastAPI
from server.app.app_factory_patch import wire_memory_store
app = FastAPI()
wire_memory_store(app)
```

## Demo
- `POST /demo/memory/write`
- `POST /demo/memory/semantic_search`
