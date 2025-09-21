# SPEC-059: Unified Macro Intelligence

## Summary

Unified Macro Intelligence (UMI) introduces a higher-order layer of automation within the ninaivalaigal system. It enables capturing, organizing, and replaying sequences of memory or task-based operations—referred to as "Macros"—that can be reused for intelligent automation, context restoration, and user-assistive workflows.

## Purpose

To record user actions, inputs, or decision flows across multiple modalities (text, screen interaction, commands) and treat them as programmable or auto-triggerable sequences (macros) associated with individual, team, or org memory.

## Scope

- Support three macro capture modes:
  - **Option A**: Script-based (via eM/CLI)
  - **Option B**: Visual/Replay-based (like a screen-recorded demonstration)
  - **Option C**: Implicit (passively detected from repeated behaviors)

- Provide macro lifecycle support:
  - Capture
  - Tokenization and summarization
  - Ranking and retrieval
  - Replay and re-embedding into AI calls

- Tag macros to memory contexts for relevance
- Enable user-defined or AI-suggested triggers for replay

## Out of Scope

- Cross-product orchestration (covered by SmritiOS)
- Macro sharing across external systems (deferred)

## Deliverables

- Macro schema definition
- Macro recording APIs (eM / MCP)
- Macro metadata indexing (e.g., trigger condition, input context)
- Replay infrastructure
- Macro dashboard in user UI

## Status

📋 **PLANNED** — initial design complete. Awaiting Redis + macro store finalization.

## Location

`specs/059-unified-macro-intelligence/`
