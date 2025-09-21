# SPEC-060: Apache AGE Property Graph Memory Model

## Summary

This SPEC introduces Apache AGE (A Graph Extension for PostgreSQL) to implement a property graph-based architecture for representing relationships between memories, macros, users, contexts, and agent flows in ninaivalaigal. The graph model allows advanced Cypher queries, dynamic traversals, and relevance calculations—serving as a backbone for future insights and orchestration.

## Purpose

To model the memory network as a property graph using Apache AGE with:

- **Nodes**: Users, Teams, Orgs, Memories, Contexts, Macros, Triggers, Agents, Topics, Sources
- **Edges**: Relationships like "CREATED", "LINKED_TO", "TRIGGERED_BY", "TAGGED_WITH", "DERIVED_FROM", etc.
- **Attributes**: Timestamps, tags, confidence, weights, user-defined labels

## Architecture

### **Dual Architecture Support**
- **Local Development**: Apple Container CLI with PostgreSQL + Apache AGE (ARM64)
- **CI/CD**: GitHub Actions with x86_64 multi-arch Docker containers
- **Production**: Kubernetes deployment with PostgreSQL + AGE extension

### **Integration Strategy**
- Builds on existing PostgreSQL + pgvector infrastructure
- Apache AGE provides Cypher query language over PostgreSQL
- Seamless integration with current database schemas
- Graph data alongside relational data in same database

## Use Cases

- Finding connected context chains: `MATCH (u:User)-[:CREATED]->(:Memory)-[:LINKED_TO]->(m:Macro)`
- Analyzing macro similarity graphs with weighted edges
- Trigger detection through graph traversal patterns
- Memory lifecycle analytics with temporal relationships
- Real-time agent reasoning and flow traceability

## Graph Schema

See `graph-assets/schema.cypher` for complete node and relationship definitions:

```cypher
// Example: User creates Memory linked to Macro triggered by Agent
CREATE (:User {id: 'u1', name: 'Arun'});
CREATE (:Memory {id: 'm1', title: 'Redis Setup', type: 'core'});
CREATE (:Macro {id: 'mac1', name: 'Setup Sequence', tag: 'infra'});
MATCH (u:User {id: 'u1'}), (m:Memory {id: 'm1'}) CREATE (u)-[:CREATED]->(m);
```

## Performance Benchmarks

See `graph-assets/benchmark.cypher` for performance testing queries:

```cypher
// Find all macros created by user with traversal
MATCH (u:User {id: 'u1'})-[:CREATED]->(:Memory)-[:LINKED_TO]->(m:Macro)
RETURN m.name LIMIT 10;
```

## Implementation Plan

### **Phase 1: Apache AGE Deployment**
- Multi-arch Docker image with PostgreSQL + Apache AGE
- Apple Container CLI configuration for local development
- CI/CD pipeline with x86_64 support

### **Phase 2: Graph Schema Implementation**
- Initialize graph schema from `schema.cypher`
- Migrate existing memory/user relationships to graph
- Add graph-based API endpoints

### **Phase 3: Intelligence Integration**
- Integrate with SPEC-031 (Memory Relevance Ranking)
- Graph-based relevance scoring using edge weights
- Macro intelligence with SPEC-059 integration

## Dependencies

- SPEC-053: Authentication (user context for graph nodes)
- SPEC-031: Memory Relevance Ranking (graph-based scoring)
- SPEC-059: Unified Macro Intelligence (macro nodes and relationships)
- Existing PostgreSQL + pgvector infrastructure

## Status

📋 **READY FOR IMPLEMENTATION** — Apache AGE architecture defined, graph assets provided, dual-architecture deployment strategy complete.

## Assets

- `SPEC-060-apache-age-deployment.md` - Deployment architecture
- `SPEC-061-property-graph-intelligence.md` - Intelligence framework
- `graph-assets/schema.cypher` - Production graph schema
- `graph-assets/benchmark.cypher` - Performance testing queries

## Location

`specs/060-property-graph-memory-model/`
