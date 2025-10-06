# 🚀 Day 1: Build the Safety Net
**Date:** Tomorrow (October 6, 2025)
**Goal:** Lock down current working state and create automatic regression guards
**Time Estimate:** 3-4 hours

---

## 📋 Morning Session (2 hours)

### ✅ Task 1: Tag Current State (10 min)

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Tag the current state
git tag -a v0.9-pre-phase1 -m "Stable baseline before Phase 1 execution"
git push origin v0.9-pre-phase1

# Verify tag exists
git tag -l "v0.9*"
```

**Completion criteria:** Tag `v0.9-pre-phase1` exists and is pushed

---

### ✅ Task 2: Document Current Working State (60 min)

Fill in all `[DOCUMENT TOMORROW]` placeholders in `WORKING_STATE.md`:

#### 2.1 Test Apple Container CLI (15 min)
```bash
# Try to start the stack
./scripts/nv-stack-start.sh

# Wait 30 seconds
sleep 30

# Document what happened in WORKING_STATE.md
# - Did it start? (Yes/No)
# - Any errors? (Copy error messages)
```

#### 2.2 Test Database Connection (10 min)
```bash
# Test PostgreSQL
psql -h localhost -U nina -d ninaivalaigal_dev -c "SELECT 1"

# If password required:
PGPASSWORD=dev_password_change_in_production psql -h localhost -U nina -d ninaivalaigal_dev -c "SELECT 1"

# Document result in WORKING_STATE.md
```

#### 2.3 Test Redis Connection (5 min)
```bash
# Test Redis
redis-cli -h localhost -p 6379 ping

# Document result in WORKING_STATE.md
```

#### 2.4 Check Database Schema (15 min)
```bash
# Check migration status
cd server
alembic current

# List tables
psql -h localhost -U nina -d ninaivalaigal_dev -c "\dt"

# Check extensions
psql -h localhost -U nina -d ninaivalaigal_dev -c "\dx"

# Document results in WORKING_STATE.md:
# - Current migration version
# - Number of tables
# - Apache AGE: Installed? (Yes/No)
# - pgvector: Installed? (Yes/No)
```

#### 2.5 Test API Health (10 min)
```bash
# Try to access API
curl http://localhost:13370/health

# If API isn't running, that's OK - document it
# Document result in WORKING_STATE.md
```

#### 2.6 Document PgBouncer Status (5 min)
```bash
# Check if PgBouncer is running
docker ps | grep pgbouncer
# OR
container ps | grep pgbouncer

# Try to connect through PgBouncer
psql -h localhost -U nina -p 6432 -d ninaivalaigal_dev -c "SELECT 1"

# Document in WORKING_STATE.md:
# - PgBouncer running? (Yes/No)
# - Can connect? (Yes/No)
# - Using bypass? (Yes/No)
```

**Completion criteria:** All `[DOCUMENT TOMORROW]` placeholders in `WORKING_STATE.md` are filled with actual data

---

### ✅ Task 3: Run Smoke Tests (30 min)

#### 3.1 Install pytest (if needed)
```bash
# Activate nina conda environment
conda activate nina

# Install pytest
pip install pytest pytest-timeout requests
```

#### 3.2 Run smoke tests
```bash
# Run smoke tests
pytest tests/smoke/test_critical_infrastructure.py -v

# Expected results:
# - Some tests will pass (e.g., database connection)
# - Some tests will be skipped (e.g., API tests if API not running)
# - Goal: 0 failures (skips are OK)
```

#### 3.3 Fix any failures
```bash
# If database test fails:
# - Start database: ./scripts/nv-db-start.sh

# If Redis test fails:
# - Start Redis: ./scripts/nv-redis-start.sh (if it exists)
# - OR start full stack: ./scripts/nv-stack-start.sh

# Re-run until no failures:
pytest tests/smoke/test_critical_infrastructure.py -v
```

**Completion criteria:** Smoke tests pass (0 failures, skips are OK)

---

## ☕ Break (15 min)

Take a break. You've made good progress!

---

## 📋 Afternoon Session (1.5 hours)

### ✅ Task 4: Verify Pre-Commit Hook (10 min)

```bash
# Check if pre-commit is installed
which pre-commit

# If not installed:
pip install pre-commit

# Install hooks
pre-commit install

# Test it works
echo "test" >> README.md
git add README.md
git commit -m "Test pre-commit hook"

# Pre-commit should run automatically
# If it runs, good! Then reset:
git reset HEAD~1
git checkout README.md
```

**Completion criteria:** Pre-commit hook runs automatically on commit

---

### ✅ Task 5: Verify Pre-Push Hook (10 min)

```bash
# Check if pre-push hook exists and is executable
ls -la .git/hooks/pre-push

# Should show:
# -rwxr-xr-x ... .git/hooks/pre-push

# If not executable:
chmod +x .git/hooks/pre-push

# Test it (don't worry, we'll use a fake remote)
# Create a test commit
echo "# Test" > TEST_FILE.md
git add TEST_FILE.md
git commit -m "Test pre-push hook"

# Try to push (will fail but hook should run)
# If smoke tests pass, hook allows push
# If smoke tests fail, hook blocks push

# Clean up test
git reset HEAD~1
rm TEST_FILE.md
```

**Completion criteria:** Pre-push hook runs and checks smoke tests

---

### ✅ Task 6: Create Rollback Safety (20 min)

```bash
# Create a "safe rollback" script
cat > scripts/rollback-to-baseline.sh << 'EOF'
#!/bin/bash
# Emergency rollback to v0.9-pre-phase1 baseline

