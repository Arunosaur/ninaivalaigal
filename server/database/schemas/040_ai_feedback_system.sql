-- SPEC-040: AI Feedback System
-- AI feedback loops, context improvement, and learning system
-- Created: 2024-09-22

-- AI feedback events table
CREATE TABLE IF NOT EXISTS ai_feedback_events (
    event_id VARCHAR(50) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN (
        'memory_relevance', 'context_quality', 'suggestion_accuracy',
        'response_helpfulness', 'memory_injection'
    )),
    feedback_value VARCHAR(10) NOT NULL CHECK (feedback_value IN ('positive', 'negative', 'neutral')),
    context JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW(),
    memory_ids TEXT[], -- Array of memory IDs related to this feedback
    session_id VARCHAR(100),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Indexes for feedback events
CREATE INDEX IF NOT EXISTS idx_ai_feedback_events_user_timestamp ON ai_feedback_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_events_type ON ai_feedback_events(feedback_type);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_events_value ON ai_feedback_events(feedback_value);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_events_session ON ai_feedback_events(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_events_memory_ids ON ai_feedback_events USING GIN(memory_ids);

-- Learning patterns table
CREATE TABLE IF NOT EXISTS ai_learning_patterns (
    pattern_id VARCHAR(50) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    evidence_count INTEGER NOT NULL DEFAULT 0,
    parameters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for learning patterns
CREATE INDEX IF NOT EXISTS idx_ai_learning_patterns_user ON ai_learning_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_learning_patterns_type ON ai_learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_ai_learning_patterns_confidence ON ai_learning_patterns(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_ai_learning_patterns_active ON ai_learning_patterns(is_active);

-- Context improvements table
CREATE TABLE IF NOT EXISTS ai_context_improvements (
    improvement_id VARCHAR(50) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    improvement_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('high', 'medium', 'low')),
    estimated_impact DECIMAL(3,2) CHECK (estimated_impact >= 0 AND estimated_impact <= 1),
    implementation_status VARCHAR(20) DEFAULT 'pending' CHECK (implementation_status IN (
        'pending', 'in_progress', 'implemented', 'rejected'
    )),
    created_at TIMESTAMP DEFAULT NOW(),
    implemented_at TIMESTAMP,
    pattern_id VARCHAR(50) REFERENCES ai_learning_patterns(pattern_id)
);

-- Indexes for context improvements
CREATE INDEX IF NOT EXISTS idx_ai_context_improvements_user ON ai_context_improvements(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_context_improvements_priority ON ai_context_improvements(priority);
CREATE INDEX IF NOT EXISTS idx_ai_context_improvements_status ON ai_context_improvements(implementation_status);
CREATE INDEX IF NOT EXISTS idx_ai_context_improvements_impact ON ai_context_improvements(estimated_impact DESC);

-- User learning preferences table
CREATE TABLE IF NOT EXISTS ai_user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    memory_relevance_threshold DECIMAL(3,2) DEFAULT 0.7,
    context_length_preference VARCHAR(20) DEFAULT 'medium' CHECK (context_length_preference IN ('short', 'medium', 'long')),
    feedback_frequency VARCHAR(20) DEFAULT 'normal' CHECK (feedback_frequency IN ('minimal', 'normal', 'frequent')),
    auto_learning_enabled BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Memory interaction tracking (for implicit feedback)
CREATE TABLE IF NOT EXISTS ai_memory_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    interaction_type VARCHAR(30) NOT NULL CHECK (interaction_type IN (
        'viewed', 'used', 'edited', 'deleted', 'shared', 'bookmarked'
    )),
    context JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    duration_seconds INTEGER, -- How long the memory was viewed/used
    relevance_score DECIMAL(3,2) -- Implicit relevance based on interaction
);

-- Indexes for memory interactions
CREATE INDEX IF NOT EXISTS idx_ai_memory_interactions_user_timestamp ON ai_memory_interactions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_memory_interactions_memory ON ai_memory_interactions(memory_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_interactions_type ON ai_memory_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_ai_memory_interactions_session ON ai_memory_interactions(session_id);

-- Learning effectiveness metrics
CREATE TABLE IF NOT EXISTS ai_learning_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    measurement_date DATE NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for learning metrics
CREATE INDEX IF NOT EXISTS idx_ai_learning_metrics_user_date ON ai_learning_metrics(user_id, measurement_date DESC);
CREATE INDEX IF NOT EXISTS idx_ai_learning_metrics_type ON ai_learning_metrics(metric_type);

-- Function to calculate learning effectiveness
CREATE OR REPLACE FUNCTION calculate_learning_effectiveness(p_user_id UUID, p_days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    effectiveness_score DECIMAL(3,2),
    improvement_trend VARCHAR(20),
    total_feedback INTEGER,
    positive_ratio DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH feedback_stats AS (
        SELECT
            COUNT(*) as total_count,
            COUNT(*) FILTER (WHERE feedback_value = 'positive') as positive_count,
            COUNT(*) FILTER (WHERE feedback_value = 'negative') as negative_count,
            AVG(CASE
                WHEN feedback_value = 'positive' THEN 1.0
                WHEN feedback_value = 'neutral' THEN 0.5
                ELSE 0.0
            END) as avg_score
        FROM ai_feedback_events
        WHERE user_id = p_user_id
            AND timestamp >= NOW() - INTERVAL '%s days'
    ),
    trend_analysis AS (
        SELECT
            AVG(CASE
                WHEN feedback_value = 'positive' THEN 1.0
                WHEN feedback_value = 'neutral' THEN 0.5
                ELSE 0.0
            END) as recent_score
        FROM ai_feedback_events
        WHERE user_id = p_user_id
            AND timestamp >= NOW() - INTERVAL '%s days'
    )
    SELECT
        COALESCE(fs.avg_score, 0.5)::DECIMAL(3,2) as effectiveness_score,
        CASE
            WHEN ta.recent_score > fs.avg_score THEN 'improving'
            WHEN ta.recent_score < fs.avg_score THEN 'declining'
            ELSE 'stable'
        END as improvement_trend,
        COALESCE(fs.total_count, 0)::INTEGER as total_feedback,
        CASE
            WHEN fs.total_count > 0 THEN (fs.positive_count::DECIMAL / fs.total_count)
            ELSE 0.0
        END::DECIMAL(3,2) as positive_ratio
    FROM feedback_stats fs
    CROSS JOIN trend_analysis ta;
END;
$$ LANGUAGE plpgsql;

-- Function to update learning patterns
CREATE OR REPLACE FUNCTION update_learning_patterns()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-generate patterns when enough feedback is collected
    IF (SELECT COUNT(*) FROM ai_feedback_events WHERE user_id = NEW.user_id) % 10 = 0 THEN
        -- Schedule pattern analysis (would be handled by background job)
        INSERT INTO ai_learning_metrics (user_id, metric_type, metric_value, measurement_date)
        VALUES (NEW.user_id, 'pattern_analysis_trigger', 1.0, CURRENT_DATE)
        ON CONFLICT DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update learning patterns
DROP TRIGGER IF EXISTS trigger_update_learning_patterns ON ai_feedback_events;
CREATE TRIGGER trigger_update_learning_patterns
    AFTER INSERT ON ai_feedback_events
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_patterns();

-- Function to clean old feedback data
CREATE OR REPLACE FUNCTION cleanup_old_feedback_data()
RETURNS void AS $$
BEGIN
    -- Keep feedback events for 1 year
    DELETE FROM ai_feedback_events
    WHERE timestamp < NOW() - INTERVAL '1 year';

    -- Keep memory interactions for 6 months
    DELETE FROM ai_memory_interactions
    WHERE timestamp < NOW() - INTERVAL '6 months';

    -- Keep learning metrics for 2 years
    DELETE FROM ai_learning_metrics
    WHERE created_at < NOW() - INTERVAL '2 years';

    -- Deactivate old learning patterns (don't delete, keep for analysis)
    UPDATE ai_learning_patterns
    SET is_active = FALSE
    WHERE last_updated < NOW() - INTERVAL '3 months'
        AND confidence < 0.6;
END;
$$ LANGUAGE plpgsql;

-- View for feedback analytics
CREATE OR REPLACE VIEW ai_feedback_analytics AS
SELECT
    u.id as user_id,
    u.email,
    COUNT(afe.event_id) as total_feedback,
    COUNT(afe.event_id) FILTER (WHERE afe.feedback_value = 'positive') as positive_feedback,
    COUNT(afe.event_id) FILTER (WHERE afe.feedback_value = 'negative') as negative_feedback,
    COUNT(afe.event_id) FILTER (WHERE afe.feedback_value = 'neutral') as neutral_feedback,
    ROUND(
        AVG(CASE
            WHEN afe.feedback_value = 'positive' THEN 1.0
            WHEN afe.feedback_value = 'neutral' THEN 0.5
            ELSE 0.0
        END), 2
    ) as satisfaction_score,
    COUNT(DISTINCT alp.pattern_id) as active_patterns,
    COUNT(DISTINCT aci.improvement_id) as pending_improvements,
    MAX(afe.timestamp) as last_feedback_at
FROM users u
LEFT JOIN ai_feedback_events afe ON afe.user_id = u.id
LEFT JOIN ai_learning_patterns alp ON alp.user_id = u.id AND alp.is_active = TRUE
LEFT JOIN ai_context_improvements aci ON aci.user_id = u.id AND aci.implementation_status = 'pending'
GROUP BY u.id, u.email;

-- Comments for documentation
COMMENT ON TABLE ai_feedback_events IS 'User feedback events for AI learning system';
COMMENT ON TABLE ai_learning_patterns IS 'Learned patterns from user feedback analysis';
COMMENT ON TABLE ai_context_improvements IS 'Generated improvements for context optimization';
COMMENT ON TABLE ai_user_preferences IS 'User preferences for AI learning behavior';
COMMENT ON TABLE ai_memory_interactions IS 'Implicit feedback from memory interactions';
COMMENT ON TABLE ai_learning_metrics IS 'Metrics tracking learning system effectiveness';
COMMENT ON VIEW ai_feedback_analytics IS 'Analytics view for feedback system performance';

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_feedback_events TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_learning_patterns TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_context_improvements TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_user_preferences TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_memory_interactions TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_learning_metrics TO nina;
GRANT SELECT ON ai_feedback_analytics TO nina;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina;
