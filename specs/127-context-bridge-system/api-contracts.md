# API Contracts

## Base URL
```
/api/v1/context-bridge
```

---

## 1. Create Context Share

**Description**: Share memory from source to target context.

**Request Body**:
```json
{
  "source_memory_id": "uuid",
  "target_context_id": "uuid",
  "mode": "reference|clone|hybrid",
  "permissions": ["read", "write"],
  "expires_at": "2025-12-31T23:59:59Z",
  "sync_policy": {
    "trigger": "on_update|scheduled|manual",
    "frequency": "realtime|hourly|daily"
  }
}
```

**Response**: `201 Created`
```json
{
  "bridge_id": "uuid",
  "mode": "reference",
  "trust_score": 85,
  "status": "active",
  "created_at": "2025-10-13T08:00:00Z"
}
```

**Errors**:
- `403 Forbidden`: Insufficient trust score
- `404 Not Found`: Memory or context not found
- `409 Conflict`: Bridge already exists

---

## 2. Get Trust Score

### `GET /context-bridge/trust-score`

**Query Parameters**:
- `source_context_id` (required): Source context UUID
- `target_context_id` (required): Target context UUID

**Response**: `200 OK`
```json
{
  "trust_score": 85,
  "level": "high",
  "allowed_actions": ["reference", "clone", "sync"],
  "factors": {
    "relationship": 35,
    "historical": 25,
    "compliance": 18,
    "security": 7
  },
  "recommendations": [
    "Enable MFA for +3 points"
  ]
}
```

---

## 3. Get Graph Links

**Query Parameters**:
- `context_id` (required): Context UUID
- `depth` (optional): Traversal depth (1-3, default: 1)

**Response**: `200 OK`
```json
{
  "nodes": [
    {
      "id": "mem-123",
      "context_id": "ctx-456",
      "type": "original|reference|clone"
    }
  ],
  "edges": [
    {
      "from": "mem-123",
      "to": "mem-789",
      "type": "REFERENCES|DERIVES_FROM",
      "trust_score": 85
    }
  ]
}
```

---

## 4. Federated Query

### `POST /context-bridge/federated-query`

**Request Body**:
```json
{
  "contexts": ["ctx-1", "ctx-2", "ctx-3"],
  "query": "MATCH (m:Memory) WHERE m.tag = 'ml' RETURN m",
  "min_trust_score": 70
}
```

**Response**: `200 OK`
```json
{
  "results": [...],
  "contexts_queried": 3,
  "contexts_blocked": 0,
  "execution_time_ms": 45
}
```

---

## 5. Update Bridge (Lifecycle Management)

### `PATCH /context-bridge/share/{bridge_id}`

**Description**: Update bridge configuration (mode, trust, expiry).

**Request Body**:
```json
{
  "mode": "hybrid",
  "permissions": ["read"],
  "expires_at": "2026-01-01T00:00:00Z",
  "sync_policy": {
    "trigger": "scheduled",
    "frequency": "daily"
  }
}
```

**Response**: `200 OK`
```json
{
  "bridge_id": "uuid",
  "updated_fields": ["mode", "sync_policy"],
  "updated_at": "2025-10-13T09:00:00Z"
}
```

---

## 6. Get Bridge Details

### `GET /context-bridge/share/{bridge_id}`

**Description**: Retrieve bridge creation and usage history.

**Response**: `200 OK`
```json
{
  "bridge_id": "uuid",
  "mode": "reference",
  "trust_score": 85,
  "created_at": "2025-10-13T08:00:00Z",
  "created_by": "user-123",
  "access_count": 150,
  "last_accessed_at": "2025-10-13T08:30:00Z",
  "status": "active"
}
```

---

## 7. Get Bridge Audit Trail

**Query Parameters**:
- `bridge_id` (optional): Specific bridge
- `start_date` (optional): ISO8601 timestamp
- `end_date` (optional): ISO8601 timestamp

**Description**: Retrieve bridge creation and usage history for compliance.

**Response**: `200 OK`
```json
{
  "audits": [
    {
      "timestamp": "2025-10-13T08:00:00Z",
      "action": "bridge_created",
      "bridge_id": "uuid",
      "user_id": "user-123",
      "trust_score": 85
    },
    {
      "timestamp": "2025-10-13T08:15:00Z",
      "action": "reference_accessed",
      "bridge_id": "uuid",
      "user_id": "user-456",
      "trust_score": 87
    }
  ],
  "total": 2
}
```

---

## 8. Revoke Bridge

### `DELETE /context-bridge/share/{bridge_id}`

**Description**: Safely remove bridge (audited).

**Response**: `200 OK`
```json
{
  "status": "revoked",
  "revoked_at": "2025-10-13T08:30:00Z"
}
```

---

## 9. Federated Embedding Search

### `POST /context-bridge/embedding-search`

**Description**: Contextual retrieval across linked contexts without data duplication. Vector joins performed in graph space.

**Request Body**:
```json
{
  "query_embedding": [0.1, 0.2, ...],  // 768-dim vector
  "contexts": ["ctx-1", "ctx-2"],
  "min_trust_score": 70,
  "top_k": 10
}
```

**Response**: `200 OK`
```json
{
  "results": [
    {
      "memory_id": "mem-123",
      "context_id": "ctx-1",
      "similarity": 0.95,
      "trust_score": 85,
      "accessed_via": "direct|hub"
    }
  ],
  "latency_ms": 45
}
```

---

## Authentication

All endpoints require JWT authentication:
```
Authorization: Bearer <jwt_token>
```

---

## Rate Limits

- 100 requests per minute per user
- 1000 federated queries per hour per organization

