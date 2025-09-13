-- Team Merger System Database Schema
-- Creates tables and policies for handling team mergers, consolidations, and restructuring

-- Team Mergers tracking table
CREATE TABLE IF NOT EXISTS team_mergers (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR(100) NOT NULL,
    merger_type VARCHAR(20) NOT NULL CHECK (merger_type IN ('consolidation', 'split', 'dissolution', 'rename')),
    source_teams JSONB NOT NULL,
    target_teams JSONB NOT NULL,
    merger_date TIMESTAMP NOT NULL,
    initiated_by VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'rolled_back')),
    memory_migration_policy JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Team merger memory mapping
CREATE TABLE IF NOT EXISTS team_merger_memory_mapping (
    id SERIAL PRIMARY KEY,
    merger_id INTEGER REFERENCES team_mergers(id) ON DELETE CASCADE,
    source_context_id INTEGER REFERENCES contexts(id),
    target_team_id VARCHAR(100),
    migration_type VARCHAR(20) NOT NULL CHECK (migration_type IN ('move', 'copy', 'archive', 'delete')),
    access_level VARCHAR(20) DEFAULT 'inherited' CHECK (access_level IN ('inherited', 'restricted', 'enhanced')),
    migration_date TIMESTAMP DEFAULT NOW()
);

-- Enhanced team memberships for merger tracking
ALTER TABLE team_memberships 
ADD COLUMN IF NOT EXISTS previous_team_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS merger_id INTEGER REFERENCES team_mergers(id),
ADD COLUMN IF NOT EXISTS migration_date TIMESTAMP;

-- Enhanced contexts for team merger history
ALTER TABLE contexts 
ADD COLUMN IF NOT EXISTS original_team_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS merged_from_teams JSONB,
ADD COLUMN IF NOT EXISTS team_merger_id INTEGER REFERENCES team_mergers(id);

-- Team merger audit trail
CREATE TABLE IF NOT EXISTS team_merger_audit (
    id SERIAL PRIMARY KEY,
    merger_id INTEGER REFERENCES team_mergers(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(100) NOT NULL,
    affected_resources JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB
);

-- Cross-team access permissions for post-merger collaboration
CREATE TABLE IF NOT EXISTS cross_team_access (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    source_team_id VARCHAR(100) NOT NULL,
    target_team_id VARCHAR(100) NOT NULL,
    access_level VARCHAR(20) NOT NULL CHECK (access_level IN ('read', 'write', 'admin')),
    granted_by VARCHAR(100) NOT NULL,
    granted_date TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    merger_id INTEGER REFERENCES team_mergers(id)
);

-- Team archival for dissolved/merged teams
CREATE TABLE IF NOT EXISTS archived_teams (
    id SERIAL PRIMARY KEY,
    original_team_id VARCHAR(100) NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    organization_id VARCHAR(100) NOT NULL,
    archived_date TIMESTAMP DEFAULT NOW(),
    archived_by VARCHAR(100) NOT NULL,
    merger_id INTEGER REFERENCES team_mergers(id),
    team_metadata JSONB,
    restoration_data JSONB
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_mergers_org_status ON team_mergers(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_team_merger_mapping_merger ON team_merger_memory_mapping(merger_id);
CREATE INDEX IF NOT EXISTS idx_team_merger_audit_merger ON team_merger_audit(merger_id);
CREATE INDEX IF NOT EXISTS idx_cross_team_access_context ON cross_team_access(context_id);
CREATE INDEX IF NOT EXISTS idx_archived_teams_org ON archived_teams(organization_id);

-- Row-level security policies for team merger data
ALTER TABLE team_mergers ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_merger_memory_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_merger_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE cross_team_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE archived_teams ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see mergers from their organization
CREATE POLICY team_merger_org_access ON team_mergers
    FOR ALL USING (
        organization_id = current_setting('app.current_user_org_id', true)
    );

-- Policy: Users can only see memory mappings from their organization's mergers
CREATE POLICY team_merger_mapping_org_access ON team_merger_memory_mapping
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM team_mergers tm 
            WHERE tm.id = merger_id 
            AND tm.organization_id = current_setting('app.current_user_org_id', true)
        )
    );

-- Policy: Users can only see audit trail from their organization's mergers
CREATE POLICY team_merger_audit_org_access ON team_merger_audit
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM team_mergers tm 
            WHERE tm.id = merger_id 
            AND tm.organization_id = current_setting('app.current_user_org_id', true)
        )
    );

-- Policy: Cross-team access within organization only
CREATE POLICY cross_team_access_org_policy ON cross_team_access
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM contexts c 
            WHERE c.id = context_id 
            AND c.organization_id = current_setting('app.current_user_org_id', true)
        )
    );

-- Policy: Archived teams within organization only
CREATE POLICY archived_teams_org_access ON archived_teams
    FOR ALL USING (
        organization_id = current_setting('app.current_user_org_id', true)
    );

-- Functions for team merger operations

