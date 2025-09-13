-- User Management Schema Extensions for Mem0
-- Supports individual users, team members, and organization creators

-- Extend users table for account types and subscription tiers
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) DEFAULT 'individual';
-- Values: 'individual', 'team_member', 'organization_admin'

ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free';
-- Values: 'free', 'pro', 'team', 'enterprise'

ALTER TABLE users ADD COLUMN IF NOT EXISTS personal_contexts_limit INTEGER DEFAULT 10;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_via VARCHAR(20) DEFAULT 'signup';
-- Values: 'signup', 'invite', 'admin'

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Organization registration tracking
CREATE TABLE IF NOT EXISTS organization_registrations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    creator_user_id INTEGER REFERENCES users(id),
    registration_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    -- Values: 'pending', 'active', 'suspended', 'cancelled'
    created_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP,
    billing_email VARCHAR(255),
    company_size VARCHAR(20),
    industry VARCHAR(50)
);

-- User invitation system
CREATE TABLE IF NOT EXISTS user_invitations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    team_id INTEGER REFERENCES teams(id),
    invited_by INTEGER REFERENCES users(id),
    invitation_token VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'pending',
    -- Values: 'pending', 'accepted', 'expired', 'cancelled'
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP,
    invitation_message TEXT
);

-- Extend recording_contexts for proper scoping
ALTER TABLE recording_contexts ADD COLUMN IF NOT EXISTS scope VARCHAR(20) DEFAULT 'personal';
-- Values: 'personal', 'team', 'organization', 'public'

ALTER TABLE recording_contexts ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private';
-- Values: 'private', 'team', 'organization', 'public'

ALTER TABLE recording_contexts ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id);
ALTER TABLE recording_contexts ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id);

-- Context sharing permissions
CREATE TABLE IF NOT EXISTS context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES recording_contexts(id),
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    permission_type VARCHAR(20) NOT NULL,
    -- Values: 'read', 'write', 'admin', 'owner'
    granted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- User sessions for web authentication
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    jwt_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS email_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    verification_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE
);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_resets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    reset_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

-- User activity logging
CREATE TABLE IF NOT EXISTS user_activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Subscription and billing
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    subscription_tier VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    -- Values: 'active', 'cancelled', 'expired', 'suspended'
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    -- Values: 'monthly', 'yearly'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255)
);

-- Usage tracking for billing and limits
CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    resource_type VARCHAR(50) NOT NULL,
    -- Values: 'contexts', 'memories', 'api_calls', 'storage_mb'
    usage_count INTEGER DEFAULT 0,
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_account_type ON users(account_type);
CREATE INDEX IF NOT EXISTS idx_user_invitations_token ON user_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_user_invitations_email ON user_invitations(email);
CREATE INDEX IF NOT EXISTS idx_context_permissions_context ON context_permissions(context_id);
CREATE INDEX IF NOT EXISTS idx_context_permissions_user ON context_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_recording_contexts_scope ON recording_contexts(scope);
CREATE INDEX IF NOT EXISTS idx_recording_contexts_owner ON recording_contexts(owner_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_timestamp ON user_activity_log(user_id, timestamp);

-- Insert default data
INSERT INTO organizations (name, description) VALUES 
('Individual Users', 'Default organization for individual users')
ON CONFLICT DO NOTHING;

-- Create default admin user (for development)
INSERT INTO users (email, name, role, account_type, email_verified, password_hash) VALUES 
('admin@mem0.local', 'System Admin', 'super_admin', 'organization_admin', TRUE, '$2b$12$dummy_hash_for_development')
ON CONFLICT (email) DO NOTHING;
