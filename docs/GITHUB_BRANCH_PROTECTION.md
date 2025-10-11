# GitHub Branch Protection Rules

**Last Updated:** 2025-10-11
**Purpose:** Enforce Phase-5 quality standards via GitHub settings
**Applies To:** `main` branch

---

## 🛡️ Overview

Branch protection rules prevent direct pushes to `main` and enforce code review + CI/CD checks before merging. This ensures the `v5.0-frontend-split-audit-final` baseline stays pristine.

---

## 🔧 Configuration Steps

### **1. Navigate to Branch Protection**
```
GitHub Repo → Settings → Branches → Add rule
Branch name pattern: main
```

---

## ✅ Required Settings

### **Protect Matching Branches**

#### ✅ **Require a pull request before merging**
- [x] Require approvals: **1**
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require review from Code Owners *(if CODEOWNERS file exists)*
- [ ] ~~Require approval of the most recent reviewable push~~ *(Optional)*
- [x] Require conversation resolution before merging

**Rationale:** No direct pushes to `main`. All changes via reviewed PRs.

---

#### ✅ **Require status checks to pass before merging**
- [x] Require branches to be up to date before merging

**Required status checks:**
1. `Smoke Tests` *(from pre-push hook)*
2. `SPEC Structure Validation` *(from .github/workflows/spec-validation.yml)*
3. `Lint` *(if CI/CD workflow added)*
4. `Type Check` *(if CI/CD workflow added)*

**Rationale:** Automated verification prevents regressions.

---

#### ✅ **Require conversation resolution before merging**
- [x] All review comments must be resolved

**Rationale:** No unresolved feedback in merged code.

---

#### ✅ **Require signed commits**
- [ ] ~~Require signed commits~~ *(Optional - enable if using GPG signing)*

**Rationale:** Enhanced security, but optional for internal teams.

---

#### ✅ **Require linear history**
- [x] Require linear history *(prevents merge commits)*

**Rationale:** Clean rebase-based history. No "Merge branch X into Y" noise.

---

#### ✅ **Include administrators**
- [x] Enforce all configured restrictions for administrators

**Rationale:** Even lead developers follow the rules (no shortcuts).

---

#### ✅ **Restrict who can push to matching branches**
- [ ] ~~Restrict pushes~~ *(Leave unchecked for internal team)*

**Rationale:** Team is trusted, but PRs are still required.

---

#### ✅ **Allow force pushes**
- [ ] Allow force pushes: **Disabled**

**Rationale:** Force pushing to `main` breaks audit trail and tags.

---

#### ✅ **Allow deletions**
- [ ] Allow deletions: **Disabled**

**Rationale:** `main` branch should never be deleted.

---

## 🚀 Additional Recommendations

### **Create `CODEOWNERS` File**
```bash
# .github/CODEOWNERS
# Phase-5 Frontend Split Ownership

# Root configuration
/package.json           @Arunosaur
/turbo.json             @Arunosaur
/.github/workflows/     @Arunosaur

# Frontend workspaces
/frontend-shared/                    @DeveloperA
/frontend-nextjs-customer/           @DeveloperB
/frontend-nextjs-admin/              @Arunosaur

# SPEC governance
/specs/                              @Arunosaur
/specs/121-frontend-shared-library/  @DeveloperA
/specs/122-customer-frontend-rollout/ @DeveloperB

# Infrastructure
/scripts/                            @Arunosaur
/tests/smoke/                        @Arunosaur
```

**Benefits:**
- Auto-assigns reviewers based on file changes
- Enforces expertise-based reviews
- Prevents accidental changes to critical files

---

### **PR Template**
Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## SPEC Reference
- **SPEC:** [SPEC-XXX](link-to-spec)
- **Phase:** Phase-5 Frontend Split
- **Status:** Draft | Ready for Review

## Summary
<!-- Brief description of changes -->

## Changes
- [ ] Frontend components
- [ ] Backend API routes
- [ ] Database migrations
- [ ] Tests added/updated
- [ ] Documentation updated

## Testing
<!-- How was this tested? -->
- [ ] Smoke tests passing
- [ ] Unit tests passing
- [ ] Manual testing performed

## Checklist
- [ ] SPEC requirements met
- [ ] Pre-commit hooks passing
- [ ] No merge conflicts with main
- [ ] Ready for review

## Screenshots (if UI changes)
<!-- Add screenshots here -->
```

---

## 🔐 Required Status Checks Configuration

### **1. Smoke Tests Check**
Already configured in `.git/hooks/pre-push`:
```bash
#!/bin/bash
pytest tests/smoke/ -v || exit 1
```

**GitHub Action equivalent** (optional):
```yaml
# .github/workflows/smoke-tests.yml
name: Smoke Tests

on:
  pull_request:
    branches: [main]

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run smoke tests
        run: pytest tests/smoke/ -v
```

---

### **2. SPEC Validation Check**
Already configured in `.github/workflows/spec-validation.yml`
- Runs on push/PR to `specs/**`
- Validates numbering continuity
- Checks README.md existence

---

### **3. Lint & Type Check** (Recommended)
```yaml
# .github/workflows/lint.yml
name: Lint & Type Check

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm install
      - run: npm run lint
      - run: npm run type-check
```

---

## 📊 Merge Strategies

### **Allowed Strategies**
- ✅ **Squash and merge** (preferred for feature branches)
- ✅ **Rebase and merge** (for clean history)
- ❌ **Merge commit** (disabled for linear history)

### **Squash Merge Settings**
```
GitHub Repo → Settings → General → Pull Requests
- [x] Allow squash merging
    - Default commit message: Pull request title and description
    - [x] Default to pull request title for commit message
```

---

## 🎯 Enforcement Timeline

### **Phase 0: Immediate (Today)**
- [x] Enable "Require pull request before merging"
- [x] Enable "Require linear history"
- [x] Disable force pushes
- [x] Disable deletions

### **Phase 1: Monday (Oct 13)**
- [ ] Add "Require status checks" (smoke tests)
- [ ] Add CODEOWNERS file
- [ ] Create PR template

### **Phase 2: Week 2**
- [ ] Enable lint/type-check CI checks
- [ ] Add frontend-specific checks (Lighthouse, bundle size)

---

## 🆘 Override Procedures

### **Emergency Hotfix Process**
If production is down and branch protection blocks urgent fix:

1. **Don't disable protection** ❌
2. **Create hotfix branch** ✅
   ```bash
   git checkout -b hotfix/critical-production-issue
   # Make fix
   git push origin hotfix/critical-production-issue
   ```
3. **Fast-track PR review** (same-day approval)
4. **Merge via squash** (maintains history)
5. **Document in postmortem**

---

## 📋 Checklist for GitHub Admin

Use this checklist when configuring branch protection:

```
Branch Protection: main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pull Request Requirements:
☐ Require pull request before merging
  ☐ Required approvals: 1
  ☐ Dismiss stale approvals
  ☐ Require conversation resolution

Status Checks:
☐ Require status checks to pass
  ☐ Require branches to be up to date
  ☐ smoke-tests
  ☐ spec-validation

History:
☐ Require linear history (rebase)

Protection:
☐ Include administrators
☐ Disable force pushes
☐ Disable deletions

Optional:
☐ Require signed commits (GPG)
☐ Restrict pushes (for public repos)
```

---

## 🔗 Related Documentation

- [DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md) - Developer workflow
- [SPEC_INDEX.md](../specs/SPEC_INDEX.md) - SPEC governance
- [PHASE_5_KICKOFF.md](../specs/PHASE_SUMMARIES/PHASE_5_KICKOFF.md) - Execution plan

---

**Questions?** See [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
