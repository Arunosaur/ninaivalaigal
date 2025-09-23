-- SPEC-041: Intelligent Related Memory Suggestions
-- Related memory discovery, intelligent suggestions, and context linking
-- Created: 2024-09-22

-- Memory suggestion interactions table
CREATE TABLE IF NOT EXISTS memory_suggestion_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(30) NOT NULL CHECK (suggestion_type IN (
        'semantic_similar', 'contextual_related', 'temporal_adjacent',
        'user_behavioral', 'collaborative', 'trending'
    )),
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN (
        'clicked', 'dismissed', 'used', 'bookmarked', 'shared', 'ignored'
    )),
    relevance_score DECIMAL(3,2) CHECK (relevance_score >= 0 AND relevance_score <= 1),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for suggestion interactions
CREATE INDEX IF NOT EXISTS idx_memory_suggestion_interactions_user_timestamp ON memory_suggestion_interactions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memory_suggestion_interactions_memory ON memory_suggestion_interactions(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_suggestion_interactions_type ON memory_suggestion_interactions(suggestion_type);
CREATE INDEX IF NOT EXISTS idx_memory_suggestion_interactions_interaction ON memory_suggestion_interactions(interaction_type);

-- Memory relationships table (for explicit relationships)
CREATE TABLE IF NOT EXISTS memory_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(30) NOT NULL CHECK (relationship_type IN (
        'similar_to', 'references', 'follows_from', 'contradicts',
        'supports', 'part_of', 'example_of', 'related_to'
    )),
    strength DECIMAL(3,2) DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    created_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    is_bidirectional BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

-- Indexes for memory relationships
CREATE INDEX IF NOT EXISTS idx_memory_relationships_source ON memory_relationships(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_target ON memory_relationships(target_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_type ON memory_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_strength ON memory_relationships(strength DESC);

-- Memory similarity cache (for performance)
CREATE TABLE IF NOT EXISTS memory_similarity_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id_1 UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    memory_id_2 UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    similarity_type VARCHAR(20) NOT NULL CHECK (similarity_type IN (
        'embedding', 'text', 'context', 'temporal', 'behavioral'
    )),
    similarity_score DECIMAL(5,4) CHECK (similarity_score >= 0 AND similarity_score <= 1),
    computed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',
    UNIQUE(memory_id_1, memory_id_2, similarity_type)
);

-- Indexes for similarity cache
CREATE INDEX IF NOT EXISTS idx_memory_similarity_cache_memory1 ON memory_similarity_cache(memory_id_1);
CREATE INDEX IF NOT EXISTS idx_memory_similarity_cache_memory2 ON memory_similarity_cache(memory_id_2);
CREATE INDEX IF NOT EXISTS idx_memory_similarity_cache_type ON memory_similarity_cache(similarity_type);
CREATE INDEX IF NOT EXISTS idx_memory_similarity_cache_score ON memory_similarity_cache(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_similarity_cache_expires ON memory_similarity_cache(expires_at);

-- User suggestion preferences
CREATE TABLE IF NOT EXISTS user_suggestion_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    algorithm_weights JSONB DEFAULT '{
        "semantic_similar": 0.25,
        "contextual_related": 0.20,
        "temporal_adjacent": 0.15,
        "user_behavioral": 0.20,
        "collaborative": 0.10,
        "trending": 0.10
    }',
    max_suggestions INTEGER DEFAULT 10 CHECK (max_suggestions > 0 AND max_suggestions <= 50),
    min_confidence DECIMAL(3,2) DEFAULT 0.3 CHECK (min_confidence >= 0 AND min_confidence <= 1),
    discovery_preferences JSONB DEFAULT '{
        "explore_old_memories": true,
        "include_trending": true,
        "collaborative_filtering": true,
        "temporal_suggestions": true
    }',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Memory access patterns (for behavioral suggestions)
CREATE TABLE IF NOT EXISTS memory_access_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    access_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT NOW(),
    access_duration_seconds INTEGER,
    access_context JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    UNIQUE(user_id, memory_id)
);

