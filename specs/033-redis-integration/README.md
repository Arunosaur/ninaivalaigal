---
{}
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
