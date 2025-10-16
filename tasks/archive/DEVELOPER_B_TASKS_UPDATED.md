# Developer B - Updated Task Assignment

**Date:** October 13, 2025
**Status:** ✅ **READY TO START**
**Focus:** SPEC-088 (API Versioning Strategy)

---

## 🎉 **GOOD NEWS: SPEC-088 is NOW AVAILABLE!**

The SPEC numbering conflict has been resolved:
- ✅ Old `088-memory-sharing` → renamed to `128-memory-sharing` (SPEC-128)
- ✅ SPEC-088 is **FREE** for your API Versioning Strategy
- ✅ Hybrid SPEC system is now in place

---

## 🎯 **Your Primary Task**

### **Create SPEC-088: API Versioning Strategy**

**Directory:** `specs/088-api-versioning-strategy/`
**File:** `specs/088-api-versioning-strategy/README.md`

---

## 🚀 **Quick Start (Recommended Path)**

### **Step 1: Create SPEC Directory**

```bash
# Create SPEC directory
mkdir -p specs/088-api-versioning-strategy
```

**Note:** No branching needed - everyone works in the same folder/computer.

### **Step 2: Create SPEC Document**

Create `specs/088-api-versioning-strategy/README.md`:

```yaml
---
id: SPEC-088
title: API Versioning Strategy
status: Draft
phase: Infrastructure
owner: developer-b
updated: 2025-10-13
depends_on: [SPEC-003, SPEC-087]
tags: [API, Versioning, Architecture]
sidebar_position: 88
---

# SPEC-088: API Versioning Strategy

**Status:** Draft
**Phase:** Infrastructure
**Owner:** Developer B
**Updated:** October 13, 2025

---

## 1) Purpose

Define and implement a comprehensive API versioning strategy for ninaivalaigal that:
- Ensures backward compatibility
- Supports gradual migration
- Maintains clear deprecation paths
- Works with GraphQL and REST endpoints

---

## 2) Goals

- [ ] Define versioning scheme (URL path vs header)
- [ ] Implement version negotiation
- [ ] Create deprecation policy
- [ ] Document migration guides
- [ ] Set up automated compatibility tests

---

## 3) Proposed Versioning Scheme

### **Option A: URL Path Versioning (Recommended)**
```
/api/v1/memory/list
/api/v2/memory/list
```

**Pros:**
- ✅ Clear and explicit
- ✅ Easy to test
- ✅ Cacheable
- ✅ Works with all HTTP clients

**Cons:**
- ❌ URL changes on version bump
- ❌ Requires route duplication

### **Option B: Header Versioning**
```
GET /api/memory/list
Accept: application/vnd.ninaivalaigal.v1+json
```

**Pros:**
- ✅ Clean URLs
- ✅ Flexible content negotiation

**Cons:**
- ❌ Less discoverable
- ❌ Harder to test manually

### **Recommendation:** URL Path Versioning (Option A)

---

## 4) Implementation Plan

### **Phase 1: Current State (v1)**
- Label existing APIs as `/api/v1/`
- No breaking changes yet
- Document current contracts

### **Phase 2: Version Infrastructure**
- Create `server/versioning/` module
- Implement version routing middleware
- Add version detection logic

### **Phase 3: Migration Tools**
- API compatibility checker
- Automated migration scripts
- Deprecation warnings in responses

### **Phase 4: v2 Planning**
- Identify breaking changes needed
- Plan v1 → v2 migration path
- Set deprecation timeline

---

## 5) Deprecation Policy

### **Timeline**
- **Warning Period:** 6 months before removal
- **Deprecation Headers:** Added to responses
- **Documentation:** Clear migration guides
- **Support:** v(n-1) maintained while v(n) stabilizes

### **Response Headers**
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sun, 01 Jun 2026 00:00:00 GMT
Link: <https://docs.ninaivalaigal.io/migration/v1-to-v2>; rel="deprecation"
```

---

## 6) Dependencies

- **SPEC-003:** Core API Architecture
- **SPEC-087:** API Surface Contracts
- **SPEC-003:** May need updates for versioning middleware

---

## 7) Success Metrics

- [ ] All endpoints versioned
- [ ] Zero breaking changes in v1
- [ ] Migration guides published
- [ ] Automated compatibility tests passing
- [ ] Developer documentation complete

---

## 8) Technical Details

### **FastAPI Implementation**
```python
# server/versioning/router.py
from fastapi import APIRouter, Header
from typing import Optional

v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

@v1_router.get("/memory/list")
async def list_memory_v1():
    # v1 implementation
    pass

@v2_router.get("/memory/list")
async def list_memory_v2():
    # v2 implementation (future)
    pass
```

