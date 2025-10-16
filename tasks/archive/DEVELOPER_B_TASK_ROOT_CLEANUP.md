# Developer B - Root Directory Cleanup Task

**Priority:** Medium
**Estimated Time:** 4-6 hours
**Status:** Not Started
**Date Created:** October 13, 2025

---

## 🎯 **Objective**

Clean up and organize the project root directory which currently has **226 files** (should be <30).

---

## ⚠️ **Current Problem**

```bash
$ ls | wc -l
226
```

**Issues:**
1. **Status files everywhere:** 50+ summary/status markdown files
2. **Multiple Dockerfiles:** 14 different Dockerfile variants
3. **Multiple Makefiles:** 3 different Makefile variants
4. **Hard to find core files:** README, LICENSE buried in clutter
5. **Poor developer experience:** New developers overwhelmed

---

## ✅ **Target State**

**Root directory should have ~25-30 files:**

```
/
├── README.md                    ← Core docs
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
├── .env.sample
├── pytest.ini
├── pyproject.toml
├── package.json
├── docker-compose.yml
├── Makefile                     ← Consolidated
├── docs/                        ← Documentation
├── specs/                       ← SPECs
├── server/                      ← Backend code
├── frontend-*/                  ← Frontend apps
├── tests/                       ← Test suites
├── scripts/                     ← Utility scripts
├── docker/                      ← NEW: All Dockerfiles
├── deployment/                  ← NEW: K8s, configs
└── archive/                     ← NEW: Old status files
```

---

## 📋 **Task Breakdown**

### **Phase 1: Audit & Categorize** (1 hour)

#### **Task 1.1: List All Files**
```bash
ls -1 > ROOT_FILES_BEFORE.txt
cat ROOT_FILES_BEFORE.txt | wc -l  # Should show 226
```

#### **Task 1.2: Categorize Files**
Create `ROOT_FILE_AUDIT.md` with categories:

