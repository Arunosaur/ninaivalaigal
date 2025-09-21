from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row


# --- tiny embedding stub (swap for your embedding service) ------------------
def embed(text: str, dim: int = 8) -> list[float]:
    v = [0.0] * dim
    for i, ch in enumerate(text[:1024]):
        v[i % dim] += (ord(ch) % 97) / 97.0
    return v

@dataclass
class PGConfig:
    dsn: str
    table: str = "memory_records"
    dim: int = 8
    use_vectors: bool = True

class PostgresStore:
    def __init__(self, cfg: PGConfig | None = None):
        dsn = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/postgres"
        self.cfg = cfg or PGConfig(dsn=dsn)

    async def _conn(self):
        return await psycopg.AsyncConnection.connect(self.cfg.dsn, row_factory=dict_row)

    async def ensure_schema(self):
        sql = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
        CREATE TABLE IF NOT EXISTS {self.cfg.table} (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          scope TEXT NOT NULL CHECK (scope IN ('personal','team','organization')),
          user_id TEXT NOT NULL,
          team_id TEXT,
          org_id  TEXT,
          kind    TEXT NOT NULL,
          text    TEXT NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
          embedding vector({self.cfg.dim}),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_{self.cfg.table}_scope ON {self.cfg.table} (scope);
        CREATE INDEX IF NOT EXISTS ix_{self.cfg.table}_user  ON {self.cfg.table} (user_id);
        CREATE INDEX IF NOT EXISTS ix_{self.cfg.table}_team  ON {self.cfg.table} (team_id);
        CREATE INDEX IF NOT EXISTS ix_{self.cfg.table}_org   ON {self.cfg.table} (org_id);
        """
        async with await self._conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

    async def write(self, rec: dict[str, Any]) -> dict[str, Any]:
        await self.ensure_schema()
        emb = embed(rec.get("text", ""), self.cfg.dim) if self.cfg.use_vectors else None
        sql = f"""
        INSERT INTO {self.cfg.table}
        (scope,user_id,team_id,org_id,kind,text,metadata,embedding)
        VALUES (%(scope)s,%(user_id)s,%(team_id)s,%(org_id)s,%(kind)s,%(text)s,%(metadata)s::jsonb,%(embedding)s)
        RETURNING *;
        """
        params = {
            "scope": rec["scope"],
            "user_id": rec["user_id"],
            "team_id": rec.get("team_id"),
            "org_id": rec.get("org_id"),
            "kind": rec["kind"],
            "text": rec["text"],
            "metadata": json.dumps(rec.get("metadata") or {}),
            "embedding": emb,
        }
        async with await self._conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                row = await cur.fetchone()
                await conn.commit()
        return row

    async def query(self, q: dict[str, Any]) -> list[dict[str, Any]]:
        filters = ["scope = %(scope)s"]
        if q.get("scope") == "personal":
            filters.append("user_id = %(user_id)s")
        elif q.get("scope") == "team":
            filters.append("team_id = %(team_id)s")
        elif q.get("scope") == "organization":
            filters.append("org_id = %(org_id)s")
        if q.get("kind"):
            filters.append("kind = %(kind)s")
        limit = max(1, min(int(q.get("limit", 10)), 100))
        params = dict(q)
        if self.cfg.use_vectors and q.get("semantic_query"):
            params["vec"] = embed(q["semantic_query"], self.cfg.dim)
            where = " AND ".join(filters + ["embedding IS NOT NULL"])
            sql = f"""
              SELECT *, (1 - (embedding <=> %(vec)s)) AS similarity
              FROM {self.cfg.table}
              WHERE {where}
              ORDER BY embedding <=> %(vec)s
              LIMIT {limit};
            """
        else:
            where = " AND ".join(filters)
            sql = f"""
              SELECT * FROM {self.cfg.table}
              WHERE {where}
              ORDER BY created_at DESC
              LIMIT {limit};
            """
        async with await self._conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return rows

    async def share(self, record_ids: Sequence[str], to_scope: str, target: dict[str, Any]) -> int:
        if not record_ids:
            return 0
        ids_tuple = tuple(record_ids)
        sql = f"""
          INSERT INTO {self.cfg.table} (scope,user_id,team_id,org_id,kind,text,metadata,embedding)
          SELECT %(to_scope)s, user_id, %(team_id)s, %(org_id)s, kind, text, metadata, embedding
          FROM {self.cfg.table}
          WHERE id IN %s;
        """
        async with await self._conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, (ids_tuple,), {"to_scope": to_scope, "team_id": target.get("team_id"), "org_id": target.get("org_id")})
                count = cur.rowcount or 0
                await conn.commit()
        return count
