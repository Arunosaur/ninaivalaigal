# Alembic Migration Enforcement Rules for Multiple Developers

**Date:** November 18, 2025  
**Purpose:** Systematic enforcement to prevent single source of truth violations

---

## 🚀 **Systematic Enforcement Strategy**

### **1. Automated Pre-Commit Hooks**

#### **Installation Script**
```bash
#!/bin/bash
# Install pre-commit hooks for Alembic enforcement

echo "🔧 Installing Alembic enforcement hooks..."

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Alembic Single Source of Truth Pre-Commit Hook

echo "🔍 Validating Alembic single source of truth..."

# Check if any Alembic files were modified
if git diff --cached --name-only | grep -q "alembic/.*\.py"; then
    echo "📝 Alembic migration files detected, running validation..."
    
    # Run single source of truth validation
    if ! ./scripts/alembic-validate-single-source.sh; then
        echo "❌ VALIDATION FAILED: Single source of truth violation detected!"
        echo "Please fix the following issues before committing:"
        echo "1. Remove duplicate table names across schemas"
        echo "2. Ensure all create_table calls specify schema"
        echo "3. Run ./scripts/alembic-validate-single-source.sh to verify"
        exit 1
    fi
    
    echo "✅ Alembic validation passed"
else
    echo "ℹ️  No Alembic changes detected, skipping validation"
fi

exit 0
EOF

chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hooks installed successfully!"
echo "📋 Enforcement rules:"
echo "   - Single source of truth validation on commits"
echo "   - Schema consistency checks"
echo "   - Duplicate table prevention"
EOF

chmod +x scripts/install-alembic-hooks.sh
```

### **2. CI/CD Pipeline Enforcement**

#### **GitHub Actions Workflow**
```yaml
# .github/workflows/alembic-validation.yml
name: Alembic Single Source of Truth Validation

on:
  push:
    branches: [ main, develop ]
    paths: [ 'alembic/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'alembic/**' ]

jobs:
  alembic-validation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install alembic sqlalchemy
    
    - name: Validate single source of truth
      run: |
        chmod +x scripts/alembic-validate-single-source.sh
        ./scripts/alembic-validate-single-source.sh
    
    - name: Check migration naming
      run: |
        # Enforce migration naming convention
        for file in alembic/*/versions/*.py; do
          if [[ -f "$file" ]]; then
            basename=$(basename "$file")
            if [[ ! "$basename" =~ ^[0-9]{8}_[0-9]{4}_ ]]; then
              echo "❌ Invalid migration filename: $basename"
              echo "Expected format: YYYYMMDD_HHMM_description.py"
              exit 1
            fi
          fi
        done
    
    - name: Validate schema targeting
      run: |
        # Ensure all create_table calls specify schema
        for file in alembic/*/versions/*.py; do
          if [[ -f "$file" ]]; then
            if grep -q "create_table" "$file" && ! grep -q "schema=" "$file"; then
              echo "❌ Missing schema specification in $file"
              echo "All create_table calls must specify schema parameter"
              exit 1
            fi
          fi
        done
```

### **3. Development Guidelines**

#### **Migration Creation Checklist**
```markdown
## Before Creating a Migration

- [ ] **Identify target schema** - Know which schema owns the table
- [ ] **Check for duplicates** - Run validation script first
- [ ] **Review naming conventions** - Use appropriate prefixes
- [ ] **Verify schema targeting** - Ensure schema= is specified

## Migration Creation Process

1. **Choose correct environment**
   ```bash
   # Core API tables
   alembic -c alembic/public/alembic.ini revision --autogenerate -m "description"
   
   # Memory service tables
   alembic -c alembic/memory/alembic.ini revision --autogenerate -m "description"
   ```

2. **Review generated migration**
   - Verify schema is specified in all create_table calls
   - Check for duplicate table names
   - Ensure proper foreign key relationships

3. **Validate before commit**
   ```bash
   ./scripts/alembic-validate-single-source.sh
   ```

4. **Commit with descriptive message**
   ```bash
   git commit -m "feat(core_api): add user_preferences table"
   ```
```

### **4. Team Training & Documentation**

#### **Developer Onboarding Checklist**
```markdown
## Alembic Training for New Developers

### ✅ Required Reading
1. `/alembic/README.md` - Architecture overview
2. `/docs/ALEMBIC-SINGLE-SOURCE-OF-TRUTH.md` - Single source of truth rules
3. `/scripts/alembic-validate-single-source.sh` - Validation tool

### ✅ Hands-on Training
1. **Create a test migration**
   ```bash
   # Practice creating a migration in dev environment
   alembic -c alembic/public/alembic.ini revision --autogenerate -m "test_table"
   ```

2. **Validate the migration**
   ```bash
   ./scripts/alembic-validate-single-source.sh
   ```

3. **Review and fix issues**
   - Understand validation failures
   - Practice fixing schema targeting
   - Learn duplicate prevention

### ✅ Assessment
- Create a migration without violations
- Fix a deliberately broken migration
- Pass validation quiz
```

