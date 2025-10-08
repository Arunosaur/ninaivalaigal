# Port Enforcement System - Machine-Readable & Automated

**Created**: October 7, 2025
**Status**: ✅ Operational
**Purpose**: Eliminate human port mismatches forever

---

## 🎯 What We Built

A **machine-enforceable** port validation system that:

1. ✅ **Canonical Matrix V2** - Single source of truth with EM included
2. ✅ **Machine-Readable Config** - `config/ports.nv.yaml` for programmatic access
3. ✅ **Automated Validation** - `scripts/validate-ports.sh` checks compliance
4. ✅ **Auto-Fix Script** - `scripts/fix-ports-spec-086.sh` corrects mismatches

---

## 📂 File Structure

```
ninaivalaigal/
├── config/
│   └── ports.nv.yaml                              # Machine-readable port matrix
├── docs/
│   ├── network/
│   │   └── NINAIVALAIGAL_PORT_MATRIX_V2.md       # Human-readable reference
│   ├── PORT_CORRECTION_PLAN.md                    # Current fix plan
│   └── PORT_ENFORCEMENT_SYSTEM.md                 # This document
└── scripts/
    ├── validate-ports.sh                          # Automated validation
    └── fix-ports-spec-086.sh                      # Automated correction
```

---

## 🚀 Usage

### 1. Validate Current Ports

```bash
# Validate Apple Dev (default)
./scripts/validate-ports.sh

# Validate specific runtime/environment
./scripts/validate-ports.sh colima test
./scripts/validate-ports.sh docker prod
```

**Output Example**:
```
╔══════════════════════════════════════════════════════════════════════╗
║          Port Validation Against Canonical Matrix V2                ║
╚══════════════════════════════════════════════════════════════════════╝

Runtime: apple
Environment: dev

=== Port Binding Validation ===

✅ PostgreSQL: Port 5452 listening (container)
❌ PgBouncer: Port 6452 NOT listening
✅ Redis: Port 6399 listening (container)
✅ API: Port 13390 listening (container)
❌ Customer UI: Port 8101 NOT listening
❌ Admin Console: Port 8201 NOT listening
⚠️  Enhanced Memory: Port 8301 NOT listening

╔══════════════════════════════════════════════════════════════════════╗
║          Validation Summary                                          ║
╚══════════════════════════════════════════════════════════════════════╝

Total Checks:    7
Passed:          3
Failed:          3
Warnings:        1

❌ Port validation FAILED

To fix port mismatches, run:
  ./scripts/fix-ports-spec-086.sh
```

### 2. Fix Port Mismatches

```bash
./scripts/fix-ports-spec-086.sh
```

This will:
- Stop and recreate containers with correct ports
- Update database connections
- Verify all services are healthy
- Display new service URLs

### 3. Integrate into CI/CD

Add to your GitHub Actions or Make targets:

```yaml
# .github/workflows/validate-ports.yml
name: Validate Ports

on: [push, pull_request]

jobs:
  validate:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Port Matrix
        run: ./scripts/validate-ports.sh apple dev
```

Or in Makefile:
```makefile
validate-ports:
\t@./scripts/validate-ports.sh $(RUNTIME) $(ENV)

fix-ports:
\t@./scripts/fix-ports-spec-086.sh
```

---

## 🔍 How It Works

### config/ports.nv.yaml Structure

```yaml
version: "2.0"

# Formula for calculating ports
formula:
  base_ports:
    postgresql: 5432
    pgbouncer: 6432
    # ... etc

  runtime_offset:
    docker: 0
    colima: 10
    apple: 20

  environment_offset:
    dev: 0
    test: 100
    prod: 200

# Complete matrix (programmatically accessible)
matrix:
  apple:
    dev:
      postgresql: 5452
      pgbouncer: 6452
      redis: 6399
      api: 13390
      ui_external: 8101
      ui_internal: 8201
      em: 8301
```

### Validation Logic

1. **Read YAML** - Parse `config/ports.nv.yaml` for expected ports
2. **Check Bindings** - Use `lsof` to find actual listening ports
3. **Compare** - Match expected vs actual
4. **Report** - Display pass/fail for each service
5. **Check Collisions** - Scan reserved ranges for unexpected ports
6. **Validate Names** - Ensure container names follow convention

### Auto-Fix Logic

1. **Get IPs** - Find current container IPs
2. **Stop Services** - Gracefully stop containers with wrong ports
3. **Restart with Correct Ports** - Use matrix values
4. **Update Dependencies** - Fix API→PgBouncer connections
5. **Health Check** - Verify all services operational
6. **Display URLs** - Show corrected access URLs

---

## 🎓 Developer Benefits

### No More Port Confusion

**Before**:
- "Which port is the API on again?"
- "Why is my UI not loading?"
- "Are we using 8100 or 8101?"

**After**:
```bash
./scripts/validate-ports.sh
# Shows exact status in 2 seconds
```