-- Function to get team merger status
CREATE OR REPLACE FUNCTION get_team_merger_status(merger_id_param INTEGER)
RETURNS TABLE (
    merger_id INTEGER,
    status VARCHAR(20),
    progress_percentage INTEGER,
    current_step VARCHAR(100),
    estimated_completion TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tm.id,
        tm.status,
        CASE 
            WHEN tm.status = 'pending' THEN 0
            WHEN tm.status = 'in_progress' THEN 50
            WHEN tm.status = 'completed' THEN 100
            WHEN tm.status = 'failed' THEN -1
            WHEN tm.status = 'rolled_back' THEN -2
        END as progress_percentage,
        CASE 
            WHEN tm.status = 'pending' THEN 'Waiting for approval'
            WHEN tm.status = 'in_progress' THEN 'Migrating data'
            WHEN tm.status = 'completed' THEN 'Completed successfully'
            WHEN tm.status = 'failed' THEN 'Failed - check logs'
            WHEN tm.status = 'rolled_back' THEN 'Rolled back'
        END as current_step,
        CASE 
            WHEN tm.status = 'in_progress' THEN NOW() + INTERVAL '30 minutes'
            ELSE NULL
        END as estimated_completion
    FROM team_mergers tm
    WHERE tm.id = merger_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to validate merger prerequisites
CREATE OR REPLACE FUNCTION validate_merger_prerequisites(
    source_teams_param JSONB,
    target_teams_param JSONB,
    org_id_param VARCHAR(100)
) RETURNS TABLE (
    is_valid BOOLEAN,
    validation_errors TEXT[]
) AS $$
DECLARE
    errors TEXT[] := '{}';
    team_id TEXT;
BEGIN
    -- Check if source teams exist
    FOR team_id IN SELECT jsonb_array_elements_text(source_teams_param)
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM teams t 
            WHERE t.id = team_id 
            AND t.organization_id = org_id_param
        ) THEN
            errors := array_append(errors, 'Source team does not exist: ' || team_id);
        END IF;
    END LOOP;
    
    -- Check if source teams have active members
    FOR team_id IN SELECT jsonb_array_elements_text(source_teams_param)
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM team_memberships tm 
            WHERE tm.team_id = team_id 
            AND tm.status = 'active'
        ) THEN
            errors := array_append(errors, 'Source team has no active members: ' || team_id);
        END IF;
    END LOOP;
    
    RETURN QUERY SELECT (array_length(errors, 1) IS NULL), errors;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate merger impact
CREATE OR REPLACE FUNCTION calculate_merger_impact(merger_id_param INTEGER)
RETURNS TABLE (
    affected_users INTEGER,
    affected_contexts INTEGER,
    affected_memories INTEGER,
    estimated_duration_minutes INTEGER
) AS $$
DECLARE
    source_teams JSONB;
    user_count INTEGER := 0;
    context_count INTEGER := 0;
    memory_count INTEGER := 0;
    team_id TEXT;
BEGIN
    -- Get source teams
    SELECT tm.source_teams INTO source_teams
    FROM team_mergers tm
    WHERE tm.id = merger_id_param;
    
    -- Count affected users
    FOR team_id IN SELECT jsonb_array_elements_text(source_teams)
    LOOP
        SELECT user_count + COUNT(*) INTO user_count
        FROM team_memberships tm
        WHERE tm.team_id = team_id AND tm.status = 'active';
    END LOOP;
    
    -- Count affected contexts
    FOR team_id IN SELECT jsonb_array_elements_text(source_teams)
    LOOP
        SELECT context_count + COUNT(*) INTO context_count
        FROM contexts c
        WHERE c.team_id = team_id;
    END LOOP;
    
    -- Count affected memories
    FOR team_id IN SELECT jsonb_array_elements_text(source_teams)
    LOOP
        SELECT memory_count + COUNT(*) INTO memory_count
        FROM memories m
        JOIN contexts c ON m.context_id = c.id
        WHERE c.team_id = team_id;
    END LOOP;
    
    RETURN QUERY SELECT 
        user_count,
        context_count,
        memory_count,
        GREATEST(5, (context_count * 2) + (memory_count / 100))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update merger timestamps
CREATE OR REPLACE FUNCTION update_merger_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER team_merger_update_timestamp
    BEFORE UPDATE ON team_mergers
    FOR EACH ROW
    EXECUTE FUNCTION update_merger_timestamp();

-- Grant permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON team_mergers TO ninaivalaigal_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_merger_memory_mapping TO ninaivalaigal_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_merger_audit TO ninaivalaigal_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON cross_team_access TO ninaivalaigal_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON archived_teams TO ninaivalaigal_app;

GRANT USAGE ON SEQUENCE team_mergers_id_seq TO ninaivalaigal_app;
GRANT USAGE ON SEQUENCE team_merger_memory_mapping_id_seq TO ninaivalaigal_app;
GRANT USAGE ON SEQUENCE team_merger_audit_id_seq TO ninaivalaigal_app;
GRANT USAGE ON SEQUENCE cross_team_access_id_seq TO ninaivalaigal_app;
GRANT USAGE ON SEQUENCE archived_teams_id_seq TO ninaivalaigal_app;

GRANT EXECUTE ON FUNCTION get_team_merger_status(INTEGER) TO ninaivalaigal_app;
GRANT EXECUTE ON FUNCTION validate_merger_prerequisites(JSONB, JSONB, VARCHAR(100)) TO ninaivalaigal_app;
GRANT EXECUTE ON FUNCTION calculate_merger_impact(INTEGER) TO ninaivalaigal_app;
