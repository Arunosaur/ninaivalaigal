---
title: SPEC-138: Custom Embedding Integration Hooks
---

# SPEC-138: Custom Embedding Integration Hooks

## Status
- 📋 **PLANNED** (Phase 2C)

## Summary
Introduces a hook system allowing external or fine-tuned embedding models to replace the default pgvector pipeline. This enables users and organizations to integrate custom embedding providers, fine-tuned models, or proprietary embedding services for enhanced semantic search and memory matching.

## Derived From
**Split from SPEC-039** - The original SPEC-039 scope included both "Memory Tags" (now SPEC-039) and "Custom Embedding Integration Hooks" (this SPEC-138). They were split to preserve clear lineage and auditability.

## Objectives
- Design hook system for embedding model integration
- Enable external embedding provider support
- Support fine-tuned model integration
- Provide model registry and selection mechanism
- Maintain compatibility with default pgvector pipeline
- Allow per-organization or per-user embedding preferences

## Deliverables
- [ ] Design Document for hook architecture
- [ ] Embedding hook API (registration, selection, execution)
- [ ] Model registry system
- [ ] Pipeline selection mechanism
- [ ] Integration with existing memory system
- [ ] Comprehensive test suite
- [ ] Documentation and usage examples

## Technical Architecture

### Hook System
- **Registration API**: Register custom embedding models
- **Selection Logic**: Choose embedding model based on context
- **Execution Pipeline**: Execute embeddings via registered hooks
- **Fallback Strategy**: Default to pgvector if hook unavailable

### Model Registry
- Store embedding model metadata
- Track model capabilities and limitations
- Manage model versions
- Support model-specific configurations

### Integration Points
- Memory creation: Use selected embedding model
- Memory search: Apply embedding for similarity
- Memory update: Re-embed with selected model
- Bulk operations: Batch embedding generation

## Related SPECS
- **SPEC-039** — Memory Tags (Complete) - Split source, related memory metadata
- **SPEC-012** — Memory Substrate (Complete) - Foundation for embedding integration
- **SPEC-031** — Memory Relevance Ranking (Complete) - Uses embeddings for scoring
- **SPEC-033** — Redis Integration (Complete) - May cache embeddings

## Dependencies
- SPEC-012 (Memory Substrate) - ✅ Complete
- SPEC-031 (Relevance Ranking) - ✅ Complete
- SPEC-033 (Redis Integration) - ✅ Complete

## Success Criteria
- [ ] External embedding models can be registered
- [ ] Custom models can replace default pgvector pipeline
- [ ] Per-organization embedding preferences supported
- [ ] Hook system maintains backward compatibility
- [ ] Performance impact < 20% vs default pipeline
- [ ] Comprehensive test coverage (>80%)

## Ownership
- Platform: Ninaivalaigal
- Category: Memory Management / Intelligence / AI Integration
- Phase: Phase 2C (Future AI Integration)
