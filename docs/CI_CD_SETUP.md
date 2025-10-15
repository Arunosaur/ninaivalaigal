# CI/CD Setup Documentation

**Last Updated**: October 15, 2025
**Status**: Production-ready

---

## Overview

Ninaivalaigal uses a comprehensive CI/CD pipeline with local pre-commit hooks and GitHub Actions workflows to ensure code quality, security, and compliance.

---

## 🔧 Pre-Commit Hooks

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# (Optional) Test all files
pre-commit run --all-files
```

### Hook Categories

#### 1. **Basic File Hygiene**
- `trailing-whitespace` - Remove trailing whitespace
- `end-of-file-fixer` - Ensure files end with newline
- `check-yaml` - Validate YAML syntax
- `check-json` - Validate JSON syntax
- `check-toml` - Validate TOML syntax
- `check-added-large-files` - Prevent large files (>500KB)
- `check-merge-conflicts` - Detect merge conflict markers
- `mixed-line-ending` - Ensure consistent line endings

#### 2. **Python Code Quality**
- `black` - Code formatter (opinionated)
- `isort` - Import sorting
- `flake8` - Linting (with docstrings & bugbear)
- `bandit` - Security scanning

**Exclusions**:
- Generated protobuf files (`*_pb2.py`, `*_pb2_grpc.py`)
- Benchmark scripts (`benchmarks/*.py`)
- CI utility scripts (`ci/*.py`)

#### 3. **Rust Code Quality**
- `cargo fmt` - Code formatter
- `cargo clippy` - Linting with strict warnings
- `cargo test --lib` - Unit tests only
- `cargo audit` - Security vulnerability scanning

**Note**: Integration tests are excluded from pre-commit (require database).

#### 4. **Security & Compliance**
- `detect-secrets` - Scan for hardcoded secrets
  - Uses `.secrets.baseline` for allowlist
  - Mark false positives: `# pragma: allowlist secret`
- `check-spdx-headers` - Ensure license headers present
- `shellcheck` - Shell script linting

#### 5. **API Contract Validation**
- `validate-api-version` - Check API version consistency
- `validate-api-contracts` - Validate protobuf/OpenAPI contracts

---

## 🎉 Post-Commit Banner

After a successful commit, you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 SUCCESS! Commit Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All pre-commit hooks passed

📦 Commit Details:
   Branch:  main
   Hash:    63585f8d
   Author:  Developer Name
   Message: feat: Add new feature

🔍 Core checks completed:
   ✓ Rust fmt/clippy/test/audit
   ✓ Python black/isort/flake8
   ✓ Security (bandit/detect-secrets)
   ✓ SPDX headers
   ✓ API contracts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Next step: git push origin main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Location**: `.git/hooks/post-commit`

---

## 🔄 GitHub Actions CI

### Workflow: `ci-lint.yml`

Mirrors all pre-commit checks in CI to ensure consistency.

**Triggers**:
- Push to `main` or `dev` branches
- Pull requests to `main` or `dev`

### Jobs

#### 1. **lint-rust**
- cargo fmt check
- cargo clippy (all targets, deny warnings)
- cargo test --lib
- cargo audit (security scan)

#### 2. **lint-python**
- black --check
- isort --check-only
- flake8
- bandit

#### 3. **security-scan**
- detect-secrets (baseline validation)
- reuse lint (license compliance)

#### 4. **validate-contracts**
- API version validation
- API contract validation

#### 5. **spdx-headers**
- SPDX license header validation

#### 6. **all-checks** (final gate)
- Depends on all other jobs
- Provides summary of passed checks

**Status**: ✅ All checks must pass before merge

---

## 🔒 Security Scanning

### Secrets Detection

**Tool**: `detect-secrets`

**Baseline**: `.secrets.baseline`

**Marking False Positives**:
```python
# This is a test credential  # pragma: allowlist secret
password = "test_password_change_in_production"  # pragma: allowlist secret
```

### Rust Dependency Audit

**Tool**: `cargo-audit`

**Check**: Run automatically in pre-commit and CI

**Manual Run**:
```bash
cd rust-services/graphops
cargo audit
```

**Advisory Database**: Updates automatically from RustSec

---

## 📄 SPDX License Headers

All source files must include SPDX headers.

**Valid Licenses**:
- `Proprietary` - Server code, core business logic
- `MIT` - Frontend, packages, scripts
- `Apache-2.0` - CLI, SDKs
- `Elastic-2.0` - Containers, K8s, Terraform

**Example (Python)**:
```python
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
```

**Example (Rust)**:
```rust
// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
```

**Auto-add Headers**:
```bash
python3 ci/add-spdx-headers.py <file_path>
```

---

## 🚫 Bypassing Hooks (Emergency Only)

**Skip pre-commit hooks** (NOT RECOMMENDED):
```bash
git commit --no-verify -m "Emergency fix"
```

**When to use**:
- Critical production hotfix
- Breaking CI infrastructure issue
- Pre-approved by tech lead

**After bypassing**:
1. Create follow-up task to fix issues
2. Document reason in commit message
3. Fix on next commit

---

## 📊 CI Performance

### Pre-Commit Hook Times

| Hook | Average Time | Notes |
|------|--------------|-------|
| Python (black/isort/flake8) | ~2s | Fast, runs only on changed files |
| Rust (fmt/clippy) | ~5s | Fast checks only |
| Rust (test) | ~10s | Library tests only |
| Rust (audit) | ~3s | Checks advisory database |
| Security (detect-secrets) | ~1s | Fast scan |
| SPDX headers | ~1s | Fast validation |

**Total**: ~20-30s for typical commit

### GitHub Actions Times

| Job | Average Time | Notes |
|-----|--------------|-------|
| lint-rust | ~5min | Includes cache warm-up |
| lint-python | ~2min | Fast Python checks |
| security-scan | ~1min | Secrets + REUSE |
| validate-contracts | ~30s | API validation |
| spdx-headers | ~30s | License check |

**Total**: ~8-10min for full CI run

---

## 🐛 Troubleshooting

### Pre-Commit Hook Failures

**Black formatting fails**:
```bash
# Auto-fix
black .

# Check specific file
black --check path/to/file.py
```

**Cargo clippy warnings**:
```bash
cd rust-services/graphops
cargo clippy --fix
```

**Secrets detected (false positive)**:
```bash
# Add pragma to line
# pragma: allowlist secret

# Update baseline
detect-secrets scan --baseline .secrets.baseline
```

**SPDX header missing**:
```bash
python3 ci/add-spdx-headers.py path/to/file
```

### CI Failures

**Rust cache issues**:
- Wait for cache to rebuild (~5min first time)
- Check `.github/workflows/ci-lint.yml` cache keys

**Python dependency issues**:
- Verify `requirements.txt` is up to date
- Check Python version (3.11 required)

**API contract validation fails**:
- Review changes to `.proto` or `.yaml` files
- Ensure API version is bumped if breaking change
- Run `python3 ci/validate-api-contracts.py` locally

---

## 🔄 Updating Hooks

### Add New Hook

1. Edit `.pre-commit-config.yaml`
2. Add hook configuration
3. Test: `pre-commit run --all-files`
4. Update this documentation
5. Update `.github/workflows/ci-lint.yml` to match

### Update Hook Version

1. Edit `.pre-commit-config.yaml`
2. Update `rev:` field
3. Run: `pre-commit autoupdate`
4. Test changes
5. Commit

---

## 📚 Additional Resources

**Pre-Commit**:
- Official docs: https://pre-commit.com
- Hook repository: https://github.com/pre-commit/pre-commit-hooks

**Rust Tools**:
- cargo-audit: https://github.com/rustsec/rustsec
- clippy: https://github.com/rust-lang/rust-clippy

**Python Tools**:
- black: https://black.readthedocs.io
- isort: https://pycqa.github.io/isort/
- flake8: https://flake8.pycqa.org
- bandit: https://bandit.readthedocs.io

**Security**:
- detect-secrets: https://github.com/Yelp/detect-secrets
- REUSE: https://reuse.software

---

## 🎯 Best Practices

1. **Run hooks locally before pushing**
   ```bash
   pre-commit run --all-files
   ```

2. **Keep commits atomic**
   - One logical change per commit
   - All hooks pass per commit
   - Makes bisecting easier

3. **Write good commit messages**
   - Use conventional commit format
   - Include context and reasoning
   - Reference issues/tickets

4. **Update baseline files**
   - `.secrets.baseline` when adding test credentials
   - Document why secrets are safe

5. **Monitor CI trends**
   - Watch for increasing run times
   - Optimize slow checks
   - Keep dependencies updated

---

**Questions?** Contact the platform team or check `#engineering` in Slack.
