-- Consolidated Database Initialization
-- PostgreSQL 15 + Apache AGE + pgvector
-- Replaces both nv-db and graph-db

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE extension
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create main graph for ninaivalaigal intelligence
SELECT create_graph('ninaivalaigal_intelligence');

-- Create core tables with UUID primary keys
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL DEFAULT 'individual',
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_via VARCHAR(50) NOT NULL DEFAULT 'api',
    email_verified BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    domain VARCHAR(255),
    settings JSON,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI embedding dimension
    user_id UUID REFERENCES users(id),
    team_id UUID REFERENCES teams(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id),
    team_id UUID REFERENCES teams(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_value VARCHAR(255) NOT NULL,
    memory_id UUID REFERENCES memories(id),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_contexts_user_id ON contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens(user_id);

-- Insert test user with known UUID for authentication
INSERT INTO users (id, email, name, password_hash, account_type, subscription_tier, role, created_via, email_verified, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'test@ninaivalaigal.com',
    'Test User',
    '$2b$12$LQv3c1yqBwEHxPuNYuTuT.BVf1ejmflPDcwLcaekRWC/vUiKvRg/2',
    'individual',
    'free',
    'user',
    'api',
    true,
    true
) ON CONFLICT (id) DO NOTHING;

-- Insert sample data
INSERT INTO memories (content, user_id) VALUES
('Sample memory for testing consolidated database', '00000000-0000-0000-0000-000000000001'::UUID),
('Another test memory with vector capabilities', '00000000-0000-0000-0000-000000000001'::UUID)
ON CONFLICT DO NOTHING;

-- Create graph nodes for the same data (simplified for initialization)
SELECT * FROM cypher('ninaivalaigal_intelligence', $$
CREATE (u:User {id: '00000000-0000-0000-0000-000000000001', name: 'Test User', email: 'test@ninaivalaigal.com'})
RETURN u
$$) AS (u agtype);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nina;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nina;
