-- Database Schema for Redaction Audit System
-- Add redaction audit tables to support comprehensive audit trail

-- Redaction audit table for tracking all redaction events
CREATE TABLE IF NOT EXISTS redaction_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    context_id INTEGER REFERENCES contexts(id),
    request_id VARCHAR(255),
    redaction_applied BOOLEAN NOT NULL,
    redaction_type VARCHAR(100),
    sensitivity_tier VARCHAR(50),
    patterns_matched JSONB,
    entropy_score FLOAT,
    original_length INTEGER,
    redacted_length INTEGER,
    processing_time_ms FLOAT,
    confidence_scores JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Security alert events table
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    user_id INTEGER REFERENCES users(id),
    context_id INTEGER REFERENCES contexts(id),
    metadata JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Security events table for detailed event tracking
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    context_id INTEGER REFERENCES contexts(id),
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add sensitivity tier and redaction metadata to existing tables
ALTER TABLE memories ADD COLUMN IF NOT EXISTS sensitivity_tier VARCHAR(50) DEFAULT 'internal';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS redaction_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS original_entropy_score FLOAT;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS redaction_audit_id UUID REFERENCES redaction_audits(id);

ALTER TABLE contexts ADD COLUMN IF NOT EXISTS sensitivity_tier VARCHAR(50) DEFAULT 'internal';
ALTER TABLE contexts ADD COLUMN IF NOT EXISTS auto_classified BOOLEAN DEFAULT FALSE;
ALTER TABLE contexts ADD COLUMN IF NOT EXISTS classification_confidence FLOAT;
ALTER TABLE contexts ADD COLUMN IF NOT EXISTS last_sensitivity_review TIMESTAMP WITH TIME ZONE;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_redaction_audits_user_id ON redaction_audits(user_id);
CREATE INDEX IF NOT EXISTS idx_redaction_audits_timestamp ON redaction_audits(timestamp);
CREATE INDEX IF NOT EXISTS idx_redaction_audits_context_id ON redaction_audits(context_id);
CREATE INDEX IF NOT EXISTS idx_redaction_audits_sensitivity_tier ON redaction_audits(sensitivity_tier);

CREATE INDEX IF NOT EXISTS idx_alert_events_timestamp ON alert_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_events_severity ON alert_events(severity);
CREATE INDEX IF NOT EXISTS idx_alert_events_event_type ON alert_events(event_type);
CREATE INDEX IF NOT EXISTS idx_alert_events_user_id ON alert_events(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_resolved ON alert_events(resolved);

CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_endpoint ON security_events(endpoint);

CREATE INDEX IF NOT EXISTS idx_memories_sensitivity_tier ON memories(sensitivity_tier);
CREATE INDEX IF NOT EXISTS idx_contexts_sensitivity_tier ON contexts(sensitivity_tier);

-- Views for common queries
CREATE OR REPLACE VIEW redaction_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    sensitivity_tier,
    COUNT(*) as total_redactions,
    COUNT(*) FILTER (WHERE redaction_applied = true) as successful_redactions,
    AVG(processing_time_ms) as avg_processing_time,
    AVG(entropy_score) as avg_entropy_score
FROM redaction_audits 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), sensitivity_tier
ORDER BY hour DESC;

CREATE OR REPLACE VIEW security_alert_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    severity,
    event_type,
    COUNT(*) as alert_count,
    COUNT(*) FILTER (WHERE resolved = false) as unresolved_count
FROM alert_events 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), severity, event_type
ORDER BY hour DESC;

-- Function to clean up old audit records (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_audit_records(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old redaction audits
    DELETE FROM redaction_audits 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old security events (keep alerts longer)
    DELETE FROM security_events 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Delete resolved alerts older than retention period
    DELETE FROM alert_events 
    WHERE resolved = true 
    AND resolved_at < NOW() - INTERVAL '1 day' * retention_days;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically set sensitivity tier based on content
CREATE OR REPLACE FUNCTION auto_classify_sensitivity()
RETURNS TRIGGER AS $$
BEGIN
    -- Simple auto-classification based on keywords
    IF NEW.sensitivity_tier IS NULL OR NEW.sensitivity_tier = 'internal' THEN
        -- Check for restricted keywords
        IF NEW.payload::text ~* '(password|secret|key|token|credential|ssn|credit.card)' THEN
            NEW.sensitivity_tier = 'restricted';
            NEW.auto_classified = true;
            NEW.classification_confidence = 0.8;
        -- Check for confidential keywords  
        ELSIF NEW.payload::text ~* '(confidential|private|internal|proprietary)' THEN
            NEW.sensitivity_tier = 'confidential';
            NEW.auto_classified = true;
            NEW.classification_confidence = 0.6;
        -- Check for public indicators
        ELSIF NEW.payload::text ~* '(public|open.source|documentation)' THEN
            NEW.sensitivity_tier = 'public';
            NEW.auto_classified = true;
            NEW.classification_confidence = 0.7;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply auto-classification trigger to memories
DROP TRIGGER IF EXISTS auto_classify_memory_sensitivity ON memories;
CREATE TRIGGER auto_classify_memory_sensitivity
    BEFORE INSERT OR UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION auto_classify_sensitivity();

-- Apply auto-classification trigger to contexts
DROP TRIGGER IF EXISTS auto_classify_context_sensitivity ON contexts;
CREATE TRIGGER auto_classify_context_sensitivity
    BEFORE INSERT OR UPDATE ON contexts
    FOR EACH ROW
    EXECUTE FUNCTION auto_classify_sensitivity();

-- Grant permissions for application user
GRANT SELECT, INSERT, UPDATE ON redaction_audits TO mem0user;
GRANT SELECT, INSERT, UPDATE ON alert_events TO mem0user;
GRANT SELECT, INSERT, UPDATE ON security_events TO mem0user;
GRANT SELECT ON redaction_summary TO mem0user;
GRANT SELECT ON security_alert_summary TO mem0user;
GRANT EXECUTE ON FUNCTION cleanup_old_audit_records(INTEGER) TO mem0user;
