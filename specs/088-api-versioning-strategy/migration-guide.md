# API Migration Guide Template

**Last Updated**: November 2, 2025
**Related**: [SPEC-088: API Versioning Strategy](./README.md)

---

## Overview

This document provides a template for creating migration guides when releasing new API versions with breaking changes. Every version migration must include a comprehensive guide to help clients transition smoothly.

**Purpose**: Help API consumers migrate from one version to another with minimal friction.

---

## Migration Guide Template

Use this template when creating a migration guide for a new API version:

```markdown
# Migration Guide: v{OLD} → v{NEW}

**Release Date**: {DATE}
**Deprecation Date**: {DATE}
**Sunset Date**: {DATE}
**Status**: {Active/Deprecated/Sunset}

---

## Overview

### What Changed

Brief summary of what changed and why.

**Key Changes**:
- Change 1
- Change 2
- Change 3

### Why We Made These Changes

Explanation of the rationale behind the breaking changes.

### Who Is Affected

Description of which API consumers are affected by these changes.

---

## Breaking Changes

### 1. {Breaking Change Title}

**Type**: {Field Rename/Endpoint Removal/Type Change/etc.}

**Impact**: {High/Medium/Low}

**Before (v{OLD})**:
```json
{
  "old_field": "value"
}
```

**After (v{NEW})**:
```json
{
  "new_field": "value"
}
```

**Migration Steps**:
1. Update field name in your code
2. Test with new version
3. Deploy changes

**Code Example**:

**Python (Before)**:
```python
response = requests.get("/api/v1/users")
old_field = response.json()["old_field"]
```

**Python (After)**:
```python
response = requests.get("/api/v2/users")
new_field = response.json()["new_field"]
```

---

### 2. {Another Breaking Change}

{Repeat format for each breaking change}

---

## Migration Steps

### Step 1: Review Breaking Changes

Read through all breaking changes above and identify which ones affect your integration.

**Checklist**:
- [ ] Reviewed all breaking changes
- [ ] Identified affected endpoints
- [ ] Noted required code changes

### Step 2: Update Your Code

Make necessary code changes to support the new version.

**Checklist**:
- [ ] Updated field names
- [ ] Updated endpoint URLs
- [ ] Updated request/response handling
- [ ] Updated error handling

### Step 3: Test in Staging

Test your changes in a staging environment before deploying to production.

**Checklist**:
- [ ] Tested all affected endpoints
- [ ] Verified response formats
- [ ] Tested error scenarios
- [ ] Performed integration tests

### Step 4: Deploy to Production

Deploy your changes to production and monitor for issues.

**Checklist**:
- [ ] Deployed code changes
- [ ] Monitored error rates
- [ ] Verified functionality
- [ ] Updated documentation

### Step 5: Clean Up

Remove references to the old version.

**Checklist**:
- [ ] Removed old version code
- [ ] Updated internal documentation
- [ ] Notified team of completion

---

## Timeline

| Date | Milestone | Action Required |
|------|-----------|-----------------|
| {DATE} | v{NEW} Released | No action required yet |
| {DATE} | v{OLD} Deprecated | Begin migration |
| {DATE} | Migration Reminder | Complete migration soon |
| {DATE} | Final Warning | Complete migration immediately |
| {DATE} | v{OLD} Removed | Migration must be complete |

**Recommended Migration Window**: {30/60/90} days

---

## Code Examples

### Example 1: {Use Case}

**Before (v{OLD})**:
```python
# Old code
```

**After (v{NEW})**:
```python
# New code
```

### Example 2: {Another Use Case}

**Before (v{OLD})**:
```python
# Old code
```

**After (v{NEW})**:
```python
# New code
```

---

## Common Issues and Solutions

### Issue 1: {Common Problem}

**Problem**: Description of the issue

**Solution**: How to fix it

**Example**:
```python
# Solution code
```

### Issue 2: {Another Problem}

{Repeat format}

---

## Testing Checklist

**Pre-Migration Testing**:
- [ ] Test all affected endpoints with v{NEW}
- [ ] Verify response formats match expectations
- [ ] Test error scenarios
- [ ] Perform load testing
- [ ] Test edge cases

**Post-Migration Testing**:
- [ ] Monitor error rates
- [ ] Check application logs
- [ ] Verify metrics/analytics
- [ ] Test user workflows
- [ ] Monitor performance

---

## Support and Resources

### Documentation

- **v{NEW} API Reference**: {URL}
- **v{NEW} OpenAPI Schema**: {URL}
- **v{NEW} Postman Collection**: {URL}
- **Migration FAQ**: {URL}

### Support Channels

- **Email**: api-support@ninaivalaigal.com
- **Slack**: #api-migration
- **Office Hours**: {Schedule}
- **1-on-1 Consultation**: {Booking URL}

### Emergency Support

If you encounter critical issues during migration:
- **Email**: api-emergency@ninaivalaigal.com
- **Phone**: 1-800-API-HELP
- **Available**: 24/7 during migration period

---

## FAQ

### Q: Do I need to migrate immediately?

A: No, v{OLD} will remain supported until {SUNSET_DATE}. However, we recommend migrating as soon as possible.

### Q: Can I use both versions simultaneously?

A: Yes, you can use both v{OLD} and v{NEW} during the migration period.

### Q: What happens if I don't migrate by the sunset date?

A: After {SUNSET_DATE}, v{OLD} will be removed and all requests will return 410 Gone.

### Q: Can I get an extension on the migration deadline?

A: Extensions may be granted in exceptional circumstances. Contact api-extensions@ninaivalaigal.com.

### Q: Will there be downtime during the migration?

A: No, both versions run simultaneously. You can migrate at your own pace.

---

## Feedback

We'd love to hear about your migration experience:

- **Survey**: {Survey URL}
- **Email**: api-feedback@ninaivalaigal.com
- **GitHub Issues**: {Issues URL}

Your feedback helps us improve future migrations.

---

**Last Updated**: {DATE}
**Status**: {Active/Deprecated}
**Next Review**: {DATE}
```

