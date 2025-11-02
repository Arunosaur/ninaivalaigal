# Deprecation Policy

**Last Updated**: November 2, 2025
**Related**: [SPEC-088: API Versioning Strategy](./README.md)

---

## Overview

This document defines the deprecation policy for API versions in the Ninaivalaigal platform. When a new API version is released with breaking changes, the old version must be deprecated and eventually removed following this policy.

**Key Principles**:
1. **Predictable timelines** - Clear deprecation and sunset dates
2. **Advance notice** - Minimum 30 days warning
3. **Migration support** - Help clients transition
4. **Clear communication** - Multiple channels and reminders

---

## Minimum Support Period

### **Standard Support: 60 Days**

**Default timeline** for most API version deprecations:

| Period | Duration | Status | Support Level |
|--------|----------|--------|---------------|
| **Active** | Indefinite | ✅ Current version | Full support |
| **Deprecated** | 60 days | ⚠️ Transition period | Security patches only |
| **Sunset** | Permanent | ❌ Removed | No support |

**Example**:
```
Nov 1:  v2 released → v1 active (full support)
Dec 1:  v1 deprecated → v1 deprecated (security only)
Jan 30: v1 removed → v1 sunset (no support)
```

### **Extended Support: 90 Days**

**When to use**: Major versions with high usage

**Criteria**:
- 1000+ active integrations
- Critical business clients
- Complex migration requirements
- Product team approval required

**Timeline**:
```
Nov 1:  v2 released → v1 active
Dec 1:  v1 deprecated → v1 deprecated
Feb 28: v1 removed → v1 sunset
```

### **Accelerated Support: 30 Days**

**When to use**: Security-critical breaking changes

**Criteria**:
- Critical security vulnerability
- Data privacy issue
- Regulatory compliance requirement
- Security team approval required

**Timeline**:
```
Nov 1:  v2 released (security fix) → v1 active
Nov 15: v1 deprecated → v1 deprecated
Dec 1:  v1 removed → v1 sunset
```

**Requirements**:
- Emergency communication plan
- 24/7 migration support
- Dedicated support team
- Executive approval

---

## Deprecation Notice Process

### **Step 1: Internal Preparation** (Before Release)

**Activities**:
- [ ] Write migration guide
- [ ] Prepare communication templates
- [ ] Set up monitoring dashboards
- [ ] Train support team
- [ ] Create FAQ document

**Timeline**: 1-2 weeks before v2 release

### **Step 2: Release Announcement** (Day 0)

**Activities**:
- [ ] Release new version (v2)
- [ ] Publish release notes
- [ ] Send announcement email
- [ ] Post to status page
- [ ] Update documentation

**Channels**:
- Email to all API users
- Developer blog post
- Status page announcement
- Slack/Discord notification
- Twitter/social media

**Template**:
```
Subject: New API Version Released - v2 Now Available

We're excited to announce API v2 is now available!

What's New:
- Improved field naming
- Better error handling
- Enhanced performance

Migration:
- v1 remains fully supported
- Migration guide: https://docs.ninaivalaigal.com/api/v1-to-v2
- No immediate action required

Timeline:
- Today: v2 released, v1 active
- Dec 1: v1 deprecated (30 days)
- Jan 30: v1 removed (90 days)

Questions? Contact api-support@ninaivalaigal.com
```

### **Step 3: Deprecation Warning** (Day 30)

**Activities**:
- [ ] Add deprecation headers to v1 responses
- [ ] Send deprecation notice email
- [ ] Update documentation with warnings
- [ ] Post deprecation notice
- [ ] Monitor usage metrics

**HTTP Headers Added**:
```http
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30
X-API-Replacement: /api/v2/users
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
```

**Response Body Warning**:
```json
{
  "data": [...],
  "warnings": [
    {
      "code": "DEPRECATED_API_VERSION",
      "message": "API v1 is deprecated and will be removed on Jan 30, 2026.",
      "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2",
      "sunset_date": "2026-01-30",
      "days_remaining": 60
    }
  ]
}
```

