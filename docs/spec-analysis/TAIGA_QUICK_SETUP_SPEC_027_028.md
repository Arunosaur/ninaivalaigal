# Quick Taiga Setup Guide: SPEC-027/028 Refactoring

**Estimated Setup Time**: 35 minutes
**Taiga URL**: http://localhost:9000/project/ninaivalaigal
**Login**: admin / admin123

---

## Task Summary

### 1 Epic
**Eliminate SPEC-027/028 Invoice Duplication** (13 story points)

### 7 User Stories
- US#237: Create InvoicingService (5 pts)
- US#238: Create TaxCalculator (3 pts)
- US#239: Refactor SPEC-027 (2 pts)
- US#240: Refactor SPEC-028 (2 pts)
- US#241: PDF Comparison (1 pt)
- US#242: Tests & Docs (3 pts)
- US#243: Remove Legacy & Deploy (2 pts)

### 3 Technical Tasks (Backlog)
- Task#244: Pre-commit Hook (1 pt)
- Task#245: Branding DB Table (2 pts) - Future
- Task#246: WeasyPrint Evaluation (5 pts) - Future

---

## Quick Copy-Paste Templates

### Epic (Create First)

```
Title: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication

Type: Epic
Status: Ready
Priority: High
Story Points: 13

Description:
SPEC-027 (Billing Engine) and SPEC-028 (Invoice Management) have ~250 lines of duplicated code for PDF generation and tax calculation. This creates maintenance burden and risk of inconsistency.

Goal: Create shared InvoicingService to eliminate duplication while preserving distinct SPEC responsibilities.

Business Value:
• Reduce maintenance burden (1 place to update vs 2)
• Ensure invoice consistency across all touchpoints
• Enable faster feature development
• Reduce technical debt

Acceptance Criteria:
☐ invoicing_service.py created with 80%+ test coverage
☐ SPEC-027 refactored to use shared service (-100 LOC)
☐ SPEC-028 refactored to use shared service (-150 LOC)
☐ All existing tests passing
☐ PDF output identical before/after (SHA256 verified)
☐ Documentation updated in both SPECs
☐ Pre-commit hook added
☐ Production deployment successful

Links:
• docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md
• docs/refactoring/SPEC_027_028_IMPLEMENTATION_CHECKLIST.md
• SPEC_027_028_REFACTORING_SUMMARY.md

Tags: technical-debt, refactoring, spec-027, spec-028, invoicing
```

---

### US#237: Create InvoicingService

```
Title: US#237 - Create Shared InvoicingService Module

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 5

Description:
As a developer, I want a single InvoicingService that handles PDF generation and tax calculation, so that invoice logic is consistent across all SPECs.

Acceptance Criteria:
☐ server/services/invoicing_service.py created (400 lines)
☐ InvoicingService class with generate_pdf() method
☐ Dependency injection for TaxCalculator and Mailer
☐ Structured logging (invoice_id, team_id, duration_ms)
☐ Feature flag USE_INVOICING_SERVICE implemented
☐ Unit tests written (50+ tests, 80%+ coverage)

Technical Notes:
Use SPEC-028's create_pdf_invoice() as base (more comprehensive)

Subtasks:
1. Create server/services/invoicing_service.py skeleton
2. Copy SPEC-028's PDF generation code
3. Add dependency injection
4. Add structured logging
5. Add docstrings and type hints
6. Create USE_INVOICING_SERVICE feature flag
7. Write 50+ unit tests
8. Verify 80%+ coverage

Tags: invoicing, pdf-generation, high-priority
```

---

### US#238: Create TaxCalculator

```
Title: US#238 - Create Shared TaxCalculator Module

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 3

Description:
As a developer, I want a single TaxCalculator that handles all tax logic, so that tax calculations are consistent across billing and invoice management.

Acceptance Criteria:
☐ server/services/tax_calculator.py created (200 lines)
☐ TaxCalculator class with calculate() method
☐ @lru_cache on _get_tax_rate() (>80% cache hit rate)
☐ Support tax-inclusive and tax-exclusive models
☐ Jurisdiction lookup (US states, countries)
☐ Unit tests written (30+ tests)

Subtasks:
1. Create server/services/tax_calculator.py
2. Consolidate tax logic from SPEC-027 and SPEC-028
3. Add @lru_cache to _get_tax_rate()
4. Support tax-inclusive/exclusive calculations
5. Add jurisdiction lookup
6. Add structured logging
7. Write 30+ unit tests
8. Test cache hit rate (>80%)

Tags: tax-calculation, invoicing, high-priority
```

