# SPEC-031: Memory Relevance Ranking (Redis-Enabled)

## 📌 Overview
This SPEC introduces a Redis-backed relevance scoring system to rank memory tokens based on their contextual importance. It enables rapid retrieval of the most relevant memories during user sessions, serving as the core intelligence feature for ninaivalaigal.

---

## 🎯 Goals
- Score memory tokens using contextual metadata (e.g., recency, frequency, user affinity)
- Cache scores using Redis with TTL-based invalidation
- Enable fast, ranked retrieval during memory API access
- Allow feedback-based tuning of relevance in the future (SPEC-040)

---

## 🏗️ Architecture

### Redis-Based Relevance Scoring
- **Key Format**: `relevance:{user_id}:{memory_id}`
- **Score Calculation**:
  - +1 for each access in past hour
  - +5 for user-flagged "important"
  - Decayed score based on time since last use
- **TTL**: 1 hour (recomputed on access or feedback)

### Data Flow
1. On memory access → Update relevance score in Redis
2. On memory retrieval → Fetch top-N tokens by score
3. On feedback (future SPEC-040) → Adjust score weights

---

## 🧠 Algorithm
```python
score = (
    weight_time_decay(last_access_time) +
    weight_access_frequency(recent_accesses) +
    weight_user_importance_flag(is_flagged)
)
```

---

## 🚀 Redis Keys & TTLs

| Redis Key Format                | TTL     | Description                            |
|--------------------------------|---------|----------------------------------------|
| `relevance:{user}:{memory_id}` | 1 hour  | Stores score and metadata              |
| `relevance:top:{user}`         | 15 mins | Cached sorted set for top-N memories   |

---

## ⚙️ API Changes

### GET `/memory/relevant`
- **Params**: `user_id`, `context`, `limit=10`
- **Returns**: Top-ranked memories based on cached relevance

---

## 🔒 Security & Isolation
- User-scoped cache keys
- TTL to prevent stale leakage
- Role-based access to feedback tuning (future)

---

## ✅ Acceptance Criteria
- [ ] Memory accesses update Redis scores
- [ ] `/memory/relevant` returns ranked list within 5ms
- [ ] TTL-based eviction works
- [ ] Redis key usage < 10MB per 10K users

---

## 🔗 Dependencies
- SPEC-033 (Redis Core)
- SPEC-045 (Session Management)
- SPEC-040 (Feedback Loop – future)

---

## 🧪 Testing Plan
- Unit tests for scoring algorithm
- Integration test: access → score → retrieval loop
- Performance test: 10K keys, latency < 5ms

---

## 📈 Metrics to Monitor
- Redis hits/misses
- Top memory retrieval latency
- Score decay vs freshness correlation

---

## 🗓️ Timeline
| Task                        | Duration |
|-----------------------------|----------|
| Scoring Logic & TTL Cache   | 2 days   |
| API Integration             | 1 day    |
| Testing & Benchmarking      | 2 days   |

---

## 📂 Files
- `redis_client.py`: Score cache logic
- `relevance_engine.py`: Scoring algorithm
- `api/memory.py`: Endpoint logic

---

## 🏁 Outcome
> Enables fast, context-aware memory recall using relevance ranking backed by Redis. This is the first step toward intelligence-guided memory workflows.
