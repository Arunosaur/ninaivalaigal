# Developer Roles & Responsibilities - Flexible Model

**Created:** October 13, 2025  
**Philosophy:** Primary ownership with flexible collaboration

---

## 🎯 **Core Principle**

**Primary Ownership + Pragmatic Flexibility**

- Each developer **owns** specific areas (primary responsibility)
- BUT can **contribute** to any area when:
  - Primary owner is unavailable
  - Blocking issue needs immediate fix
  - Collaboration improves outcome
  - Skills/availability align

**Goal:** Move fast, don't get blocked, but maintain clear accountability

---

## 👨‍💻 **Developer A: Frontend & Test Infrastructure Lead**

### **Primary Ownership (Your Main Focus)**

#### **Frontend Production Code**
- `frontend-nextjs-customer/` (TypeScript/React/Next.js)
- `frontend-nextjs-admin/` (TypeScript/React/Next.js)
- UI components, pages, layouts, styles
- Frontend utilities and hooks

#### **Test Infrastructure (Python)**
- `tests/auth_aware/` - Auth test fixtures, helpers, utilities
- `tests/e2e/` - Playwright tests (TypeScript)
- Test harness and framework code
- Mock/stub utilities for testing

#### **Testing Coverage**
- E2E tests (Playwright)
- Frontend unit tests (Vitest)
- Component tests
- Visual regression tests

---

### **Can Contribute To (When Needed)**

✅ **Backend Test Files**
- Integration tests that test API endpoints
- Test fixtures used by multiple test suites
- Test utilities and helpers

✅ **Documentation**
- Testing documentation
- Frontend documentation
- README updates

✅ **Bug Fixes**
- Critical frontend bugs
- Test failures blocking development
- CI/CD issues affecting tests

---

### **Should Avoid (Unless Emergency)**

❌ **Backend Production Code**
- `server/*.py` business logic
- API endpoint implementations
- Database models and migrations
- Core backend services

❌ **Infrastructure**
- Kubernetes configs
- Docker production images
- Database schema changes
- Deployment pipelines

---

## ⚙️ **Developer C: Backend & Infrastructure Lead**

### **Primary Ownership (Your Main Focus)**

#### **Backend Production Code**
- `server/` - FastAPI application code
- API endpoints and business logic
- Database models and ORM
- Authentication/authorization logic
- Backend services and utilities

#### **Infrastructure**
- Docker configurations
- Kubernetes deployments
- CI/CD pipelines
- Database migrations (`alembic/`)
- Monitoring and logging

#### **Backend Testing**
- Backend unit tests
- API integration tests
- Database tests
- Performance tests

---

### **Can Contribute To (When Needed)**

✅ **Test Infrastructure**
- Shared test fixtures (conftest.py)
- Test configuration and setup
- Helping debug test failures
- Backend test utilities

✅ **Frontend Issues**
- API integration bugs
- CORS issues
- Authentication flow issues
- Critical frontend bugs blocking development

✅ **Documentation**
- API documentation
- Backend architecture docs
- Deployment guides

---

### **Should Avoid (Unless Emergency)**

❌ **Frontend Production Code**
- React components
- Frontend routing
- UI/UX implementation
- Frontend state management

❌ **Frontend Tests**
- E2E test implementation (unless blocking)
- Component tests
- Frontend unit tests

---

## 👨‍💼 **Developer B: Documentation & Architecture Lead**

### **Primary Ownership (Your Main Focus)**

#### **Documentation**
- All `docs/` files
- SPEC creation and maintenance
- Architecture diagrams
- API documentation
- Testing guides

#### **Quality Assurance**
- Documentation standards
- SPEC validation scripts
- Content organization
- Version control for docs

#### **Project Organization**
- File structure cleanup
- Root directory organization
- Archive management
- Tooling for documentation

---

### **Can Contribute To (When Needed)**

✅ **Testing Documentation**
- Test patterns and guides
- Testing troubleshooting
- Test templates

✅ **Code Examples**
- Documentation code samples
- Tutorial code
- Example implementations

✅ **Scripts and Tools**
- Documentation build scripts
- Validation tools
- Automation scripts

✅ **Root Cleanup**
- File organization (current task)
- Archive management
- Structure improvements

---

### **Should Avoid (Unless Emergency)**

❌ **Production Code**
- Frontend or backend implementation
- Business logic
- API endpoints

❌ **Test Implementation**
- Writing actual tests
- Test fixtures (can document them though)
- Test infrastructure code

---

## 🤝 **Collaboration Guidelines**

### **When to Collaborate (No Permission Needed)**

✅ **Shared Areas:**
- `tests/conftest.py` - Shared test configuration
- `.github/workflows/` - CI/CD affecting your work
- `README.md` - Project overview
- Bug fixes in your domain that touch other code

✅ **Helping Others:**
- Code reviews
- Pair programming
- Debugging assistance
- Emergency bug fixes

✅ **Unblocking Work:**
- If primary owner unavailable and work is blocked
- Critical path items
- Time-sensitive issues

---

### **When to Ask/Coordinate**

⚠️ **Major Changes:**
- Architectural changes
- Breaking API changes
- Database schema changes
- File structure reorganization

⚠️ **Primary Owner's Domain:**
- Large feature implementation in another's area
- Refactoring someone else's code
- Changes affecting multiple areas

