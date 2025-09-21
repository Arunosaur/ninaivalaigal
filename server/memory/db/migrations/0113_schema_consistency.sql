-- SPEC-011: Schema Consistency and Best Practices Migration
-- Fixes data types, adds UUIDs, improves constraints and indexes

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. CONVERT ALL PRIMARY KEYS TO UUIDs
-- Start with independent tables first, then dependent ones

-- Users table (foundational)
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey CASCADE;
ALTER TABLE users ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE users ADD PRIMARY KEY (id);

-- Organizations table
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_pkey CASCADE;
ALTER TABLE organizations ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE organizations ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE organizations ADD PRIMARY KEY (id);

-- Teams table
ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_pkey CASCADE;
ALTER TABLE teams ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE teams ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE teams ADD PRIMARY KEY (id);

-- Update foreign key references in teams
ALTER TABLE teams ALTER COLUMN organization_id TYPE UUID USING uuid_generate_v4();

-- Contexts table
ALTER TABLE contexts DROP CONSTRAINT IF EXISTS contexts_pkey CASCADE;
ALTER TABLE contexts ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE contexts ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE contexts ADD PRIMARY KEY (id);

-- Update foreign key references in contexts
ALTER TABLE contexts ALTER COLUMN owner_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE contexts ALTER COLUMN team_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE contexts ALTER COLUMN organization_id TYPE UUID USING uuid_generate_v4();

-- Memories table (already done, but ensure consistency)
-- This should already be UUID from previous migration

-- Dependent tables
ALTER TABLE team_members DROP CONSTRAINT IF EXISTS team_members_pkey CASCADE;
ALTER TABLE team_members ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE team_members ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE team_members ADD PRIMARY KEY (id);
ALTER TABLE team_members ALTER COLUMN team_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE team_members ALTER COLUMN user_id TYPE UUID USING uuid_generate_v4();

ALTER TABLE context_permissions DROP CONSTRAINT IF EXISTS context_permissions_pkey CASCADE;
ALTER TABLE context_permissions ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE context_permissions ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE context_permissions ADD PRIMARY KEY (id);
ALTER TABLE context_permissions ALTER COLUMN context_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE context_permissions ALTER COLUMN user_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE context_permissions ALTER COLUMN team_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE context_permissions ALTER COLUMN organization_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE context_permissions ALTER COLUMN granted_by TYPE UUID USING uuid_generate_v4();

ALTER TABLE organization_registrations DROP CONSTRAINT IF EXISTS organization_registrations_pkey CASCADE;
ALTER TABLE organization_registrations ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE organization_registrations ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE organization_registrations ADD PRIMARY KEY (id);
ALTER TABLE organization_registrations ALTER COLUMN organization_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE organization_registrations ALTER COLUMN creator_user_id TYPE UUID USING uuid_generate_v4();

ALTER TABLE user_invitations DROP CONSTRAINT IF EXISTS user_invitations_pkey CASCADE;
ALTER TABLE user_invitations ALTER COLUMN id TYPE UUID USING uuid_generate_v4();
ALTER TABLE user_invitations ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE user_invitations ADD PRIMARY KEY (id);
ALTER TABLE user_invitations ALTER COLUMN organization_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE user_invitations ALTER COLUMN team_id TYPE UUID USING uuid_generate_v4();
ALTER TABLE user_invitations ALTER COLUMN invited_by TYPE UUID USING uuid_generate_v4();

-- Fix memory_lifecycle_policies to use proper UUID references
ALTER TABLE memory_lifecycle_policies ALTER COLUMN user_id TYPE UUID USING
    CASE WHEN user_id IS NULL THEN NULL ELSE uuid_generate_v4() END;
ALTER TABLE memory_lifecycle_policies ALTER COLUMN team_id TYPE UUID USING
    CASE WHEN team_id IS NULL THEN NULL ELSE uuid_generate_v4() END;
ALTER TABLE memory_lifecycle_policies ALTER COLUMN org_id TYPE UUID USING
    CASE WHEN org_id IS NULL THEN NULL ELSE uuid_generate_v4() END;

-- 2. STANDARDIZE TIMESTAMPS TO TIMESTAMPTZ
ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMPTZ USING last_login AT TIME ZONE 'UTC';

ALTER TABLE organizations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE organizations ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE teams ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE teams ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE contexts ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE contexts ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE memories ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE memories ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE team_members ALTER COLUMN joined_at TYPE TIMESTAMPTZ USING joined_at AT TIME ZONE 'UTC';