---

## Example: v1 → v2 Migration Guide

Here's a complete example of a migration guide:

# Migration Guide: v1 → v2

**Release Date**: November 1, 2025
**Deprecation Date**: December 1, 2025
**Sunset Date**: January 30, 2026
**Status**: Active

---

## Overview

### What Changed

API v2 introduces improved field naming, better error handling, and enhanced response formats.

**Key Changes**:
- Field names changed from snake_case to camelCase
- Timestamps now use ISO 8601 format
- Error responses now include error codes
- New pagination format

### Why We Made These Changes

These changes improve API consistency, make it easier to use from JavaScript clients, and provide better error information for debugging.

### Who Is Affected

All API consumers using v1 endpoints for users, memories, and contexts.

---

## Breaking Changes

### 1. Field Name Changes

**Type**: Field Rename
**Impact**: HIGH

**Before (v1)**:
```json
{
  "user_name": "john_doe",
  "created_date": "2025-11-02"
}
```

**After (v2)**:
```json
{
  "username": "john_doe",
  "createdAt": "2025-11-02T08:00:00Z"
}
```

**Migration Steps**:
1. Update all field references from `user_name` to `username`
2. Update all field references from `created_date` to `createdAt`
3. Update date parsing to handle ISO 8601 format

**Code Example**:

**Python (Before)**:
```python
response = requests.get("/api/v1/users/123")
user_name = response.json()["user_name"]
created = datetime.strptime(response.json()["created_date"], "%Y-%m-%d")
```

**Python (After)**:
```python
response = requests.get("/api/v2/users/123")
username = response.json()["username"]
created = datetime.fromisoformat(response.json()["createdAt"])
```

### 2. Error Response Format

**Type**: Response Structure Change
**Impact**: MEDIUM

**Before (v1)**:
```json
{
  "error": "User not found"
}
```

**After (v2)**:
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": {}
  }
}
```

**Migration Steps**:
1. Update error handling to parse new error structure
2. Use error codes for programmatic error handling

**Code Example**:

**Python (Before)**:
```python
try:
    response = requests.get("/api/v1/users/123")
    response.raise_for_status()
except requests.HTTPError as e:
    error_msg = e.response.json()["error"]
    print(f"Error: {error_msg}")
```

**Python (After)**:
```python
try:
    response = requests.get("/api/v2/users/123")
    response.raise_for_status()
except requests.HTTPError as e:
    error = e.response.json()["error"]
    print(f"Error {error['code']}: {error['message']}")
```

---

## Migration Steps

### Step 1: Review Breaking Changes

✅ Field name changes (user_name → username)
✅ Timestamp format changes (date → ISO 8601)
✅ Error response structure changes

### Step 2: Update Your Code

Update all references to changed fields and error handling.

### Step 3: Test in Staging

Test with v2 endpoints in staging environment.

### Step 4: Deploy to Production

Deploy changes and monitor for issues.

### Step 5: Clean Up

Remove v1 references after successful migration.

---

## Timeline

| Date | Milestone | Action Required |
|------|-----------|-----------------|
| Nov 1 | v2 Released | No action required yet |
| Dec 1 | v1 Deprecated | Begin migration |
| Jan 15 | Migration Reminder | Complete migration soon |
| Jan 25 | Final Warning | Complete migration immediately |
| Jan 30 | v1 Removed | Migration must be complete |

**Recommended Migration Window**: 60 days

---

## Support and Resources

### Documentation

- **v2 API Reference**: https://docs.ninaivalaigal.com/api/v2
- **v2 OpenAPI Schema**: https://api.ninaivalaigal.com/api/v2/openapi.json
- **Migration FAQ**: https://docs.ninaivalaigal.com/api/v1-to-v2/faq

### Support Channels

- **Email**: api-support@ninaivalaigal.com
- **Slack**: #api-migration
- **Office Hours**: Tuesdays 2-4 PM CST

---

## References

- **[SPEC-088: API Versioning Strategy](./README.md)** - Overall versioning approach
- **[breaking-changes.md](./breaking-changes.md)** - Breaking change definitions
- **[deprecation-policy.md](./deprecation-policy.md)** - Deprecation policy
- **[format.md](./format.md)** - API version format specifications

---

**Last Updated**: November 2, 2025
**Status**: 📋 Planned (Documentation Phase)
**Template Version**: 1.0
