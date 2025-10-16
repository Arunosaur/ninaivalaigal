# ⚙️ Developer C: Sprint Tasks
## **Backend & Infrastructure Lead**

**Sprint**: October 13-26, 2025
**Focus**: Technical Debt + ML Pipeline Foundation
**Working Directory**: `/Users/swami/WorkSpace/ninaivalaigal`

---

## 🎯 **Your Sprint Goals**

1. ✅ Resolve TD-001 (30 flake8 violations) - **PRIORITY 1**
2. ✅ Achieve 80%+ backend test coverage
3. ✅ Implement production monitoring
4. ✅ Create complete SPEC-126 (ML Pipeline)

---

## ⚠️ **CRITICAL: TD-001 Must Be Fixed First**

TD-001 is blocking pre-commit hooks. This is your **Day 1 Priority**.

---

## 📅 **Week 1: Technical Debt & Quality** (Oct 13-19)

### **Monday, Oct 13: TD-001 - Fix Flake8 Violations**
**Working on**: `main` branch
**Time**: 8 hours (allocated, likely finish in 2-3 hours)

#### **CRITICAL TASK: Fix All 30 Flake8 Violations**

- [ ] **Pull latest**
  ```bash
  git checkout main
  git pull origin main
  # CRITICAL: Fix TD-001 first thing today!
  ```

- [ ] **Run flake8 to identify violations** (15 min)
  ```bash
  flake8 --count --statistics server/ alembic/ tests/
  ```

- [ ] **Fix D103 violations (9 files)** (1 hour)
  **Issue**: Missing docstrings in public functions

  Files to fix:
  - `alembic/env_new.py` (2 violations)
  - `alembic/versions/0112_staff_management.py` (2 violations)
  - `ninaivalaigal_ci_rbac_pack/rbac/permissions.py` (5 violations)

  **Fix**: Add docstrings
  ```python
  def function_name():
      """Brief description of what function does."""
      # existing code
  ```

- [ ] **Fix B007 violations (13 files)** (1 hour)
  **Issue**: Loop variable not used (should start with underscore)

  Files to fix (examples):
  - `tests/auth/test_rate_limiting.py`
  - `tests/auth_aware/test_fixtures.py`
  - `tests/auth_aware/test_multi_user_scenarios.py`
  - Plus 10 more test files

  **Fix**: Rename unused loop vars
  ```python
  # Before
  for user in users:
      do_something()  # user not used

  # After
  for _user in users:
      do_something()
  ```

- [ ] **Fix F841 violations (8 files)** (30 min)
  **Issue**: Local variable assigned but never used

  Files to fix:
  - `tests/foundation/spec_058/test_documentation_links.py`
  - `tests/foundation/spec_063/test_agentic_core.py`
  - Plus 6 more test files

  **Fix**: Either use the variable or prefix with underscore
  ```python
  # Option 1: Use it
  result = function()
  assert result is not None

  # Option 2: Mark as intentionally unused
  _result = function()
  ```

- [ ] **Verify all violations fixed** (15 min)
  ```bash
  flake8 --count --statistics server/ alembic/ tests/
  # Should show 0 violations
  ```

- [ ] **Run full test suite** (15 min)
  ```bash
  pytest -v
  # Ensure all tests still pass
  ```

- [ ] **Commit and push** (15 min)
  ```bash
  git add -A
  git commit -m "fix(TD-001): Resolve all 30 flake8 violations

  - Add docstrings to alembic functions (D103)
  - Rename unused loop variables with _ prefix (B007)
  - Fix unused local variables (F841)

  All pre-commit hooks now pass without --no-verify

  Resolves: TD-001"

  git push origin main
  ```

- [ ] **Notify team** (5 min)
  - Post in Slack: "TD-001 resolved! All flake8 violations fixed."
  - Mention in standup tomorrow

**Remaining Time Today** (5-6 hours): Start backend testing

---

### **Monday Afternoon: Backend Testing Foundation**
**Working on**: `main` branch (continuing)
**Time**: 5 hours

#### Tasks:
- [ ] **Pull latest** (TD-001 is already pushed)
  ```bash
  git pull origin main
  # Now working on server/tests/
  ```

