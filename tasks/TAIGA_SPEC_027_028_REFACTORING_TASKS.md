# Taiga Tasks: SPEC-027/028 Refactoring

**Date**: October 31, 2025
**Taiga URL**: http://localhost:9000/project/ninaivalaigal
**Epic**: Technical Debt Reduction
**Priority**: High

---

## Epic/User Story Structure

### Main Epic: "Eliminate SPEC-027/028 Code Duplication"

**Epic Details**:
```
Title: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Type: Epic
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 13 (2-3 days)
Sprint: Current/Next Sprint

Description:
SPEC-027 (Billing Engine) and SPEC-028 (Invoice Management) have ~250 lines
of duplicated code for PDF generation and tax calculation. This creates
maintenance burden and risk of inconsistency.

Goal: Create shared InvoicingService to eliminate duplication while preserving
distinct SPEC responsibilities.

Business Value:
- Reduce maintenance burden (1 place to update vs 2)
- Ensure invoice consistency across all touchpoints
- Enable faster feature development
- Reduce technical debt

Technical Approach:
Extract duplicate code into server/services/invoicing_service.py and have
both SPECs use the shared service.

Links:
- Refactoring Plan: docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md
- Implementation Checklist: docs/refactoring/SPEC_027_028_IMPLEMENTATION_CHECKLIST.md
- Summary: SPEC_027_028_REFACTORING_SUMMARY.md

Acceptance Criteria:
✓ invoicing_service.py created with 80%+ test coverage
✓ SPEC-027 refactored to use shared service (-100 LOC)
✓ SPEC-028 refactored to use shared service (-150 LOC)
✓ All existing tests passing
✓ PDF output identical before/after refactoring (SHA256 verified)
✓ Documentation updated in both SPECs
✓ Pre-commit hook added to prevent future duplication
✓ Production deployment successful with <0.1% error rate
```

---

## User Stories (Under Epic)

### US#237: Create Shared InvoicingService Module

**User Story Details**:
```
Title: US#237 - Create Shared InvoicingService Module
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 5 (Day 1)
Sprint: Current Sprint

Description:
As a developer, I want a single InvoicingService that handles PDF generation
and tax calculation, so that invoice logic is consistent across all SPECs.

Acceptance Criteria:
✓ server/services/invoicing_service.py created (400 lines)
✓ InvoicingService class with generate_pdf() method
✓ Dependency injection for TaxCalculator and Mailer
✓ Structured logging added (invoice_id, team_id, duration_ms)
✓ Feature flag USE_INVOICING_SERVICE implemented
✓ Unit tests written (50+ tests, 80%+ coverage)

Technical Notes:
- Use SPEC-028's create_pdf_invoice() as base (more comprehensive)
- Add optional dependency injection for easier testing
- Keep ReportLab for Phase 1 (WeasyPrint future enhancement)

Links:
- Implementation Checklist: Step 1-2 (Day 1 Morning)
- Refactoring Plan: Phase 1 section
```

**Subtasks**:
1. ☐ Create `server/services/invoicing_service.py` skeleton
2. ☐ Copy SPEC-028's PDF generation code as base
3. ☐ Add dependency injection (__init__ accepts TaxCalculator, Mailer)
4. ☐ Add structured logging to generate_pdf()
5. ☐ Add docstrings and type hints
6. ☐ Create `USE_INVOICING_SERVICE` feature flag in config
7. ☐ Write 50+ unit tests
8. ☐ Verify 80%+ test coverage

---

### US#238: Create Shared TaxCalculator Module

**User Story Details**:
```
Title: US#238 - Create Shared TaxCalculator Module
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 3 (Day 1 Afternoon)
Sprint: Current Sprint

Description:
As a developer, I want a single TaxCalculator that handles all tax logic,
so that tax calculations are consistent across billing and invoice management.

Acceptance Criteria:
✓ server/services/tax_calculator.py created (200 lines)
✓ TaxCalculator class with calculate() method
✓ @lru_cache decorator on _get_tax_rate() (>80% cache hit rate)
✓ Support for tax-inclusive and tax-exclusive models
✓ Jurisdiction lookup (US states, countries)
✓ Unit tests written (30+ tests)

Technical Notes:
- Consolidate tax logic from both SPEC-027 and SPEC-028
- Add caching to prevent repetitive DB lookups
- Support multiple tax models

Links:
- Implementation Checklist: Step 3 (Day 1 Afternoon)
- Refactoring Plan: Tax Calculation section
```

