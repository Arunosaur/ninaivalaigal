-- SPEC-040/041: Graph Intelligence Integration
-- Apache AGE graph database schema for memory-token-user relationships
-- Enables graph-based reasoning, context injection, and AI differentiation

-- Load Apache AGE extension if not already loaded
CREATE EXTENSION IF NOT EXISTS age;

-- Load the AGE extension into the search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the graph for ninaivalaigal intelligence
SELECT create_graph('ninaivalaigal_intelligence');

-- =============================================================================
-- GRAPH SCHEMA SETUP: Memory-Token-User Intelligence Network
-- =============================================================================

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

-- =============================================================================
-- GRAPH INTELLIGENCE TABLES: Metadata and Analytics
-- =============================================================================

-- Graph sync status tracking
CREATE TABLE IF NOT EXISTS graph_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    last_sync_at TIMESTAMP DEFAULT NOW(),
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending, syncing, complete, error
    records_synced INTEGER DEFAULT 0,
    sync_duration_ms INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
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
    cluster_type VARCHAR(50) NOT NULL, -- memory_cluster, token_cluster, user_cluster
    entity_ids UUID[] NOT NULL,
    cluster_center UUID, -- central entity in the cluster
    cohesion_score DECIMAL(5,4) NOT NULL, -- how tightly clustered
    size INTEGER NOT NULL,
    algorithm_used VARCHAR(50) NOT NULL, -- louvain, leiden, kmeans
    algorithm_params JSONB DEFAULT '{}',
    calculated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours'),
    metadata JSONB DEFAULT '{}'
);

-- Graph path analysis
CREATE TABLE IF NOT EXISTS graph_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    path_length INTEGER NOT NULL,
    path_nodes UUID[] NOT NULL,
    path_relationships VARCHAR(50)[] NOT NULL,
    path_strength DECIMAL(5,4) NOT NULL,
    path_type VARCHAR(50) NOT NULL, -- shortest, strongest, most_frequent
    calculated_at TIMESTAMP DEFAULT NOW(),
    calculation_time_ms INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Graph sync status indexes
CREATE INDEX IF NOT EXISTS idx_graph_sync_status_table ON graph_sync_status(table_name);
CREATE INDEX IF NOT EXISTS idx_graph_sync_status_updated ON graph_sync_status(updated_at);

