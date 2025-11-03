# ✅ SPEC-027/028 Refactoring Tasks Created in Taiga

**Date**: October 31, 2025, 12:20 PM UTC-05:00
**Method**: Python API Script + Taiga API
**Status**: ✅ **COMPLETE**

---

## Summary

Successfully created **1 Epic + 7 User Stories + 57 Subtasks** in Taiga for the SPEC-027/028 refactoring effort.

---

## What Was Created

### 1 Epic

**Epic #190**: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
- **ID**: 9
- **Ref**: #190
- **Tags**: technical-debt, refactoring, spec-027, spec-028, invoicing
- **Status**: Ready
- **Description**: Complete epic description with business value, acceptance criteria, and links to documentation

### 7 User Stories (18 Story Points Total)

| # | Title | Ref | Points | Tags | Subtasks |
|---|-------|-----|--------|------|----------|
| 1 | US#237 - Create Shared InvoicingService Module | #191 | 5 | invoicing, pdf-generation, high-priority | 8 |
| 2 | US#238 - Create Shared TaxCalculator Module | #200 | 3 | tax-calculation, invoicing, high-priority | 8 |
| 3 | US#239 - Refactor SPEC-027 to Use InvoicingService | #209 | 2 | spec-027, billing-engine, refactoring, high-priority | 7 |
| 4 | US#240 - Refactor SPEC-028 to Use InvoicingService | #217 | 2 | spec-028, invoice-management, refactoring, high-priority | 7 |
| 5 | US#241 - Parallel Run PDF Comparison | #225 | 1 | testing, validation, pdf-generation, high-priority | 7 |
| 6 | US#242 - Complete Test Suite and Documentation | #233 | 3 | testing, documentation, coverage, high-priority | 9 |
| 7 | US#243 - Remove Legacy Code and Deploy to Production | #243 | 2 | deployment, production, cleanup, high-priority | 11 |

**Total**: 18 story points, 57 subtasks

---

## Taiga Links

### View All Tasks

```
Backlog: http://localhost:9000/project/ninaivalaigal/backlog
Epic: http://localhost:9000/project/ninaivalaigal/epic/190
```

### Individual User Stories

```
#191 US#237: http://localhost:9000/project/ninaivalaigal/us/191
#200 US#238: http://localhost:9000/project/ninaivalaigal/us/200
#209 US#239: http://localhost:9000/project/ninaivalaigal/us/209
#217 US#240: http://localhost:9000/project/ninaivalaigal/us/217
#225 US#241: http://localhost:9000/project/ninaivalaigal/us/225
#233 US#242: http://localhost:9000/project/ninaivalaigal/us/233
#243 US#243: http://localhost:9000/project/ninaivalaigal/us/243
```

---

## Verification

### Backlog Count

- **Before**: 166 user stories
- **After**: 173 user stories
- **Added**: 7 user stories ✅

### Story Points

- **Project Total**: 100 points
- **Defined Points**: 3 points
- **This Epic**: 18 points (not yet added to sprint)

---

## Each User Story Includes