- [ ] **Run coverage report** (15 min)
  ```bash
  pytest --cov=server --cov-report=html --cov-report=term
  open htmlcov/index.html
  ```
  - [ ] Note current coverage percentage
  - [ ] Identify untested modules
  - [ ] Prioritize critical paths

- [ ] **Add tests for refresh token endpoints** (2 hours)
  ```
  File: server/tests/test_token_refresh.py (new file)
  ```
  ```python
  import pytest
  from datetime import datetime, timedelta

  class TestTokenRefresh:
      def test_refresh_token_success(self, client, auth_headers):
          """Test successful token refresh"""
          # Your test here

      def test_refresh_token_expired(self, client):
          """Test refresh with expired token"""
          # Your test here

      def test_refresh_token_invalid(self, client):
          """Test refresh with invalid token"""
          # Your test here

      def test_refresh_token_revoked(self, client):
          """Test refresh with revoked token"""
          # Your test here
  ```

- [ ] **Add tests for token revocation** (1.5 hours)
  ```
  File: server/tests/test_token_revocation.py (new file)
  ```
  - [ ] Test single token revocation
  - [ ] Test revoke all tokens
  - [ ] Test revoke with invalid token
  - [ ] Test revoke unauthorized

- [ ] **Add edge case tests** (1.5 hours)
  - [ ] Concurrent token refresh requests
  - [ ] Refresh token reuse detection
  - [ ] Token rotation scenarios
  - [ ] Database connection failures

**Deliverable**: 10+ new test cases, TD-001 resolved

---

### **Tuesday, Oct 14: Backend Testing Expansion**
**Working on**: `main` branch (continuing)
**Time**: 8 hours

#### Tasks:
- [ ] **Add integration tests** (4 hours)
  ```
  File: tests/integration/test_auth_flow.py (new file)
  ```
  - [ ] Test complete auth flow (signup → login → refresh → revoke)
  - [ ] Test multi-device scenario
  - [ ] Test token expiry and renewal
  - [ ] Test session management

- [ ] **Add database tests** (2 hours)
  ```
  File: tests/integration/test_database_migrations.py
  ```
  - [ ] Test migration 0114 (refresh tokens)
  - [ ] Test rollback scenario
  - [ ] Test data integrity
  - [ ] Test foreign key constraints

- [ ] **Add Redis integration tests** (2 hours)
  ```
  File: tests/integration/test_redis_cache.py (new file)
  ```
  - [ ] Test session storage in Redis
  - [ ] Test cache invalidation
  - [ ] Test Redis connection failure handling
  - [ ] Test cache TTL

**Deliverable**: Integration test suite, coverage approaching 80%

---

### **Wednesday, Oct 15: Infrastructure Hardening**
**Working on**: `main` branch
**Time**: 8 hours

#### Tasks:
- [ ] **Pull latest changes**
  ```bash
  git pull origin main
  # Working on server/health.py and monitoring today
  ```

- [ ] **Add health check endpoints** (3 hours)
  ```
  File: server/health.py (enhance existing)
  ```
  ```python
  @router.get("/health/live")
  async def liveness():
      """Kubernetes liveness probe"""
      return {"status": "alive"}

  @router.get("/health/ready")
  async def readiness():
      """Kubernetes readiness probe"""
      # Check database connection
      # Check Redis connection
      # Check critical services
      return {"status": "ready", "checks": {...}}

  @router.get("/health/detailed")
  async def detailed_health():
      """Detailed health with metrics"""
      return {
          "database": check_db(),
          "redis": check_redis(),
          "disk": check_disk(),
          "memory": check_memory(),
      }
  ```

- [ ] **Implement metrics collection** (2 hours)
  ```
  File: server/metrics.py (new file)
  ```
  - [ ] Request count by endpoint
  - [ ] Response time percentiles
  - [ ] Error rate tracking
  - [ ] Active connections
  - [ ] Database query times

- [ ] **Configure alerts** (1 hour)
  ```
  File: server/alerts.py (new file)
  ```
  - [ ] High error rate alert
  - [ ] Slow response time alert
  - [ ] Database connection alert
  - [ ] Disk space alert

- [ ] **Add readiness probes** (1 hour)
  - [ ] Test database connectivity
  - [ ] Test Redis connectivity
  - [ ] Test external service connectivity

- [ ] **Documentation** (1 hour)
  ```
  File: docs/MONITORING.md
  ```
  - [ ] How to access metrics
  - [ ] How to interpret alerts
  - [ ] Troubleshooting guide