echo "⚠️  WARNING: This will reset to baseline (v0.9-pre-phase1)"
echo "Any uncommitted changes will be LOST"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo "📦 Stashing any uncommitted changes..."
git stash save "emergency-stash-$(date +%Y%m%d-%H%M%S)"

echo "🔄 Resetting to baseline..."
git reset --hard v0.9-pre-phase1

echo "✅ Rolled back to v0.9-pre-phase1"
echo "📋 Check WORKING_STATE.md for baseline state"
echo ""
echo "If you had uncommitted changes, they're in:"
git stash list | head -1
EOF

chmod +x scripts/rollback-to-baseline.sh

# Test (dry run)
./scripts/rollback-to-baseline.sh
# Type "no" to cancel
```

**Completion criteria:** Rollback script exists and is tested

---

### ✅ Task 7: Create Daily Progress Tracker (15 min)

```bash
cat > DAILY_PROGRESS.md << 'EOF'
# Daily Progress Tracker
Start Date: October 6, 2025

## 📊 Phase 1: Operational Hardening (Weeks 1-4)

### Week 1: Hybrid Runtime + Testing
- [ ] Day 1 (Oct 6): Safety net complete
- [ ] Day 2 (Oct 7): Document cleanup
- [ ] Day 3 (Oct 8): Apple CLI reliable startup
- [ ] Day 4 (Oct 9): PgBouncer fix/bypass
- [ ] Day 5 (Oct 10): First 5 tests passing

### Regression Count: 0
[Log any regressions here]

## 📝 Daily Notes

### October 6, 2025 (Day 1)
**Goal:** Build safety net
**Completed:**
- [ ] Tagged v0.9-pre-phase1
- [ ] Documented working state
- [ ] Smoke tests passing
- [ ] Pre-push hook active

**Blockers:** [None yet]
**Tomorrow:** Document cleanup
EOF
```

**Completion criteria:** `DAILY_PROGRESS.md` created

---

### ✅ Task 8: Commit Safety Net (15 min)

```bash
# Stage all safety net files
git add tests/smoke/test_critical_infrastructure.py
git add .git/hooks/pre-push
git add WORKING_STATE.md
git add DOCUMENT_CLEANUP_PLAN.md
git add DAY_1_CHECKLIST.md
git add DAILY_PROGRESS.md
git add scripts/rollback-to-baseline.sh

# Commit (pre-commit hook will run automatically)
git commit -m "🔒 Phase 1 Day 1: Safety net complete

- Add smoke tests for critical infrastructure
- Add pre-push hook to prevent regressions
- Document current working state
- Create rollback safety script
- Add daily progress tracker

All safety measures in place before Phase 1 execution."

# Pre-push hook will run when you push:
git push origin main
```

**Completion criteria:** Safety net committed and pushed

---

## 🎯 End-of-Day Validation

Run this checklist before declaring Day 1 complete:

```bash
# 1. Smoke tests pass
pytest tests/smoke/ -v
echo "✅ Smoke tests: PASS"

# 2. Pre-push hook active
ls -la .git/hooks/pre-push | grep "x"
echo "✅ Pre-push hook: ACTIVE"

# 3. Working state documented
grep -q "\[DOCUMENT TOMORROW\]" WORKING_STATE.md
if [ $? -eq 0 ]; then
    echo "❌ Working state: INCOMPLETE (still has placeholders)"
else
    echo "✅ Working state: DOCUMENTED"
fi

# 4. Baseline tagged
git tag -l | grep "v0.9-pre-phase1"
echo "✅ Baseline: TAGGED"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Day 1 Complete! Ready for Phase 1."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

---

## 📝 If Something Goes Wrong

### Database won't connect:
```bash
# Check if database is running
ps aux | grep postgres

# Try starting database
./scripts/nv-db-start.sh

# If Apple CLI script exists:
./scripts/nv-stack-start.sh
```

### Redis won't connect:
```bash
# Check if Redis is running
ps aux | grep redis

# Try starting Redis
redis-server &
```

### Smoke tests fail:
```bash
# Don't panic - this is expected on first run
# Document the failures in WORKING_STATE.md
# Under "Known Broken Items"

# Example:
echo "- [ ] Smoke test: test_database_accessible - FAIL (database not running)" >> WORKING_STATE.md
```

### Pre-commit hook fails:
```bash
# See what failed
git commit -m "test"

# Common issues:
# - Black formatting: Run `black .`
# - flake8 errors: Run `flake8 server/`
# - isort: Run `isort .`

# Fix and retry
```

---

## 🎯 Success Criteria (All Must Be Green)

✅ **Smoke test passes 100%** (or skips are documented)
✅ **Pre-push hook active** (runs on `git push`)
✅ **Working state documented** (no `[DOCUMENT TOMORROW]` placeholders)
✅ **Baseline tagged** (`v0.9-pre-phase1` exists)
✅ **Changes committed and pushed**

**When all are green: Day 1 COMPLETE → Proceed to Day 2 (Document Cleanup)**

---

## 💬 Notes

- **Don't rush** - Take breaks
- **Document honestly** - If something is broken, write it down
- **Ask for help** - If stuck, that's OK
- **Celebrate progress** - Even small wins count

**Remember:** The goal is SAFETY, not speed. We're preventing future regressions.
