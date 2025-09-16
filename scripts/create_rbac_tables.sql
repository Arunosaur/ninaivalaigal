-- RBAC Database Migration Script
-- Creates tables for Role-Based Access Control system
-- Run this script to add RBAC tables to existing mem0db database

-- Create role_assignments table
CREATE TABLE IF NOT EXISTS role_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('VIEWER', 'MEMBER', 'MAINTAINER', 'ADMIN', 'OWNER', 'SYSTEM')),
    scope_type VARCHAR(20) NOT NULL CHECK (scope_type IN ('global', 'org', 'team', 'context')),
    scope_id VARCHAR(50),
    granted_by INTEGER NOT NULL REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Unique constraint for user-scope combination
    CONSTRAINT idx_role_assignments_user_scope UNIQUE (user_id, scope_type, scope_id)
);

-- Create indexes for role_assignments
CREATE INDEX IF NOT EXISTS idx_role_assignments_user_id ON role_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_role_assignments_scope ON role_assignments(scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_role_assignments_active ON role_assignments(is_active);

-- Create permission_audits table
CREATE TABLE IF NOT EXISTS permission_audits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN ('read', 'create', 'update', 'delete', 'share', 'export', 'administer', 'invite', 'approve', 'backup', 'restore', 'configure', 'audit')),
    resource VARCHAR(20) NOT NULL CHECK (resource IN ('memory', 'context', 'team', 'org', 'audit', 'user', 'invitation', 'backup', 'system', 'api')),
    resource_id VARCHAR(50),
    scope_type VARCHAR(20),
    scope_id VARCHAR(50),
    allowed BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    request_ip INET,
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10)
);

-- Create indexes for permission_audits
CREATE INDEX IF NOT EXISTS idx_permission_audits_user_id ON permission_audits(user_id);
CREATE INDEX IF NOT EXISTS idx_permission_audits_timestamp ON permission_audits(timestamp);
CREATE INDEX IF NOT EXISTS idx_permission_audits_resource ON permission_audits(resource, resource_id);
CREATE INDEX IF NOT EXISTS idx_permission_audits_allowed ON permission_audits(allowed);
CREATE INDEX IF NOT EXISTS idx_permission_audits_action ON permission_audits(action);

-- Create permission_delegations table
CREATE TABLE IF NOT EXISTS permission_delegations (
    id SERIAL PRIMARY KEY,
    delegator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delegate_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource VARCHAR(20) NOT NULL CHECK (resource IN ('memory', 'context', 'team', 'org', 'audit', 'user', 'invitation', 'backup', 'system', 'api')),
    actions VARCHAR(255) NOT NULL, -- Comma-separated action names
    resource_id VARCHAR(50),
    scope_type VARCHAR(20),
    scope_id VARCHAR(50),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    reason TEXT
);

-- Create indexes for permission_delegations
CREATE INDEX IF NOT EXISTS idx_permission_delegations_delegator ON permission_delegations(delegator_id);
CREATE INDEX IF NOT EXISTS idx_permission_delegations_delegate ON permission_delegations(delegate_id);
CREATE INDEX IF NOT EXISTS idx_permission_delegations_active ON permission_delegations(is_active);
CREATE INDEX IF NOT EXISTS idx_permission_delegations_expires ON permission_delegations(expires_at);

-- Create access_requests table
CREATE TABLE IF NOT EXISTS access_requests (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource VARCHAR(20) NOT NULL CHECK (resource IN ('memory', 'context', 'team', 'org', 'audit', 'user', 'invitation', 'backup', 'system', 'api')),
    action VARCHAR(20) NOT NULL CHECK (action IN ('read', 'create', 'update', 'delete', 'share', 'export', 'administer', 'invite', 'approve', 'backup', 'restore', 'configure', 'audit')),
    resource_id VARCHAR(50),
    scope_type VARCHAR(20),
    scope_id VARCHAR(50),
    justification TEXT NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_reason TEXT,
    expires_at TIMESTAMP
);

-- Create indexes for access_requests
CREATE INDEX IF NOT EXISTS idx_access_requests_requester ON access_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status);
CREATE INDEX IF NOT EXISTS idx_access_requests_reviewer ON access_requests(reviewed_by);
CREATE INDEX IF NOT EXISTS idx_access_requests_requested_at ON access_requests(requested_at);

-- Add RBAC columns to existing users table (if not already present)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS default_role VARCHAR(20) DEFAULT 'MEMBER' CHECK (default_role IN ('VIEWER', 'MEMBER', 'MAINTAINER', 'ADMIN', 'OWNER', 'SYSTEM')),
ADD COLUMN IF NOT EXISTS is_system_admin BOOLEAN DEFAULT false;

-- Create default role assignments for existing users
INSERT INTO role_assignments (user_id, role, scope_type, scope_id, granted_by, granted_at, is_active)
SELECT 
    id as user_id,
    'MEMBER' as role,
    'global' as scope_type,
    NULL as scope_id,
    1 as granted_by, -- Assume first user is system admin
    CURRENT_TIMESTAMP as granted_at,
    true as is_active
FROM users 
WHERE id NOT IN (SELECT user_id FROM role_assignments WHERE scope_type = 'global' AND scope_id IS NULL)
ON CONFLICT (user_id, scope_type, scope_id) DO NOTHING;

-- Set first user as system admin (if exists)
UPDATE users SET is_system_admin = true, default_role = 'SYSTEM' WHERE id = 1;
UPDATE role_assignments SET role = 'SYSTEM' WHERE user_id = 1 AND scope_type = 'global' AND scope_id IS NULL;

-- Create indexes on existing tables for RBAC performance
CREATE INDEX IF NOT EXISTS idx_contexts_owner_id ON contexts(owner_id);
CREATE INDEX IF NOT EXISTS idx_contexts_team_id ON contexts(team_id);
CREATE INDEX IF NOT EXISTS idx_contexts_organization_id ON contexts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contexts_scope ON contexts(scope);

CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories(context);

CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);

-- Add comments for documentation
COMMENT ON TABLE role_assignments IS 'Stores role assignments for users in different scopes (global, org, team, context)';
COMMENT ON TABLE permission_audits IS 'Audit log for all permission checks and access attempts';
COMMENT ON TABLE permission_delegations IS 'Temporary permission delegations between users';
COMMENT ON TABLE access_requests IS 'Requests for elevated access or permissions';

COMMENT ON COLUMN role_assignments.scope_type IS 'Type of scope: global, org, team, or context';
COMMENT ON COLUMN role_assignments.scope_id IS 'ID of the scope (org_id, team_id, context_id, or NULL for global)';
COMMENT ON COLUMN permission_audits.allowed IS 'Whether the permission check was allowed (true) or denied (false)';
COMMENT ON COLUMN access_requests.status IS 'Status of the access request: pending, approved, or rejected';

-- Grant permissions to mem0user (assuming this is the application user)
GRANT SELECT, INSERT, UPDATE, DELETE ON role_assignments TO mem0user;
GRANT SELECT, INSERT, UPDATE, DELETE ON permission_audits TO mem0user;
GRANT SELECT, INSERT, UPDATE, DELETE ON permission_delegations TO mem0user;
GRANT SELECT, INSERT, UPDATE, DELETE ON access_requests TO mem0user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE role_assignments_id_seq TO mem0user;
GRANT USAGE, SELECT ON SEQUENCE permission_audits_id_seq TO mem0user;
GRANT USAGE, SELECT ON SEQUENCE permission_delegations_id_seq TO mem0user;
GRANT USAGE, SELECT ON SEQUENCE access_requests_id_seq TO mem0user;

COMMIT;