### **Version Detection Middleware**
```python
# server/middleware/version_detector.py
def detect_api_version(request):
    # Check URL path first
    if "/api/v2/" in request.url.path:
        return "v2"
    elif "/api/v1/" in request.url.path:
        return "v1"

    # Fallback to Accept header
    accept = request.headers.get("Accept", "")
    if "v2" in accept:
        return "v2"

    # Default to v1
    return "v1"
```

---

## 9) Open Questions

1. Should GraphQL endpoints be versioned separately?
2. Do we need per-endpoint versioning or only top-level?
3. Should we support version ranges (e.g., `v1.1`, `v1.2`)?
4. How to handle breaking changes in GraphQL schema?

---

## 10) Next Steps

1. **Review this SPEC** with team
2. **Get approval** for versioning approach
3. **Implement** version routing middleware
4. **Label** existing endpoints as v1
5. **Document** versioning policy
6. **Create** migration guide template

---

## References

- **SPEC-003:** Core API Architecture
- **SPEC-087:** API Surface Contracts
- **REST API Versioning Best Practices:** https://restfulapi.net/versioning/

---

**Status:** Draft - Awaiting Review
```

### **Step 3: Update SPEC Index**

Add entry to `specs/SPEC_INDEX.md`:

```markdown
### Infrastructure Phase
- **SPEC-088:** API Versioning Strategy ⚠️ DRAFT
  - Owner: Developer B
  - Status: In Progress
  - Phase: Infrastructure
  - Dependencies: SPEC-003, SPEC-087
```

### **Step 4: Commit Changes**

```bash
# Add files
git add specs/088-api-versioning-strategy/ specs/SPEC_INDEX.md

# Commit
git commit -m "feat(spec): Add SPEC-088 API Versioning Strategy (draft)"

# Push to main
git push origin main
```

**Note:** No branches - direct commits to main since everyone is on same machine.

---

## 🎨 **OPTIONAL: Visualize Your SPEC**

Good news! **The dashboard is already LIVE!** ✅

### **View Your SPEC After Creating It**

1. **Regenerate Dashboard**
```bash
cd ~/WorkSpace/dev-tools/spec-dashboard-generator
python3 spec-dashboard-generator.py /Users/swami/WorkSpace/ninaivalaigal
```

2. **View in Browser** (server already running)
```
http://localhost:3000/dashboard
http://localhost:3000/timeline
http://localhost:3000/timeline-gantt
```

**Note:** The docs server is already running! Just regenerate the JSON and refresh your browser.

**No container build needed** - we're using local npm for now.

---

## 📚 **New SPEC System Reference**

We now have a hybrid SPEC system:

### **What's New?**
- ✅ **YAML front-matter** in SPECs (see template above)
- ✅ **Dashboard generator** (analytics tool)
- ✅ **Docusaurus portal** (public docs)
- ✅ **Gantt charts** (timeline visualization)

### **Documentation**
- `HYBRID_SPEC_SYSTEM.md` - Complete system guide
- `TOOLS_REFERENCE.md` - Tool locations & usage
- `~/WorkSpace/dev-tools/spec-dashboard-generator/README.md` - Dashboard tool docs

### **Do I Need to Learn This Now?**
**NO!** Just follow the YAML front-matter template above. The dashboard/visualization is optional.

---

## 🎯 **Priority Order**

1. **HIGH:** Create SPEC-088 document (above)
2. **MEDIUM:** Review with team
3. **LOW:** Set up dashboard visualization (optional)

---

## ✅ **Deliverables**

When you're done, you should have:

- [ ] Created `specs/088-api-versioning-strategy/README.md`
- [ ] Updated `specs/SPEC_INDEX.md`
- [ ] Committed and pushed to main
- [ ] (Optional) Viewed your SPEC on the live dashboard

---

## ❓ **Questions?**

- **SPEC conflicts?** ✅ Resolved - SPEC-088 is free
- **Container setup required?** ❌ No, optional
- **YAML front-matter?** ✅ Use template above
- **Dashboard?** ❌ Not required, just for visualization

---

## 📊 **Summary**

**What changed since last task file:**
- ✅ SPEC-088 is now **available** (conflict resolved)
- ✅ New **YAML front-matter** format for SPECs
- ✅ Optional **dashboard/visualization** tools
- ✅ Simpler workflow - just create SPEC document

**Your focus:** Write SPEC-088 document (see template above)

**Container setup:** Optional, only for visualization

---

**Estimated Time:** 3-4 hours
**Difficulty:** Medium (architecture design)
**Status:** ✅ Ready to start immediately

---

Good luck! 🚀
