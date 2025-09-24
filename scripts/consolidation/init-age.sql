-- Initialize Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS vector;

-- Load AGE into search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the main graph
SELECT create_graph('ninaivalaigal_intelligence');

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