ALTER TABLE organization_registrations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE organization_registrations ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE user_invitations ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC';
ALTER TABLE user_invitations ALTER COLUMN accepted_at TYPE TIMESTAMPTZ USING accepted_at AT TIME ZONE 'UTC';
ALTER TABLE user_invitations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE user_invitations ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- 3. STANDARDIZE JSON TO JSONB
ALTER TABLE organizations ALTER COLUMN settings TYPE JSONB USING settings::JSONB;
ALTER TABLE organization_registrations ALTER COLUMN registration_data TYPE JSONB USING registration_data::JSONB;

-- 4. ADD MISSING UPDATED_AT COLUMNS WHERE NEEDED
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE context_permissions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- 5. ADD PROPER FOREIGN KEY CONSTRAINTS
-- Users relationships
ALTER TABLE team_members ADD CONSTRAINT fk_team_members_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE team_members ADD CONSTRAINT fk_team_members_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;

-- Organization relationships
ALTER TABLE teams ADD CONSTRAINT fk_teams_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE organization_registrations ADD CONSTRAINT fk_org_reg_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE organization_registrations ADD CONSTRAINT fk_org_reg_creator_user_id
    FOREIGN KEY (creator_user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Context relationships
ALTER TABLE contexts ADD CONSTRAINT fk_contexts_owner_id
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contexts ADD CONSTRAINT fk_contexts_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE contexts ADD CONSTRAINT fk_contexts_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Context permissions
ALTER TABLE context_permissions ADD CONSTRAINT fk_context_permissions_context_id
    FOREIGN KEY (context_id) REFERENCES contexts(id) ON DELETE CASCADE;
ALTER TABLE context_permissions ADD CONSTRAINT fk_context_permissions_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE context_permissions ADD CONSTRAINT fk_context_permissions_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE context_permissions ADD CONSTRAINT fk_context_permissions_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE context_permissions ADD CONSTRAINT fk_context_permissions_granted_by
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Memory relationships
ALTER TABLE memories ADD CONSTRAINT fk_memories_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE memories ADD CONSTRAINT fk_memories_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE memories ADD CONSTRAINT fk_memories_org_id
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Lifecycle policy relationships
ALTER TABLE memory_lifecycle_policies ADD CONSTRAINT fk_lifecycle_policies_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE memory_lifecycle_policies ADD CONSTRAINT fk_lifecycle_policies_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE memory_lifecycle_policies ADD CONSTRAINT fk_lifecycle_policies_org_id
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- User invitations
ALTER TABLE user_invitations ADD CONSTRAINT fk_user_invitations_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE user_invitations ADD CONSTRAINT fk_user_invitations_team_id
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE user_invitations ADD CONSTRAINT fk_user_invitations_invited_by
    FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE CASCADE;

-- 6. ADD PERFORMANCE INDEXES
-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Organization indexes
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);
CREATE INDEX IF NOT EXISTS idx_organizations_domain ON organizations(domain);

-- Team indexes
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_organization_id ON teams(organization_id);

-- Context indexes
CREATE INDEX IF NOT EXISTS idx_contexts_owner_id ON contexts(owner_id);
CREATE INDEX IF NOT EXISTS idx_contexts_team_id ON contexts(team_id);
CREATE INDEX IF NOT EXISTS idx_contexts_organization_id ON contexts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contexts_scope ON contexts(scope);

-- Memory indexes (additional to lifecycle ones)
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories(context);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);

-- Team member indexes
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_role ON team_members(role);

-- Context permission indexes
CREATE INDEX IF NOT EXISTS idx_context_permissions_context_id ON context_permissions(context_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_user_id ON context_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_team_id ON context_permissions(team_id);

-- 7. ADD UPDATED_AT TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contexts_updated_at BEFORE UPDATE ON contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_members_updated_at BEFORE UPDATE ON team_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_context_permissions_updated_at BEFORE UPDATE ON context_permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_memory_lifecycle_policies_updated_at BEFORE UPDATE ON memory_lifecycle_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. RECREATE THE LIFECYCLE STATS VIEW WITH PROPER TYPES
DROP VIEW IF EXISTS memory_lifecycle_stats CASCADE;
CREATE OR REPLACE VIEW memory_lifecycle_stats AS
SELECT
    scope,
    user_id,
    team_id,
    org_id,
    lifecycle_status,
    COUNT(*) as memory_count,
    AVG(access_count) as avg_access_count,
    MIN(created_at) as oldest_memory,
    MAX(last_accessed_at) as most_recent_access
FROM memories
GROUP BY scope, user_id, team_id, org_id, lifecycle_status;