✅ **Title**: Clear, actionable (US#237-243 naming)
✅ **Description**: User story format with acceptance criteria
✅ **Tags**: Proper categorization (technical-debt, spec-027, invoicing, etc.)
✅ **Status**: New (ready for sprint assignment)
✅ **Points**: Story point estimation
✅ **Epic Link**: Linked to main epic
✅ **Subtasks**: Step-by-step implementation tasks

---

## Example: US#237 (InvoicingService)

```
Title: US#237 - Create Shared InvoicingService Module
Ref: #191
Status: New
Points: 5
Epic: #190 (Technical Debt: Eliminate SPEC-027/028 Invoice Duplication)

Tags:
- invoicing
- pdf-generation
- high-priority

Description:
As a developer, I want a single InvoicingService that handles PDF
generation and tax calculation, so that invoice logic is consistent
across all SPECs.

Acceptance Criteria:
☐ server/services/invoicing_service.py created (400 lines)
☐ InvoicingService class with generate_pdf() method
☐ Dependency injection for TaxCalculator and Mailer
☐ Structured logging (invoice_id, team_id, duration_ms)
☐ Feature flag USE_INVOICING_SERVICE implemented
☐ Unit tests written (50+ tests, 80%+ coverage)

Subtasks (8):
1. Create server/services/invoicing_service.py skeleton
2. Copy SPEC-028's PDF generation code
3. Add dependency injection
4. Add structured logging
5. Add docstrings and type hints
6. Create USE_INVOICING_SERVICE feature flag
7. Write 50+ unit tests
8. Verify 80%+ coverage
```

---

## Python Script Created

**File**: `scripts/create_taiga_refactoring_tasks.py`

**Features**:
- Authenticates with Taiga API
- Creates Epic with full description
- Creates 7 User Stories with proper fields
- Adds 57 subtasks across all stories
- Handles Taiga API requirements (status, points format)
- Provides summary with links

**Usage**:
```bash
python3 scripts/create_taiga_refactoring_tasks.py
```

---

## Next Steps

### Immediate (Now)

1. **Review in Taiga**:
   ```
   http://localhost:9000/project/ninaivalaigal/backlog
   ```
   - Verify all 7 stories are present
   - Check epic linking
   - Review tags and descriptions

2. **Assign to Sprint** (Optional):
   - Drag stories into current sprint
   - Set sprint goal: "Eliminate SPEC-027/028 code duplication"
   - Total: 18 points (fits in one 2-3 day sprint)

3. **Assign Developer**:
   - Assign epic to developer
   - Schedule 2-3 day focused implementation block

### During Sprint

4. **Move Through Kanban**:
   ```
   New → Ready → In Progress → In Review → Done
   ```

5. **Daily Updates**:
   - Move tasks as they progress
   - Update story points if needed
   - Add comments on blockers

6. **Track Progress**:
   - Burndown chart shows daily progress
   - 18 points should burn down over 2-3 days

---

## Tags Created

All stories tagged with appropriate labels:

- `technical-debt` - Epic-level categorization
- `refactoring` - Code improvement focus
- `spec-027` - SPEC-027 specific work
- `spec-028` - SPEC-028 specific work
- `invoicing` - Invoice-related functionality
- `pdf-generation` - PDF generation work
- `tax-calculation` - Tax calculation logic
- `high-priority` - Priority marking
- `testing` - Test-related work
- `documentation` - Documentation updates
- `coverage` - Test coverage work
- `deployment` - Deployment tasks
- `production` - Production deployment
- `cleanup` - Code cleanup tasks
- `validation` - Validation and comparison
- `billing-engine` - Billing engine work
- `invoice-management` - Invoice management work

---

## Implementation Sequence

Tasks are numbered to follow the implementation plan:

### Day 1: Foundation (8 points)
- ✅ US#237: Create InvoicingService (5 points)
- ✅ US#238: Create TaxCalculator (3 points)

### Day 2: Integration (5 points)
- ✅ US#239: Refactor SPEC-027 (2 points)
- ✅ US#240: Refactor SPEC-028 (2 points)
- ✅ US#241: PDF Comparison (1 point)

### Day 3: Completion (5 points)
- ✅ US#242: Tests & Docs (3 points)
- ✅ US#243: Deploy to Production (2 points)

---

## Success Metrics

### Taiga Metrics

- ✅ Epic created with complete description
- ✅ 7 user stories created with proper fields
- ✅ 57 subtasks distributed across stories
- ✅ All stories linked to epic
- ✅ All stories tagged appropriately
- ✅ All stories have acceptance criteria

### Code Metrics (To Track During Implementation)

- **LOC Reduction**: -250 lines target
- **Test Coverage**: 80%+ target
- **Performance**: <500ms PDF generation (p95)
- **Consistency**: 100% PDF byte match
- **Error Rate**: <0.1% in production

---

## Verification Screenshot

See: `taiga_refactoring_tasks_created.png`

Shows:
- Search filtered by "US#237"
- 4 of 7 stories visible in results
- All stories have "New" status
- All stories properly tagged
- Story points visible

---

## Documentation References

All tasks reference these documents:

1. **Refactoring Plan**: `docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md`
2. **Implementation Checklist**: `docs/refactoring/SPEC_027_028_IMPLEMENTATION_CHECKLIST.md`
3. **Summary**: `SPEC_027_028_REFACTORING_SUMMARY.md`
4. **Taiga Tasks Guide**: `tasks/TAIGA_SPEC_027_028_REFACTORING_TASKS.md`
5. **Quick Setup**: `TAIGA_QUICK_SETUP_SPEC_027_028.md`

---

## API Script Details

### Authentication
```python
✅ Authenticated with Taiga at http://localhost:9000/api/v1
✅ Project ID: 1 (ninaivalaigal)
```

### Epic Creation
```python
✅ Epic created: ID 9, Ref #190
✅ Subject: "Technical Debt: Eliminate SPEC-027/028 Invoice Duplication"
✅ Tags: technical-debt, refactoring, spec-027, spec-028, invoicing
```

### User Story Creation
```python
✅ Story 1: US#237 → ID 184, Ref #191 (5 points, 8 tasks)
✅ Story 2: US#238 → ID 185, Ref #200 (3 points, 8 tasks)
✅ Story 3: US#239 → ID 186, Ref #209 (2 points, 7 tasks)
✅ Story 4: US#240 → ID 187, Ref #217 (2 points, 7 tasks)
✅ Story 5: US#241 → ID 188, Ref #225 (1 point, 7 tasks)
✅ Story 6: US#242 → ID 189, Ref #233 (3 points, 9 tasks)
✅ Story 7: US#243 → ID 190, Ref #243 (2 points, 11 tasks)
```

---

## Conclusion

✅ **All tasks successfully created in Taiga!**

**Total Time**: ~5 minutes (automated via Python script)
**Manual Equivalent**: ~35 minutes (if done by hand)
**Time Saved**: 30 minutes

**Ready For**:
- Sprint assignment
- Developer assignment
- Implementation (2-3 days)

---

**Created**: October 31, 2025, 12:20 PM
**Method**: Python API automation
**Status**: Complete and verified
**Next**: Assign to sprint and developer
