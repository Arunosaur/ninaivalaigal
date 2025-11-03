# SPEC-074 GDPR Compliance - Deployment Checklist

**Date**: November 2, 2025
**Status**: Phase 1 Complete
**Assigned To**: Developer G

---

## ✅ Pre-Deployment Verification

### 1. Code Verification

- [x] All Python files compile without errors
- [x] No linter errors
- [x] All imports resolve correctly
- [x] Module structure is correct
- [x] Router registered in `main.py`

### 2. Database Migration

- [ ] **Migration file exists**: `alembic/versions/0127_spec074_gdpr_compliance_schema.py`
- [ ] **Migration tested**: Run `alembic upgrade head` successfully
- [ ] **Tables created**: `public.data_subject_requests`, `public.data_exports`
- [ ] **Indexes created**: 9 performance indexes verified
- [ ] **Foreign keys**: Verified CASCADE relationships

**Command to apply migration**:
```bash
cd server
alembic upgrade head
```

**Command to verify tables**:
```bash
psql -d ninaivalaigal_dev -c "\dt public.data_*"
```

### 3. API Endpoints

- [ ] **Router registered**: Check `/api/v1/compliance` prefix
- [ ] **Authentication**: JWT tokens work
- [ ] **Request validation**: Pydantic models work
- [ ] **Error handling**: Proper error responses

**Command to test**:
```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.jwt_token')

# Test DSAR endpoint
curl -X POST http://localhost:8000/api/v1/compliance/dsar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Test DSAR"}'
```

### 4. Data Collection

- [ ] **Data sources accessible**: Memory, contexts, teams, etc.
- [ ] **Collection works**: Test with real user data
- [ ] **Export generation**: JSON export works
- [ ] **File download**: Download endpoint functional

---

## 🚀 Deployment Steps

### Step 1: Apply Database Migration

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
cd server
alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Running upgrade 0126 -> 0127, spec074_gdpr_compliance_schema
```

### Step 2: Verify Tables Created

```bash
psql -d ninaivalaigal_dev <<EOF
\dt public.data_*
\d public.data_subject_requests
\d public.data_exports
EOF
```

**Expected tables**:
- `public.data_subject_requests`
- `public.data_exports`

### Step 3: Verify API Registration

```bash
# Start server (if not running)
cd server
python -m uvicorn main:app --reload

# In another terminal, check API docs
curl http://localhost:8000/docs | grep -i compliance

# Or check OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.paths | keys | .[] | select(. | contains("compliance"))'
```

### Step 4: Run Test Script

```bash
python3 scripts/test_gdpr_compliance.py
```

**Expected**: All tests pass

### Step 5: Manual Endpoint Testing

Use the Quick Start guide: `specs/074-gdpr-compliance/QUICK_START.md`

---

## 🔍 Post-Deployment Verification

### Functional Tests

1. **DSAR Request**
   - [ ] Submit DSAR via API
   - [ ] Verify request created in database
   - [ ] Check status tracking works
   - [ ] Verify export generation

2. **Erasure Request**
   - [ ] Submit erasure request (test user only!)
   - [ ] Verify legal obligation checks
   - [ ] Confirm data deletion/anonymization
   - [ ] Verify audit trail preserved

3. **Data Export**
   - [ ] Request data export
   - [ ] Verify JSON format
   - [ ] Check download URL generation
   - [ ] Verify expiry handling

### Database Verification

```sql
-- Check request table
SELECT COUNT(*) FROM public.data_subject_requests;

-- Check export table
SELECT COUNT(*) FROM public.data_exports;

-- Verify indexes
SELECT indexname FROM pg_indexes
WHERE tablename IN ('data_subject_requests', 'data_exports');
```

### Performance Checks

- [ ] Index usage verified (EXPLAIN ANALYZE)
- [ ] Query performance acceptable (<100ms)
- [ ] No N+1 query problems

---

## ⚠️ Important Notes

1. **Erasure Testing**
   - ⚠️ **NEVER test erasure on production data**
   - ⚠️ Use test users only
   - ⚠️ Erasure is **irreversible**

2. **Legal Obligations**
   - Billing records may be retained
   - Audit trails are preserved (anonymized)
   - Financial data may not be deletable

3. **Phase 2 Items**
   - Encryption (AES-256) - placeholder
   - Export storage (S3/Azure) - in-memory
   - XML/CSV formatting - JSON only

---

## 📋 Rollback Plan

If migration fails:

```bash
# Rollback migration
cd server
alembic downgrade -1

# Verify rollback
psql -d ninaivalaigal_dev -c "\dt public.data_*"
```

If API issues:

```bash
# Remove router from main.py temporarily
# Comment out:
# from compliance.api import router as compliance_router
# app.include_router(compliance_router)
```

---

## 📚 Documentation

- **Quick Start**: `specs/074-gdpr-compliance/QUICK_START.md`
- **Final Summary**: `docs/spec-analysis/SPEC_074_PHASE1_FINAL_SUMMARY.md`
- **Implementation Details**: `docs/spec-analysis/SPEC_074_IMPLEMENTATION_COMPLETE.md`

---

## ✅ Sign-Off

- [ ] Migration applied successfully
- [ ] Tables verified
- [ ] API endpoints tested
- [ ] Data collection verified
- [ ] Documentation reviewed
- [ ] Ready for production testing

**Completed By**: _______________
**Date**: _______________
**Status**: ☐ Ready for Production | ☐ Needs More Testing