### Predictable Patterns

**Mental Model**:
```
Final Port = Base + Environment(×100) + Runtime(×10)

Apple Dev API = 13370 + 0 + 20 = 13390
Colima Test API = 13370 + 100 + 10 = 13480
```

### Self-Documenting

```bash
# Quick reference
cat config/ports.nv.yaml | grep -A 10 "apple:" | grep -A 7 "dev:"

# Or read the pretty docs
open docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md
```

---

## 🛡️ Enforcement Points

### 1. Pre-Commit Hook (Optional)

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/validate-ports.sh || {
  echo "Port validation failed. Fix before committing."
  exit 1
}
```

### 2. CI/CD Pipeline

```yaml
# Enforce on every PR
- name: Validate Ports
  run: |
    chmod +x scripts/validate-ports.sh
    ./scripts/validate-ports.sh apple dev
```

### 3. Startup Scripts

```bash
# In nina-intelligence-stack-start-unified.sh
echo "Validating port allocations..."
./scripts/validate-ports.sh "$NINA_RUNTIME" "$NINA_ENV" || exit 1
```

### 4. Manual Validation

```bash
# Run anytime you're unsure
make validate-ports
```

---

## 📊 What Gets Validated

| Check Type | Description | Action on Failure |
|------------|-------------|-------------------|
| **Port Bindings** | Is expected port listening? | ❌ Fail |
| **Container Names** | Match naming convention? | ❌ Fail |
| **Port Collisions** | Unexpected ports in range? | ⚠️ Warning |
| **Health Checks** | Services responding? | ⚠️ Warning |

---

## 🔄 Updating the Matrix

### Adding a New Service

1. **Update `config/ports.nv.yaml`**:
```yaml
formula:
  base_ports:
    new_service: 9000  # Choose unused base port

matrix:
  apple:
    dev:
      new_service: 9020  # base + runtime_offset
```

2. **Update Documentation**:
```bash
# Edit docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md
# Add new service to all tables
```

3. **Update Validation**:
```bash
# In scripts/validate-ports.sh
SERVICES=("postgresql" "pgbouncer" "redis" "api" "ui_external" "ui_internal" "em" "new_service")
SERVICE_NAMES=("PostgreSQL" "PgBouncer" "Redis" "API" "Customer UI" "Admin Console" "EM" "New Service")
```

4. **Test**:
```bash
./scripts/validate-ports.sh
# Should now check new_service
```

### Changing Port Assignments

**DON'T DO THIS** unless absolutely necessary. Port matrix is meant to be stable.

If you must:
1. Update YAML
2. Update all documentation
3. Run fix script on all environments
4. Notify team
5. Update any external integrations

---

## 🎯 Success Metrics

### Before Enforcement System
- ❌ Port mismatches discovered during demos
- ❌ Manual port tracking in scattered docs
- ❌ No validation until runtime errors
- ❌ "Which port?" questions daily

### After Enforcement System
- ✅ Port validation in <2 seconds
- ✅ Single source of truth (YAML)
- ✅ Auto-fix available
- ✅ Zero manual lookups needed

---

## 🔗 Integration Points

### With Existing Scripts

```bash
# nina-intelligence-stack-start-unified.sh
# Add at beginning:
echo "Validating ports before startup..."
./scripts/validate-ports.sh "$NINA_RUNTIME" "$NINA_ENV"

# nina-api-diagnose-repair (future)
# Can read ports.nv.yaml to know expected values
```

### With Monitoring

```python
# server/observability/port_monitor.py
import yaml

def get_expected_port(service, runtime, env):
    with open('config/ports.nv.yaml') as f:
        config = yaml.safe_load(f)
    return config['matrix'][runtime][env][service]

# Use in health checks
expected_api_port = get_expected_port('api', 'apple', 'dev')
```

---

## 📚 Related Files

- **Canonical Reference**: `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
- **Machine Config**: `config/ports.nv.yaml`
- **SPEC**: `specs/SPEC-086-multi-runtime-port-allocation.md`
- **Current Issues**: `docs/PORT_CORRECTION_PLAN.md`
- **Container Docs**: `docs/CONTAINER_ARCHITECTURE.md`

---

## ✅ Checklist: Using This System

- [ ] 1. Read canonical matrix: `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
- [ ] 2. Make scripts executable: `chmod +x scripts/*.sh`
- [ ] 3. Run validation: `./scripts/validate-ports.sh`
- [ ] 4. Fix any issues: `./scripts/fix-ports-spec-086.sh`
- [ ] 5. Add to CI/CD (optional but recommended)
- [ ] 6. Add port validation to startup scripts
- [ ] 7. Bookmark the port matrix doc
- [ ] 8. Celebrate never having port confusion again! 🎉

---

**Bottom Line**: Port confusion is now a solved problem. The matrix is canonical, machine-readable, and automatically validated.

✅ **OPERATIONAL - USE THESE TOOLS RELIGIOUSLY**
