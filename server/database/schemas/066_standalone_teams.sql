-- SPEC-066: Standalone Team Accounts Database Schema
-- Enables team creation without organization requirement
-- Created: 2024-09-23

-- Add standalone team support to existing teams table
ALTER TABLE teams ADD COLUMN IF NOT EXISTS is_standalone BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS upgrade_eligible BOOLEAN DEFAULT TRUE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS team_invite_code VARCHAR(32) UNIQUE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS max_members INTEGER DEFAULT 10;

-- Add standalone team reference to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS standalone_team_id UUID REFERENCES teams(id);

-- Create team invitations table for secure invite system
CREATE TABLE IF NOT EXISTS team_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    invited_by_user_id UUID NOT NULL REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'contributor',
    status VARCHAR(50) DEFAULT 'pending', -- pending, accepted, expired, revoked
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
    accepted_at TIMESTAMP,
    accepted_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_teams_is_standalone ON teams(is_standalone);
CREATE INDEX IF NOT EXISTS idx_teams_created_by_user ON teams(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_teams_invite_code ON teams(team_invite_code);
CREATE INDEX IF NOT EXISTS idx_users_standalone_team ON users(standalone_team_id);
CREATE INDEX IF NOT EXISTS idx_team_invitations_token ON team_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_team_invitations_email ON team_invitations(email);
CREATE INDEX IF NOT EXISTS idx_team_invitations_team ON team_invitations(team_id);
CREATE INDEX IF NOT EXISTS idx_team_invitations_status ON team_invitations(status);

-- Create team membership tracking table
CREATE TABLE IF NOT EXISTS team_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'contributor', -- admin, contributor, viewer
    joined_at TIMESTAMP DEFAULT NOW(),
    invited_by_user_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, removed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

-- Create indexes for team memberships
CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_user ON team_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_role ON team_memberships(role);
CREATE INDEX IF NOT EXISTS idx_team_memberships_status ON team_memberships(status);

-- Create team upgrade history table
CREATE TABLE IF NOT EXISTS team_upgrade_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    organization_id UUID REFERENCES organizations(id),
    upgraded_by_user_id UUID NOT NULL REFERENCES users(id),
    upgrade_type VARCHAR(50) NOT NULL, -- to_organization, billing_enabled
    upgrade_data JSONB, -- Store upgrade-specific data
    upgraded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'completed' -- pending, completed, failed, reverted
);

-- Create index for upgrade history
CREATE INDEX IF NOT EXISTS idx_team_upgrade_history_team ON team_upgrade_history(team_id);
CREATE INDEX IF NOT EXISTS idx_team_upgrade_history_org ON team_upgrade_history(organization_id);

-- Function to generate secure team invite codes
CREATE OR REPLACE FUNCTION generate_team_invite_code() RETURNS VARCHAR(32) AS $$
DECLARE
    code VARCHAR(32);
    exists BOOLEAN;
BEGIN
    LOOP
        -- Generate 8-character alphanumeric code
        code := upper(substring(md5(random()::text) from 1 for 8));
        
        -- Check if code already exists
        SELECT EXISTS(SELECT 1 FROM teams WHERE team_invite_code = code) INTO exists;
        
        -- If unique, return the code
        IF NOT exists THEN
            RETURN code;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to generate secure invitation tokens
CREATE OR REPLACE FUNCTION generate_invitation_token() RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN encode(gen_random_bytes(32), 'base64');
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate invite codes for standalone teams
CREATE OR REPLACE FUNCTION set_team_invite_code() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_standalone = TRUE AND NEW.team_invite_code IS NULL THEN
        NEW.team_invite_code := generate_team_invite_code();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_team_invite_code
    BEFORE INSERT OR UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION set_team_invite_code();

-- Trigger to auto-generate invitation tokens
CREATE OR REPLACE FUNCTION set_invitation_token() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.invitation_token IS NULL THEN
        NEW.invitation_token := generate_invitation_token();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_invitation_token
    BEFORE INSERT ON team_invitations
    FOR EACH ROW
    EXECUTE FUNCTION set_invitation_token();

-- Function to check if user can join team (respects max_members)
CREATE OR REPLACE FUNCTION can_user_join_team(team_uuid UUID) RETURNS BOOLEAN AS $$
DECLARE
    current_members INTEGER;
    max_allowed INTEGER;
BEGIN
    -- Get current member count and max allowed
    SELECT 
        COUNT(tm.user_id),
        t.max_members
    INTO current_members, max_allowed
    FROM teams t
    LEFT JOIN team_memberships tm ON t.id = tm.team_id AND tm.status = 'active'
    WHERE t.id = team_uuid
    GROUP BY t.max_members;
    
    -- Return true if under limit
    RETURN COALESCE(current_members, 0) < COALESCE(max_allowed, 10);
END;
$$ LANGUAGE plpgsql;

-- View for team statistics
CREATE OR REPLACE VIEW team_stats AS
SELECT 
    t.id,
    t.name,
    t.is_standalone,
    t.max_members,
    COUNT(tm.user_id) as current_members,
    COUNT(CASE WHEN tm.role = 'admin' THEN 1 END) as admin_count,
    COUNT(CASE WHEN tm.role = 'contributor' THEN 1 END) as contributor_count,
    COUNT(CASE WHEN tm.role = 'viewer' THEN 1 END) as viewer_count,
    t.created_at,
    t.updated_at
FROM teams t
LEFT JOIN team_memberships tm ON t.id = tm.team_id AND tm.status = 'active'
GROUP BY t.id, t.name, t.is_standalone, t.max_members, t.created_at, t.updated_at;

-- Insert sample data for testing (only if tables are empty)
DO $$
BEGIN
    -- Only insert if no standalone teams exist
    IF NOT EXISTS (SELECT 1 FROM teams WHERE is_standalone = TRUE) THEN
        -- Create a sample standalone team
        INSERT INTO teams (id, name, is_standalone, created_by_user_id, max_members)
        VALUES (
            gen_random_uuid(),
            'Sample Standalone Team',
            TRUE,
            (SELECT id FROM users LIMIT 1), -- Use first available user
            5
        );
        
        RAISE NOTICE 'Sample standalone team created for testing';
    END IF;
END $$;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON team_invitations TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_memberships TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_upgrade_history TO nina;
GRANT SELECT ON team_stats TO nina;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina;