### **5. Code Review Templates**

#### **Pull Request Template**
```markdown
## Alembic Migration Review

### 📋 Migration Details
- **Schema:** [core_api/memory/intelligence/graphops/compliance]
- **Tables Added:** [List of tables]
- **Tables Modified:** [List of tables]
- **Breaking Changes:** [Yes/No, describe]

### 🔍 Validation Checklist
- [ ] Single source of truth validation passes
- [ ] All create_table calls specify schema
- [ ] No duplicate table names
- [ ] Migration follows naming convention
- [ ] Foreign key relationships are correct
- [ ] Downgrade migration is tested

### 🧪 Testing
- [ ] Migration applied successfully in dev
- [ ] Downgrade migration tested
- [ ] Application works with new schema
- [ ] Performance impact assessed

### 📝 Reviewer Notes
[Additional comments about the migration]
```

### **6. Monitoring & Alerting**

#### **Schema Health Monitoring**
```bash
#!/bin/bash
# scripts/alembic-health-monitor.sh

echo "🏥 Alembic Schema Health Check"
echo "================================"

# Check for validation failures
if ! ./scripts/alembic-validate-single-source.sh > /dev/null 2>&1; then
    echo "🚨 ALERT: Single source of truth validation failed!"
    echo "Action required: Check recent migrations"
    exit 1
fi

# Check for unapplied migrations
echo "📊 Checking migration status..."
./scripts/alembic-status-all.sh

# Check for migration conflicts
echo "🔍 Checking for migration conflicts..."
if git status --porcelain | grep -q "alembic.*\.py"; then
    echo "⚠️  WARNING: Uncommitted migration changes detected"
fi

echo "✅ Health check complete"
```

### **7. Rollback Procedures**

#### **Emergency Rollback Script**
```bash
#!/bin/bash
# scripts/alembic-emergency-rollback.sh

SCHEMA=${1:-"all"}
REVISION=${2:-"base"}

echo "🚨 EMERGENCY ROLLBACK INITIATED"
echo "Schema: $SCHEMA"
echo "Target revision: $REVISION"
echo

if [[ "$SCHEMA" == "all" ]]; then
    echo "Rolling back all schemas..."
    ./taiga/.venv/bin/alembic -c alembic/public/alembic.ini downgrade "$REVISION"
    ./taiga/.venv/bin/alembic -c alembic/graphops/alembic.ini downgrade "$REVISION"
    ./taiga/.venv/bin/alembic -c alembic/memory/alembic.ini downgrade "$REVISION"
    ./taiga/.venv/bin/alembic -c alembic/intelligence/alembic.ini downgrade "$REVISION"
else
    echo "Rolling back $SCHEMA schema..."
    ./taiga/.venv/bin/alembic -c "alembic/$SCHEMA/alembic.ini" downgrade "$REVISION"
fi

echo "✅ Rollback complete"
echo "📋 Post-rollback actions:"
echo "1. Verify application functionality"
echo "2. Check data integrity"
echo "3. Document rollback reason"
echo "4. Schedule fix deployment"
```

---

## 🛡️ **Enforcement Rules Summary**

### **Automatic Enforcement**
1. **Pre-commit hooks** - Block commits with violations
2. **CI/CD validation** - Fail builds on violations
3. **Automated testing** - Run validation in all environments

### **Manual Enforcement**
1. **Code review templates** - Ensure reviewer validation
2. **Development guidelines** - Clear process documentation
3. **Team training** - Ensure developer understanding

### **Monitoring & Recovery**
1. **Health monitoring** - Continuous schema validation
2. **Alerting** - Immediate notification of issues
3. **Rollback procedures** - Quick recovery from violations

---

## 🎯 **Success Metrics**

### **Prevention Metrics**
- **Zero violations** in production
- **100% validation pass rate** on commits
- **No duplicate tables** across schemas

### **Detection Metrics**
- **Immediate detection** of violations
- **Fast resolution** of issues (< 1 hour)
- **Clear documentation** of fixes

### **Team Metrics**
- **100% developer training** completion
- **Consistent code review** quality
- **Zero emergency rollbacks** due to violations

---

**Implementation Date:** November 18, 2025  
**Review Date:** Quarterly  
**Owner:** Database Architecture Team