**Deliverable**: Production-ready monitoring

**NOTE**: Mid-sprint check-in @ 2:00 PM

---

### **Thursday, Oct 16: Database Optimization**
**Working on**: `main` branch (continuing)
**Time**: 8 hours

#### Tasks:
- [ ] **Pull latest changes**
  ```bash
  git pull origin main
  # Working on alembic/ and server/database.py today
  ```

- [ ] **Analyze slow queries** (2 hours)
  ```bash
  # Enable query logging
  # Run application under load
  # Analyze pg_stat_statements
  ```
  - [ ] Identify top 10 slowest queries
  - [ ] Document findings in `/docs/PERFORMANCE_ANALYSIS.md`

- [ ] **Add missing indexes** (3 hours)
  ```
  File: alembic/versions/0115_add_performance_indexes.py (new)
  ```
  Create migration to add indexes:
  - [ ] Index on `refresh_tokens.user_id`
  - [ ] Index on `refresh_tokens.expires_at`
  - [ ] Index on `memories.created_at`
  - [ ] Index on `memories.user_id, created_at` (composite)
  - [ ] Test performance improvement

- [ ] **Optimize connection pooling** (2 hours)
  ```
  File: server/database.py
  ```
  - [ ] Configure pool size based on load
  - [ ] Add connection timeout handling
  - [ ] Add connection retry logic
  - [ ] Add pool metrics

- [ ] **Test optimization impact** (1 hour)
  ```bash
  # Run benchmark before optimization
  # Run benchmark after optimization
  # Document improvement
  ```

**Deliverable**: Optimized database performance

---

### **Friday, Oct 17: Testing & Code Review**
**Working on**: `main` branch (final day Week 1)
**Time**: 8 hours

#### Tasks:
- [ ] **Run full test suite** (2 hours)
  ```bash
  git pull origin main
  pytest -v --cov=server --cov-report=html
  # Verify all your week's work is tested
  ```

- [ ] **Verify coverage goals met** (1 hour)
  - [ ] Backend coverage > 80%
  - [ ] Critical paths > 90%
  - [ ] Document coverage report
  - [ ] Push any final changes: `git push origin main`

- [ ] **Week 1 wrap-up** (2 hours)
  - [ ] Self-review all code from this week
  - [ ] Update CHANGELOG if needed
  - [ ] Document any discovered issues
  - [ ] Prepare week 1 summary for demo

- [ ] **Code review Developer A's work** (2 hours)
  - [ ] Review E2E tests
  - [ ] Review auth-aware testing
  - [ ] Provide constructive feedback

- [ ] **Sprint demo preparation** (1 hour)
  - [ ] Prepare metrics dashboard demo
  - [ ] Prepare health check demo
  - [ ] Prepare performance improvement stats
  - [ ] Document talking points

**Deliverable**: All Week 1 work ready for merge

---

## 📅 **Week 2: ML Pipeline Specification** (Oct 20-24)

### **Monday, Oct 20: ML Pipeline - Foundation**
**Working on**: `main` branch
**Time**: 8 hours

#### Tasks:
- [ ] **Pull latest and create spec directory**
  ```bash
  git checkout main
  git pull origin main
  mkdir -p specs/126-ml-model-training-pipeline
  # Week 2 starts - coordinate in standup
  ```

- [ ] **Create SPEC-126 README.md** (4 hours)
  ```
  File: specs/126-ml-model-training-pipeline/README.md
  ```

  Include sections:
  - [ ] Overview and objectives
  - [ ] ML use cases for ninaivalaigal
    - Memory relevance scoring
    - Auto-tagging suggestions
    - Related memory recommendations
    - User behavior prediction
  - [ ] Training data requirements
  - [ ] Model types to support
  - [ ] Infrastructure requirements

- [ ] **Define ML architecture** (4 hours)
  ```
  File: specs/126-ml-model-training-pipeline/architecture.md
  ```
  - [ ] Data collection pipeline
  - [ ] Feature engineering
  - [ ] Model training infrastructure
  - [ ] Model versioning and storage
  - [ ] Model deployment pipeline
  - [ ] A/B testing framework

**Deliverable**: ML pipeline foundation

---