**Subtasks**:
1. ☐ Create `server/services/tax_calculator.py`
2. ☐ Consolidate tax logic from SPEC-027 and SPEC-028
3. ☐ Add @lru_cache to _get_tax_rate()
4. ☐ Support tax-inclusive and tax-exclusive calculations
5. ☐ Add jurisdiction lookup (US states)
6. ☐ Add structured logging
7. ☐ Write 30+ unit tests
8. ☐ Test cache hit rate (expect >80%)

---

### US#239: Refactor SPEC-027 to Use InvoicingService

**User Story Details**:
```
Title: US#239 - Refactor SPEC-027 (Billing Engine) to Use InvoicingService
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 2 (Day 2 Morning)
Sprint: Current Sprint
Depends on: US#237, US#238

Description:
As a developer, I want SPEC-027 to use the shared InvoicingService instead
of its own generate_invoice_pdf() function, so that invoice generation is
consistent and maintainable.

Acceptance Criteria:
✓ billing_engine_integration_api.py updated (-100 lines)
✓ generate_invoice_pdf() removed
✓ InvoicingService imported and used
✓ Feature flag check implemented
✓ All existing SPEC-027 tests passing
✓ Stripe webhook flow verified
✓ Integration tests passing

Technical Notes:
- Keep legacy code path during migration (feature flag)
- Update webhook handlers to use new service
- Verify Stripe integration still works

Links:
- Implementation Checklist: Step 4 (Day 2 Morning)
- Refactoring Plan: Phase 2 section
```

**Subtasks**:
1. ☐ Import InvoicingService in billing_engine_integration_api.py
2. ☐ Replace generate_invoice_pdf() calls with InvoicingService.generate_pdf()
3. ☐ Add feature flag check (USE_INVOICING_SERVICE)
4. ☐ Update webhook handlers
5. ☐ Run SPEC-027 integration tests
6. ☐ Verify Stripe webhook flow
7. ☐ Test subscription → invoice → PDF flow

---

### US#240: Refactor SPEC-028 to Use InvoicingService

**User Story Details**:
```
Title: US#240 - Refactor SPEC-028 (Invoice Management) to Use InvoicingService
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 2 (Day 2 Afternoon)
Sprint: Current Sprint
Depends on: US#237, US#238

Description:
As a developer, I want SPEC-028 to use the shared InvoicingService instead
of its own create_pdf_invoice() function, so that customer portal invoices
are consistent with billing invoices.

Acceptance Criteria:
✓ invoice_management_api.py updated (-150 lines)
✓ create_pdf_invoice() removed
✓ InvoicingService imported and used
✓ Feature flag check implemented
✓ All existing SPEC-028 tests passing
✓ Customer portal displays correctly
✓ Accounting exports working

Technical Notes:
- Keep legacy code path during migration (feature flag)
- Update customer portal endpoints
- Verify accounting CSV/Excel exports

Links:
- Implementation Checklist: Step 5 (Day 2 Afternoon)
- Refactoring Plan: Phase 3 section
```

**Subtasks**:
1. ☐ Import InvoicingService in invoice_management_api.py
2. ☐ Replace create_pdf_invoice() calls with InvoicingService.generate_pdf()
3. ☐ Add feature flag check (USE_INVOICING_SERVICE)
4. ☐ Update customer portal endpoints
5. ☐ Run SPEC-028 integration tests
6. ☐ Verify customer portal display
7. ☐ Test accounting exports (CSV, Excel)

---

### US#241: Parallel Run - PDF Comparison Validation

**User Story Details**:
```
Title: US#241 - Parallel Run PDF Comparison (Old vs New)
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 1 (Day 2 Evening)
Sprint: Current Sprint
Depends on: US#239, US#240

Description:
As a QA engineer, I want to compare PDFs generated by the old and new services
to ensure they are byte-identical, so that we can confidently deploy without
visual regressions.

Acceptance Criteria:
✓ Generate 100 invoices with both old and new service
✓ Compare SHA256 hashes of PDFs
✓ Log any differences for investigation
✓ 100% match rate achieved
✓ Script documented for future use

Technical Notes:
- Create scripts/compare_invoice_pdfs.py
- Use staging environment
- Compare byte hashes, not visual appearance

Links:
- Implementation Checklist: Step 6 (Day 2 Evening)
- Refactoring Plan: Migration Strategy section
```

