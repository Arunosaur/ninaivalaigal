# SPEC-061: Property Graph Intelligence Framework

## Objective
Integrate a property graph model to represent memory, context, and macro relations in Ninaivalaigal.

## Core Concepts
- **Nodes**: memory, macro, user, agent, topic, source
- **Edges**: relevance_to, created_by, triggered_by, linked_to, derived_from

## Storage Engine
- Apache AGE (Cypher over PostgreSQL)
- Graph DB integrated into existing Postgres stack

## Example Graph Use Cases
- Traverse memory chains from macro to execution
- Rank memory relevance using node/edge weights
- Find subgraphs related to a given user’s macro

## Benefits
- First-class graph semantics
- Fine-grained memory linking
- Query patterns like: “What macros reference this context?”

## Dependencies
- SPEC-053 (auth), SPEC-031 (ranking), SPEC-040 (feedback)
