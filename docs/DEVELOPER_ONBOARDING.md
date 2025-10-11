# Developer Onboarding: Phase-5 Frontend Split

**Last Updated:** 2025-10-11
**Phase:** Phase-5 Execution Excellence
**Team Size:** 2 developers (same computer)

---

## 🎯 Welcome to Ninaivalaigal

You're joining at an exciting time! We're in **Phase-5: Frontend Split**, transforming our monolithic frontend into a modern Turborepo workspace with:
- Customer-facing Next.js app
- Internal admin Next.js app
- Shared component library

**Your mission:** Help deliver production-grade frontend architecture in 9 weeks.

---

## 🚀 Quick Start (< 5 Minutes)

### **1. Verify Environment**
```bash
# Navigate to workspace (already exists)
cd /Users/swami/WorkSpace/ninaivalaigal

# Activate conda environment
conda activate nina

# Verify tools
node --version    # Should be v18+
npm --version     # Should be 9+
python --version  # Should be 3.11+
```

### **2. Check Container Stack**
```bash
# Verify containers are running
container list | grep ninaivalaigal-dev

# Expected output:
# ninaivalaigal-dev-db
# ninaivalaigal-dev-pgbouncer
# ninaivalaigal-dev-redis
# ninaivalaigal-dev-api
```

### **3. Pull Latest Code**
```bash
# Get latest from main
git checkout main
git pull origin main

# Verify you're on baseline tag
git describe --tags
# Should show: v5.0-frontend-split-audit-final
```

### **4. Create Your Feature Branch**
```bash
# SPEC-122 example (customer app)
git checkout -b feature/122-customer-app-baseline

# Push to remote (sets up tracking)
git push -u origin feature/122-customer-app-baseline
```

✅ **You're ready to code!**

---

## 📋 Your First Assignment

### **SPEC-122: Customer Frontend Baseline**

**Goal:** Bootstrap the customer-facing Next.js application

**Location:** `frontend-nextjs-customer/`

**Key Tasks:**
1. Initialize Next.js 15 with App Router
2. Configure TypeScript strict mode
3. Set up basic routing (`/`, `/login`, `/dashboard`)
4. Import shared components from `frontend-shared`
5. Create customer-specific components (MemoryCard, SearchBar)

**Dependencies:**
- ✅ Waits for SPEC-121 (`frontend-shared`) to be merged
- ✅ References SPEC-124 (Turborepo config)

**Deliverable:** Customer app running at `http://localhost:3000`

---

## 🛠️ Development Workflow

### **Daily Routine**
```bash
# Morning: Sync with main
git fetch origin
git rebase origin/main

# Work on your feature
# ... make changes ...

# Run checks before committing
npm run lint
npm run type-check
pytest tests/smoke/

# Commit with SPEC reference
git add .
git commit -m "feat(SPEC-122): Initialize customer app routing"

# Push to your branch
git push origin feature/122-customer-app-baseline

# Evening: Open/update draft PR
gh pr create --draft --title "WIP: SPEC-122 Customer App Baseline"
```

### **Commit Message Convention**
```
feat(SPEC-XXX): Add new feature
fix(SPEC-XXX): Fix bug
docs(SPEC-XXX): Update documentation
test(SPEC-XXX): Add tests
chore(SPEC-XXX): Tooling/config changes

Examples:
feat(SPEC-122): Initialize Next.js customer app
fix(SPEC-121): Export Button component types
docs(SPEC-124): Add Turborepo architecture diagram
```

---

## 🔀 Coordination Rules (Same Computer)

### **File Ownership During Development**

| Directory | Owner | Status |
|-----------|-------|--------|
| `frontend-shared/` | Developer A | Active development |
| `frontend-nextjs-customer/` | Developer B (You?) | Active development |
| `frontend-nextjs-admin/` | Reserved | Future |
| `package.json` (root) | Coordinate | Notify before touching |
| `turbo.json` | Coordinate | Notify before touching |
| `.github/workflows/` | Lead only | No direct edits |

### **Communication Protocol**
Before editing shared files, quick check:
```
You: "About to add 'frontend-nextjs-customer' to turbo.json workspaces"
Lead: "Go ahead, I'm not touching it"
```

### **No Merge Conflicts Rule**
Since you're on the same computer:
1. ✅ Work in different directories
2. ✅ Rebase daily (not merge)
3. ✅ Push feature branches continuously
4. ✅ Communicate before touching root files

---

## 🧪 Testing Requirements

