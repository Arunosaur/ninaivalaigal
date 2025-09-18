# SPEC <ID>: <Title>

## Problem
<What value this delivers. Business outcomes, not impl.>

## Scope
- In
- Out

## Interfaces
- HTTP:
  - POST /remember {text, metadata}
  - GET  /recall?q=..&k=..
- Python:
  - memory.remember(text, metadata)
  - memory.recall(query, k=5)

## Acceptance
See `acceptance.md` .

## Rollout
- Feature flag: MEMORY_PROVIDER (native|http)
- Migration: N/A (or link)