-- Graph analytics indexes
CREATE INDEX IF NOT EXISTS idx_graph_analytics_metric ON graph_analytics(metric_name, metric_type);
CREATE INDEX IF NOT EXISTS idx_graph_analytics_entity ON graph_analytics(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_graph_analytics_calculated ON graph_analytics(calculated_at);

-- Graph reasoning cache indexes
CREATE INDEX IF NOT EXISTS idx_graph_reasoning_query_hash ON graph_reasoning_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_graph_reasoning_query_type ON graph_reasoning_cache(query_type);
CREATE INDEX IF NOT EXISTS idx_graph_reasoning_expires ON graph_reasoning_cache(expires_at);

-- Graph intelligence insights indexes
CREATE INDEX IF NOT EXISTS idx_graph_insights_type ON graph_intelligence_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_graph_insights_user ON graph_intelligence_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_graph_insights_team ON graph_intelligence_insights(team_id);
CREATE INDEX IF NOT EXISTS idx_graph_insights_confidence ON graph_intelligence_insights(confidence_score);

-- Graph relationship strength indexes
CREATE INDEX IF NOT EXISTS idx_graph_rel_strength_source ON graph_relationship_strength(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_graph_rel_strength_target ON graph_relationship_strength(target_id, target_type);
CREATE INDEX IF NOT EXISTS idx_graph_rel_strength_type ON graph_relationship_strength(relationship_type);
CREATE INDEX IF NOT EXISTS idx_graph_rel_strength_score ON graph_relationship_strength(strength_score);

-- Graph clusters indexes
CREATE INDEX IF NOT EXISTS idx_graph_clusters_type ON graph_clusters(cluster_type);
CREATE INDEX IF NOT EXISTS idx_graph_clusters_calculated ON graph_clusters(calculated_at);
CREATE INDEX IF NOT EXISTS idx_graph_clusters_expires ON graph_clusters(expires_at);

-- Graph paths indexes
CREATE INDEX IF NOT EXISTS idx_graph_paths_source ON graph_paths(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_paths_target ON graph_paths(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_paths_type ON graph_paths(path_type);
CREATE INDEX IF NOT EXISTS idx_graph_paths_length ON graph_paths(path_length);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_graph_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER update_graph_sync_status_timestamp
    BEFORE UPDATE ON graph_sync_status
    FOR EACH ROW EXECUTE FUNCTION update_graph_timestamp();

CREATE TRIGGER update_graph_reasoning_cache_timestamp
    BEFORE UPDATE ON graph_reasoning_cache
    FOR EACH ROW EXECUTE FUNCTION update_graph_timestamp();

-- Function to increment cache hits
CREATE OR REPLACE FUNCTION increment_cache_hits()
RETURNS TRIGGER AS $$
BEGIN
    NEW.cache_hits = OLD.cache_hits + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate relationship strength decay
CREATE OR REPLACE FUNCTION calculate_relationship_decay()
RETURNS TRIGGER AS $$
BEGIN
    -- Apply time-based decay to relationship strength
    IF OLD.calculated_at < NOW() - INTERVAL '1 day' THEN
        NEW.strength_score = GREATEST(
            OLD.strength_score * OLD.decay_factor,
            0.0001  -- minimum strength threshold
        );
        NEW.calculated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_graph_relationship_decay
    BEFORE UPDATE ON graph_relationship_strength
    FOR EACH ROW EXECUTE FUNCTION calculate_relationship_decay();

-- =============================================================================
-- VIEWS FOR CONVENIENT ACCESS
-- =============================================================================

-- Active graph insights view
CREATE OR REPLACE VIEW active_graph_insights AS
SELECT 
    i.*,
    u.name as user_name,
    t.name as team_name
FROM graph_intelligence_insights i
LEFT JOIN users u ON i.user_id = u.id
LEFT JOIN teams t ON i.team_id = t.id
WHERE i.expires_at > NOW()
ORDER BY i.confidence_score DESC, i.created_at DESC;

-- Strong relationships view
CREATE OR REPLACE VIEW strong_graph_relationships AS
SELECT 
    r.*,
    CASE 
        WHEN r.source_type = 'Memory' THEN m1.title
        WHEN r.source_type = 'User' THEN u1.name
        WHEN r.source_type = 'Token' THEN 'Token'
        ELSE r.source_type
    END as source_name,
    CASE 
        WHEN r.target_type = 'Memory' THEN m2.title
        WHEN r.target_type = 'User' THEN u2.name
        WHEN r.target_type = 'Token' THEN 'Token'
        ELSE r.target_type
    END as target_name
FROM graph_relationship_strength r
LEFT JOIN memories m1 ON r.source_id = m1.id AND r.source_type = 'Memory'
LEFT JOIN memories m2 ON r.target_id = m2.id AND r.target_type = 'Memory'
LEFT JOIN users u1 ON r.source_id = u1.id AND r.source_type = 'User'
LEFT JOIN users u2 ON r.target_id = u2.id AND r.target_type = 'User'
WHERE r.strength_score > 0.5
ORDER BY r.strength_score DESC;

-- Current graph clusters view
CREATE OR REPLACE VIEW current_graph_clusters AS
SELECT 
    c.*,
    array_length(c.entity_ids, 1) as actual_size
FROM graph_clusters c
WHERE c.expires_at > NOW()
ORDER BY c.cohesion_score DESC, c.calculated_at DESC;

-- Graph performance metrics view
CREATE OR REPLACE VIEW graph_performance_metrics AS
SELECT 
    'reasoning_cache' as component,
    COUNT(*) as total_entries,
    AVG(execution_time_ms) as avg_execution_time_ms,
    SUM(cache_hits) as total_cache_hits,
    AVG(confidence_score) as avg_confidence_score
FROM graph_reasoning_cache
WHERE created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'intelligence_insights' as component,
    COUNT(*) as total_entries,
    0 as avg_execution_time_ms,
    0 as total_cache_hits,
    AVG(confidence_score) as avg_confidence_score
FROM graph_intelligence_insights
WHERE created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'relationship_strength' as component,
    COUNT(*) as total_entries,
    0 as avg_execution_time_ms,
    0 as total_cache_hits,
    AVG(strength_score) as avg_confidence_score
FROM graph_relationship_strength
WHERE calculated_at > NOW() - INTERVAL '24 hours';

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Insert initial sync status records
INSERT INTO graph_sync_status (table_name, sync_status) VALUES
('memories', 'pending'),
('users', 'pending'),
('teams', 'pending'),
('contexts', 'pending')
ON CONFLICT DO NOTHING;

-- Insert initial graph analytics configuration
INSERT INTO graph_analytics (metric_name, metric_value, metric_type, entity_type) VALUES
('total_nodes', 0, 'node_count', 'all'),
('total_edges', 0, 'edge_count', 'all'),
('avg_clustering_coefficient', 0, 'clustering', 'all'),
('graph_density', 0, 'density', 'all')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- CLEANUP FUNCTIONS
-- =============================================================================

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_graph_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM graph_reasoning_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM graph_intelligence_insights WHERE expires_at < NOW();
    
    DELETE FROM graph_clusters WHERE expires_at < NOW();
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to recalculate graph metrics
CREATE OR REPLACE FUNCTION recalculate_graph_metrics()
RETURNS VOID AS $$
BEGIN
    -- This would contain actual graph metric calculations
    -- For now, we'll update the timestamp to indicate recalculation
    UPDATE graph_analytics 
    SET calculated_at = NOW()
    WHERE metric_type IN ('node_count', 'edge_count', 'clustering', 'density');
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON SCHEMA ag_catalog IS 'Apache AGE graph database schema for ninaivalaigal intelligence';
COMMENT ON TABLE graph_sync_status IS 'Tracks synchronization status between relational and graph data';
COMMENT ON TABLE graph_analytics IS 'Stores calculated graph metrics and analytics';
COMMENT ON TABLE graph_reasoning_cache IS 'Caches graph query results for performance optimization';
COMMENT ON TABLE graph_intelligence_insights IS 'Stores AI-generated insights from graph analysis';
COMMENT ON TABLE graph_relationship_strength IS 'Tracks and calculates relationship strength between entities';
COMMENT ON TABLE graph_clusters IS 'Stores graph clustering analysis results';
COMMENT ON TABLE graph_paths IS 'Stores calculated paths between entities in the graph';

COMMENT ON VIEW active_graph_insights IS 'Current active insights with user and team information';
COMMENT ON VIEW strong_graph_relationships IS 'Relationships with high strength scores';
COMMENT ON VIEW current_graph_clusters IS 'Currently valid graph clusters';
COMMENT ON VIEW graph_performance_metrics IS 'Performance metrics for graph operations';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'SPEC-040/041: Graph Intelligence schema created successfully!';
    RAISE NOTICE 'Graph name: ninaivalaigal_intelligence';
    RAISE NOTICE 'Node types: Memory, Token, User, Team, Context, Macro, Narrative';
    RAISE NOTICE 'Edge types: 15 relationship types for comprehensive graph reasoning';
    RAISE NOTICE 'Analytics tables: 6 tables for metrics, caching, and insights';
    RAISE NOTICE 'Performance views: 4 views for convenient data access';
END $$;
