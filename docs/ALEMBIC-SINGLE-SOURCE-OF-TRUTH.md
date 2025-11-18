# Alembic Single Source of Truth Architecture

**Date:** November 18, 2025  
**Status:** ✅ **ACTIVE - Clean Implementation**

---

## 🎯 **Single Source of Truth Principle**

This architecture ensures **no table duplication** across schemas and **clear ownership** for each data domain.

---

## 📊 **Schema Ownership**

### **core_api Schema** (Main Application)
**Owner**: Python API Service  
**Purpose**: All main application tables  
**Tables**: users, mfa_*, sso_*, security_*, anomaly_*, device_*, risk_*

### **ag_catalog Schema** (GraphOps)
**Owner**: Rust GraphOps Service  
**Purpose**: Apache AGE graph catalog + application tables  
**Tables**: graph_schema_registry, age_*

### **memory Schema** (Memory Service)
**Owner**: Python API Service  
**Purpose**: Memory relationships and data  
**Tables**: memory_relationships, memory_*

### **intelligence_graph Schema** (AI Service)
**Owner**: Python API Service  
**Purpose**: AI insights and intelligence data  
**Tables**: intelligence_insights, intelligence_*

### **Compliance Schemas** (Isolated)
**Owner**: Compliance Service  
**Purpose**: Regulatory compliance data  
**Tables**: gdpr_*, hipaa_*, soc2_*, iso27001_*, incident_*, pentest_*, threat_intelligence

---

## 🔧 **Migration Commands**

### **Core API (Main Application)**
```bash
# Create migration
alembic -c alembic/public/alembic.ini revision --autogenerate -m "description"

# Apply migration
alembic -c alembic/public/alembic.ini upgrade head

# Check status
alembic -c alembic/public/alembic.ini current
```

### **All Schemas**
```bash
# Check all statuses
./scripts/alembic-status-all.sh

# Validate single source of truth
./scripts/alembic-validate-single-source.sh

# Upgrade all schemas
./scripts/alembic-upgrade-all.sh
```

---

## ✅ **Validation Rules**

1. **No Duplicate Tables**: Each table name exists in only one schema
2. **Explicit Schema Targeting**: All create_table calls specify schema
3. **Clear Ownership**: Each schema has a single responsible service
4. **Consistent Naming**: Related tables use appropriate prefixes

---

## 🚨 **Prevention Measures**

### **Automated Validation**
```bash
# Run before committing
./scripts/alembic-validate-single-source.sh

# Pre-commit hook (recommended)
#!/bin/sh
./scripts/alembic-validate-single-source.sh || exit 1
```

### **Development Guidelines**
1. **Always specify schema** in create_table calls
2. **Use descriptive table names** with appropriate prefixes
3. **Check for conflicts** before creating new tables
4. **Run validation** after each migration

---

## 📋 **Migration History**

### **2025-11-18: Single Source of Truth Reset**
- Cleaned up all previous migrations
- Created consistent schema structure
- Established clear ownership boundaries
- Added validation scripts

---

**For technical details, see:** `/alembic/README.md`  
**For validation, see:** `/scripts/alembic-validate-single-source.sh`