**Categories:**
- **Keep in Root** (core files like README, LICENSE)
- **Move to docs/archive/** (status files, summaries)
- **Move to docker/** (Dockerfiles)
- **Move to deployment/** (K8s, configs)
- **Delete** (duplicates, obsolete)

**Example categorization:**
```markdown
## Keep in Root
- README.md
- LICENSE
- CONTRIBUTING.md
- CHANGELOG.md
- .gitignore
- pytest.ini
- pyproject.toml

## Move to docs/archive/session-summaries/
- DAY_3_COMPLETE_STACK.md
- DAY_4_FINAL_SUCCESS.md
- PHASE1_SESSION_SUMMARY.md
- API_CONTAINER_FIX_SUMMARY.md
... (50+ files)

## Move to docker/
- Dockerfile
- Dockerfile.api
- Dockerfile.ui
... (14 files)

## Move to deployment/
- docker-compose.yml → deployment/docker-compose.dev.yml
- kubernetes configs (if any)

## Consolidate/Delete
- Makefile + Makefile.compose + Makefile.dev → Single Makefile
```

---

### **Phase 2: Create New Structure** (1 hour)

#### **Task 2.1: Create Directories**
```bash
# Archive directories
mkdir -p docs/archive/session-summaries
mkdir -p docs/archive/container-builds
mkdir -p docs/archive/spec-work
mkdir -p docs/archive/license-work

# Deployment directories
mkdir -p docker/api
mkdir -p docker/ui
mkdir -p docker/services
mkdir -p deployment/dev
mkdir -p deployment/staging
mkdir -p deployment/prod
```

#### **Task 2.2: Create README files**
```bash
# docs/archive/README.md
# docker/README.md
# deployment/README.md
```

**Content for `docs/archive/README.md`:**
```markdown
# Archived Documentation

This directory contains historical documentation and status files.

## Directory Structure

- **session-summaries/**: Daily/phase completion summaries
- **container-builds/**: Container build status and fixes
- **spec-work/**: Historical SPEC analysis and cleanup
- **license-work/**: Licensing compliance work

## Note

These files are kept for historical reference but are no longer actively maintained.
```

---

### **Phase 3: Move Files** (2-3 hours)

#### **Task 3.1: Move Status/Summary Files**
```bash
# Session summaries
mv DAY_3_*.md docs/archive/session-summaries/
mv DAY_4_*.md docs/archive/session-summaries/
mv PHASE*.md docs/archive/session-summaries/
mv *SUMMARY*.md docs/archive/session-summaries/
mv *PROGRESS*.md docs/archive/session-summaries/
mv EXECUTIVE_SUMMARY.md docs/archive/session-summaries/

# Container/build related
mv API_CONTAINER_*.md docs/archive/container-builds/
mv CONTAINER_BUILD_*.md docs/archive/container-builds/
mv *_STACK.md docs/archive/container-builds/

# SPEC work
mv ACCURATE_SPEC_ANALYSIS.md docs/archive/spec-work/
mv CLEANUP_STATUS_*.md docs/archive/spec-work/
mv LEGACY_NAMING_CLEANUP.md docs/archive/spec-work/

# License work
mv LICENSE-MATRIX.md docs/archive/license-work/
mv COMPLIANCE*.md docs/archive/license-work/
mv ENFORCEMENT_POLICY.md docs/archive/license-work/
mv *LICENSE*.md docs/archive/license-work/  # Except LICENSE itself!
```

#### **Task 3.2: Move Dockerfiles**
```bash
# API Dockerfiles
mv Dockerfile.api docker/api/Dockerfile
mv Dockerfile.minimal docker/api/Dockerfile.minimal

# UI Dockerfiles
mv Dockerfile.ui docker/ui/Dockerfile
mv Dockerfile.ui.simple docker/ui/Dockerfile.simple

# Service Dockerfiles
mv Dockerfile.em docker/services/Dockerfile.em
mv Dockerfile.mcp docker/services/Dockerfile.mcp
mv Dockerfile.mem0 docker/services/Dockerfile.mem0
mv Dockerfile.postgres docker/services/Dockerfile.postgres
mv Dockerfile.pgbouncer docker/services/Dockerfile.pgbouncer

# Keep main Dockerfile in root (for primary build)
# Dockerfile stays in root
```

#### **Task 3.3: Consolidate Makefiles**
```bash
# Merge Makefile.compose and Makefile.dev into Makefile
# Create backup first
cp Makefile Makefile.backup

# Manually merge (requires review)
# Add sections:
# - make dev (from Makefile.dev)
# - make compose-up/down (from Makefile.compose)
# - make test, lint, format
# - make docker-build

# After merge, remove old ones
rm Makefile.compose Makefile.dev Makefile.backup
```

#### **Task 3.4: Move Deployment Configs**
```bash
# If you find docker-compose variants
mv docker-compose.dev.yml deployment/dev/
mv docker-compose.staging.yml deployment/staging/  # if exists
mv docker-compose.prod.yml deployment/prod/  # if exists

# Keep main docker-compose.yml in root or deployment/
# Decision: Keep in root for convenience
```

---

### **Phase 4: Update References** (1-2 hours)

#### **Task 4.1: Update Documentation**
```bash
# Update README.md with new structure
# Update CONTRIBUTING.md with new paths
# Update any scripts that reference moved files
```

**Files to check for references:**
- `README.md`
- `CONTRIBUTING.md`
- `docs/*.md`
- `scripts/*.sh`
- `.github/workflows/*.yml`
- `Makefile`

#### **Task 4.2: Update Build Scripts**
```bash
# Search for Dockerfile references
grep -r "Dockerfile\." .github/ scripts/ Makefile

# Update to use new paths:
# docker build -f docker/api/Dockerfile ...
# docker build -f docker/ui/Dockerfile ...
```

#### **Task 4.3: Test Builds**
```bash
# Test that all builds still work
docker build -f docker/api/Dockerfile -t test-api .
docker build -f docker/ui/Dockerfile -t test-ui .

# Test compose
docker-compose up --build -d
docker-compose down
```

---

### **Phase 5: Document & Validate** (1 hour)

#### **Task 5.1: Create Root Directory Guide**
```bash
# Create ROOT_DIRECTORY_STRUCTURE.md
```

**Content:**
```markdown
# Root Directory Structure

## Core Files (Keep in Root)

| File | Purpose |
|------|---------|
| README.md | Project overview |
| LICENSE | Open source license |
| CONTRIBUTING.md | Contribution guidelines |
| CHANGELOG.md | Version history |
| .gitignore | Git ignore rules |
| .env.sample | Environment template |
| pytest.ini | Test configuration |
| pyproject.toml | Python project config |
| docker-compose.yml | Local dev environment |
| Makefile | Build automation |

## Directory Structure

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `docs/` | Documentation | Guides, architecture, API docs |
| `docs/archive/` | Historical docs | Old summaries, status files |
| `specs/` | SPEC documents | Feature specifications |
| `server/` | Backend code | FastAPI application |
| `frontend-*/` | Frontend apps | Next.js applications |
| `tests/` | Test suites | Pytest, Playwright tests |
| `scripts/` | Utilities | Build, deploy, maintenance scripts |
| `docker/` | Docker configs | Dockerfiles organized by service |
| `deployment/` | Deploy configs | K8s, compose files by environment |
| `alembic/` | DB migrations | Database version control |

## Docker Structure

```
docker/
├── api/
│   ├── Dockerfile           # Production API
│   └── Dockerfile.minimal   # Minimal build
├── ui/
│   ├── Dockerfile           # Production UI
│   └── Dockerfile.simple    # Simple build
└── services/
    ├── Dockerfile.postgres
    ├── Dockerfile.redis
    └── ...