**Email Template**:
```
Subject: Action Required - API v1 Deprecated

API v1 has been deprecated and will be removed in 60 days.

Important Dates:
- Today: v1 deprecated (warnings added)
- Jan 30: v1 removed (60 days)

Action Required:
1. Review migration guide
2. Update to v2 endpoints
3. Test in staging
4. Deploy to production

Migration Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
Support: api-support@ninaivalaigal.com
```

### **Step 4: Migration Reminders** (Day 45)

**Activities**:
- [ ] Send reminder email to active v1 users
- [ ] Post reminder on status page
- [ ] Reach out to high-volume users directly
- [ ] Offer migration assistance

**Email Template**:
```
Subject: Reminder - API v1 Removal in 15 Days

This is a reminder that API v1 will be removed in 15 days.

Timeline:
- Jan 15: v1 removal in 15 days (TODAY)
- Jan 30: v1 removed

Your Usage:
- Last 7 days: 1,234 v1 requests
- Migration status: Not started

Need Help?
- Migration guide: https://docs.ninaivalaigal.com/api/v1-to-v2
- Schedule consultation: calendly.com/api-support
- Email: api-support@ninaivalaigal.com
```

### **Step 5: Final Warning** (Day 55)

**Activities**:
- [ ] Send final warning email
- [ ] Contact remaining v1 users
- [ ] Offer emergency migration support
- [ ] Prepare for sunset

**Email Template**:
```
Subject: URGENT - API v1 Removal in 5 Days

FINAL NOTICE: API v1 will be removed in 5 days.

Timeline:
- Jan 25: v1 removal in 5 days (TODAY)
- Jan 30: v1 REMOVED - All v1 requests will fail

Action Required IMMEDIATELY:
1. Migrate to v2 before Jan 30
2. Test thoroughly
3. Monitor for errors

Emergency Support:
- Priority support: api-emergency@ninaivalaigal.com
- Phone: 1-800-API-HELP
- 24/7 support available
```

### **Step 6: Sunset** (Day 60)

**Activities**:
- [ ] Remove v1 endpoints
- [ ] Return 410 Gone for v1 requests
- [ ] Send sunset confirmation email
- [ ] Archive v1 documentation
- [ ] Monitor for stragglers

**410 Gone Response**:
```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "API_VERSION_REMOVED",
    "message": "API v1 was removed on Jan 30, 2026. Please use v2.",
    "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2",
    "replacement": "/api/v2/users",
    "sunset_date": "2026-01-30"
  }
}
```

**Email Template**:
```
Subject: API v1 Has Been Removed

API v1 has been removed as scheduled.

All v1 requests now return 410 Gone.

Next Steps:
- Ensure all systems use v2
- Monitor for errors
- Contact support if issues arise

v2 Documentation: https://docs.ninaivalaigal.com/api/v2
Support: api-support@ninaivalaigal.com
```

---

## Sunset Timeline

### **Complete Timeline Visualization**

```
Day 0     Day 30    Day 45    Day 55    Day 60    Day 90
  |         |         |         |         |         |
  v2        v1        Reminder  Final     v1        Archive
Released  Deprecated           Warning   Removed   Complete
  |         |         |         |         |         |
  └─────────┴─────────┴─────────┴─────────┴─────────┘

  Active Period      Deprecated Period      Sunset
  (Full Support)     (Security Only)        (Removed)
```

### **Timeline Activities**

| Day | Milestone | Activity | Communication |
|-----|-----------|----------|---------------|
| 0 | v2 Released | Deploy v2, v1 active | Release announcement |
| 30 | v1 Deprecated | Add warnings | Deprecation notice |
| 45 | Reminder | Check usage | Migration reminder |
| 55 | Final Warning | Last chance | Urgent notice |
| 60 | v1 Removed | Return 410 Gone | Sunset confirmation |
| 90 | Archive Complete | Archive docs | Archive notice |

---

## Communication Plan to Users

### **Communication Channels**

| Channel | Frequency | Audience | Purpose |
|---------|-----------|----------|---------|
| **Email** | Day 0, 30, 45, 55, 60 | All API users | Primary notification |
| **Status Page** | Day 0, 30, 60 | Public | Transparency |
| **Developer Blog** | Day 0, 30 | Developers | Detailed info |
| **Documentation** | Continuous | All users | Reference |
| **Slack/Discord** | Day 0, 30, 55 | Community | Discussion |
| **Social Media** | Day 0, 30 | Public | Awareness |
| **Direct Outreach** | Day 45, 55 | High-volume users | Personal support |