### **Tuesday, Oct 21: ML Pipeline - Data & Training**
**Working on**: `main` branch (continuing)
**Time**: 8 hours

#### Tasks:
- [ ] **Design data schema** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/data-schema.md
  ```
  - [ ] Training data tables
  - [ ] Feature store schema
  - [ ] Model metadata schema
  - [ ] Experiment tracking schema
  - [ ] Define data retention policies

- [ ] **Define training pipeline** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/training-pipeline.md
  ```
  - [ ] Data extraction and validation
  - [ ] Feature generation
  - [ ] Model training workflows
  - [ ] Hyperparameter tuning
  - [ ] Model evaluation metrics
  - [ ] Model selection criteria

- [ ] **Choose MLOps tools** (2 hours)
  ```
  File: specs/126-ml-model-training-pipeline/tooling.md
  ```
  Evaluate and recommend:
  - [ ] **Kubeflow** vs **MLflow** vs **Custom**
  - [ ] Model storage: S3/GCS/MinIO
  - [ ] Experiment tracking
  - [ ] Feature store: Feast vs custom
  - [ ] Model serving: TensorFlow Serving vs custom

**Deliverable**: Complete data and training design

---

### **Wednesday, Oct 22: ML Pipeline - API & Deployment**
**Working on**: `main` branch (continuing)
**Time**: 8 hours

#### Tasks:
- [ ] **Define API endpoints** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/api-contracts.md
  ```
  - [ ] `POST /ml/train` - Start training job
  - [ ] `GET /ml/jobs/:id` - Get training status
  - [ ] `GET /ml/models` - List models
  - [ ] `POST /ml/models/:id/deploy` - Deploy model
  - [ ] `POST /ml/predict` - Make predictions
  - [ ] `GET /ml/metrics` - Model performance metrics

- [ ] **Design deployment strategy** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/deployment.md
  ```
  - [ ] Model registry design
  - [ ] Deployment workflows (staging → production)
  - [ ] Rollback procedures
  - [ ] A/B testing setup
  - [ ] Monitoring and alerting

- [ ] **Create database migrations plan** (2 hours)
  ```
  File: specs/126-ml-model-training-pipeline/migrations.md
  ```
  - [ ] Tables for model metadata
  - [ ] Tables for training jobs
  - [ ] Tables for predictions
  - [ ] Tables for feedback/labels

**Deliverable**: Complete API and deployment design

**NOTE**: Mid-sprint check-in @ 2:00 PM

---

### **Thursday, Oct 23: ML Pipeline - Implementation Plan**
**Working on**: `main` branch (continuing)
**Time**: 8 hours

#### Tasks:
- [ ] **Create Docker configurations** (3 hours)
  ```
  Files: specs/126-ml-model-training-pipeline/docker/
  ```
  - [ ] `Dockerfile.training` - Training environment
  - [ ] `Dockerfile.serving` - Model serving
  - [ ] `docker-compose.ml.yml` - Local ML stack
  - [ ] Document dependencies and versions

- [ ] **Define CI/CD for ML** (2 hours)
  ```
  File: specs/126-ml-model-training-pipeline/cicd.md
  ```
  - [ ] Automated model testing
  - [ ] Model validation pipeline
  - [ ] Deployment automation
  - [ ] Rollback automation