-- Indexes for access patterns
CREATE INDEX IF NOT EXISTS idx_memory_access_patterns_user ON memory_access_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_patterns_memory ON memory_access_patterns(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_patterns_count ON memory_access_patterns(access_count DESC);
CREATE INDEX IF NOT EXISTS idx_memory_access_patterns_last_accessed ON memory_access_patterns(last_accessed DESC);

-- Suggestion algorithm performance metrics
CREATE TABLE IF NOT EXISTS suggestion_algorithm_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_type VARCHAR(30) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    success_rate DECIMAL(3,2) CHECK (success_rate >= 0 AND success_rate <= 1),
    avg_relevance_score DECIMAL(3,2),
    total_suggestions INTEGER DEFAULT 0,
    positive_interactions INTEGER DEFAULT 0,
    measurement_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(algorithm_type, user_id, measurement_date)
);

-- Index for algorithm metrics
CREATE INDEX IF NOT EXISTS idx_suggestion_algorithm_metrics_algorithm ON suggestion_algorithm_metrics(algorithm_type);
CREATE INDEX IF NOT EXISTS idx_suggestion_algorithm_metrics_user_date ON suggestion_algorithm_metrics(user_id, measurement_date DESC);
CREATE INDEX IF NOT EXISTS idx_suggestion_algorithm_metrics_success_rate ON suggestion_algorithm_metrics(success_rate DESC);

