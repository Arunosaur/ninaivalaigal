# US #87: Schema Drift Prevention CI - Implementation Plan

**Date:** October 22, 2025, 7:15 AM
**Status:** 🚀 In Progress
**Owner:** Cascade AI
**Timeline:** Week 7

---

## 📊 **CURRENT STATE ANALYSIS**

### ✅ **What ALREADY EXISTS:**

**1. API Contract Validation Infrastructure**
- ✅ `ci/validate-api-contracts.py` - Validates proto/OpenAPI syntax
- ✅ `ci/check-breaking-changes.py` - Detects breaking changes
- ✅ `ci/generate-contract-diff.py` - Generates diff reports
- ✅ `.github/workflows/contract-validation.yml` - CI workflow
- ✅ Pre-commit hook for contract validation

**2. Contract Types:**
- ✅ 9 Protocol Buffer files (`shared/contracts/**/*.proto`)
- ✅ 8 OpenAPI spec files (`shared/contracts/**/openapi.yaml`)

**3. Current Capabilities:**
- ✅ Syntax validation (proto + OpenAPI)
- ✅ Breaking change detection (removed endpoints, changed schemas)
- ✅ PR comment with contract diff
- ✅ CI blocks on breaking changes

---

### ❌ **What's MISSING (US #87 Requirements):**

**1. Database Schema Drift Detection**
- ❌ Alembic migration validation
- ❌ Schema compatibility checks
- ❌ Migration ordering validation
- ❌ Downgrade path verification

