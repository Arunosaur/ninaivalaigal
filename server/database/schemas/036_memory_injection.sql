-- SPEC-036: Memory Injection Rules
-- Smart memory injection, context rules, and AI integration
-- Created: 2024-09-23

-- Memory injection rules table
CREATE TABLE IF NOT EXISTS memory_injection_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(30) NOT NULL CHECK (trigger_type IN (
        'context_match', 'keyword_presence', 'semantic_similarity',
        'user_pattern', 'time_based', 'location_based', 'activity_based'
    )),
    strategy VARCHAR(20) NOT NULL CHECK (strategy IN (
        'immediate', 'contextual', 'proactive', 'reactive', 'background'
    )),
    priority VARCHAR(15) NOT NULL CHECK (priority IN (
        'critical', 'high', 'medium', 'low', 'background'
    )),
    conditions JSONB NOT NULL DEFAULT '{}',
    actions JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for injection rules
CREATE INDEX IF NOT EXISTS idx_memory_injection_rules_user ON memory_injection_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_injection_rules_trigger ON memory_injection_rules(trigger_type);
CREATE INDEX IF NOT EXISTS idx_memory_injection_rules_strategy ON memory_injection_rules(strategy);
CREATE INDEX IF NOT EXISTS idx_memory_injection_rules_priority ON memory_injection_rules(priority);
CREATE INDEX IF NOT EXISTS idx_memory_injection_rules_active ON memory_injection_rules(is_active);

-- Memory injection records table
CREATE TABLE IF NOT EXISTS memory_injection_records (
    injection_id VARCHAR(50) PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_id VARCHAR(50) REFERENCES memory_injection_rules(rule_id),
    relevance_score DECIMAL(3,2) CHECK (relevance_score >= 0 AND relevance_score <= 1),
    injection_reason TEXT,
    context_snapshot JSONB DEFAULT '{}',
    injected_at TIMESTAMP DEFAULT NOW(),
    user_response VARCHAR(20) CHECK (user_response IN ('accepted', 'dismissed', 'ignored', 'used')),
    response_time_seconds INTEGER,
    effectiveness_score DECIMAL(3,2) CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1)
);

-- Indexes for injection records
CREATE INDEX IF NOT EXISTS idx_memory_injection_records_memory ON memory_injection_records(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_injection_records_user_time ON memory_injection_records(user_id, injected_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_injection_records_rule ON memory_injection_records(rule_id);
CREATE INDEX IF NOT EXISTS idx_memory_injection_records_response ON memory_injection_records(user_response);
CREATE INDEX IF NOT EXISTS idx_memory_injection_records_relevance ON memory_injection_records(relevance_score DESC);

-- Injection context patterns table
CREATE TABLE IF NOT EXISTS injection_context_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_type VARCHAR(50) NOT NULL,
    context_signature JSONB NOT NULL,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    total_injections INTEGER DEFAULT 0,
    successful_injections INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    pattern_strength DECIMAL(3,2) DEFAULT 0.0,
    UNIQUE(user_id, context_type, context_signature)
);

-- Indexes for context patterns
CREATE INDEX IF NOT EXISTS idx_injection_context_patterns_user ON injection_context_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_injection_context_patterns_type ON injection_context_patterns(context_type);
CREATE INDEX IF NOT EXISTS idx_injection_context_patterns_success ON injection_context_patterns(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_injection_context_patterns_strength ON injection_context_patterns(pattern_strength DESC);

-- User injection preferences table
CREATE TABLE IF NOT EXISTS user_injection_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    injection_frequency VARCHAR(20) DEFAULT 'normal' CHECK (injection_frequency IN ('minimal', 'normal', 'frequent')),
    max_injections_per_session INTEGER DEFAULT 5 CHECK (max_injections_per_session > 0),
    preferred_strategies JSONB DEFAULT '["contextual", "proactive"]',
    blocked_triggers JSONB DEFAULT '[]',
    quiet_hours JSONB DEFAULT '{"start": 22, "end": 8}',
    location_aware BOOLEAN DEFAULT TRUE,
    activity_tracking BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Injection performance metrics table
CREATE TABLE IF NOT EXISTS injection_performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rule_id VARCHAR(50) REFERENCES memory_injection_rules(rule_id),
    trigger_type VARCHAR(30) NOT NULL,
    strategy VARCHAR(20) NOT NULL,
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    average_relevance DECIMAL(3,2) DEFAULT 0.0,
    average_response_time DECIMAL(6,2) DEFAULT 0.0,
    measurement_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, rule_id, measurement_date)
);

