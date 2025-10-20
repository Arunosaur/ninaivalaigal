# Taiga Labels and Task Improvements

**Date:** October 20, 2025
**Status:** Recommendations to implement

---

## 🟡 Suggestion 1: Standardized Labels in Taiga

### **Why This Matters**
Makes filtering and Kanban board management dramatically easier, especially when tracking 130+ specs.

### **Recommended Label Structure**

#### **Priority Labels**
- `p0-blocker` - Critical blockers (Tasks #85, #79, #83)
- `p1-high` - High priority (Tasks #86, #87, #88)
- `p2-future` - Future work (Tasks #89, #90)

#### **Phase Labels**
- `phase0-infra` - Infrastructure foundation (Task #85)
- `phase1-contracts` - Contracts layer (Task #79)
- `phase2-gateway` - API Gateway (Task #83)
- `phase3-decomposition` - Service decomposition (Task #88)

#### **Time Labels**
- `oct-2025` - October 2025 work
- `nov-2025` - November 2025 work
- `dec-2025` - December 2025 work
- `jan-2026` - January 2026 work
- `q1-2026` - Q1 2026 work
- `q2-2026` - Q2 2026 work
- `q3-2026` - Q3 2026 work

#### **SPEC Labels**
- `spec-099` - Rust + Go Migration
- `spec-100` - API Modularization

#### **Technical Labels**
- `rust` - Rust-related work
- `go` - Go-related work
- `python` - Python-related work
- `contracts` - Contract-related work
- `performance` - Performance optimization
- `security` - Security-related
- `observability` - Monitoring/tracing

### **Implementation Steps**

1. **Create Labels in Taiga:**
   - Go to Project Settings → Labels
   - Create each label with appropriate color:
     - Red for P0
     - Yellow for P1
     - Green for P2
     - Blue for phases
     - Purple for time periods

2. **Tag Existing Tasks:**
   ```
   Task #85: p0-blocker, phase0-infra, oct-2025, nov-2025, spec-099
   Task #79: p0-blocker, phase1-contracts, nov-2025, dec-2025, spec-100, spec-099
   Task #83: p0-blocker, phase2-gateway, dec-2025, spec-100
   Task #86: p1-high, performance, nov-2025, spec-099
   Task #87: p1-high, contracts, dec-2025, q1-2026, spec-099, spec-100
   Task #88: p1-high, phase3-decomposition, dec-2025, jan-2026, q1-2026, spec-100
   Task #89: p2-future, q2-2026, spec-100
   Task #90: p2-future, q3-2026, spec-100, security
   ```

3. **Set Up Kanban Filters:**
   - Filter by `oct-2025` to see current month work
   - Filter by `p0-blocker` to see critical path
   - Filter by `spec-099` to track Rust migration
   - Filter by `phase1-contracts` to see contracts work

### **Benefits**
- ✅ Easy filtering by priority
- ✅ Easy filtering by time period
- ✅ Easy grouping by SPEC
- ✅ Visual clarity on Kanban board
- ✅ Scalable to 130+ specs

---

## 🟡 Suggestion 2: Task #88 Early Decomposition Prep

### **The Problem**
Task #88 (Core API Decomposition) is 4-6 weeks of burst effort (Week 9-12). This is risky because:
- 49K lines of monolithic code
- 54 routers to separate
- Complex dependencies
- High risk of delay

### **Recommendation: Start Earlier with Design Spikes**

#### **Week 6-7: Interface Refactoring Prep (NEW)**

Add a new task: **"Task #88-Prep: Core API Interface Refactoring"**

**Goal:** Reduce burst effort in Week 9-12 by preparing interfaces early.

**Deliverables:**
- [ ] **Map Service Boundaries (Week 6)**
  - Document which routers go to which service
  - Identify shared dependencies
  - Map database access patterns
  - Document cross-service calls

- [ ] **Create Interface Contracts (Week 7)**
  - Define internal APIs between services
  - Create stub interfaces for separation
  - Document expected request/response flows
  - Identify potential circular dependencies

- [ ] **Refactor Shared Code (Week 7)**
  - Extract shared utilities to `shared/` directory
  - Break circular imports
  - Create common models
  - Document authentication flow

**Effort:** 1 week (can be done by Developer A while waiting for Task #83)

**Benefits:**
- ✅ Reduces Week 9-12 effort from 6 weeks → 4 weeks
- ✅ Identifies problems early
- ✅ Makes actual decomposition less risky
- ✅ Developer A can work on this in Week 7 (parallel with Task #83)

#### **Updated Timeline with Prep Work**

```
Week 6: Task #79 completes
Week 7: Developer A starts Task #88-Prep (while Developer C does Task #83)
Week 8: Task #83 completes, Task #88-Prep completes
Week 9-12: Task #88 (now easier due to prep work)
```

### **Implementation Steps**

1. **Create Task #91: "Core API Interface Refactoring Prep"**
   - Priority: P1
   - Effort: 1 week
   - Timeline: Week 7
   - Assigned: Developer A
   - Depends On: Task #79 (contracts)
   - Prepares: Task #88 (decomposition)

2. **Update Task #88 Description:**
   - Add "Depends On: Task #91 (prep work)"
   - Reduce effort estimate: 4-6 weeks → 4 weeks
   - Update success criteria to reference interface contracts

3. **Update 3-Month Execution Plan:**
   - Add Week 7 prep phase
   - Show parallel work: Developer C (Gateway) + Developer A (Prep)
   - Update critical path diagram

### **Code Organization for Prep Work**

```
ninaivalaigal/
├── shared/
│   ├── contracts/        # OpenAPI specs (Task #79)
│   ├── models/           # Shared Pydantic models (NEW)
│   ├── utils/            # Shared utilities (NEW)
│   ├── auth/             # Common auth logic (NEW)
│   └── database/         # DB connection utilities (NEW)
│
├── services/
│   ├── core-api/         # Future: Auth, Users, Teams, RBAC
│   │   ├── interfaces/   # Service interfaces (NEW - Week 7)
│   │   ├── routers/      # FastAPI routers
│   │   └── dependencies/ # Service-specific deps
│   │
│   ├── memory-service/   # Rust (already exists)
│   └── graphops/         # Rust (already exists)
```

### **Benefits of Early Prep**
- ✅ **Reduces Risk:** Identifies circular dependencies before decomposition
- ✅ **Reduces Burst Effort:** Spreads work across 2 weeks instead of 1 sprint
- ✅ **Parallel Work:** Developer A productive during Developer C's Gateway work
- ✅ **Better Design:** Time to think through interfaces properly
- ✅ **Easier Testing:** Can test interfaces before actual split

---

## 📊 Revised Timeline with Improvements

### **Original Timeline**
```
Week 6: Contracts done
Week 7: Developer A idle (waiting for #83)
Week 8: Gateway done
Week 9-12: Core decomp (6 weeks burst)
```

### **Improved Timeline**
```
Week 6: Contracts done → Tag with labels
Week 7: Developer A: Interface Prep (parallel with Gateway)
Week 8: Gateway done, Prep done
Week 9-12: Core decomp (4 weeks, easier due to prep)
```

**Time Saved:** 2 weeks
**Risk Reduction:** High
**Developer Utilization:** Improved (no idle time)

---

## ✅ Action Items

### **Immediate (This Week)**
- [ ] Create Taiga labels (p0-blocker, p1-high, oct-2025, etc.)
- [ ] Tag all existing tasks (#85, #79, #83, #86, #87, #88, #89, #90)
- [ ] Set up Kanban filters by priority and time

### **Week 6 (Nov 25 - Dec 1)**
- [ ] Create Task #91: Core API Interface Refactoring Prep
- [ ] Assign to Developer A
- [ ] Update Task #88 to depend on Task #91

### **Week 7 (Dec 2 - Dec 8)**
- [ ] Developer A: Execute Task #91 (prep work)
- [ ] Developer C: Execute Task #83 (Gateway)
- [ ] Both teams parallel, no idle time

---

## 📈 Expected Impact

### **Taiga Labels:**
- **Findability:** 10x easier to filter tasks
- **Planning:** Visual clarity on Kanban board
- **Scalability:** Ready for 130+ specs
- **Team Coordination:** Clear what's P0 vs P1 vs P2

### **Early Decomposition Prep:**
- **Time Savings:** 2 weeks reduction in burst effort
- **Risk Mitigation:** Identify issues early
- **Quality:** Better interface design with time to think
- **Velocity:** No idle time for Developer A

---

## 🎯 Bottom Line

**Both suggestions are excellent and should be implemented:**

1. **Taiga Labels:** Implement immediately (today)
   - Takes 30 minutes to set up
   - Massive improvement in task management
   - Essential for 130+ specs

2. **Task #88 Prep:** Add to Week 7 plan
   - Creates Task #91 (1 week prep)
   - Reduces Task #88 from 6 weeks → 4 weeks
   - Eliminates Developer A idle time in Week 7

**Total Improvement:**
- ✅ Better task tracking
- ✅ 2 weeks time saved
- ✅ Lower risk
- ✅ Better team utilization

---

**Status:** Ready to implement
**Owner:** Project Manager / Developer C
**Priority:** P1 (do this week)
