-- SPEC-011 migration: Memory Lifecycle Management
-- Adds TTL, archival, and lifecycle tracking capabilities

-- Add lifecycle columns to memories (the actual table used by the application)
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT now(),
ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS lifecycle_status TEXT DEFAULT 'active' CHECK (lifecycle_status IN ('active', 'expiring', 'expired', 'archived', 'deleted'));

-- Create index for efficient lifecycle queries
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_status ON memories(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_memory_expires_at ON memories(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_last_accessed ON memories(last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_memory_archived_at ON memories(archived_at) WHERE archived_at IS NOT NULL;

-- Create lifecycle policies table
CREATE TABLE IF NOT EXISTS memory_lifecycle_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope TEXT NOT NULL CHECK (scope IN ('personal','team','organization')),
    user_id TEXT,
    team_id TEXT,
    org_id TEXT,
    policy_type TEXT NOT NULL CHECK (policy_type IN ('ttl', 'archival', 'purge')),
    policy_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index for policy lookups
CREATE INDEX IF NOT EXISTS idx_lifecycle_policies_scope ON memory_lifecycle_policies(scope, user_id, team_id, org_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_policies_type ON memory_lifecycle_policies(policy_type, enabled);

-- Create lifecycle events table for audit trail
CREATE TABLE IF NOT EXISTS memory_lifecycle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'accessed', 'expired', 'archived', 'restored', 'deleted')),
    event_data JSONB DEFAULT '{}'::jsonb,
    triggered_by TEXT, -- user_id or 'system'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index for event queries
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_memory_id ON memory_lifecycle_events(memory_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_type ON memory_lifecycle_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_created_at ON memory_lifecycle_events(created_at);

-- Create function to update last_accessed_at on memory retrieval
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE memories
    SET last_accessed_at = now(),
        access_count = access_count + 1
    WHERE id = NEW.memory_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for access tracking (will be used when memories are recalled)
-- Note: This will be activated by the application layer, not automatically

-- Create function to mark expired memories
CREATE OR REPLACE FUNCTION mark_expired_memories()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE memories
    SET lifecycle_status = 'expired'
    WHERE expires_at IS NOT NULL
      AND expires_at <= now()
      AND lifecycle_status = 'active';

    GET DIAGNOSTICS expired_count = ROW_COUNT;

    -- Log the expiration events
    INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
    SELECT id, 'expired', 'system', jsonb_build_object('expired_at', now())
    FROM memories
    WHERE lifecycle_status = 'expired'
      AND expires_at <= now();

    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to archive old memories
CREATE OR REPLACE FUNCTION archive_old_memories(days_threshold INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    UPDATE memories
    SET lifecycle_status = 'archived',
        archived_at = now()
    WHERE last_accessed_at < (now() - INTERVAL '1 day' * days_threshold)
      AND lifecycle_status = 'active'
      AND expires_at IS NULL; -- Don't archive memories that have explicit TTL

    GET DIAGNOSTICS archived_count = ROW_COUNT;

    -- Log the archival events
    INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
    SELECT id, 'archived', 'system', jsonb_build_object('archived_at', now(), 'days_inactive', days_threshold)
    FROM memories
    WHERE lifecycle_status = 'archived'
      AND archived_at = now();

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Insert default lifecycle policies for different scopes
INSERT INTO memory_lifecycle_policies (scope, policy_type, policy_config) VALUES
('personal', 'archival', '{"days_inactive": 180, "enabled": true}'::jsonb),
('team', 'archival', '{"days_inactive": 365, "enabled": true}'::jsonb),
('organization', 'archival', '{"days_inactive": 730, "enabled": true}'::jsonb)
ON CONFLICT DO NOTHING;

-- Create view for lifecycle statistics
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
