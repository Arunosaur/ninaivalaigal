# Validation Scripts for Mac Studio Deployment

## 🎯 Overview

Based on external code review feedback, these validation scripts test the highest-risk break points after file reorganization and ensure production readiness.

## 📋 Available Scripts

### 1. `validate_system.sh` - Comprehensive System Validation
**Purpose**: Full system validation following the external review checklist
**Usage**: `./validate_system.sh`

**What it tests**:
- ✅ Fresh environment setup (venv + dependencies)
- ✅ Style/typing gates (pre-commit hooks)
- ✅ Database setup and migrations
- ✅ Unit/integration tests
- ✅ Server startup and health checks
- ✅ Memory substrate functionality
- ✅ Import path validation

### 2. `validate_production_readiness.sh` - Critical Risk Areas
**Purpose**: Validates the 8 highest-risk break points identified in external review
**Usage**: `./validate_production_readiness.sh`

**Critical areas tested**:
1. **Python import paths** - Most likely to break after re-org
2. **Entry scripts** - manage.sh, run_server.py, start_* scripts
3. **Database migrations** - alembic/, alembic.ini configuration
4. **Auth/RBAC surface** - JWT tests, policy files
5. **CLI + IDE integrations** - client/, vscode-client/
6. **CI configuration** - GitHub workflows, docker-compose.ci.yml
7. **Memory substrate** - Spec 011.1 functionality
8. **Security middleware** - Integration and functionality

### 3. `validate_cli_flow.sh` - CLI Happy Path Testing
**Purpose**: Tests the complete user journey through CLI
**Usage**: `./validate_cli_flow.sh`

**User journey tested**:
- CLI availability and basic functionality
- Server connection and API endpoints
- Memory operations and context management
- End-to-end workflow validation

## 🚀 Mac Studio Deployment Workflow

### Step 1: Local Validation
```bash
# Run on development machine
./validate_production_readiness.sh
```

### Step 2: Mac Studio Setup
```bash
# On Mac Studio
git clone https://github.com/Arunosaur/ninaivalaigal.git
cd ninaivalaigal

# Fresh environment validation
./validate_system.sh

# Production readiness check
./validate_production_readiness.sh
```

### Step 3: Address Issues
- Review any warnings or errors
- Fix environment-specific issues
- Ensure all critical systems are operational

### Step 4: Deploy
- Set up GitHub Actions runner
- Configure production secrets
- Deploy and monitor

## 🔍 Expected Results

### ✅ What Should Pass
- Memory substrate functionality (Spec 011.1)
- Import paths and package boundaries
- Database migrations and schema
- RBAC policy validation
- CLI basic functionality
- CI configuration syntax

### ⚠️ Expected Warnings
- Async event loop warnings (normal in validation context)
- Pre-commit dependency issues (environment-specific)
- Docker Compose warnings (if Docker not running)
- Server endpoints not responding (if server not started)

### ❌ Critical Failures
- Import path failures
- Database migration errors
- Memory substrate factory pattern failures
- Security middleware integration issues

## 📊 Success Criteria

**Production Ready**: All critical systems validated with 0 validation errors
**Deployment Ready**: Memory substrate working + import paths resolved + database operational

## 🎯 External Review Alignment

These scripts directly address the external review feedback:

> "The top areas that usually crack (imports, alembic config, entry scripts, CLI ↔ server paths) already have tests present to catch regressions. Run the validation script above; if pytest + the CLI smoke pass, you're safe to proceed with the Mac Studio offload."

All identified risk areas are systematically validated to ensure safe Mac Studio deployment.
