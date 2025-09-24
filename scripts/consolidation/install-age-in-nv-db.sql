-- ============================================================================
-- SINGLE DATABASE CONSOLIDATION: Install Apache AGE in nv-db
-- ============================================================================
-- This script installs Apache AGE extension in the existing nv-db database
-- Eliminates the need for separate graph-db container
-- Creates unified PostgreSQL + Graph database architecture

-- Install Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE extension into search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the main graph for ninaivalaigal intelligence
SELECT create_graph('ninaivalaigal_intelligence');

-- ============================================================================
-- GRAPH SCHEMA: Memory-Token-User Intelligence Network
-- ============================================================================

-- Create vertex labels (node types)
SELECT create_vlabel('ninaivalaigal_intelligence', 'Memory');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Token');
SELECT create_vlabel('ninaivalaigal_intelligence', 'User');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Team');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Context');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Macro');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Narrative');

-- Create edge labels (relationship types)
SELECT create_elabel('ninaivalaigal_intelligence', 'CREATED');
SELECT create_elabel('ninaivalaigal_intelligence', 'OWNS');
SELECT create_elabel('ninaivalaigal_intelligence', 'TAGGED_WITH');
SELECT create_elabel('ninaivalaigal_intelligence', 'DERIVED_FROM');
SELECT create_elabel('ninaivalaigal_intelligence', 'MEMBER_OF');
SELECT create_elabel('ninaivalaigal_intelligence', 'RELATED_TO');
SELECT create_elabel('ninaivalaigal_intelligence', 'ACCESSED');
SELECT create_elabel('ninaivalaigal_intelligence', 'SIMILAR_TO');
SELECT create_elabel('ninaivalaigal_intelligence', 'CONTAINS');
SELECT create_elabel('ninaivalaigal_intelligence', 'INFLUENCED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'PROMOTED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'ANNOTATED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'FOLLOWED');
SELECT create_elabel('ninaivalaigal_intelligence', 'COLLABORATED_ON');
SELECT create_elabel('ninaivalaigal_intelligence', 'SHARED_WITH');

-- ============================================================================
-- GRAPH ANALYTICS TABLES: Now in same database as relational data
-- ============================================================================

-- Graph sync status tracking
CREATE TABLE IF NOT EXISTS graph_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_id VARCHAR(100) NOT NULL UNIQUE,
    table_name VARCHAR(100) NOT NULL,
    total_records INTEGER DEFAULT 0,
    synced_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    sync_status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    error_details TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0
);

-- Graph analytics and metrics
CREATE TABLE IF NOT EXISTS graph_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- node_count, edge_count, centrality, clustering
    entity_id UUID, -- specific entity the metric applies to
    entity_type VARCHAR(50), -- Memory, Token, User, Team
    calculated_at TIMESTAMP DEFAULT NOW(),
    calculation_duration_ms INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Graph reasoning cache
CREATE TABLE IF NOT EXISTS graph_reasoning_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA256 of the query
    query_type VARCHAR(50) NOT NULL, -- similarity, path, recommendation, clustering
    query_params JSONB NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score DECIMAL(5,4) DEFAULT 0.0,
    execution_time_ms INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '1 hour'),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Graph intelligence insights
CREATE TABLE IF NOT EXISTS graph_intelligence_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_type VARCHAR(50) NOT NULL, -- pattern, anomaly, recommendation, prediction
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    impact_level VARCHAR(20) NOT NULL, -- low, medium, high, critical
    entity_ids UUID[] DEFAULT '{}', -- entities involved in the insight
    graph_data JSONB NOT NULL, -- graph structure supporting the insight
    actionable_items TEXT[] DEFAULT '{}',
    user_id UUID REFERENCES users(id),
    team_id UUID REFERENCES teams(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '7 days')
);

-- Graph relationship strength tracking
CREATE TABLE IF NOT EXISTS graph_relationship_strength (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    strength_score DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    interaction_count INTEGER DEFAULT 1,
    last_interaction TIMESTAMP DEFAULT NOW(),
    decay_factor DECIMAL(3,2) DEFAULT 0.95, -- for time-based decay
    calculated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    UNIQUE(source_id, target_id, relationship_type)
);