⚠️ **Potential Conflicts:**
- Editing files someone is actively working on
- Changes that might conflict with ongoing work
- Anything that might duplicate effort

---

## 🚦 **Decision Framework**

### **Ask Yourself:**

1. **Is this my primary area?**
   - YES → Go ahead
   - NO → Continue to #2

2. **Is it blocking me or the team?**
   - YES → Do it, inform owner
   - NO → Continue to #3

3. **Is the primary owner available?**
   - NO → Do it, document decision
   - YES → Continue to #4

4. **Will it save significant time?**
   - YES → Quick sync with owner, then do it
   - NO → Ask owner to handle it

---

## 📊 **Example Scenarios**

### **Scenario 1: Backend Test Failing (Developer A's Tests)**

**Developer C finds the issue:**
- ✅ **Quick fix?** → Fix it, commit with clear message
- ⚠️ **Complex fix?** → Ping Developer A or fix with note
- 📝 **Always:** Document what was fixed and why

**Result:** Don't get blocked, maintain velocity

---

### **Scenario 2: Frontend API Integration Bug**

**Developer A needs backend change:**
- ✅ **Small fix?** → Developer C fixes immediately
- ⚠️ **API change needed?** → Quick sync, Developer C implements
- 📋 **Large refactor?** → Plan together, Developer C leads

**Result:** Fast turnaround on integration issues

---

### **Scenario 3: Test Infrastructure Needs Update**

**Who does it?**
- ✅ **Developer A primary** (test infrastructure owner)
- ✅ **Developer C can help** (if Developer A busy)
- 🤝 **Collaborate** (if complex or affects both)

**Result:** Whoever is available and has context

---

### **Scenario 4: Root Directory Cleanup**

**Current assignment:**
- ✅ **Developer B primary** (documentation/organization owner)
- ✅ **Developer A/C can help** (moving files, testing builds)

**Result:** Developer B leads, others assist as needed

---

## 📝 **Communication Protocol**

### **When Making Changes Outside Your Area:**

```
# Git commit message format:
[area]: Brief description

Rationale: Why this change was needed
Context: What prompted it (blocking issue, bug, etc.)
Owner notified: @developer-name (or "unavailable")
Tests: What was tested
```

**Example:**
```
[backend/tests]: Fix failing auth test fixtures

Rationale: Test failures blocking my frontend integration work
Context: Developer C unavailable, needed to unblock
Owner notified: Will sync with Developer C after
Tests: pytest tests/auth_aware/ passing
```

---

## ✅ **Success Metrics**

### **Good Signs:**
- ✅ Team isn't blocked waiting for others
- ✅ Clear ownership and accountability
- ✅ Fast turnaround on issues
- ✅ Good communication about cross-area work
- ✅ No duplicate effort

### **Warning Signs:**
- ⚠️ Stepping on each other's toes
- ⚠️ Unclear who owns what
- ⚠️ Changes made without communication
- ⚠️ Primary owners feeling undermined
- ⚠️ Quality degrading in non-primary areas

---

## 🎯 **Summary Table**

| Area | Primary Owner | Can Contribute | Should Avoid |
|------|--------------|----------------|--------------|
| **Frontend Code** | Developer A | Developer C (bugs) | Developer B |
| **Backend Code** | Developer C | Developer A (critical) | Developer B |
| **Test Infrastructure** | Developer A | Developer C | Developer B |
| **Backend Tests** | Developer C | Developer A | Developer B |
| **Documentation** | Developer B | All | - |
| **Root Cleanup** | Developer B | All | - |
| **CI/CD** | Developer C | All | - |

---

## 💡 **Philosophy in Action**

### **Developer A & C Working on Tests:**

**Scenario:**
- Developer A: Building test infrastructure (fixtures, helpers)
- Developer C: Fixing flake8 violations in test files
- Both: Contributing to test quality

**Coordination:**
- Developer A focuses on new test infrastructure
- Developer C fixes existing test issues
- Both review each other's test PRs
- Quick syncs if touching same files

**Result:** ✅ Tests improve faster, no blocking

---

### **When Developer B is Busy:**

**Scenario:**
- Developer B assigned root cleanup
- But Developer B also has SPEC work
- Timeline pressure on cleanup

**Flexibility:**
- Developer A/C help move obvious files
- Developer B reviews and approves structure
- Developer B handles complex decisions
- Team finishes cleanup faster

**Result:** ✅ Pragmatic collaboration

---

## 🔄 **This is a Living Document**

**Update this when:**
- Roles evolve
- New patterns emerge
- Team grows
- Conflict areas identified
- Better processes discovered

---

## 🎯 **Bottom Line**

**Primary Ownership:**
- Clear accountability
- Quality standards
- Deep expertise

**Flexible Collaboration:**
- Don't get blocked
- Help each other
- Move fast
- Maintain quality

**Communication:**
- Document decisions
- Inform primary owners
- Learn from each other
- Improve together

---

**Status:** ✅ Active  
**Review:** Monthly or as needed  
**Philosophy:** "Strong opinions, weakly held. Clear ownership, flexible execution."

---

**Created by:** Developer C  
**Approved by:** Team  
**Last Updated:** October 13, 2025
