# SPEC-033: Redis Integration for Caching, Session & Performance

## 📌 Status
**Planned** – Redis has been discussed previously but not yet formalized in implementation or documentation.

## 🎯 Objective
Integrate Redis as a cross-cutting infrastructure layer to boost performance, ensure scalable session handling, and enable advanced memory management features.

---

## 🔧 Intended Use Cases

### 1. 🔁 Memory Token Caching
- **Purpose**: Reduce latency for frequently accessed memory tokens.
- **Key**: `memory:<memory_id>`
- **TTL**: 1 hour (configurable)
- **Eviction**: LRU-based eviction for expired/stale items.

### 2. 🧠 Relevance Score Caching
- **Purpose**: Cache computed relevance ranking scores (SPEC-031)
- **Key**: `score:<user_id>:<context_id>:<token_id>`
- **TTL**: 15 minutes (for freshness)
- **Used By**: Relevance ranking system for e^M.

### 3. 🔐 Session / Auth Cache
- **Purpose**: Support JWT session states, CSRF protection, and temporary auth data.
- **Key**: `session:<user_id>`
- **TTL**: 30 minutes or configurable session length.
- **Integration**: FastAPI middleware for sessions & CSRF.

### 4. 🚦 API Rate Limiting
- **Purpose**: Enforce fair usage with token bucket or leaky bucket model.
- **Key**: `rate:<user_id>:<endpoint>`
- **Policy**: 100 requests / min (configurable by tier)
- **Integration**: Gateway/Proxy middleware.

### 5. 📬 Queue for Asynchronous Tasks (optional)
- **Purpose**: Redis Queue (RQ) for background processing
- **Examples**:
  - Memory token indexing
  - Notification triggers (SPEC-028)
  - Archival jobs (SPEC-011)

---

## 📦 Architecture & Deployment

- **Redis Instance**:
  - Containerized via Docker Compose or Helm Chart in K8s
  - Shared across services (auth, MCP, FastAPI, token service)
- **Security**:
  - Password-protected with ENV secrets
  - Redis ACLs for scoped access

---

## 🔍 Observability & Maintenance

- TTL monitoring and eviction stats
- CLI commands for:
  - Viewing top keys
  - Resetting rate limits
  - Clearing cache
- Prometheus exporter (optional) for Redis metrics

---

## 🧪 Testing

| Component | Test Case | Outcome |
|----------|-----------|---------|
| Memory Cache | Load same memory twice | 2nd fetch should hit Redis |
| Session Store | Simulate login | Redis should persist session |
| Rate Limiting | 101 requests in a minute | 101st should fail |
| Relevance Score | Compute → Store → Expire | TTL expiry should remove cache |

---

## ✅ Acceptance Criteria

- Redis instance runs alongside the Ninaivalaigal stack
- All components successfully use Redis for intended use cases
- Observability and TTL control is in place
- Secure access (ACL or password) is enforced

---

## 📁 Location

`specs/033-redis-integration/`

## 📌 Dependencies

- SPEC-002 (Authentication)
- SPEC-011 (Lifecycle & Garbage Collection)
- SPEC-031 (Relevance Scoring System)
- SPEC-028 (Notifications)

---

## 🚀 Outcome

This SPEC ensures Ninaivalaigal benefits from low-latency memory fetches, better session handling, smarter rate limits, and scalable async processing.