**Subtasks**:
1. ☐ Create `scripts/compare_invoice_pdfs.py`
2. ☐ Generate 100 sample invoices on staging
3. ☐ Run both old and new PDF generation
4. ☐ Compare SHA256 hashes
5. ☐ Log any mismatches
6. ☐ Investigate and fix any differences
7. ☐ Document comparison process

---

### US#242: Complete Test Suite and Documentation

**User Story Details**:
```
Title: US#242 - Complete Test Suite (80%+ Coverage) and Documentation
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 3 (Day 3 Morning)
Sprint: Current Sprint
Depends on: US#237, US#238, US#239, US#240

Description:
As a developer, I want comprehensive tests and documentation for the
InvoicingService, so that future developers can maintain and extend it
confidently.

Acceptance Criteria:
✓ test_invoicing_service.py with 50+ unit tests
✓ test_tax_calculator.py with 30+ unit tests
✓ test_invoice_integration.py with 10+ integration tests
✓ Snapshot tests for PDF byte equality
✓ 80%+ test coverage for invoicing_service.py
✓ API documentation complete
✓ SPEC-027 and SPEC-028 updated with delegation notes

Technical Notes:
- Use pytest-snapshot for PDF regression tests
- Add structured logging validation tests
- Document all public methods

Links:
- Implementation Checklist: Step 7 (Day 3 Morning)
- Refactoring Plan: Testing Strategy section
```

**Subtasks**:
1. ☐ Write `tests/services/test_invoicing_service.py` (50+ tests)
2. ☐ Write `tests/services/test_tax_calculator.py` (30+ tests)
3. ☐ Write `tests/integration/test_invoice_flow.py` (10+ tests)
4. ☐ Add snapshot tests for PDF byte equality
5. ☐ Run pytest-cov and verify 80%+ coverage
6. ☐ Create API documentation for InvoicingService
7. ☐ Update SPEC-027 spec.md with delegation note
8. ☐ Update SPEC-028 spec.md with delegation note
9. ☐ Update architecture diagrams

---

### US#243: Remove Legacy Code and Deploy to Production

**User Story Details**:
```
Title: US#243 - Remove Legacy Code and Deploy to Production
Type: User Story
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Assigned to: [Developer TBD]
Estimated Points: 2 (Day 3 Afternoon)
Sprint: Current Sprint
Depends on: US#241, US#242

Description:
As a developer, I want to remove the legacy PDF generation code and deploy
the refactored service to production, so that we eliminate technical debt
and maintain a clean codebase.

Acceptance Criteria:
✓ USE_INVOICING_SERVICE=true in production
✓ Monitor for 24 hours (error rate <0.1%)
✓ generate_invoice_pdf_legacy() removed from SPEC-027
✓ create_pdf_invoice() removed from SPEC-028
✓ Feature flag code removed
✓ Coverage report pushed to dashboard
✓ CHANGELOG.md updated
✓ Deployment successful

Technical Notes:
- Gradual rollout: 10% → 50% → 100%
- Monitor error rates and performance
- Rollback plan ready if needed

Links:
- Implementation Checklist: Step 8 (Day 3 Afternoon)
- Refactoring Plan: Phase 4 section
```

**Subtasks**:
1. ☐ Enable USE_INVOICING_SERVICE=true on staging (10% traffic)
2. ☐ Monitor for errors (expect 0)
3. ☐ Increase to 50% of traffic
4. ☐ Monitor performance metrics
5. ☐ Enable for 100% of production traffic
6. ☐ Monitor for 24 hours
7. ☐ Remove generate_invoice_pdf_legacy() from SPEC-027
8. ☐ Remove create_pdf_invoice() from SPEC-028
9. ☐ Remove feature flag code
10. ☐ Push coverage report to dashboard
11. ☐ Update CHANGELOG.md

---

## Technical Tasks (Additional)

### Task#244: Add Pre-commit Hook for Duplication Prevention

