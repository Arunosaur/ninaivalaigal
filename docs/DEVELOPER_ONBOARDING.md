# Developer Onboarding Guide

**Welcome to ninaivalaigal!** 🎉
**Last Updated:** October 12, 2025

---

## 📚 What is ninaivalaigal?

- Context-aware command capture
- Persistent memory for AI agents
- Multi-user team collaboration
- Enterprise-grade authentication

**Tech Stack:**
- **Backend:** Python 3.11+, FastAPI
- **Database:** PostgreSQL 15+ with pgvector
- **Cache:** Redis 7+
- **Frontend:** Next.js 15, TypeScript, Tailwind CSS
- **Container:** Apple Container CLI (ARM64) or Docker

---

## 🚀 Quick Setup (Mac/Linux)

### Prerequisites
```bash
# Check versions
python --version  # Need 3.11+
psql --version    # Need PostgreSQL 15+
redis-cli --version  # Need Redis 7+
node --version    # Need Node 18+
```

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ninaivalaigal.git
cd ninaivalaigal
```

### 2. Backend Setup
```bash
# Create conda environment
conda create -n nina python=3.11
conda activate nina

# Install dependencies
pip install -r server/requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Database Setup
```bash
# Start PostgreSQL (if not running)
# Mac: brew services start postgresql@15
# Linux: sudo systemctl start postgresql

# Create database
createdb ninaivalaigal

# Run migrations
cd server
alembic upgrade head
```

### 4. Redis Setup
```bash
# Start Redis
# Mac: brew services start redis
# Linux: sudo systemctl start redis

# Verify
redis-cli ping  # Should return "PONG"
```

### 5. Start Backend
```bash
# In server/ directory
python run_server.py

# Or use Makefile
make dev-api

# API will be at http://localhost:13390
```

### 6. Frontend Setup
```bash
# Customer app
cd frontend-nextjs-customer
npm install
npm run dev
# Opens at http://localhost:3000

# Admin app (optional)
cd frontend-nextjs-admin
npm install
npm run dev
# Opens at http://localhost:3001
```

---

## 🧪 Running Tests

### Backend Tests
```bash
# All tests
make test

# Specific test suites
make test-auth          # Authentication tests
make test-memory        # Memory system tests
make test-database      # Database tests

# With coverage
make test-coverage
```

### Frontend Tests
```bash
cd frontend-nextjs-customer
npm test

# E2E tests
npm run test:e2e
```

### Agentic Tests
```bash
# Auto-detect LLM (OpenAI or Ollama)
make test-agentic

# Force OpenAI
make test-agentic-openai

# Force Ollama (free)
make test-agentic-ollama
```

---

## 📁 Repository Structure

```
ninaivalaigal/
├── server/                 # Backend API
│   ├── auth.py            # Authentication logic
│   ├── memory_api.py      # Memory endpoints
│   ├── database/          # Models and operations
│   └── routers/           # FastAPI routers
├── frontend-nextjs-customer/  # Customer-facing app
│   ├── app/               # Next.js 15 app directory
│   ├── components/        # React components
│   └── contexts/          # Auth context, etc.
├── frontend-nextjs-admin/     # Admin console
├── tests/                 # Backend tests
│   ├── test_auth.py       # Auth tests
│   └── agentic/           # Agentic UI tests
├── specs/                 # Technical specifications
│   ├── 001-core-memory-system/
│   ├── 002-user-management/
│   └── ...
├── docs/                  # Documentation
└── Makefile               # Development commands
```

---

## 🎯 Key Concepts

### 1. Memory System (SPEC-001)
- **Context:** Named recording session (e.g., "project-x")
- **Memory:** Individual captured command or data
- **Recall:** Search memories by similarity

### 2. User Management (SPEC-006)
- **Signup:** Create account (individual or organization)
- **Login:** Returns JWT token (24-hour expiry)
- **RBAC:** Role-based access control
- **Note:** SPEC-006 consolidates all user management, authentication, and signup functionality

