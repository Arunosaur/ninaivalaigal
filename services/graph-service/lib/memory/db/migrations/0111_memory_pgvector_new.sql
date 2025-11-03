-- Spec 011.1 migration: pgvector baseline
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS memory_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scope TEXT NOT NULL CHECK (scope IN ('personal','team','organization')),
  user_id TEXT NOT NULL,
  team_id TEXT,
  org_id  TEXT,
  kind    TEXT NOT NULL,
  text    TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(8),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
