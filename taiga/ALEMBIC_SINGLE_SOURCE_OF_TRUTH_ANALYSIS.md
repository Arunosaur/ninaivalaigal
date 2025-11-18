# Alembic Migration Single Source of Truth Analysis
**Date:** November 18, 2025  
**Status:** ⚠️ **CRITICAL ISSUES FOUND - VIOLATION OF SINGLE SOURCE OF TRUTH**

---

## 🚨 **Critical Issues Discovered**

### **Issue 1: Schema Inconsistency**
- **Migration 20251114_0800_complete.py**: Creates tables in `core_api` schema
- **Migration 20251116_0100_consolidate_auth_security.py**: Creates tables in default (public) schema
- **Impact**: Same table names in different schemas = CONFUSION

### **Issue 2: Duplicate Table Creation**
The table `mfa_webauthn_credentials` is created in BOTH migrations:
```sql
-- First migration (core_api schema)
CREATE TABLE core_api.mfa_webauthn_credentials (...)

-- Second migration (public schema)  
CREATE TABLE mfa_webauthn_credentials (...)
```

### **Issue 3: Multiple Schema Environments**
Found **11 separate Alembic environments** instead of the planned 4:
- **Original 4**: public, graphops, memory, intelligence ✅
- **Additional 7**: compliance, hipaa, incident_response, iso27001, pentest, security, soc2 ⚠️

---

## 📊 **Current Schema Analysis**

### **✅ Proper Schema Separation (No Conflicts)**
| Schema | Tables | Purpose | Status |
|--------|--------|---------|--------|
| `public` | Core application tables | Main app | ✅ Clean |
| `ag_catalog` | Apache AGE tables | GraphOps | ✅ Clean |
| `memory` | Memory relationships | Memory service | ✅ Clean |
| `intelligence_graph` | Intelligence data | AI service | ✅ Clean |

### **⚠️ Compliance Schemas (Properly Separated)**
| Schema | Tables | Purpose | Status |
|--------|--------|---------|--------|
| `compliance` | gdpr_* tables | GDPR compliance | ✅ Clean |
| `hipaa` | hipaa_* tables | HIPAA compliance | ✅ Clean |
| `security` | threat_intelligence | Security data | ✅ Clean |
| `soc2` | soc2_* tables | SOC2 compliance | ✅ Clean |
| `iso27001` | iso27001_* tables | ISO27001 compliance | ✅ Clean |
| `incident_response` | incidents, response_* | Incident management | ✅ Clean |
| `pentest` | pentest_*, vulnerability_* | Security testing | ✅ Clean |

### **❌ PROBLEM: Core API Schema Confusion**
| Schema | Tables | Issue | Resolution Needed |
|--------|--------|-------|-------------------|
| `core_api` | users, mfa_*, sso_* | Created in first migration | ⚠️ INCONSISTENT |
| `public` | users, mfa_*, auth_* | Created in second migration | ⚠️ DUPLICATE |

---

## 🔍 **Root Cause Analysis**

### **Problem 1: Schema Target Confusion**
```python
# First migration (CORRECT - uses core_api schema)
op.create_table("users", ..., schema="core_api")

# Second migration (WRONG - uses default schema)
op.create_table("users", ...)  # Goes to public schema
```

### **Problem 2: Environment Configuration**
- **public/env.py**: Correctly configured for `public` schema
- **Migration files**: Not following schema conventions
- **Version tracking**: Each schema has separate `alembic_version` table ✅

### **Problem 3: Table Naming Strategy**
- **Compliance schemas**: Proper prefixing (gdpr_*, hipaa_*, soc2_*) ✅
- **Core schemas**: Inconsistent schema usage ❌

---

## 🎯 **Recommendations**

### **Immediate Actions Required**

#### **1. Fix Schema Inconsistency**
```python
# Option A: Move everything to core_api schema (RECOMMENDED)
# Update second migration to use schema="core_api"

# Option B: Move everything to public schema
# Update first migration to remove schema="core_api"
```

#### **2. Resolve Duplicate Tables**
- Choose ONE schema for core API tables
- Consolidate `mfa_webauthn_credentials` creation
- Ensure single source of truth for auth tables

#### **3. Standardize Schema Strategy**
```python
# RECOMMENDED APPROACH:
- core_api: All main application tables
- public: Views, functions, procedures only
- compliance schemas: Keep as-is (properly separated)
```

### **Process Improvements**

#### **1. Schema Governance**
- **Document schema ownership** clearly
- **Enforce schema prefixes** for compliance tables
- **Single schema per service/domain**

#### **2. Migration Standards**
- **Always specify schema** in create_table calls
- **No cross-schema table duplication**
- **Consistent naming conventions**

#### **3. Validation Scripts**
```bash
# Add script to check for duplicate table names
./scripts/alembic-validate-no-duplicates.sh

# Add script to verify schema consistency  
./scripts/alembic-validate-schema-consistency.sh
```

---

## 🏗️ **Recommended Architecture**

### **Clean Schema Separation**
```
core_api/           # Main application tables
├── users
├── mfa_*
├── auth_*
├── billing_*
└── ...

public/             # Views, functions, procedures
├── admin_views
├── reporting_views
└── ...

compliance/         # All compliance tables
├── gdpr_*
├── hipaa_*
├── soc2_*
├── iso27001_*
└── ...

graphops/           # Apache AGE tables
├── ag_catalog
└── ...

memory/             # Memory service tables
├── memory_*
└── ...

intelligence/       # AI service tables
├── intelligence_*
└── ...

security/           # Security-specific tables
├── threat_intelligence
└── ...
```

---

## 📋 **Action Items**

### **Priority 1: Critical (Fix Now)**
1. **Fix duplicate `mfa_webauthn_credentials` table**
2. **Standardize core API schema usage**
3. **Update migration to use consistent schema**

### **Priority 2: High (This Week)**
1. **Create validation scripts**
2. **Document schema ownership**
3. **Update development guidelines**

### **Priority 3: Medium (Next Sprint)**
1. **Review all migration patterns**
2. **Create schema governance process**
3. **Add automated duplicate detection**

---

## ✅ **What's Working Well**

1. **Compliance schemas**: Properly separated with clear prefixes
2. **Version tracking**: Each schema has independent alembic_version table
3. **No table name conflicts**: Across different compliance schemas
4. **Multi-environment setup**: Working correctly for schema isolation

---

## 🎯 **Next Steps**

1. **IMMEDIATE**: Fix the schema inconsistency in the latest migration
2. **TODAY**: Create validation script to prevent future duplicates
3. **THIS WEEK**: Document and enforce schema governance
4. **ONGOING**: Monitor for single source of truth compliance

---

**Analysis completed on November 18, 2025**  
**CRITICAL: Schema inconsistency found - requires immediate attention**  
**Multiple environments are fine, but schema consistency must be maintained** ⚠️