-- Graph clustering results
CREATE TABLE IF NOT EXISTS graph_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    cluster_center_id UUID, -- reference to the cluster center entity
    cohesion_score DECIMAL(5,4) DEFAULT 0.0,
    cluster_size INTEGER DEFAULT 1,
    calculated_at TIMESTAMP DEFAULT NOW(),
    algorithm_used VARCHAR(50) DEFAULT 'community_detection',
    metadata JSONB DEFAULT '{}'
);

-- Graph path analysis
CREATE TABLE IF NOT EXISTS graph_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    path_length INTEGER NOT NULL,
    path_strength DECIMAL(5,4) DEFAULT 0.0,
    path_nodes UUID[] NOT NULL,
    path_relationships VARCHAR(50)[] NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    query_context JSONB DEFAULT '{}',

    UNIQUE(source_id, target_id, path_length)
);

-- ============================================================================
-- PERFORMANCE VIEWS: Unified analytics across relational and graph data
-- ============================================================================

-- Active insights with user context
CREATE OR REPLACE VIEW active_graph_insights AS
SELECT
    gi.*,
    u.name as user_name,
    u.email as user_email,
    t.name as team_name
FROM graph_intelligence_insights gi
LEFT JOIN users u ON gi.user_id = u.id
LEFT JOIN teams t ON gi.team_id = t.id
WHERE gi.expires_at > NOW()
ORDER BY gi.confidence_score DESC, gi.created_at DESC;

-- Strong relationships for recommendation engine
CREATE OR REPLACE VIEW strong_graph_relationships AS
SELECT *
FROM graph_relationship_strength
WHERE strength_score > 0.7
  AND last_interaction > (NOW() - INTERVAL '30 days')
ORDER BY strength_score DESC, last_interaction DESC;

-- Current valid clusters
CREATE OR REPLACE VIEW current_graph_clusters AS
SELECT
    cluster_id,
    COUNT(*) as cluster_size,
    AVG(cohesion_score) as avg_cohesion,
    MAX(calculated_at) as last_calculated
FROM graph_clusters c
WHERE calculated_at > (NOW() - INTERVAL '24 hours')
GROUP BY cluster_id
ORDER BY avg_cohesion DESC, cluster_size DESC;

-- Graph performance metrics
CREATE OR REPLACE VIEW graph_performance_metrics AS
SELECT
    'reasoning_cache' as component,
    COUNT(*) as total_entries,
    AVG(execution_time_ms) as avg_execution_time_ms,
    SUM(cache_hits) as total_cache_hits,
    COUNT(*) FILTER (WHERE expires_at > NOW()) as active_entries
FROM graph_reasoning_cache
UNION ALL
SELECT
    'relationship_strength' as component,
    COUNT(*) as total_entries,
    AVG(strength_score * 1000) as avg_strength_score_x1000, -- scale for consistency
    COUNT(*) FILTER (WHERE last_interaction > NOW() - INTERVAL '7 days') as recent_interactions,
    COUNT(*) FILTER (WHERE strength_score > 0.5) as strong_relationships
FROM graph_relationship_strength
UNION ALL
SELECT
    'graph_clusters' as component,
    COUNT(DISTINCT cluster_id) as total_clusters,
    AVG(cohesion_score * 1000) as avg_cohesion_x1000, -- scale for consistency
    COUNT(*) FILTER (WHERE calculated_at > NOW() - INTERVAL '24 hours') as recent_calculations,
    COUNT(*) as total_cluster_memberships
FROM graph_clusters;

-- ============================================================================
-- UTILITY FUNCTIONS: Graph maintenance and optimization
-- ============================================================================

