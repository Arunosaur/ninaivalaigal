---
title: Untitled SPEC
---


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

📋 **IN PROGRESS** — initial design complete. Intelligence engine implemented (~40-50%). Macro recording and replay pending.

## Taiga Stories

The following Taiga stories have been created for SPEC-059:

**Phase 1: Foundation**
- **US#1007**: UMI-001: Macro Schema Definition & Database Design

**Phase 2: Recording APIs**
- **US#1031**: UMI-002: Macro Recording API - Option A (Script-based via eM/CLI)
- **US#1032**: UMI-003: Macro Recording API - Option B (Visual/Replay-based)
- **US#1033**: UMI-004: Macro Recording API - Option C (Implicit Detection)

**Phase 3: Indexing**
- **US#1017**: UMI-005: Macro Metadata Indexing System

**Phase 4: Replay**
- **US#1034**: UMI-006: Macro Replay Infrastructure

**Phase 5: UI**
- **US#1035**: UMI-007: Macro Dashboard User Interface

All stories are tagged with `spec-059` and are ready for implementation.

## Location

`specs/059-unified-macro-intelligence/`
