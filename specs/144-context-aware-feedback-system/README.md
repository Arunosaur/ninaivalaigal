---
title: SPEC-144: Context-Aware Feedback System
status: Planned
priority: High
category: Intelligence
phase: Phase 3
---

# SPEC-144: Context-Aware Feedback System

**Status:** 📋 **PLANNED**
**Priority:** High
**Category:** Intelligence / AI Feedback
**Phase:** Phase 3
**Dependencies:** SPEC-040 (Feedback Loop System - Complete)

---

## 🎯 Overview

**Context-Aware Feedback System** is a meta-feedback layer that sits above memory-centric feedback (SPEC-040), focused on **AI reasoning context itself** rather than individual memory relevance. This system learns not just which memories are good, but how **context composition** affects the AI's downstream quality.

**Distinction from SPEC-040:**
- **SPEC-040:** Memory-centric feedback (users score individual memories, adjust memory relevance)
- **SPEC-144:** Context-aware feedback (feedback on context composition, reasoning quality, prompt optimization)

---

## 🧠 Core Purpose

**Ninaivalaigal is evolving into a context intelligence engine, not just a memory repository.** Context-aware feedback enables the system to learn:
- Which context windows work best for different query types
- How to prioritize graph nodes for reasoning
- How to auto-tune prompt windows based on feedback
- How to balance context length, relevance, and tone

Without context-aware feedback:
- GraphOps layer can't learn which nodes to prioritize for reasoning
- Reasoner can't auto-tune its prompt window
- The e^M Feedback Loop stays static — it improves recall, but not reasoning context

---

## 📋 Key Features

### 1. Context Quality Feedback Collection

**Feedback Types:**
- **Context Length Feedback:**
  - "Response feels off-topic" → Reduce window length / drop low-relevance memories
  - "Missing important context" → Expand context window / include more related memories
- **Context Relevance Feedback:**
  - "You ignored my last summary" → Boost contextual recall from prior summary nodes
  - "Too much unrelated information" → Filter context more aggressively
- **Tone/Alignment Feedback:**
  - "Too technical for this query" → Adjust model context weighting toward emotional/social memories
  - "Too casual for business context" → Increase weight on formal/business memories
- **Retrieval Bias Feedback:**
  - "Keeps surfacing one user's memories only" → Apply fairness/entropy regularization to recall set
  - "Missing team context" → Balance individual vs team memory weights

### 2. Context Composition Scorer

**Functionality:**
- Analyzes context composition quality before sending to LLM
- Scores based on:
  - Memory diversity (entropy)
  - Temporal distribution
  - Relevance distribution
  - Tone alignment
  - Length appropriateness
- Provides pre-flight context quality metrics

### 3. Context Compression Model

**Functionality:**
- Intelligently compresses context when too long
- Prioritizes memories based on:
  - Current feedback patterns
  - Query type
  - User preferences
  - Context composition scores
- Maintains quality while reducing token usage

### 4. LLM Telemetry Correlation

**Functionality:**
- Correlates feedback with LLM output quality
- Tracks:
  - Response relevance scores
  - User satisfaction metrics
  - Error rates
  - Response coherence
- Links feedback to specific context compositions

### 5. Adaptive Context Gating

**Functionality:**
- Dynamic context window sizing based on task type
- Query classification (technical, casual, business, creative)
- Context weighting adjustment per category
- Automatic context pruning based on feedback patterns

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│  Context-Aware Feedback Layer (SPEC-144)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Context Quality  │  │ Context         │                │
│  │ Feedback         │  │ Composition     │                │
│  │ Collector        │  │ Scorer          │                │
│  └─────────────────┘  └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ LLM Telemetry    │  │ Adaptive Context│                │
│  │ Correlator       │  │ Gating Engine   │                │
│  └─────────────────┘  └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐                                       │
│  │ Context         │                                       │
│  │ Compression     │                                       │
│  │ Model           │                                       │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Memory-Centric Feedback (SPEC-040) - Complete              │
│  - Memory relevance scoring                                  │
│  - Individual memory feedback                                │
│  - Memory ranking adjustment                                 │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

- **SPEC-040:** Uses memory feedback data as ground truth signals
- **SPEC-031:** Memory Relevance Ranking (context relevance calculation)
- **SPEC-061:** Graph Intelligence (graph node prioritization)
- **SPEC-063:** Agentic Core Execution (context injection points)

---

## 📊 Use Cases

### Example 1: Context Too Long

**Scenario:** User provides query, gets off-topic response

**Feedback:** "Response feels off-topic"

**System Adaptation:**
- Reduce context window length
- Drop low-relevance memories
- Increase relevance threshold
- Log context composition for future learning

**Result:** Better focused responses with shorter context

### Example 2: Missing Key Insight

**Scenario:** User mentions "you ignored my last summary"

**Feedback:** "You ignored my last summary"

**System Adaptation:**
- Boost contextual recall from prior summary nodes
- Increase weight on recent summary memories
- Expand temporal window for summary-related queries

**Result:** System maintains continuity across conversations