```

## Rules

1. **No status/summary files in root** - Use docs/archive/
2. **No multiple Dockerfile variants in root** - Use docker/ subdirs
3. **One Makefile** - Consolidated build commands
4. **Core files only** - If not essential, move to subdirectory
```

#### **Task 5.2: Validate**
```bash
# Count files in root
ls -1 | wc -l  # Should be < 30

# Create after/before comparison
ls -1 > ROOT_FILES_AFTER.txt
diff ROOT_FILES_BEFORE.txt ROOT_FILES_AFTER.txt > ROOT_CLEANUP_DIFF.txt

# Verify builds
make test
make docker-build  # or equivalent
```

#### **Task 5.3: Update README**
Add section to README.md:
```markdown
## Project Structure

See [ROOT_DIRECTORY_STRUCTURE.md](./ROOT_DIRECTORY_STRUCTURE.md) for detailed directory organization.

Quick navigation:
- 📖 **Documentation**: [`docs/`](./docs/)
- 📋 **SPECs**: [`specs/`](./specs/)
- ⚙️ **Backend**: [`server/`](./server/)
- 🎨 **Frontend**: [`frontend-nextjs-customer/`](./frontend-nextjs-customer/)
- 🧪 **Tests**: [`tests/`](./tests/)
- 🐳 **Docker**: [`docker/`](./docker/)
```

---

## ✅ **Deliverables**

When complete, you should have:

- [ ] Root directory with < 30 files
- [ ] `ROOT_FILE_AUDIT.md` - Categorization of all files
- [ ] `ROOT_CLEANUP_DIFF.txt` - Before/after comparison
- [ ] `ROOT_DIRECTORY_STRUCTURE.md` - New structure documentation
- [ ] `docs/archive/` - Organized historical files
- [ ] `docker/` - Organized Dockerfiles
- [ ] `deployment/` - Deployment configurations
- [ ] Updated README.md with structure overview
- [ ] All builds verified working
- [ ] No broken references

---

## 🚨 **Important Notes**

### **Before Moving Files:**
1. **Check git status** - Don't move uncommitted work
2. **Backup** - Create branch: `git checkout -b cleanup/root-directory`
3. **Search for references** - `grep -r "filename" .`

### **Don't Delete:**
- `.git/` directory
- `node_modules/` (in .gitignore)
- `.venv/` or virtual environments
- Any active development files

### **Git Best Practices:**
```bash
# Work on branch
git checkout -b cleanup/root-directory

# Commit in logical chunks
git add docs/archive/
git commit -m "docs: Move session summaries to archive"

git add docker/
git commit -m "chore: Organize Dockerfiles into docker/ directory"

# Final commit
git commit -m "chore: Complete root directory cleanup

- Reduced root files from 226 to ~25
- Organized historical docs into docs/archive/
- Moved Dockerfiles to docker/ subdirectories
- Consolidated Makefiles
- Updated all references
- Verified all builds working

Refs: DEVELOPER_B_TASK_ROOT_CLEANUP.md"
```

---

## 📊 **Success Metrics**

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| Root files | 226 | < 30 | TBD |
| Dockerfiles in root | 14 | 1 | TBD |
| Makefiles | 3 | 1 | TBD |
| Status files in root | 50+ | 0 | TBD |
| Build time | Baseline | Same | TBD |

---

## 🆘 **If You Get Stuck**

### **Common Issues:**

**Q: File has references I can't find?**
```bash
# Search everywhere
grep -r "filename" . --exclude-dir=node_modules --exclude-dir=.git
```

**Q: Build breaks after moving Dockerfile?**
```bash
# Check docker-compose.yml, Makefile, .github/workflows/
# Update build context or dockerfile path
```

**Q: Too many files to categorize?**
```bash
# Start with obvious ones:
# 1. Move all DAY_*.md first
# 2. Move all *SUMMARY*.md next
# 3. Move all Dockerfile.*
# 4. Review remaining files
```

---

## 🎯 **Tips for Success**

1. **Work incrementally** - Move one category at a time
2. **Test frequently** - Run builds after each major move
3. **Commit often** - Small commits are easier to revert
4. **Document decisions** - Note why files were moved/kept
5. **Ask for review** - Get feedback before final commit

---

**Status:** 📋 Ready to Start
**Priority:** Medium
**Owner:** Developer B
**Timeline:** Thursday-Friday, Oct 16-17

---

**Good luck, Developer B! This will greatly improve the project! 🚀**