-- Index for performance metrics
CREATE INDEX IF NOT EXISTS idx_injection_performance_metrics_user_date ON injection_performance_metrics(user_id, measurement_date DESC);
CREATE INDEX IF NOT EXISTS idx_injection_performance_metrics_rule ON injection_performance_metrics(rule_id);
CREATE INDEX IF NOT EXISTS idx_injection_performance_metrics_trigger ON injection_performance_metrics(trigger_type);

-- Function to update injection performance metrics
CREATE OR REPLACE FUNCTION update_injection_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update daily performance metrics when injection records are updated
    INSERT INTO injection_performance_metrics 
    (user_id, rule_id, trigger_type, strategy, success_count, total_count, measurement_date)
    SELECT 
        NEW.user_id,
        NEW.rule_id,
        r.trigger_type,
        r.strategy,
        CASE WHEN NEW.user_response IN ('accepted', 'used') THEN 1 ELSE 0 END,
        1,
        CURRENT_DATE
    FROM memory_injection_rules r
    WHERE r.rule_id = NEW.rule_id
    ON CONFLICT (user_id, rule_id, measurement_date)
    DO UPDATE SET
        success_count = injection_performance_metrics.success_count + 
                       CASE WHEN NEW.user_response IN ('accepted', 'used') THEN 1 ELSE 0 END,
        total_count = injection_performance_metrics.total_count + 1,
        average_relevance = (injection_performance_metrics.average_relevance * 
                           (injection_performance_metrics.total_count - 1) + 
                           COALESCE(NEW.relevance_score, 0.5)) / injection_performance_metrics.total_count;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update performance metrics
DROP TRIGGER IF EXISTS trigger_update_injection_performance ON memory_injection_records;
CREATE TRIGGER trigger_update_injection_performance
    AFTER INSERT OR UPDATE ON memory_injection_records
    FOR EACH ROW
    EXECUTE FUNCTION update_injection_performance_metrics();

-- Function to calculate injection context patterns
CREATE OR REPLACE FUNCTION update_context_patterns(
    p_user_id UUID,
    p_context_type VARCHAR(50),
    p_context_signature JSONB,
    p_was_successful BOOLEAN
)
RETURNS void AS $$
BEGIN
    INSERT INTO injection_context_patterns 
    (user_id, context_type, context_signature, total_injections, successful_injections)
    VALUES (p_user_id, p_context_type, p_context_signature, 1, CASE WHEN p_was_successful THEN 1 ELSE 0 END)
    ON CONFLICT (user_id, context_type, context_signature)
    DO UPDATE SET
        total_injections = injection_context_patterns.total_injections + 1,
        successful_injections = injection_context_patterns.successful_injections + 
                               CASE WHEN p_was_successful THEN 1 ELSE 0 END,
        success_rate = (injection_context_patterns.successful_injections + 
                       CASE WHEN p_was_successful THEN 1 ELSE 0 END)::DECIMAL / 
                       (injection_context_patterns.total_injections + 1),
        pattern_strength = LEAST(1.0, (injection_context_patterns.total_injections + 1) / 10.0),
        last_updated = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to get optimal injection timing