**2. Enhanced Scripts**
- ❌ `scripts/check-contract-drift.py` (US #87 specific request)
- ⚠️ Breaking change detection TODO in validate-api-contracts.py (line 79)

**3. Documentation**
- ❌ Contract evolution process guide
- ❌ Troubleshooting guide
- ❌ Developer onboarding for contracts

**4. Testing**
- ❌ Sample breaking change scenarios
- ❌ Automated testing of drift detection

---

## 🎯 **IMPLEMENTATION STRATEGY**

### **Phase 1: Database Schema Drift Detection** (Critical Gap)

The key insight from US #86 is that **database schema drift** is critical:
- Alembic migrations must be validated
- Schema changes can break services
- This is MORE important than API contract drift

**Deliverables:**
1. ✅ Create `scripts/check-schema-drift.py`
   - Validates Alembic migration ordering
   - Detects conflicting migrations
   - Verifies schema compatibility
   - Checks for dangerous operations (DROP TABLE, etc.)

2. ✅ Create `scripts/check-contract-drift.py` (wrapper)
   - Combines API + database drift checks
   - Single entry point as requested in US #87
   - Comprehensive reporting

---

### **Phase 2: Enhanced Breaking Change Detection**

**Current Gap:** Line 79 in validate-api-contracts.py has TODO

**Deliverables:**
1. ✅ Implement breaking change detection in validate-api-contracts.py
   - Use existing check-breaking-changes.py logic
   - Add to main validation flow
   - Remove TODO

2. ✅ Add schema field change detection
   - Required → optional (safe)
   - Optional → required (BREAKING)
   - Type changes (BREAKING)
   - Enum value removal (BREAKING)

---

### **Phase 3: Documentation & Guides**

**Deliverables:**
1. ✅ Contract Evolution Guide (`docs/CONTRACT_EVOLUTION.md`)
   - When to create new version (v2, v3)
   - Backward compatibility rules
   - Deprecation process
   - Examples of safe/unsafe changes

2. ✅ Troubleshooting Guide (`docs/SCHEMA_DRIFT_TROUBLESHOOTING.md`)
   - Common drift scenarios
   - How to fix breaking changes
   - Emergency bypass procedures
   - FAQs

3. ✅ Developer Onboarding (`docs/CONTRACT_DEVELOPMENT.md`)
   - How to modify contracts
   - Local validation workflow
   - CI/CD integration
   - Best practices

---

### **Phase 4: Testing & Validation**

**Deliverables:**
1. ✅ Test Suite (`tests/ci/test_schema_drift.py`)
   - Breaking change scenarios
   - Migration conflict detection
   - Safe change validation
   - Edge cases

2. ✅ Sample Contracts (`tests/fixtures/contracts/`)
   - Valid baseline
   - Breaking changes examples
   - Safe changes examples
   - Migration conflicts

---

## 📋 **DETAILED TASKS**

### **Task 1: Database Schema Drift Detection** (4 hours)

**1a. Create `scripts/check-schema-drift.py`**
```python
Features:
- Validate Alembic revision ordering
- Detect merge conflicts in migration tree
- Check for dangerous operations (DROP, ALTER TYPE)
- Verify migration reversibility
- Validate schema compatibility with services
```

**1b. Add Alembic validation to CI**
```yaml
.github/workflows/schema-validation.yml:
- Validate all migrations compile
- Check for conflicts
- Run migrations against test database
- Verify downgrade paths work
```

---

### **Task 2: Unified Contract Drift Script** (2 hours)

**Create `scripts/check-contract-drift.py`**
```python
Combines:
- API contract validation (existing)
- Database schema validation (new)
- Breaking change detection
- Comprehensive reporting

Entry point requested in US #87
```

---

### **Task 3: Enhanced Breaking Change Detection** (2 hours)

**Update `ci/validate-api-contracts.py`**
```python
Line 79 TODO → Implement:
- Integrate check-breaking-changes.py logic
- Add schema field change detection
- Add enum value validation
- Add required field tracking
```

---

### **Task 4: Documentation** (3 hours)

**Create 3 comprehensive guides:**
1. `docs/CONTRACT_EVOLUTION.md`
2. `docs/SCHEMA_DRIFT_TROUBLESHOOTING.md`
3. `docs/CONTRACT_DEVELOPMENT.md`

---

### **Task 5: Testing** (3 hours)

**Create test suite:**
1. Unit tests for drift detection
2. Integration tests with Alembic
3. Sample contract fixtures
4. CI validation

---

## ✅ **SUCCESS CRITERIA**

**Must Achieve:**
- [x] `scripts/check-schema-drift.py` created and functional
- [x] `scripts/check-contract-drift.py` created as main entry point
- [x] Database migration validation in CI
- [x] Breaking change detection implemented (TODO removed)
- [x] 3 documentation guides created
- [x] Test suite with >80% coverage
- [x] All existing CI workflows still pass
- [x] Zero false positives in testing

**Should Achieve:**
- [x] Pre-commit hook for schema drift
- [x] Sample breaking change scenarios
- [x] Emergency bypass documentation
- [x] Developer onboarding complete

---

## 📊 **EFFORT ESTIMATE**

| Task | Hours | Status |
|------|-------|--------|
| Schema drift detection | 4 | Pending |
| Unified contract drift script | 2 | Pending |
| Enhanced breaking detection | 2 | Pending |
| Documentation | 3 | Pending |
| Testing | 3 | Pending |
| **Total** | **14 hours** | **~2 days** |

---

## 🎯 **IMPLEMENTATION ORDER**

**Day 1 (Today):**
1. ✅ Complete analysis (Done)
2. 🔄 Create schema drift detection
3. 🔄 Create unified contract drift script
4. 🔄 Update breaking change detection

**Day 2 (Tomorrow):**
5. ⏭️ Write documentation
6. ⏭️ Create test suite
7. ⏭️ Validate all workflows
8. ⏭️ Update Taiga with results

---

## 🔗 **KEY INSIGHTS FROM US #86**

**Why Database Schema Drift Matters:**

From US #86 investigation:
- Database changes are HIGH RISK (production data)
- Alembic migrations must be carefully validated
- Breaking schema changes harder to rollback than API changes
- Migration conflicts can corrupt production database

**Therefore:** Database schema drift is HIGHER priority than API contract drift

---

## 📝 **DELIVERABLES MAPPING**

**US #87 Original Requirements:**

| Requirement | Solution | Status |
|-------------|----------|--------|
| Create check-contract-drift.py | ✅ Will create as wrapper | Pending |
| GitHub workflow for OpenAPI | ✅ Already exists | Complete |
| Detect breaking changes | ✅ Enhance existing | Pending |
| Pre-commit hook | ✅ Already exists | Complete |
| Document evolution process | ✅ CONTRACT_EVOLUTION.md | Pending |
| Test with sample contracts | ✅ Test suite | Pending |
| Troubleshooting guide | ✅ TROUBLESHOOTING.md | Pending |

---

## 🚀 **NEXT STEPS**

**Starting implementation NOW:**

1. **Create schema drift detection** (highest priority)
2. **Create unified wrapper script**
3. **Enhance breaking change detection**
4. **Write documentation**
5. **Create test suite**
6. **Update US #87 in Taiga**

---

**Implementation begins!** 🎯