-- Function to update memory access patterns
CREATE OR REPLACE FUNCTION update_memory_access_pattern(
    p_user_id UUID,
    p_memory_id UUID,
    p_access_duration INTEGER DEFAULT NULL,
    p_access_context JSONB DEFAULT '{}',
    p_session_id VARCHAR(100) DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO memory_access_patterns
    (user_id, memory_id, access_count, last_accessed, access_duration_seconds, access_context, session_id)
    VALUES (p_user_id, p_memory_id, 1, NOW(), p_access_duration, p_access_context, p_session_id)
    ON CONFLICT (user_id, memory_id)
    DO UPDATE SET
        access_count = memory_access_patterns.access_count + 1,
        last_accessed = NOW(),
        access_duration_seconds = COALESCE(p_access_duration, memory_access_patterns.access_duration_seconds),
        access_context = p_access_context,
        session_id = COALESCE(p_session_id, memory_access_patterns.session_id);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate memory similarity
CREATE OR REPLACE FUNCTION calculate_memory_similarity(
    p_memory_id_1 UUID,
    p_memory_id_2 UUID,
    p_similarity_type VARCHAR(20) DEFAULT 'embedding'
)
RETURNS DECIMAL(5,4) AS $$
DECLARE
    similarity_score DECIMAL(5,4);
BEGIN
    -- Check cache first
    SELECT ms.similarity_score INTO similarity_score
    FROM memory_similarity_cache ms
    WHERE ((ms.memory_id_1 = p_memory_id_1 AND ms.memory_id_2 = p_memory_id_2)
           OR (ms.memory_id_1 = p_memory_id_2 AND ms.memory_id_2 = p_memory_id_1))
        AND ms.similarity_type = p_similarity_type
        AND ms.expires_at > NOW();

    IF similarity_score IS NOT NULL THEN
        RETURN similarity_score;
    END IF;

    -- Calculate similarity based on type
    IF p_similarity_type = 'embedding' THEN
        -- Use pgvector cosine similarity
        SELECT (1 - (m1.embedding <=> m2.embedding)) INTO similarity_score
        FROM memories m1, memories m2
        WHERE m1.id = p_memory_id_1 AND m2.id = p_memory_id_2;

    ELSIF p_similarity_type = 'text' THEN
        -- Use text similarity
        SELECT ts_rank(to_tsvector('english', m1.content), to_tsquery('english',
                      replace(replace(m2.content, ' ', ' & '), '''', ''))) INTO similarity_score
        FROM memories m1, memories m2
        WHERE m1.id = p_memory_id_1 AND m2.id = p_memory_id_2;

    ELSIF p_similarity_type = 'temporal' THEN
        -- Calculate temporal similarity (closer in time = higher similarity)
        SELECT GREATEST(0, 1 - EXTRACT(EPOCH FROM ABS(m1.created_at - m2.created_at)) / 86400 / 30) INTO similarity_score
        FROM memories m1, memories m2
        WHERE m1.id = p_memory_id_1 AND m2.id = p_memory_id_2;

    ELSE
        similarity_score := 0.0;
    END IF;

    -- Cache the result
    INSERT INTO memory_similarity_cache
    (memory_id_1, memory_id_2, similarity_type, similarity_score)
    VALUES (p_memory_id_1, p_memory_id_2, p_similarity_type, COALESCE(similarity_score, 0.0))
    ON CONFLICT (memory_id_1, memory_id_2, similarity_type)
    DO UPDATE SET
        similarity_score = COALESCE(similarity_score, 0.0),
        computed_at = NOW(),
        expires_at = NOW() + INTERVAL '24 hours';

    RETURN COALESCE(similarity_score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- Function to get user's frequently accessed memories
CREATE OR REPLACE FUNCTION get_user_frequent_memories(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    memory_id UUID,
    access_count INTEGER,
    last_accessed TIMESTAMP,
    frequency_score DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        map.memory_id,
        map.access_count,
        map.last_accessed,
        LEAST(1.0, (map.access_count::DECIMAL / 100.0) *
              (1.0 - EXTRACT(EPOCH FROM NOW() - map.last_accessed) / 86400 / 30))::DECIMAL(3,2) as frequency_score
    FROM memory_access_patterns map
    JOIN memories m ON m.id = map.memory_id
    WHERE map.user_id = p_user_id
        AND m.user_id = p_user_id  -- Ensure user owns the memory
    ORDER BY frequency_score DESC, map.access_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired similarity cache
CREATE OR REPLACE FUNCTION cleanup_expired_similarity_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM memory_similarity_cache
    WHERE expires_at < NOW();

    -- Also clean up old suggestion interactions (keep 6 months)
    DELETE FROM memory_suggestion_interactions
    WHERE timestamp < NOW() - INTERVAL '6 months';

    -- Clean up old access patterns (keep 1 year)
    DELETE FROM memory_access_patterns
    WHERE last_accessed < NOW() - INTERVAL '1 year';
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update access patterns when memories are accessed
CREATE OR REPLACE FUNCTION trigger_update_access_pattern()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called when memories are accessed via API
    -- For now, it's a placeholder for manual access tracking
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- View for suggestion analytics
CREATE OR REPLACE VIEW memory_suggestion_analytics AS
SELECT
    u.id as user_id,
    u.email,
    COUNT(msi.interaction_id) as total_suggestions,
    COUNT(msi.interaction_id) FILTER (WHERE msi.interaction_type IN ('clicked', 'used')) as positive_interactions,
    ROUND(
        AVG(CASE
            WHEN msi.interaction_type = 'used' THEN 1.0
            WHEN msi.interaction_type = 'clicked' THEN 0.7
            WHEN msi.interaction_type = 'dismissed' THEN 0.0
            ELSE 0.3
        END), 2
    ) as satisfaction_score,
    COUNT(DISTINCT msi.suggestion_type) as algorithms_used,
    MAX(msi.timestamp) as last_suggestion_at,
    COUNT(DISTINCT map.memory_id) as memories_accessed,
    AVG(map.access_count) as avg_memory_access_count
FROM users u
LEFT JOIN memory_suggestion_interactions msi ON msi.user_id = u.id
LEFT JOIN memory_access_patterns map ON map.user_id = u.id
GROUP BY u.id, u.email;

-- Comments for documentation
COMMENT ON TABLE memory_suggestion_interactions IS 'User interactions with memory suggestions for learning';
COMMENT ON TABLE memory_relationships IS 'Explicit relationships between memories';
COMMENT ON TABLE memory_similarity_cache IS 'Cached similarity scores for performance';
COMMENT ON TABLE user_suggestion_preferences IS 'User preferences for suggestion algorithms';
COMMENT ON TABLE memory_access_patterns IS 'User memory access patterns for behavioral suggestions';
COMMENT ON TABLE suggestion_algorithm_metrics IS 'Performance metrics for suggestion algorithms';
COMMENT ON VIEW memory_suggestion_analytics IS 'Analytics view for suggestion system performance';

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_suggestion_interactions TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_relationships TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_similarity_cache TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_suggestion_preferences TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON memory_access_patterns TO nina;
GRANT SELECT, INSERT, UPDATE, DELETE ON suggestion_algorithm_metrics TO nina;
GRANT SELECT ON memory_suggestion_analytics TO nina;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina;