-- Function to cleanup expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_graph_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM graph_reasoning_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    DELETE FROM graph_intelligence_insights WHERE expires_at < NOW();

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to recalculate relationship strength with decay
CREATE OR REPLACE FUNCTION apply_relationship_decay()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE graph_relationship_strength
    SET
        strength_score = strength_score * decay_factor,
        calculated_at = NOW()
    WHERE last_interaction < (NOW() - INTERVAL '7 days')
      AND strength_score > 0.01; -- don't decay below threshold

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to recalculate graph metrics
CREATE OR REPLACE FUNCTION recalculate_graph_metrics()
RETURNS VOID AS $$
BEGIN
    -- This would contain actual graph metric calculations
    -- For now, just update the calculated_at timestamp
    UPDATE graph_analytics SET calculated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INDEXES: Performance optimization for graph operations
-- ============================================================================

-- Graph sync status indexes
CREATE INDEX IF NOT EXISTS idx_graph_sync_status_table ON graph_sync_status(table_name);
CREATE INDEX IF NOT EXISTS idx_graph_sync_status_status ON graph_sync_status(sync_status);

-- Graph analytics indexes
CREATE INDEX IF NOT EXISTS idx_graph_analytics_entity ON graph_analytics(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_graph_analytics_metric ON graph_analytics(metric_name, metric_type);
CREATE INDEX IF NOT EXISTS idx_graph_analytics_calculated ON graph_analytics(calculated_at);

-- Graph reasoning cache indexes
CREATE INDEX IF NOT EXISTS idx_graph_reasoning_cache_type ON graph_reasoning_cache(query_type);
CREATE INDEX IF NOT EXISTS idx_graph_reasoning_cache_expires ON graph_reasoning_cache(expires_at);

-- Graph relationship strength indexes
CREATE INDEX IF NOT EXISTS idx_graph_relationship_source ON graph_relationship_strength(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_graph_relationship_target ON graph_relationship_strength(target_id, target_type);
CREATE INDEX IF NOT EXISTS idx_graph_relationship_strength ON graph_relationship_strength(strength_score);
CREATE INDEX IF NOT EXISTS idx_graph_relationship_interaction ON graph_relationship_strength(last_interaction);

-- Graph clusters indexes
CREATE INDEX IF NOT EXISTS idx_graph_clusters_cluster_id ON graph_clusters(cluster_id);
CREATE INDEX IF NOT EXISTS idx_graph_clusters_entity ON graph_clusters(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_graph_clusters_calculated ON graph_clusters(calculated_at);

-- Graph paths indexes
CREATE INDEX IF NOT EXISTS idx_graph_paths_source ON graph_paths(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_paths_target ON graph_paths(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_paths_length ON graph_paths(path_length);

-- ============================================================================
-- COMMENTS: Documentation for consolidated schema
-- ============================================================================

COMMENT ON SCHEMA ag_catalog IS 'Apache AGE graph database schema for ninaivalaigal intelligence';
COMMENT ON TABLE graph_sync_status IS 'Tracks synchronization status between relational and graph data';
COMMENT ON TABLE graph_analytics IS 'Stores calculated graph metrics and analytics';
COMMENT ON TABLE graph_reasoning_cache IS 'Caches graph query results for performance optimization';
COMMENT ON TABLE graph_intelligence_insights IS 'Stores AI-generated insights from graph analysis';
COMMENT ON TABLE graph_relationship_strength IS 'Tracks and calculates relationship strength between entities';
COMMENT ON TABLE graph_clusters IS 'Stores graph clustering results and community detection';
COMMENT ON TABLE graph_paths IS 'Caches calculated paths between entities for performance';

COMMENT ON VIEW active_graph_insights IS 'Current active insights with user and team information';
COMMENT ON VIEW strong_graph_relationships IS 'Relationships with high strength scores';
COMMENT ON VIEW current_graph_clusters IS 'Currently valid graph clusters';
COMMENT ON VIEW graph_performance_metrics IS 'Performance metrics for graph operations';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Apache AGE successfully installed in nv-db!';
    RAISE NOTICE 'Graph schema created: ninaivalaigal_intelligence';
    RAISE NOTICE 'Analytics tables created in same database';
    RAISE NOTICE 'Single source of truth established ✅';
END $$;