---

### US#239: Refactor SPEC-027

```
Title: US#239 - Refactor SPEC-027 to Use InvoicingService

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 2
Depends on: US#237, US#238

Description:
As a developer, I want SPEC-027 to use the shared InvoicingService instead of its own generate_invoice_pdf() function.

Acceptance Criteria:
☐ billing_engine_integration_api.py updated (-100 lines)
☐ generate_invoice_pdf() removed
☐ InvoicingService imported and used
☐ Feature flag check implemented
☐ All SPEC-027 tests passing
☐ Stripe webhook flow verified

Subtasks:
1. Import InvoicingService
2. Replace generate_invoice_pdf() calls
3. Add feature flag check
4. Update webhook handlers
5. Run integration tests
6. Verify Stripe flow
7. Test subscription → invoice → PDF

Tags: spec-027, billing-engine, refactoring
```

---

### US#240: Refactor SPEC-028

```
Title: US#240 - Refactor SPEC-028 to Use InvoicingService

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 2
Depends on: US#237, US#238

Description:
As a developer, I want SPEC-028 to use the shared InvoicingService so that customer portal invoices are consistent with billing invoices.

Acceptance Criteria:
☐ invoice_management_api.py updated (-150 lines)
☐ create_pdf_invoice() removed
☐ InvoicingService imported and used
☐ Feature flag check implemented
☐ All SPEC-028 tests passing
☐ Customer portal displays correctly
☐ Accounting exports working

Subtasks:
1. Import InvoicingService
2. Replace create_pdf_invoice() calls
3. Add feature flag check
4. Update customer portal endpoints
5. Run integration tests
6. Verify portal display
7. Test accounting exports

Tags: spec-028, invoice-management, refactoring
```

---

### US#241: PDF Comparison

```
Title: US#241 - Parallel Run PDF Comparison

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 1
Depends on: US#239, US#240

Description:
As a QA engineer, I want to compare PDFs generated by old and new services to ensure byte-identical output.

Acceptance Criteria:
☐ Generate 100 invoices with both services
☐ Compare SHA256 hashes
☐ Log any differences
☐ 100% match rate achieved
☐ Script documented

Subtasks:
1. Create scripts/compare_invoice_pdfs.py
2. Generate 100 sample invoices on staging
3. Run both old and new PDF generation
4. Compare SHA256 hashes
5. Log any mismatches
6. Investigate and fix differences
7. Document comparison process

Tags: testing, validation, pdf-generation
```

---

### US#242: Tests & Documentation

```
Title: US#242 - Complete Test Suite and Documentation

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 3
Depends on: US#237, US#238, US#239, US#240

Description:
As a developer, I want comprehensive tests and documentation for InvoicingService.

Acceptance Criteria:
☐ test_invoicing_service.py with 50+ unit tests
☐ test_tax_calculator.py with 30+ unit tests
☐ test_invoice_integration.py with 10+ tests
☐ Snapshot tests for PDF byte equality
☐ 80%+ test coverage
☐ API documentation complete
☐ SPEC-027 and SPEC-028 updated with delegation notes

Subtasks:
1. Write test_invoicing_service.py (50+ tests)
2. Write test_tax_calculator.py (30+ tests)
3. Write test_invoice_integration.py (10+ tests)
4. Add snapshot tests
5. Run pytest-cov (verify 80%+)
6. Create API documentation
7. Update SPEC-027 spec.md
8. Update SPEC-028 spec.md
9. Update architecture diagrams

Tags: testing, documentation, coverage
```

---

### US#243: Remove Legacy & Deploy

```
Title: US#243 - Remove Legacy Code and Deploy to Production

Type: User Story
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: High
Story Points: 2
Depends on: US#241, US#242

Description:
As a developer, I want to remove legacy PDF generation code and deploy the refactored service to production.

Acceptance Criteria:
☐ USE_INVOICING_SERVICE=true in production
☐ Monitor for 24 hours (error rate <0.1%)
☐ generate_invoice_pdf_legacy() removed from SPEC-027
☐ create_pdf_invoice() removed from SPEC-028
☐ Feature flag code removed
☐ Coverage report pushed
☐ CHANGELOG.md updated
☐ Deployment successful

Subtasks:
1. Enable flag on staging (10% traffic)
2. Monitor for errors
3. Increase to 50% traffic
4. Monitor performance
5. Enable 100% production traffic
6. Monitor for 24 hours
7. Remove legacy code from SPEC-027
8. Remove legacy code from SPEC-028
9. Remove feature flag code
10. Push coverage report
11. Update CHANGELOG.md

Tags: deployment, production, cleanup
```