CREATE OR REPLACE FUNCTION get_optimal_injection_timing(
    p_user_id UUID,
    p_context_type VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE(
    recommended_time TIME,
    confidence DECIMAL(3,2),
    based_on_patterns INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        TIME '14:00:00' as recommended_time,  -- Default afternoon time
        0.7::DECIMAL(3,2) as confidence,
        COUNT(*)::INTEGER as based_on_patterns
    FROM injection_context_patterns icp
    WHERE icp.user_id = p_user_id
        AND (p_context_type IS NULL OR icp.context_type = p_context_type)
        AND icp.success_rate > 0.5;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old injection data
CREATE OR REPLACE FUNCTION cleanup_old_injection_data()
RETURNS void AS $$
BEGIN
    -- Keep injection records for 6 months
    DELETE FROM memory_injection_records 
    WHERE injected_at < NOW() - INTERVAL '6 months';
    
    -- Keep performance metrics for 2 years
    DELETE FROM injection_performance_metrics 
    WHERE measurement_date < CURRENT_DATE - INTERVAL '2 years';
    
    -- Clean up unused context patterns (no activity for 3 months)
    DELETE FROM injection_context_patterns 
    WHERE last_updated < NOW() - INTERVAL '3 months'
        AND total_injections < 5;
    
    -- Deactivate old unused rules
    UPDATE memory_injection_rules 
    SET is_active = FALSE 
    WHERE updated_at < NOW() - INTERVAL '6 months'
        AND rule_id NOT IN (
            SELECT DISTINCT rule_id 
            FROM memory_injection_records 
            WHERE injected_at > NOW() - INTERVAL '1 month'
        );
END;
$$ LANGUAGE plpgsql;

-- View for injection analytics
CREATE OR REPLACE VIEW injection_analytics AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(mir.injection_id) as total_injections,
    COUNT(mir.injection_id) FILTER (WHERE mir.user_response IN ('accepted', 'used')) as successful_injections,
    ROUND(
        AVG(CASE 
            WHEN mir.user_response = 'used' THEN 1.0
            WHEN mir.user_response = 'accepted' THEN 0.8
            WHEN mir.user_response = 'dismissed' THEN 0.2
            ELSE 0.5
        END), 2
    ) as effectiveness_score,
    COUNT(DISTINCT mir.rule_id) as active_rules,
    AVG(mir.relevance_score) as avg_relevance_score,
    COUNT(DISTINCT icp.pattern_id) as learned_patterns,
    MAX(mir.injected_at) as last_injection_at
FROM users u
LEFT JOIN memory_injection_records mir ON mir.user_id = u.id
LEFT JOIN injection_context_patterns icp ON icp.user_id = u.id
GROUP BY u.id, u.email;

-- View for rule performance
CREATE OR REPLACE VIEW rule_performance_summary AS
SELECT 
    mir.rule_id,
    r.name as rule_name,
    r.trigger_type,
    r.strategy,
    r.priority,
    COUNT(mir.injection_id) as total_injections,
    COUNT(mir.injection_id) FILTER (WHERE mir.user_response IN ('accepted', 'used')) as successful_injections,
    ROUND(
        COUNT(mir.injection_id) FILTER (WHERE mir.user_response IN ('accepted', 'used'))::DECIMAL / 
        NULLIF(COUNT(mir.injection_id), 0), 2
    ) as success_rate,
    AVG(mir.relevance_score) as avg_relevance_score,
    AVG(mir.response_time_seconds) as avg_response_time
FROM memory_injection_rules r
LEFT JOIN memory_injection_records mir ON mir.rule_id = r.rule_id
WHERE r.is_active = TRUE
GROUP BY mir.rule_id, r.name, r.trigger_type, r.strategy, r.priority;

-- Comments for documentation
COMMENT ON TABLE memory_injection_rules IS 'User-defined rules for smart memory injection';
COMMENT ON TABLE memory_injection_records IS 'Log of all memory injection events and user responses';
COMMENT ON TABLE injection_context_patterns IS 'Learned patterns for optimal injection contexts';
COMMENT ON TABLE user_injection_preferences IS 'User preferences for memory injection behavior';
COMMENT ON TABLE injection_performance_metrics IS 'Performance metrics for injection rules and strategies';
COMMENT ON VIEW injection_analytics IS 'Analytics view for injection system performance per user';
COMMENT ON VIEW rule_performance_summary IS 'Performance summary for injection rules';

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_injection_rules TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_injection_records TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON injection_context_patterns TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_injection_preferences TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON injection_performance_metrics TO nina;
GRANT SELECT ON injection_analytics TO nina;
GRANT SELECT ON rule_performance_summary TO nina;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina;