### **Before Every Commit**
```bash
# 1. Smoke tests MUST pass
pytest tests/smoke/ -v

# 2. Linting MUST pass
npm run lint

# 3. Type checking MUST pass
npm run type-check
```

### **Pre-Push Hook Will Run**
The git hook automatically runs smoke tests. If they fail:
- ❌ Push is blocked
- ✅ Fix the issue (don't use `--no-verify`)

### **Your Tests**
Add tests for your features in:
```
frontend-nextjs-customer/
├── __tests__/
│   ├── components/
│   └── pages/
```

---

## 📚 Key Resources

### **SPECs (Your Bible)**
- **SPEC-121:** [frontend-shared library](../specs/121-frontend-shared-library/README.md)
- **SPEC-122:** [customer frontend](../specs/122-customer-frontend-rollout/README.md)
- **SPEC-124:** [Turborepo CI/CD](../specs/124-unified-workspace-cicd/README.md)

### **Phase Documents**
- [SPEC_INDEX.md](../specs/SPEC_INDEX.md) - Master index
- [PHASE_5_KICKOFF.md](../specs/PHASE_SUMMARIES/PHASE_5_KICKOFF.md) - 9-week plan
- [FRONTEND_SPLIT_GAP_ANALYSIS.md](../specs/PHASE_SUMMARIES/FRONTEND_SPLIT_GAP_ANALYSIS.md) - Audit baseline

### **Architectural Docs**
- [CONTAINER_ARCHITECTURE.md](CONTAINER_ARCHITECTURE.md) - Apple Container CLI setup
- [PORT_ENFORCEMENT_SYSTEM.md](PORT_ENFORCEMENT_SYSTEM.md) - Port standards

---

## 🐛 Common Issues & Solutions

### **Issue: `npm install` fails**
```bash
# Solution: Clean install
rm -rf node_modules package-lock.json
npm install
```

### **Issue: Smoke tests fail on push**
```bash
# Check container status
container list | grep ninaivalaigal-dev

# Restart if needed
./scripts/ninaivalaigal-dev-stack-start.sh

# Re-run tests
pytest tests/smoke/ -v
```

### **Issue: "Container not found" in tests**
```bash
# Database or PgBouncer not running
container list

# Restart full stack
./scripts/ninaivalaigal-dev-stack-start.sh
```

### **Issue: Git rebase conflicts**
```bash
# If conflicts during rebase
git status  # See which files conflict

# Edit conflicting files
code <conflicted-file>

# Mark as resolved
git add <conflicted-file>
git rebase --continue
```

---

## 🎯 Success Criteria

### **Week 1 Goals**
- [ ] Feature branch created and pushed
- [ ] Draft PR opened
- [ ] Basic Next.js app running
- [ ] First component imported from `frontend-shared`
- [ ] Smoke tests passing

### **Week 2 Goals**
- [ ] All customer pages scaffolded
- [ ] Component library integrated
- [ ] TypeScript types aligned
- [ ] PR ready for review

---

## 🆘 Getting Help

### **Technical Questions**
- Check SPEC documents first (specs/XXX-name/README.md)
- Search closed PRs on GitHub
- Ask lead developer (in person, same computer!)

### **Blockers**
If something blocks you:
1. Document the blocker (what you tried)
2. Notify lead immediately (don't wait)
3. Switch to a non-blocked task
4. Update draft PR with blocker note

### **Code Reviews**
- Mark PR as "Ready for Review" when complete
- Respond to feedback within 24 hours
- Use "Request Changes" discussions constructively

---

## 🚀 Phase-5 Vision

We're building **self-governing frontend architecture**:
- ✅ Modern Turborepo monorepo
- ✅ Shared component library (DRY principle)
- ✅ Customer + Admin separation
- ✅ Zero technical debt from day 1
- ✅ Automated testing & CI/CD

**Your contribution matters.** Every component, every test, every commit builds toward production-grade enterprise software.

**Welcome to the team!** 🎉

---

## 📝 Quick Reference Commands

```bash
# Daily sync
git fetch origin && git rebase origin/main

# Run full test suite
npm run test

# Run smoke tests only
pytest tests/smoke/ -v

# Check pre-commit hooks
pre-commit run --all-files

# Start container stack
./scripts/ninaivalaigal-dev-stack-start.sh

# Check container health
container list | grep ninaivalaigal-dev

# Phase-5 verification
make phase5-verify
```

---

**Questions?** Ask lead developer or check [SPEC_INDEX.md](../specs/SPEC_INDEX.md)