### Example 3: Tone Misalignment

**Scenario:** User asks casual question, gets technical response

**Feedback:** "Too technical for this query"

**System Adaptation:**
- Adjust model context weighting toward emotional/social memories
- Reduce weight on technical documentation
- Classify query as "casual" and apply appropriate context filter

**Result:** Responses match user's communication style

### Example 4: Retrieval Bias

**Scenario:** System keeps surfacing one user's memories only

**Feedback:** "Keeps surfacing one user's memories only"

**System Adaptation:**
- Apply fairness/entropy regularization to recall set
- Balance individual vs team memory weights
- Increase diversity in context composition

**Result:** More balanced, representative context

---

## 🔧 Technical Implementation

### API Endpoints

**Context Feedback Collection:**
- `POST /api/v1/context/feedback` - Submit context quality feedback
  - Request body: `{ feedback_type, context_id, feedback_value, details, query_id }`

**Context Composition Analysis:**
- `GET /api/v1/context/composition/{context_id}` - Get context composition metrics
- `POST /api/v1/context/composition/analyze` - Analyze context composition before LLM call

**Context Optimization:**
- `POST /api/v1/context/optimize` - Optimize context based on feedback patterns
- `GET /api/v1/context/recommendations/{query_id}` - Get context composition recommendations

### Database Schema

**Tables:**
- `context_feedback_events` - Context quality feedback events
- `context_composition_scores` - Context composition quality metrics
- `context_optimization_rules` - Learned optimization rules
- `llm_telemetry_correlation` - LLM output quality correlation data

### Machine Learning Components

**Models:**
- Context composition scorer (ensemble of heuristics + ML)
- Context compression model (priority ranking model)
- Query type classifier (for adaptive gating)
- Context quality predictor (pre-flight quality estimation)

---

## 🎯 Success Criteria

### Phase 1: Foundation (Weeks 1-4)
- [ ] Context feedback collection API
- [ ] Basic context composition scoring
- [ ] Database schema for context feedback
- [ ] Integration with SPEC-040 feedback data

### Phase 2: Analysis (Weeks 5-8)
- [ ] LLM telemetry correlation
- [ ] Context compression model (basic)
- [ ] Context quality dashboard
- [ ] Feedback pattern analysis

### Phase 3: Optimization (Weeks 9-12)
- [ ] Adaptive context gating
- [ ] Advanced context compression
- [ ] Query type classification
- [ ] Context composition recommendations

### Phase 4: Integration (Weeks 13-16)
- [ ] GraphOps integration (node prioritization)
- [ ] Reasoner integration (prompt window tuning)
- [ ] Full e^M feedback loop integration
- [ ] Performance optimization

---

## 📈 Metrics & Observability

**Key Metrics:**
- Context composition quality scores
- Feedback collection rate
- Context optimization success rate
- LLM response quality improvement
- Context length reduction (with maintained quality)
- User satisfaction improvement

**Dashboards:**
- Context feedback trends
- Context composition quality over time
- Optimization rule effectiveness
- Query type distribution
- Context length distribution

---

## 🔗 Dependencies

### Required (Complete)
- **SPEC-040:** Feedback Loop System (provides memory feedback ground truth)
- **SPEC-031:** Memory Relevance Ranking (context relevance calculation)
- **SPEC-033:** Redis Integration (event storage and processing)
- **SPEC-061:** Graph Intelligence (graph node prioritization)

### Related (Planned)
- **SPEC-063:** Agentic Core Execution (context injection points)
- **SPEC-135:** Multi-Agent Expert Protocol (agent context coordination)

---

## 💡 Benefits

### Immediate
- Better context composition before LLM calls
- Reduced token usage while maintaining quality
- Improved response relevance

### Short-term
- Adaptive context window sizing
- Query-type-specific context optimization
- Reduced off-topic responses

### Long-term
- Self-improving context intelligence layer
- GraphOps learns optimal node prioritization
- Reasoner auto-tunes prompt windows
- e^M feedback loop becomes truly dynamic

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Feedback collection overhead | Use async processing, batch feedback |
| Context compression quality loss | Gradual optimization, quality gates |
| Model complexity | Start with heuristics, add ML incrementally |
| Integration complexity | Phased rollout, extensive testing |

---

## 📝 Notes

### Design Philosophy
- **Learn from usage:** Context feedback drives continuous improvement
- **Meta-layer approach:** Works above memory feedback, not replaces it
- **Adaptive optimization:** System learns optimal context compositions
- **Quality first:** Maintain response quality while optimizing context

### Relationship to SPEC-040
- **SPEC-040:** Improves individual memory relevance
- **SPEC-144:** Improves context composition and reasoning quality
- **Together:** Complete feedback loop from memory → context → reasoning → output

---

**Status:** 📋 Planned
**Next Step:** Define detailed architecture and acceptance criteria
**ETA:** Phase 3 (after SPEC-040 stabilization)

---

*This SPEC represents the natural Phase 3+ evolution beyond SPEC-040's memory-centric feedback, enabling Ninaivalaigal to become a true context intelligence engine.*