### 3. Context Scopes (SPEC-007)
- **Personal:** Only you can access
- **Team:** Shared with team members
- **Organization:** Visible to org users

---

## 🔧 Common Tasks

### Create a New API Endpoint
```python
# server/routers/my_feature.py
from fastapi import APIRouter, Depends
from auth import get_current_user

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.get("/hello")
async def hello(current_user = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}
```

### Add Database Model
```python
# server/database/models.py
from sqlalchemy import Column, String, UUID
from database import Base

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
```

### Create Migration
```bash
cd server
alembic revision -m "Add my_table"
# Edit alembic/versions/XXX_add_my_table.py
alembic upgrade head
```

---

## 📖 Key Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview and quick start |
| `docs/JWT_TOKEN_USAGE.md` | Authentication guide |
| `docs/MIGRATION_JWT_AUTH.md` | Migration guide for JWT |
| `specs/SPEC_INDEX.md` | All technical specifications |
| `specs/001-core-memory-system/spec.md` | Memory system architecture |
| `specs/002-user-management/README.md` | Auth implementation |

---

## 🐛 Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
pg_isready

# Check credentials in .env
cat .env | grep DATABASE_URL

# Reset database
dropdb ninaivalaigal && createdb ninaivalaigal
alembic upgrade head
```

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping

# Check Redis URL in .env
cat .env | grep REDIS_URL
```

### API Server Won't Start
```bash
# Check port 13390 is not in use
lsof -i :13390

# Check Python environment
conda activate nina
python --version  # Should be 3.11+
```

### Frontend Won't Start
```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

---

## 🤝 Contributing

### Git Workflow
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Run tests
make test

# 4. Commit
git add .
git commit -m "feat: Add my feature"

# 5. Push
git push origin feature/my-feature

# 6. Create PR on GitHub
```

### Commit Message Format
```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- chore: Maintenance
```

---

## 💬 Getting Help

**Documentation:**
- Read the SPECs in `specs/` directory
- Check `docs/` for guides
- Review existing code for examples

**Questions:**
- Ask in team chat
- Create GitHub issue
- Check existing issues first

**Debugging:**
- Use `print()` statements liberally
- Check logs in terminal
- Use browser DevTools for frontend
- Use `pytest -vv` for detailed test output

---

## 🎉 You're Ready!

**Next Steps:**
1. ✅ Environment set up
2. ✅ Tests passing
3. ✅ Understand key concepts
4. 🚀 Start coding!

**Recommended First Task:**
- Read SPEC-001 (Core Memory System)
- Read SPEC-006 (User Management, Authentication & Signup)
- Run the app and try signup/login
- Create a context and store a memory
- Explore the codebase

**Welcome to the team! 🚀**

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

---

# General Developer Onboarding

This section provides a general guide for setting up the local environment and contributing to the project. For phase-specific instructions, please see the sections above.

## How to Set Up Local Environment

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Arunosaur/ninaivalaigal.git
    cd ninaivalaigal
    ```

2.  **Install dependencies:**
    This project uses a `Makefile` for common tasks.
    ```bash
    make install
    ```

3.  **Set up the database:**
    ```bash
    make db-setup
    ```

4.  **Run the application:**
    ```bash
    make run
    ```
    This will start all the required services.

## How to Contribute

1.  **Create a feature branch:**
    Follow the naming convention `feature/SPEC-XXX-description`.
    ```bash
    git checkout -b feature/your-feature-name
    ```

2.  **Make your changes.** Adhere to the coding standards and conventions in the existing codebase.

3.  **Run tests:**
    Ensure all tests pass before committing.
    ```bash
    make test
    ```

4.  **Commit your changes:**
    Follow the commit message convention outlined in this guide.
    ```bash
    git commit -m "feat(SPEC-XXX): your feature name"
    ```

5.  **Push to your branch:**
    ```bash
    git push origin feature/your-feature-name
    ```

6.  **Create a pull request.**
    Open a draft pull request early to get feedback. Mark it as "Ready for Review" when it's complete.