### **Email List Segmentation**

**Segment 1: Active v1 Users**
- Users with v1 requests in last 30 days
- Priority: HIGH
- Communication: All emails + direct outreach

**Segment 2: Inactive v1 Users**
- Users with no v1 requests in last 30 days
- Priority: MEDIUM
- Communication: Standard emails only

**Segment 3: v2-Only Users**
- Users already migrated to v2
- Priority: LOW
- Communication: Release announcement only

### **Message Tone Guidelines**

**Day 0-30** (Informative):
- Positive tone
- Emphasize benefits of v2
- No urgency

**Day 30-55** (Encouraging):
- Helpful tone
- Offer migration support
- Gentle urgency

**Day 55-60** (Urgent):
- Direct tone
- Clear deadline
- Strong urgency
- Offer emergency support

---

## Migration Support

### **Support Resources**

**Documentation**:
- [ ] Migration guide with examples
- [ ] API v2 reference documentation
- [ ] FAQ document
- [ ] Video tutorials
- [ ] Code samples in multiple languages

**Support Channels**:
- [ ] Email support: api-support@ninaivalaigal.com
- [ ] Slack channel: #api-migration
- [ ] Office hours: Weekly migration Q&A sessions
- [ ] 1-on-1 consultations: For high-volume users
- [ ] Emergency hotline: For critical issues

### **Migration Assistance Program**

**Tier 1: Self-Service** (All Users)
- Migration guide
- Code examples
- FAQ
- Community support

**Tier 2: Guided Migration** (Enterprise Users)
- Dedicated support engineer
- Migration plan review
- Testing assistance
- Deployment support

**Tier 3: White-Glove Migration** (Strategic Partners)
- Full migration service
- Code updates
- Testing and validation
- Post-migration monitoring

### **Migration Validation**

**Pre-Migration Checklist**:
- [ ] Read migration guide
- [ ] Identify affected endpoints
- [ ] Update code to v2
- [ ] Update tests
- [ ] Test in staging environment

**Post-Migration Checklist**:
- [ ] Deploy to production
- [ ] Monitor error rates
- [ ] Verify functionality
- [ ] Remove v1 references
- [ ] Update documentation

### **Monitoring and Metrics**

**Track During Deprecation Period**:
- v1 request volume (daily)
- v2 adoption rate (%)
- Active v1 users (count)
- Migration completion rate (%)
- Support ticket volume

**Success Criteria**:
- 90%+ users migrated before sunset
- <10 support tickets on sunset day
- Zero critical incidents during transition

---

## Exception Process

### **When to Grant Extensions**

**Valid Reasons**:
- Critical business dependency
- Complex integration requiring more time
- External factors beyond client control
- Strategic partnership considerations

**Invalid Reasons**:
- Lack of planning
- Resource constraints (without mitigation plan)
- "Didn't see the emails"

### **Extension Request Process**

1. **Submit Request** (Before Day 50)
   - Email: api-extensions@ninaivalaigal.com
   - Include: Business justification, timeline, mitigation plan

2. **Review** (2-3 business days)
   - Product team reviews
   - Technical feasibility assessment
   - Business impact evaluation

3. **Decision**
   - Approved: Extended timeline granted (max +30 days)
   - Denied: Standard timeline applies

4. **Conditions**
   - Detailed migration plan required
   - Weekly progress updates
   - Dedicated support assigned

---

## References

- **[SPEC-088: API Versioning Strategy](./README.md)** - Overall versioning approach
- **[SPEC-089: Breaking Change Management](../089-breaking-change-management/README.md)** - Breaking change process
- **[migration-guide.md](./migration-guide.md)** - Migration guide template
- **[breaking-changes.md](./breaking-changes.md)** - Breaking change examples

---

**Last Updated**: November 2, 2025
**Status**: 📋 Planned (Documentation Phase)
**Next Review**: Upon first API version deprecation
