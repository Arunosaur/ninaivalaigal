-- init-ninaivalaigal-db.sql
-- Database initialization script for Ninaivalaigal PostgreSQL container
-- This script runs automatically when the container starts for the first time

-- Create the main database if it doesn't exist (should already be created by POSTGRES_DB)
-- SELECT 'CREATE DATABASE ninaivalaigal_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ninaivalaigal_db')\gexec

-- Connect to the ninaivalaigal_db database
\c ninaivalaigal_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create core tables for Ninaivalaigal
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    organization_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(organization_id, slug)
);

CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(team_id, user_id)
);

CREATE TABLE IF NOT EXISTS recording_contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    team_id INTEGER REFERENCES teams(id),
    scope VARCHAR(50) DEFAULT 'personal', -- personal, team, organization
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    context_id INTEGER REFERENCES recording_contexts(id),
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    team_id INTEGER REFERENCES teams(id),
    memory_type VARCHAR(50) DEFAULT 'observation',
    metadata JSONB,
    embedding VECTOR(1536), -- for future vector search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES recording_contexts(id),
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    permission_type VARCHAR(50) NOT NULL, -- read, write, admin
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_teams_organization ON teams(organization_id);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories(context_id);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_contexts_owner ON recording_contexts(owner_id);
CREATE INDEX IF NOT EXISTS idx_contexts_scope ON recording_contexts(scope);

-- Insert default organization and users for testing
INSERT INTO organizations (name, slug, description) 
VALUES ('ACME Corporation', 'acme_corp', 'Default test organization')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO teams (name, slug, organization_id, description)
VALUES ('Engineering', 'engineering', 1, 'Engineering team')
ON CONFLICT (organization_id, slug) DO NOTHING;

INSERT INTO users (username, email, organization_id, password_hash)
VALUES 
    ('arun', 'arun@acme.com', 1, '$2b$12$example_hash_for_testing'),
    ('test_user', 'test@acme.com', 1, '$2b$12$example_hash_for_testing')
ON CONFLICT (username) DO NOTHING;

INSERT INTO team_members (team_id, user_id, role)
VALUES 
    (1, 1, 'lead'),
    (1, 2, 'member')
ON CONFLICT (team_id, user_id) DO NOTHING;

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE recording_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_permissions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic ones - can be expanded)
CREATE POLICY users_own_data ON users
    FOR ALL USING (username = current_setting('app.current_user', true));

CREATE POLICY org_data_access ON organizations
    FOR ALL USING (slug = current_setting('app.current_org', true));

CREATE POLICY team_data_access ON teams
    FOR ALL USING (organization_id::text = current_setting('app.current_org_id', true));

CREATE POLICY memory_access ON memories
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true) OR
        organization_id::text = current_setting('app.current_org_id', true)
    );

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ninaivalaigal_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ninaivalaigal_app;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ninaivalaigal_app;

-- Create a function to set user context for RLS
CREATE OR REPLACE FUNCTION set_user_context(
    p_user_id TEXT,
    p_username TEXT,
    p_org_id TEXT,
    p_org_slug TEXT
) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', p_user_id, false);
    PERFORM set_config('app.current_user', p_username, false);
    PERFORM set_config('app.current_org_id', p_org_id, false);
    PERFORM set_config('app.current_org', p_org_slug, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION set_user_context TO ninaivalaigal_app;

-- Log successful initialization
INSERT INTO memories (content, user_id, organization_id, memory_type, metadata)
VALUES (
    'Ninaivalaigal database initialized successfully',
    1,
    1,
    'system',
    '{"initialization": true, "timestamp": "' || CURRENT_TIMESTAMP || '"}'::jsonb
);

\echo 'Ninaivalaigal database initialization completed successfully!'
