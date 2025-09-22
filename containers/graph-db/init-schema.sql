-- Initialize ninaivalaigal graph schema with Apache AGE
-- This script runs after Apache AGE extension is loaded

-- Verify Apache AGE is available
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'age') THEN
        RAISE EXCEPTION 'Apache AGE extension is not installed';
    END IF;
END $$;

-- Create the main graph for ninaivalaigal
SELECT ag_catalog.create_graph('ninaivalaigal_graph');

-- Set search path to include AGE catalog
SET search_path TO ag_catalog, "$user", public;

-- Create node labels (types)
SELECT create_vlabel('ninaivalaigal_graph', 'User');
SELECT create_vlabel('ninaivalaigal_graph', 'Memory');
SELECT create_vlabel('ninaivalaigal_graph', 'Context');
SELECT create_vlabel('ninaivalaigal_graph', 'Agent');
SELECT create_vlabel('ninaivalaigal_graph', 'Team');
SELECT create_vlabel('ninaivalaigal_graph', 'Organization');
SELECT create_vlabel('ninaivalaigal_graph', 'Session');
SELECT create_vlabel('ninaivalaigal_graph', 'Macro');
SELECT create_vlabel('ninaivalaigal_graph', 'Token');

-- Create edge labels (relationships)
SELECT create_elabel('ninaivalaigal_graph', 'CREATED');
SELECT create_elabel('ninaivalaigal_graph', 'ACCESSED');
SELECT create_elabel('ninaivalaigal_graph', 'BELONGS_TO');
SELECT create_elabel('ninaivalaigal_graph', 'MEMBER_OF');
SELECT create_elabel('ninaivalaigal_graph', 'OWNS');
SELECT create_elabel('ninaivalaigal_graph', 'LINKED_TO');
SELECT create_elabel('ninaivalaigal_graph', 'SIMILAR_TO');
SELECT create_elabel('ninaivalaigal_graph', 'REFERENCES');
SELECT create_elabel('ninaivalaigal_graph', 'TAGGED_WITH');
SELECT create_elabel('ninaivalaigal_graph', 'EXECUTED');
SELECT create_elabel('ninaivalaigal_graph', 'CONTAINS');
SELECT create_elabel('ninaivalaigal_graph', 'SHARED_WITH');
SELECT create_elabel('ninaivalaigal_graph', 'DERIVED_FROM');
SELECT create_elabel('ninaivalaigal_graph', 'FEEDBACK');
SELECT create_elabel('ninaivalaigal_graph', 'SUGGESTS');

-- Create indexes for performance
-- Note: AGE uses PostgreSQL indexes on the underlying tables

-- Create a view for easier graph querying (graceful handling of empty graph)
CREATE OR REPLACE VIEW graph_stats AS
SELECT 
    'ninaivalaigal_graph' as graph_name,
    COALESCE((SELECT count(*) FROM ag_catalog.ag_label WHERE name LIKE '%' AND kind = 'v'), 0) as node_types,
    COALESCE((SELECT count(*) FROM ag_catalog.ag_label WHERE name LIKE '%' AND kind = 'e'), 0) as edge_types,
    'Graph schema initialized' as status;

-- Grant permissions
GRANT USAGE ON SCHEMA ag_catalog TO graphuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ag_catalog TO graphuser;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'ninaivalaigal graph schema initialized successfully';
    RAISE NOTICE 'Graph: ninaivalaigal_graph created with % node types and % edge types',
        (SELECT count(*) FROM ag_label WHERE graph_name = 'ninaivalaigal_graph' AND kind = 'v'),
        (SELECT count(*) FROM ag_label WHERE graph_name = 'ninaivalaigal_graph' AND kind = 'e');
END $$;
