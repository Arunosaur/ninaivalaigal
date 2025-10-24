# Deprecation Workflow

**Purpose:** How to deprecate contracts and endpoints
**Audience:** Backend developers, architecture team

---

## Deprecation Process

### Step 1: Announcement (Day 0)

**Create deprecation notice:**
```markdown
# DEPRECATION NOTICE: API v1

**Date:** October 22, 2025
**Deprecated Version:** v1
**Replacement:** v2
**Sunset Date:** December 22, 2025 (60 days)

## What's Deprecated
- `/api/v1/users` endpoint
- `UserResponse.user_name` field (use `full_name`)

## Migration Required
See [MIGRATION_V1_V2.md](./MIGRATION_V1_V2.md)

## Support
- Questions: #backend-support
- Migration help: @backend-team
```

**Communicate:**
- Post in Slack (#announcements)
- Email stakeholders
- Update documentation
- Add to sprint notes

---

### Step 2: Mark as Deprecated (Day 0)

**Add warning headers:**
```python
from fastapi import Response

@app.get("/api/v1/users", deprecated=True)
async def list_users_v1():
    """
    ⚠️ DEPRECATED: Use /api/v2/users instead

    This endpoint will be removed on December 22, 2025.
    Migration guide: https://docs.internal/v1-v2
    """
    return Response(
        content=json_data,
        headers={
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2025-12-22",
            "X-API-Replacement": "/api/v2/users",
            "Link": '<https://docs.internal/v1-v2>; rel="deprecation"'
        }
    )
```

**Update OpenAPI:**
```python
@app.get(
    "/api/v1/users",
    deprecated=True,
    description="⚠️ **DEPRECATED:** Migrate to v2 by Dec 22, 2025"
)
```

---

### Step 3: Monitor Usage (Days 1-30)

**Track metrics:**
```python
# Emit deprecation metrics
@app.middleware("http")
async def track_deprecated_usage(request: Request, call_next):
    if request.url.path.startswith("/api/v1/"):
        metrics.increment("api.v1.usage", tags={
            "endpoint": request.url.path,
            "client": request.headers.get("User-Agent")
        })
    return await call_next(request)
```

**Weekly reports:**
- v1 usage count
- Top clients still on v1
- Migration progress

---

### Step 4: Contact Laggards (Day 30)

**Identify clients still on v1:**
```sql
SELECT
    client_id,
    COUNT(*) as v1_requests,
    MAX(timestamp) as last_v1_request
FROM api_logs
WHERE version = 'v1'
AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY client_id
ORDER BY v1_requests DESC
```

**Reach out:**
- Email client teams
- Offer migration support
- Set deadline reminder

---

### Step 5: Final Warning (Day 45)

**Add breaking warning:**
```python
@app.get("/api/v1/users", deprecated=True)
async def list_users_v1():
    # Add prominent warning
    response_data["_warning"] = {
        "code": "API_SUNSET_IMMINENT",
        "message": "This API will be removed in 15 days",
        "sunset_date": "2025-12-22",
        "action_required": "Migrate to /api/v2/users immediately"
    }
    return response_data
```

---

### Step 6: Removal (Day 60)

**Remove deprecated version:**

1. **Disable endpoints:**
```python
# Remove v1 router
# app.include_router(v1_router)  # Commented out
```

2. **Return 410 Gone:**
```python
@app.get("/api/v1/users", status_code=410)
async def v1_gone():
    return {
        "error": "API v1 has been removed",
        "removed_on": "2025-12-22",
        "replacement": "/api/v2/users",
        "migration_guide": "https://docs.internal/v1-v2"
    }
```

3. **Clean up code:**
```bash
# After 30 days of 410 responses, fully remove
rm -rf shared/contracts/my-service/v1/
# Move to archive if needed
mv shared/contracts/my-service/v1/ shared/contracts/archive/v1-removed-2025-12-22/
```

---

## Deprecation Timeline Examples

### Standard: 60 Days
```
Day 0:  Announce deprecation
Day 0:  Add deprecation warnings
Day 7:  Weekly status check
Day 14: Weekly status check
Day 21: Weekly status check
Day 30: Contact clients still on v1
Day 45: Final warning (15 days left)
Day 60: Remove v1 endpoints
Day 90: Archive v1 code
```

### Extended: 90 Days
For widely-used APIs with many clients

### Accelerated: 30 Days
For security-critical changes

---

## Minimum Deprecation Period

| API Type | Minimum Period | Typical Period |
|----------|----------------|----------------|
| Public API | 90 days | 180 days |
| Internal API | 30 days | 60 days |
| Experimental API | 14 days | 30 days |
| Security-critical | 7 days | 14 days |

---

## Deprecation Checklist

Before deprecating:

- [ ] New version (v2) is production-ready
- [ ] Migration guide written
- [ ] Stakeholders notified (30+ days notice)
- [ ] Deprecation warnings added to endpoints
- [ ] Metrics tracking v1 usage
- [ ] Support plan for migration help
- [ ] Timeline communicated clearly
- [ ] Architecture team approval

During deprecation:

- [ ] Weekly usage reports
- [ ] Contact clients still on v1
- [ ] Offer migration support
- [ ] Monitor error rates
- [ ] Update documentation

After removal:

- [ ] Verify v1 usage is zero
- [ ] Remove v1 code
- [ ] Archive documentation
- [ ] Update API index
- [ ] Post-mortem (lessons learned)

---

## Communication Template

```markdown
Subject: [ACTION REQUIRED] API v1 Deprecation - Migrate by Dec 22

Hi Team,

**API v1 is deprecated** and will be removed on **December 22, 2025** (60 days).

## What's Changing
- `/api/v1/users` → `/api/v2/users`
- Field `user_name` → `full_name`

## Action Required
1. Update your code to use `/api/v2/users`
2. Test changes in staging
3. Deploy to production before Dec 22

## Resources
- Migration Guide: https://docs.internal/v1-v2
- Support: #backend-support or @backend-team
- Questions: Reply to this email

## Timeline
- Today (Oct 22): v1 deprecated
- Nov 22 (30 days): v1 usage should be minimal
- Dec 22 (60 days): v1 removed

Thanks,
Backend Team
```

---

## Graceful Degradation

Instead of hard removal, consider:

### Option 1: Rate Limit
```python
@app.get("/api/v1/users")
@rate_limit("1 request/minute")  # Slow down deprecated API
async def list_users_v1():
    pass
```

### Option 2: Paid Support
```python
# v1 available only for enterprise customers
if not customer.has_extended_support:
    return 410  # Gone
```

### Option 3: Read-Only
```python
@app.get("/api/v1/users")  # GET still works
async def get_users_v1(): pass

@app.post("/api/v1/users")  # POST returns 410
async def create_user_v1():
    return 410
```

---

## References
- [VERSIONING_STRATEGY.md](./VERSIONING_STRATEGY.md)
- [BREAKING_CHANGES.md](./BREAKING_CHANGES.md)
- [COMPATIBILITY.md](./COMPATIBILITY.md)