**Task Details**:
```
Title: Task#244 - Add Pre-commit Hook to Prevent Invoice PDF Duplication
Type: Task
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: Medium
Assigned to: [Developer TBD]
Estimated Points: 1
Sprint: Current Sprint

Description:
Add a pre-commit hook that prevents developers from creating duplicate
generate_invoice_pdf functions outside of invoicing_service.py.

Acceptance Criteria:
✓ .pre-commit-config.yaml updated
✓ Hook triggers on duplicate generate_invoice_pdf functions
✓ Hook tested and verified
✓ CONTRIBUTING.md documentation updated

Technical Notes:
- Use grep to search for duplicate function definitions
- Exclude test files from check
- Provide helpful error message

Links:
- Implementation Checklist: Refinement #10
```

**Subtasks**:
1. ☐ Update .pre-commit-config.yaml with hook
2. ☐ Test hook triggers on duplicate code
3. ☐ Verify hook doesn't false-positive on tests
4. ☐ Document in CONTRIBUTING.md
5. ☐ Commit and push

---

### Task#245: Create Branding Settings Database Table

**Task Details**:
```
Title: Task#245 - Create Branding Settings Database Table
Type: Task
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: Low (Future Enhancement)
Assigned to: [Developer TBD]
Estimated Points: 2
Sprint: Backlog

Description:
Move BrandingConfig from code to database table to allow admin-panel updates
without code changes.

Acceptance Criteria:
✓ database/schemas/branding_settings.sql created
✓ Alembic migration generated
✓ CRUD endpoints in admin API
✓ InvoicingService loads branding from database
✓ Tests updated

Technical Notes:
- This is a future enhancement (not blocking refactoring)
- Enables customer self-service branding
- Could be part of SPEC-028 Phase 2

Links:
- Implementation Checklist: Refinement #3
```

**Subtasks**:
1. ☐ Create database/schemas/branding_settings.sql
2. ☐ Generate Alembic migration
3. ☐ Add CRUD endpoints to admin API
4. ☐ Update InvoicingService to load from DB
5. ☐ Write tests
6. ☐ Update documentation

---

### Task#246: Evaluate WeasyPrint for HTML→PDF (Future)

**Task Details**:
```
Title: Task#246 - Evaluate WeasyPrint for HTML→PDF Invoice Generation
Type: Task
Epic: Eliminate SPEC-027/028 Invoice Duplication
Status: Backlog
Priority: Low (Future Enhancement)
Assigned to: [Developer TBD]
Estimated Points: 5
Sprint: Backlog

Description:
Evaluate replacing ReportLab with WeasyPrint (HTML/CSS → PDF) for easier
invoice styling and localization.

Acceptance Criteria:
✓ WeasyPrint proof-of-concept created
✓ invoice.html Jinja2 template created
✓ Performance comparison (WeasyPrint vs ReportLab)
✓ Recommendation document created
✓ Decision made (keep ReportLab or switch)

Technical Notes:
- This is Phase 2 (after current refactoring)
- HTML→PDF separates content from presentation
- Easier to style with CSS
- May be slower than ReportLab

Links:
- Implementation Checklist: Refinement #4
```

**Subtasks**:
1. ☐ Install WeasyPrint and test basic PDF generation
2. ☐ Create invoice.html Jinja2 template
3. ☐ Create invoice.css stylesheet
4. ☐ Generate sample invoices with WeasyPrint
5. ☐ Compare performance (ReportLab vs WeasyPrint)
6. ☐ Compare file sizes
7. ☐ Write recommendation document
8. ☐ Team decision

---

## Milestones

### Milestone 1: Foundation Complete (End of Day 1)
- ✓ US#237 Complete (InvoicingService created)
- ✓ US#238 Complete (TaxCalculator created)
- ✓ 80+ unit tests written
- ✓ Feature flag implemented

### Milestone 2: Integration Complete (End of Day 2)
- ✓ US#239 Complete (SPEC-027 refactored)
- ✓ US#240 Complete (SPEC-028 refactored)
- ✓ US#241 Complete (PDF comparison validated)
- ✓ Both SPECs using shared service

### Milestone 3: Production Deployment (End of Day 3)
- ✓ US#242 Complete (Tests and docs complete)
- ✓ US#243 Complete (Legacy code removed, deployed)
- ✓ 80%+ test coverage achieved
- ✓ Production running on new service

