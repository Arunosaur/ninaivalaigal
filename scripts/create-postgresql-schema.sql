-- PostgreSQL schema for mem0 production
-- Generated: 2025-09-12T07:50:00-05:00

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS memories CASCADE;
DROP TABLE IF EXISTS contexts CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contexts table
CREATE TABLE contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE DEFAULT 1,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, user_id)
);

-- Memories table
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE DEFAULT 1,
    type VARCHAR(100) NOT NULL,
    source VARCHAR(100),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_memories_context_id ON memories(context_id);
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_type ON memories(type);
CREATE INDEX idx_contexts_user_id ON contexts(user_id);
CREATE INDEX idx_contexts_active ON contexts(is_active);
CREATE INDEX idx_contexts_name ON contexts(name);

-- Insert default user for single-user mode compatibility
INSERT INTO users (id, username, email, password_hash) 
VALUES (1, 'default_user', 'user@mem0.local', 'placeholder_hash')
ON CONFLICT (id) DO NOTHING;
