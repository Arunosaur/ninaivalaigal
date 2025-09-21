# SPEC-060: Property Graph Memory Model

## Summary

This SPEC introduces a property graph-based architecture for representing relationships between memories, macros, users, contexts, and agent flows in ninaivalaigal. The graph model allows advanced queries, dynamic traversals, and relevance calculations—serving as a backbone for future insights and orchestration.

## Purpose

To model the memory network as a property graph with:

- **Nodes**: Users, Teams, Orgs, Memories, Contexts, Macros, Triggers, Agents
- **Edges**: Relationships like "recalls", "owned_by", "invoked_by", "linked_to", "extends", etc.
- **Attributes**: Timestamps, tags, confidence, user-defined labels

## Use Cases

- Finding connected context chains
- Analyzing macro similarity graphs
- Trigger detection through graph traversal
- Memory lifecycle analytics
- Real-time agent reasoning and flow traceability

## Implementation Ideas

- Use RedisGraph, Neo4j, or pg_graph extension for PostgreSQL
- GraphQL-style query layer for frontend exploration
- Export/import for property graph snapshots

## Dependencies

- Unified Macro Intelligence (SPEC-059)
- Redis-backed memory ranking (SPEC-031)
- MCP token stream indexing

## Status

📋 **PLANNED** — conceptual model defined. Implementation pending Redis/graph library selection.

## Location

`specs/060-property-graph-memory-model/`