- [ ] **Create implementation task breakdown** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/implementation-plan.md
  ```
  - [ ] Phase 1: Data pipeline (estimate: 2 weeks)
  - [ ] Phase 2: Training infrastructure (estimate: 2 weeks)
  - [ ] Phase 3: Serving infrastructure (estimate: 1 week)
  - [ ] Phase 4: Monitoring and A/B testing (estimate: 1 week)
  - [ ] Total estimate: 6 weeks
  - [ ] Dependencies and risks

**Deliverable**: Ready-to-implement ML specification

---

### **Friday, Oct 24: ML Pipeline - Review & Documentation**
**Working on**: `main` branch (final day)
**Time**: 8 hours

#### Tasks:
- [ ] **Write implementation guide** (3 hours)
  ```
  File: specs/126-ml-model-training-pipeline/IMPLEMENTATION_GUIDE.md
  ```
  - [ ] Step-by-step implementation instructions
  - [ ] Code examples and templates
  - [ ] Testing strategies
  - [ ] Common pitfalls and solutions

- [ ] **Create architectural diagrams** (2 hours)
  ```
  File: specs/126-ml-model-training-pipeline/diagrams/
  ```
  - [ ] Data flow diagram (text-based/ASCII)
  - [ ] Training pipeline flow
  - [ ] Deployment pipeline flow
  - [ ] System integration diagram

- [ ] **Code review Developer B's work** (2 hours)
  - [ ] Review SPEC-082 (Analytics)
  - [ ] Review SPEC-088 (Versioning)
  - [ ] Provide backend perspective feedback

- [ ] **Sprint demo preparation** (1 hour)
  - [ ] Prepare SPEC-126 walkthrough
  - [ ] Prepare technical debt resolution summary
  - [ ] Prepare monitoring demo
  - [ ] Document achievements

**Deliverable**: Complete SPEC-126 ready for next sprint implementation

**NOTE**: Sprint review & demo @ 3:00 PM

---

## 🛠️ **Development Commands**

### **Testing**
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=server --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_token_refresh.py -v

# Run with markers
pytest -m "integration" -v
```

### **Linting**
```bash
# Run flake8
flake8 --count --statistics server/ alembic/ tests/

# Run mypy
mypy server/

# Run black
black server/ tests/

# Run isort
isort server/ tests/
```

### **Database**
```bash
# Create migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### **Performance Testing**
```bash
# Run load test
locust -f tests/load/locustfile.py

# Profile code
python -m cProfile -o profile.stats server/main.py
```

---

## ✅ **Daily Checklist**

### **Before Starting Work**
- [ ] Pull latest from main: `git pull origin main`
- [ ] Run test suite to ensure baseline: `pytest -v`
- [ ] Coordinate: Mention which files you're working on today

### **During Work**
- [ ] Write tests before/with implementation (TDD)
- [ ] **Commit frequently** (every 1-2 hours)
- [ ] Run tests after each commit
- [ ] Check coverage: `pytest --cov=server`
- [ ] Document as you code
- [ ] Push regularly: `git push origin main`

### **Before End of Day**
- [ ] Run full test suite: `pytest -v --cov=server`
- [ ] Run linting: `flake8 server/ alembic/ tests/`
- [ ] **Push all work to main**: `git push origin main`
- [ ] Update task checklist (this file)
- [ ] Note blockers for standup

**Note**: Working directly on `main` - you're touching server/ and tests/ which are mostly yours!

---

## 📊 **Success Metrics**

### **Week 1 Goals**
- [ ] TD-001 resolved (zero flake8 violations)
- [ ] Backend test coverage > 80%
- [ ] Production monitoring operational
- [ ] Database optimized

### **Week 2 Goals**
- [ ] SPEC-126 complete and approved
- [ ] ML architecture defined
- [ ] Implementation plan ready
- [ ] All documentation complete

### **Overall Sprint Goals**
- [ ] All PRs merged
- [ ] Test coverage maintained >80%
- [ ] Zero technical debt violations
- [ ] Ready for Phase 3 implementation

---

## 🆘 **Resources & Help**

### **Documentation**
- Technical Debt: `/technical-debt/README.md`
- Testing Guide: `/docs/TESTING_STRATEGY.md`
- Database Docs: `/docs/DATABASE_PATTERNS.md`

### **Code Examples**
- Existing tests: `/tests/`
- Alembic migrations: `/alembic/versions/`
- Server code: `/server/`

### **Getting Help**
- Frontend questions: Ask Developer A
- Documentation questions: Ask Developer B
- Blockers: Mention in standup immediately
- Quick questions: Slack anytime

---

## 🎯 **Tips for Success**

1. **Fix TD-001 First**: This unblocks the entire team
2. **Test Coverage**: Aim for >80% but prioritize critical paths
3. **Document as You Go**: Don't leave it for the end
4. **Ask for Help**: ML pipeline is complex - collaborate
5. **Review Early**: Get feedback on SPEC-126 early in Week 2

---

## 📝 **Notes Section**

### **Blockers**
<!-- Add any blockers here -->

### **Questions for Standup**
<!-- Add questions here -->

### **Performance Metrics**
<!-- Track before/after metrics -->

### **Ideas**
<!-- Note improvement ideas -->

---

**Good luck, Developer C! Let's build robust infrastructure! ⚙️🚀**
