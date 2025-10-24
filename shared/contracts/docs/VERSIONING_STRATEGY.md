# Versioning Strategy

**Purpose:** Version numbering and support policy
**Audience:** Architecture team, developers

---

## Version Scheme

We use **path-based major versioning**:

```
/api/v1/users
/api/v2/users
/api/v3/users
```

**No minor versions** (v1.1, v1.2) - only major versions.

---

## Version Numbering

### Major Version (v1, v2, v3)

**Increment when:** Breaking changes required

**Examples:**
- v1 → v2: Renamed fields
- v2 → v3: Removed endpoints
- v3 → v4: Changed auth mechanism

**Never skip versions:** v1 → v2 → v3 (not v1 → v3)

---

## Multiple Version Support

### Support Policy

| Version | Status | Support Duration |
|---------|--------|------------------|
| Current (vN) | Active | Indefinite |
| Current-1 (vN-1) | Deprecated | 30-90 days |
| Current-2 (vN-2) | Unsupported | Removed |

**Example:**
- v3 released → v3 active, v2 deprecated, v1 removed
- v2 released → v2 active, v1 deprecated

---

## Version Lifecycle

### 1. Development
- Create new version directory
- Implement changes
- Write tests

### 2. Beta (Optional)
- Deploy to staging
- Internal testing
- Early adopter feedback

### 3. Release
- Deploy to production
- Both versions available
- Announce to stakeholders

### 4. Deprecation
- Mark old version deprecated
- Add warnings to responses
- Monitor usage

### 5. Sunset
- Remove old version
- Archive documentation
- Update links

---

## Sunset Timeline

### Standard Timeline: 60 Days

```
Day 0:  v2 released, v1 active
Day 30: v1 deprecated warning added
Day 60: v1 removed from production
Day 90: v1 archived
```

### Extended Timeline: 90 Days
For major versions with many users

### Accelerated Timeline: 30 Days
For security-critical breaking changes

---

## Version Support Matrix

Current state (October 2025):

| Service | v1 | v2 | v3 |
|---------|----|----|-----|
| auth | ✅ Active | - | - |
| memory | ✅ Active | - | - |
| graph | ✅ Active | - | - |
| business | ✅ Active | - | - |
| admin | ✅ Active | - | - |

---

## Deprecation Warnings

### HTTP Header
```python
@app.get("/api/v1/users")
async def list_users_v1():
    return Response(
        headers={
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2025-12-22",
            "X-API-Replacement": "/api/v2/users"
        }
    )
```

### Response Body
```json
{
  "data": [...],
  "warnings": [
    {
      "code": "DEPRECATED_API_VERSION",
      "message": "API v1 is deprecated. Migrate to v2 by Dec 22, 2025.",
      "migration_guide": "https://docs.internal/v1-to-v2"
    }
  ]
}
```

---

## Version Negotiation

### URL-based (Recommended)
```
GET /api/v1/users  # Client specifies version
GET /api/v2/users
```

### Header-based (Not Used)
```
GET /api/users
Accept: application/vnd.ninaivalaigal.v2+json
```

**We use URL-based** for simplicity.

---

## Backward Compatibility

### Within Same Version (v1)
**Always maintain** backward compatibility:
- Add optional fields ✅
- Add endpoints ✅
- Never remove fields ❌
- Never rename fields ❌

### Across Versions (v1 → v2)
**No compatibility required** - breaking changes allowed

---

## Version Documentation

Each version must have:
- Migration guide
- Changelog
- Deprecated features list
- Sunset timeline

**Location:** `shared/contracts/my-service/v2/MIGRATION.md`

---

## References
- [VERSIONING.md](./VERSIONING.md) - Version workflow
- [BREAKING_CHANGES.md](./BREAKING_CHANGES.md) - Breaking change policy
- [DEPRECATION.md](./DEPRECATION.md) - Deprecation process
