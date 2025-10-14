# Federation Topology

## Overview

Context bridges can federate via three topology patterns, each optimized for different use cases.

---

## 1. Peer-to-Peer Federation (Direct Edge)

**Description**: Direct connections between contexts without intermediary.

**Topology**:
```
Context A ←————————————→ Context B
     ↓                        ↓
  Memory 1 ←——Reference——→ Memory 2
```

**When to Use**:
- Small teams (2-10 contexts)
- High trust between contexts
- Low latency requirements
- Simple sharing patterns

**Characteristics**:
- Lowest latency (<50ms)
- Simple routing
- No central point of failure
- Scales to ~100 peer connections

---

## 2. Hub Federation (Central Graph Index)

**Description**: Contexts connect through central Medhasys/Ninaivalaigal graph hub.

**Topology**:
```
       Context A
           ↓
    [Central Hub]
       ↙    ↓    ↘
Context B  C  D  E
```

**When to Use**:
- Large organizations (>10 contexts)
- Need global search/discovery
- Centralized governance
- Mixed trust levels

**Characteristics**:
- Central indexing
- Global query capability
- Policy enforcement point
- Scales to 10,000+ contexts

**Routing**: All queries route through hub for trust evaluation and caching.

---

## 3. Hybrid Federation (Peer Edge + Central Hub)

**Description**: Direct peer connections for frequent access, hub for discovery.

**Topology**:
```
Context A ←direct→ Context B
    ↓               ↓
  [Hub for discovery]
    ↓               ↓
Context C ←direct→ Context D
```

**When to Use**:
- Best of both worlds
- Frequent peer access + global discovery
- Performance-critical paths
- Large-scale deployments

**Characteristics**:
- Fast paths: <50ms (direct)
- Slow paths: <200ms (via hub)
- Hub caches frequently accessed bridges
- Automatic promotion to direct edge

---

## Implementation in GraphOps

### Direct Edge Query:
```cypher
// Direct reference
MATCH (source:Memory {id: $source_id})-[:REFERENCES]->(target:Memory)
WHERE target.context_id = $target_context
RETURN target
```

### Hub-Mediated Query:
```cypher
// Via central hub
MATCH (source:Memory {id: $source_id})-[:FEDERATED_VIA]->
      (hub:FederationHub)-[:ROUTES_TO]->
      (target:Memory)
WHERE target.context_id = $target_context
  AND hub.trust_score >= 70
RETURN target
```

### Hybrid Query (Optimized):
```cypher
// Try direct first, fallback to hub
MATCH path = shortestPath(
  (source:Memory {id: $source_id})-[*1..2]-(target:Memory)
)
WHERE target.context_id = $target_context
  AND ALL(r IN relationships(path) WHERE r.trust_score >= 70)
RETURN target, length(path) as hops
ORDER BY hops ASC
LIMIT 1
```

---

## Performance Comparison

| Topology | Latency (p95) | Scalability | Complexity | Cost |
|----------|---------------|-------------|------------|------|
| **Peer-to-Peer** | <50ms | ~100 contexts | Low | Low |
| **Hub** | <200ms | 10,000+ contexts | Medium | Medium |
| **Hybrid** | <50ms (hot), <200ms (cold) | 10,000+ contexts | High | Medium |

---

## Caching Strategy

### Peer-to-Peer:
- Cache at endpoints only
- Simple TTL (5 minutes)

### Hub:
- Central cache (Redis)
- Shared across all contexts
- Smart eviction based on access frequency

### Hybrid:
- Hot path: Endpoint cache
- Cold path: Hub cache
- Automatic promotion: >10 accesses/hour → direct edge

---

## Migration Path

```
Phase 1: Start with Peer-to-Peer (simplest)
   ↓
Phase 2: Add Hub for discovery (as contexts grow)
   ↓
Phase 3: Optimize to Hybrid (for performance)
```

