# Memory Service API Reference

**US#93/US#95:** Memory Router Rationalization - SPEC-131

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints (except `/health`) require JWT authentication:
```
Authorization: Bearer <jwt-token>
```

---

## Existing Endpoints

### Health
- `GET /health` - Service health check

### Memory CRUD
- `POST /memory/remember` - Create memory
- `POST /memory/recall` - Search/recall memories
- `GET /memory/memories` - List all memories
- `DELETE /memory/memories/:id` - Delete memory

---

## New Endpoints (US#93/US#95)

### Injection API

#### Analyze Injection Opportunities
```http
POST /memory/injection/analyze
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "current_activity": "coding",
  "location_context": {},
  "temporal_context": {},
  "semantic_context": {
    "language": "rust",
    "topic": "testing"
  },
  "user_state": {},
  "environment": {},
  "max_candidates": 10
}
```

**Response:**
```json
{
  "candidates": [
    {
      "memory_id": "uuid",
      "relevance_score": 0.8,
      "injection_reason": "Context match: coding",
      "rule_id": null,
      "confidence": 0.8,
      "urgency": 0.7,
      "context_match": {...},
      "suggested_timing": "immediate",
      "metadata": {...}
    }
  ],
  "total_candidates": 1,
  "analysis_time_ms": 15.2,
  "rules_evaluated": 0,
  "context_summary": {...}
}
```

#### Execute Memory Injection
```http
POST /memory/injection/execute
Content-Type: application/json

{
  "context": {
    "current_activity": "coding",
    "semantic_context": {...}
  },
  "strategy": "contextual",
  "max_injections": 5
}
```

**Response:**
```json
{
  "injected_memories": [...],
  "execution_time_ms": 45.3,
  "strategy_used": "contextual",
  "success_count": 3,
  "context_snapshot": {...}
}
```

#### Bulk Inject Memories (High-Performance)
```http
POST /memory/injection/bulk
Content-Type: application/json

[
  {
    "content": "Memory content 1",
    "metadata": {"source": "test"}
  },
  {
    "content": "Memory content 2",
    "metadata": {"source": "test"}
  }
]
```

**Response:**
```json
{
  "total_requested": 2,
  "success_count": 2,
  "failed_count": 0,
  "execution_time_ms": 12.5,
  "results": [
    {
      "success": true,
      "memory_id": "uuid",
      "error": null
    }
  ]
}
```

---

### Queue API

#### Enqueue Task
```http
POST /queue/tasks
Content-Type: application/json

{
  "task_type": "memory_processing",
  "parameters": {
    "memory_id": "uuid",
    "text": "content",
    "metadata": {}
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "enqueued",
  "message": "Task memory_processing enqueued successfully"
}
```

#### Get Job Status
```http
GET /queue/jobs/:job_id
```

**Response:**
```json
{
  "id": "uuid",
  "status": "queued",
  "created_at": "2025-11-02T10:00:00Z",
  "started_at": null,
  "ended_at": null,
  "result": null,
  "error": null
}
```

#### Get Queue Statistics
```http
GET /queue/stats
```

**Response:**
```json
{
  "queues": {
    "default": {
      "length": 5,
      "failed_job_count": 0,
      "scheduled_job_count": 0,
      "started_job_count": 0,
      "deferred_job_count": 0
    }
  },
  "total_jobs": 5,
  "healthy": true
}
```

#### Process Memory Async (Convenience)
```http
POST /queue/memory/:memory_id/process?text=content&metadata={}
```

**Response:**
```json
{
  "job_id": "uuid",
  "memory_id": "uuid",
  "status": "processing",
  "message": "Memory processing started in background"
}
```

#### Queue Health Check
```http
GET /queue/health
```

**Response:**
```json
{
  "status": "healthy",
  "connected": true,
  "queues": 5,
  "total_failed_jobs": 0,
  "total_started_jobs": 0,
  "queue_details": {...}
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized (JWT required)
- `404` - Not Found
- `500` - Internal Server Error

---

## Performance Targets (SPEC-131)

- **Bulk Injection:** >1000 memories/sec
- **Queue Enqueue:** P99 < 10ms
- **Injection Analysis:** <100ms for typical context

---

## Testing

### Unit Tests
```bash
cargo test
```

### Integration Tests
```bash
cargo test --test injection_api_tests
cargo test --test queue_api_tests
```

### Performance Benchmarks
```bash
cargo bench --bench injection_benchmark
./scripts/run_performance_tests.sh
```
