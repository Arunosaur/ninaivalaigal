-- SPEC-007: Unified Context Scope System Migration
-- Implements unified context management with personal/team/organization scopes

-- Drop legacy tables if they exist
DROP TABLE IF EXISTS recording_contexts CASCADE;
DROP TABLE IF EXISTS legacy_contexts CASCADE;

-- Create unified contexts table
CREATE TABLE IF NOT EXISTS contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scope VARCHAR(20) NOT NULL DEFAULT 'personal', -- personal, team, organization
    owner_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    visibility VARCHAR(20) DEFAULT 'private', -- private, shared, public
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure proper scope ownership constraints
    CONSTRAINT scope_ownership_check CHECK (
        (scope = 'personal' AND owner_id IS NOT NULL AND team_id IS NULL AND organization_id IS NULL) OR
        (scope = 'team' AND team_id IS NOT NULL AND owner_id IS NULL AND organization_id IS NULL) OR
        (scope = 'organization' AND organization_id IS NOT NULL AND owner_id IS NULL AND team_id IS NULL)
    ),

    -- Ensure valid scope values
    CONSTRAINT valid_scope CHECK (scope IN ('personal', 'team', 'organization')),

    -- Ensure valid visibility values
    CONSTRAINT valid_visibility CHECK (visibility IN ('private', 'shared', 'public'))
);

-- Create context permissions table for fine-grained access control
CREATE TABLE IF NOT EXISTS context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    permission_level VARCHAR(20) NOT NULL, -- read, write, admin, owner
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Ensure valid permission levels
    CONSTRAINT valid_permission_level CHECK (permission_level IN ('read', 'write', 'admin', 'owner')),

    -- Ensure at least one target (user, team, or org)
    CONSTRAINT permission_target_check CHECK (
        (user_id IS NOT NULL AND team_id IS NULL AND organization_id IS NULL) OR
        (team_id IS NOT NULL AND user_id IS NULL AND organization_id IS NULL) OR
        (organization_id IS NOT NULL AND user_id IS NULL AND team_id IS NULL)
    ),

    -- Prevent duplicate permissions
    UNIQUE(context_id, user_id, team_id, organization_id)
);

-- Create context sharing table for cross-scope sharing
CREATE TABLE IF NOT EXISTS context_shares (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER REFERENCES users(id),
    shared_with_team_id INTEGER REFERENCES teams(id),
    shared_with_organization_id INTEGER REFERENCES organizations(id),
    shared_by INTEGER REFERENCES users(id) NOT NULL,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'read',
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Ensure valid permission levels
    CONSTRAINT valid_share_permission CHECK (permission_level IN ('read', 'write')),

    -- Ensure exactly one share target
    CONSTRAINT share_target_check CHECK (
        (shared_with_user_id IS NOT NULL AND shared_with_team_id IS NULL AND shared_with_organization_id IS NULL) OR
        (shared_with_team_id IS NOT NULL AND shared_with_user_id IS NULL AND shared_with_organization_id IS NULL) OR
        (shared_with_organization_id IS NOT NULL AND shared_with_user_id IS NULL AND shared_with_team_id IS NULL)
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_contexts_scope ON contexts(scope);
CREATE INDEX IF NOT EXISTS idx_contexts_owner_id ON contexts(owner_id);
CREATE INDEX IF NOT EXISTS idx_contexts_team_id ON contexts(team_id);
CREATE INDEX IF NOT EXISTS idx_contexts_organization_id ON contexts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contexts_is_active ON contexts(is_active);
CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON contexts(created_at);

CREATE INDEX IF NOT EXISTS idx_context_permissions_context_id ON context_permissions(context_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_user_id ON context_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_team_id ON context_permissions(team_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_organization_id ON context_permissions(organization_id);

CREATE INDEX IF NOT EXISTS idx_context_shares_context_id ON context_shares(context_id);
CREATE INDEX IF NOT EXISTS idx_context_shares_user_id ON context_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_context_shares_team_id ON context_shares(shared_with_team_id);
CREATE INDEX IF NOT EXISTS idx_context_shares_organization_id ON context_shares(shared_with_organization_id);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_contexts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contexts_updated_at
    BEFORE UPDATE ON contexts
    FOR EACH ROW
    EXECUTE FUNCTION update_contexts_updated_at();

-- Insert default contexts for existing users (migration safety)
INSERT INTO contexts (name, description, scope, owner_id, visibility)
SELECT
    'Default Personal Context',
    'Auto-created personal context for ' || username,
    'personal',
    id,
    'private'
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM contexts WHERE owner_id = users.id AND scope = 'personal'
);

-- Create view for context access resolution
CREATE OR REPLACE VIEW context_access AS
SELECT DISTINCT
    c.id as context_id,
    c.name,
    c.scope,
    c.visibility,
    CASE
        WHEN c.scope = 'personal' THEN c.owner_id
        WHEN cp.user_id IS NOT NULL THEN cp.user_id
        WHEN cs.shared_with_user_id IS NOT NULL THEN cs.shared_with_user_id
        ELSE NULL
    END as user_id,
    CASE
        WHEN c.scope = 'personal' AND c.owner_id IS NOT NULL THEN 'owner'
        WHEN cp.permission_level IS NOT NULL THEN cp.permission_level
        WHEN cs.permission_level IS NOT NULL THEN cs.permission_level
        WHEN c.visibility = 'public' THEN 'read'
        ELSE NULL
    END as permission_level
FROM contexts c
LEFT JOIN context_permissions cp ON c.id = cp.context_id
LEFT JOIN context_shares cs ON c.id = cs.context_id
WHERE c.is_active = true
  AND (cs.expires_at IS NULL OR cs.expires_at > CURRENT_TIMESTAMP)
  AND (cp.expires_at IS NULL OR cp.expires_at > CURRENT_TIMESTAMP);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON contexts TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON context_permissions TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON context_shares TO postgres;
GRANT SELECT ON context_access TO postgres;
GRANT USAGE ON SEQUENCE contexts_id_seq TO postgres;
GRANT USAGE ON SEQUENCE context_permissions_id_seq TO postgres;
GRANT USAGE ON SEQUENCE context_shares_id_seq TO postgres;