---

### Task#244: Pre-commit Hook

```
Title: Task#244 - Add Pre-commit Hook for Duplication Prevention

Type: Task
Epic: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
Status: Ready
Priority: Medium
Task Points: 1

Description:
Add pre-commit hook that prevents duplicate generate_invoice_pdf functions outside invoicing_service.py.

Acceptance Criteria:
☐ .pre-commit-config.yaml updated
☐ Hook triggers on duplicate functions
☐ Hook tested and verified
☐ CONTRIBUTING.md updated

Subtasks:
1. Update .pre-commit-config.yaml
2. Test hook triggers
3. Verify no false positives
4. Document in CONTRIBUTING.md
5. Commit and push

Tags: ci-cd, pre-commit, prevention
```

---

## Labels to Create in Taiga

```
• technical-debt (color: orange)
• refactoring (color: blue)
• spec-027 (color: purple)
• spec-028 (color: purple)
• invoicing (color: green)
• pdf-generation (color: green)
• tax-calculation (color: green)
• high-priority (color: red)
• testing (color: cyan)
• documentation (color: gray)
```

---

## Taiga UI Steps

### Create Epic

1. Navigate to http://localhost:9000/project/ninaivalaigal
2. Click "Epics" in left sidebar
3. Click "+ New Epic" button
4. **Title**: Technical Debt: Eliminate SPEC-027/028 Invoice Duplication
5. **Description**: Copy from template above
6. **Status**: Ready
7. **Assigned to**: [Leave blank or assign]
8. Add tags: technical-debt, refactoring, spec-027, spec-028, invoicing
9. Click "Save"

### Create User Stories

1. Click "Backlog" in left sidebar
2. Click "+ New User Story" button
3. For **each user story** (US#237-243):
   - Copy title from template
   - Copy description from template
   - **Link to epic**: Select epic from dropdown
   - **Status**: Ready
   - **Priority**: High
   - **Story Points**: (see template)
   - **Tags**: (see template)
   - Click "Save"
   - After save, click "Tasks" tab
   - Add each subtask from template
   - Click "Save"

### Create Technical Tasks

1. Click "Issues" or "Tasks" in left sidebar
2. Click "+ New Task"
3. For **each task** (Task#244-246):
   - Copy title and description
   - Link to epic
   - Set status and priority
   - Add tags
   - Click "Save"

---

## Sprint Assignment

**Recommended Sprint**: Current Sprint

**Sprint Goal**: Eliminate SPEC-027/028 code duplication

**Story Points**: 13 (fits in one sprint with focused work)

**Tasks to Add**:
1. Drag all 7 user stories (US#237-243) into current sprint
2. Drag Task#244 into current sprint
3. Leave Task#245 and Task#246 in backlog (future work)

---

## Tracking Progress

### Kanban Board View

```
Ready → In Progress → In Review → Done

Day 1:
  US#237 [In Progress]
  US#238 [Ready]

Day 2:
  US#237 [Done]
  US#238 [Done]
  US#239 [In Progress]
  US#240 [Ready]

Day 3:
  US#239 [Done]
  US#240 [Done]
  US#241 [Done]
  US#242 [In Progress]
  US#243 [Ready]
```

---

## Burndown Chart

**Initial Story Points**: 13
**Daily Target**:
- End of Day 1: 5 points completed (8 remaining)
- End of Day 2: 10 points completed (3 remaining)
- End of Day 3: 13 points completed (0 remaining)

---

## Quick Command Summary

```bash
# Full documentation
cat tasks/TAIGA_SPEC_027_028_REFACTORING_TASKS.md

# Implementation checklist
cat docs/refactoring/SPEC_027_028_IMPLEMENTATION_CHECKLIST.md

# Refactoring plan
cat docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md

# Summary
cat SPEC_027_028_REFACTORING_SUMMARY.md

# Open Taiga
open http://localhost:9000/project/ninaivalaigal
```

---

**Estimated Setup**: 35 minutes
**Implementation**: 2-3 days
**Business Value**: Eliminate 250 lines of technical debt