---

## Sprint Planning

### Recommended Sprint Assignment

**Sprint**: Current Sprint (Week of Nov 4-8, 2025)

**Sprint Goal**: Eliminate SPEC-027/028 code duplication and improve invoice consistency

**Sprint Capacity**: 13 story points (2-3 days focused work)

**Sprint Backlog**:
- Epic: Eliminate SPEC-027/028 Invoice Duplication (13 points)
  - US#237: Create InvoicingService (5 points)
  - US#238: Create TaxCalculator (3 points)
  - US#239: Refactor SPEC-027 (2 points)
  - US#240: Refactor SPEC-028 (2 points)
  - US#241: PDF Comparison (1 point)
  - US#242: Tests & Docs (3 points)
  - US#243: Remove Legacy & Deploy (2 points)
  - Task#244: Pre-commit Hook (1 point)

**Future Sprints** (Backlog):
- Task#245: Branding DB Table (2 points)
- Task#246: WeasyPrint Evaluation (5 points)

---

## Taiga Board Setup

### Kanban Columns

```
New → Ready → In Progress → In Review → Done
```

**Initial Status for All Tasks**: Ready

**Flow**:
1. Developer starts US#237 → moves to "In Progress"
2. Completes implementation → moves to "In Review"
3. Code review approved → moves to "Done"
4. Repeat for US#238, US#239, etc.

---

## Labels/Tags to Add

- `technical-debt`
- `refactoring`
- `spec-027`
- `spec-028`
- `invoicing`
- `pdf-generation`
- `tax-calculation`
- `high-priority`

---

## How to Create in Taiga

### Step 1: Create Epic

1. Go to http://localhost:9000/project/ninaivalaigal
2. Login: admin / admin123
3. Click "Epics" in left sidebar
4. Click "+ New Epic"
5. Copy epic details from above
6. Save

### Step 2: Create User Stories

1. Click "Backlog" in left sidebar
2. Click "+ New User Story"
3. For each US (US#237 through US#243):
   - Copy title and description
   - Link to epic
   - Set status to "Ready"
   - Set priority to "High"
   - Add story points
   - Add labels/tags
   - Save

### Step 3: Add Subtasks to User Stories

1. Open each user story
2. Click "Tasks" tab
3. Click "+ Add Task"
4. Copy subtasks from checklist above
5. Save

### Step 4: Create Technical Tasks

1. Click "Backlog" in left sidebar
2. Click "+ New Task"
3. For each Task (Task#244 through Task#246):
   - Copy title and description
   - Link to epic
   - Set status
   - Set priority
   - Add task points
   - Save

---

## Daily Standup Updates

### Day 1 (Foundation)
```
Yesterday: Epic created, US#237-238 started
Today: Complete InvoicingService and TaxCalculator
Blockers: None
```

### Day 2 (Integration)
```
Yesterday: Completed foundation (US#237-238)
Today: Refactor SPEC-027 and SPEC-028 (US#239-241)
Blockers: None
```

### Day 3 (Validation & Deploy)
```
Yesterday: Completed integration (US#239-241)
Today: Complete tests, deploy to production (US#242-243)
Blockers: None
```

---

## Success Dashboard

Track these metrics in Taiga custom fields:

| Metric | Target | Current |
|--------|--------|---------|
| Story Points Completed | 13 | 0 |
| Test Coverage | 80% | 0% |
| LOC Removed | -250 | 0 |
| PDF Match Rate | 100% | - |
| Production Error Rate | <0.1% | - |

---

## Next Steps

1. **Create Epic in Taiga** (5 minutes)
   - Use details above
   - Link to documentation

2. **Create User Stories** (20 minutes)
   - US#237 through US#243
   - Add subtasks to each

3. **Create Technical Tasks** (10 minutes)
   - Task#244 through Task#246

4. **Assign Developer** (When ready)
   - Assign to developer who will implement
   - Schedule 2-3 day focused block

5. **Start Sprint** (When team is ready)
   - Move to current sprint
   - Begin implementation

---

**Total Taiga Setup Time**: ~35 minutes
**Total Implementation Time**: 2-3 days
**Business Value**: Eliminate 250 lines of technical debt, ensure invoice consistency
