-- Ninaivalaigal Database Extensions Initialization
-- Based on extension requirements analysis

-- Core Extensions (Must Have)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS auto_explain;
CREATE EXTENSION IF NOT EXISTS pg_repack;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Complementary Extensions (Strategic Advantage)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Graph Extensions
CREATE EXTENSION IF NOT EXISTS age;

-- Similarity for RAG (SPEC-041)
CREATE EXTENSION IF NOT EXISTS pg_similarity;

-- Database Federation & Sharding (US#958, SPEC-160)
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA ag_catalog TO PUBLIC;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Ninaivalaigal extensions initialized successfully';
END $$;
