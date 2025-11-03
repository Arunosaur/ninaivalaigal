-- SPEC-060 Apache AGE Property Graph Schema
-- Comprehensive schema for ninaivalaigal memory network

-- Node Types
-- Users: Platform users and team members
-- Memories: Core memory tokens and content
-- Macros: Automated sequences and workflows
-- Agents: AI agents and processing entities
-- Topics: Categorization and tagging
-- Sources: External references and origins
-- Contexts: Conversation and session contexts
-- Teams: Organizational units
-- Organizations: Top-level organizational entities

-- Relationship Types
-- CREATED: User/Agent created entity
-- LINKED_TO: Memory linked to macro/topic
-- TRIGGERED_BY: Macro triggered by agent
-- TAGGED_WITH: Entity tagged with topic
-- DERIVED_FROM: Memory derived from source
-- BELONGS_TO: User belongs to team/org
-- MEMBER_OF: Team member relationships
-- CONTAINS: Hierarchical containment
-- REFERENCES: Cross-references between entities
-- INFLUENCES: Influence relationships with weights

-- Sample Data Creation
CREATE (:User {id: 'u1', name: 'Arun', email: 'arun@medhasys.com', role: 'admin'});
CREATE (:User {id: 'u2', name: 'TeamMember', email: 'member@medhasys.com', role: 'user'});

CREATE (:Memory {id: 'm1', title: 'Redis Setup', type: 'core', content: 'SPEC-033 implementation'});
CREATE (:Memory {id: 'm2', title: 'Graph Model', type: 'architecture', content: 'SPEC-060 design'});

CREATE (:Macro {id: 'mac1', name: 'Setup Sequence', tag: 'infra', description: 'Infrastructure setup'});
CREATE (:Macro {id: 'mac2', name: 'Test Suite', tag: 'testing', description: 'Automated testing'});

CREATE (:Agent {id: 'a1', name: 'eM', type: 'ai_assistant', capabilities: 'memory_management'});
CREATE (:Agent {id: 'a2', name: 'TestBot', type: 'automation', capabilities: 'test_execution'});

CREATE (:Topic {id: 't1', label: 'Deployment', category: 'infrastructure'});
CREATE (:Topic {id: 't2', label: 'Performance', category: 'optimization'});

CREATE (:Source {id: 's1', kind: 'GitHub', ref: 'specs/053/', url: 'https://github.com/medhasys/ninaivalaigal'});
CREATE (:Source {id: 's2', kind: 'Documentation', ref: 'SPEC-060', url: 'internal://specs/060'});

CREATE (:Context {id: 'c1', name: 'Development Session', type: 'coding', duration: 3600});
CREATE (:Context {id: 'c2', name: 'Planning Meeting', type: 'discussion', duration: 1800});

CREATE (:Team {id: 'team1', name: 'Core Development', description: 'Main development team'});
CREATE (:Organization {id: 'org1', name: 'Medhasys', description: 'AI Memory Platform Company'});

-- Relationship Creation with Weights and Properties
MATCH (u:User {id: 'u1'}), (m:Memory {id: 'm1'})
CREATE (u)-[:CREATED {timestamp: '2024-09-21T21:00:00Z', confidence: 1.0}]->(m);

MATCH (u:User {id: 'u1'}), (m:Memory {id: 'm2'})
CREATE (u)-[:CREATED {timestamp: '2024-09-21T21:15:00Z', confidence: 1.0}]->(m);

MATCH (m:Memory {id: 'm1'}), (mac:Macro {id: 'mac1'})
CREATE (m)-[:LINKED_TO {weight: 0.9, relevance: 'high'}]->(mac);

MATCH (m:Memory {id: 'm2'}), (mac:Macro {id: 'mac2'})
CREATE (m)-[:LINKED_TO {weight: 0.8, relevance: 'medium'}]->(mac);

MATCH (mac:Macro {id: 'mac1'}), (a:Agent {id: 'a1'})
CREATE (mac)-[:TRIGGERED_BY {frequency: 'daily', automation_level: 0.95}]->(a);

MATCH (mac:Macro {id: 'mac2'}), (a:Agent {id: 'a2'})
CREATE (mac)-[:TRIGGERED_BY {frequency: 'on_commit', automation_level: 1.0}]->(a);

MATCH (mac:Macro {id: 'mac1'}), (t:Topic {id: 't1'})
CREATE (mac)-[:TAGGED_WITH {relevance: 0.9}]->(t);

MATCH (mac:Macro {id: 'mac2'}), (t:Topic {id: 't2'})
CREATE (mac)-[:TAGGED_WITH {relevance: 0.85}]->(t);

MATCH (m:Memory {id: 'm1'}), (s:Source {id: 's1'})
CREATE (m)-[:DERIVED_FROM {extraction_confidence: 0.95}]->(s);

MATCH (m:Memory {id: 'm2'}), (s:Source {id: 's2'})
CREATE (m)-[:DERIVED_FROM {extraction_confidence: 0.98}]->(s);

MATCH (u:User {id: 'u1'}), (team:Team {id: 'team1'})
CREATE (u)-[:MEMBER_OF {role: 'lead', since: '2024-01-01'}]->(team);

MATCH (u:User {id: 'u2'}), (team:Team {id: 'team1'})
CREATE (u)-[:MEMBER_OF {role: 'developer', since: '2024-03-01'}]->(team);

MATCH (team:Team {id: 'team1'}), (org:Organization {id: 'org1'})
CREATE (team)-[:BELONGS_TO {department: 'engineering'}]->(org);

-- Cross-Memory Relationships for Intelligence
MATCH (m1:Memory {id: 'm1'}), (m2:Memory {id: 'm2'})
CREATE (m1)-[:INFLUENCES {weight: 0.7, influence_type: 'prerequisite'}]->(m2);

-- Context Relationships
MATCH (u:User {id: 'u1'}), (c:Context {id: 'c1'})
CREATE (u)-[:PARTICIPATED_IN {role: 'primary', engagement: 0.9}]->(c);

MATCH (m:Memory {id: 'm1'}), (c:Context {id: 'c1'})
CREATE (m)-[:CREATED_IN {relevance: 0.95}]->(c);
