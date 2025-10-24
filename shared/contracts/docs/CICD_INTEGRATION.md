# CI/CD Integration Tutorial

**Purpose:** How contract validation works in CI
**Audience:** DevOps and backend developers

---

## Overview

Contract validation runs automatically in CI to prevent:
- Breaking changes in existing versions
- Invalid contract syntax
- Import errors
- Missing dependencies

---

## GitHub Actions Workflow

### .github/workflows/contracts.yml

```yaml
name: Validate Contracts

on:
  push:
    paths:
      - 'shared/contracts/**'
  pull_request:
    paths:
      - 'shared/contracts/**'

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for diff

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install contracts
        run: |
          cd shared/contracts
          pip install -e .

      - name: Validate imports
        run: |
          python -c "from ninaivalaigal_contracts.auth.v1 import *"
          python -c "from ninaivalaigal_contracts.memory.v1 import *"
          python -c "from ninaivalaigal_contracts.graph.v1 import *"
          python -c "from ninaivalaigal_contracts.business.v1 import *"
          python -c "from ninaivalaigal_contracts.admin.v1 import *"

      - name: Run tests
        run: |
          cd shared/contracts
          pytest tests/ -v --cov=. --cov-report=term

      - name: Check breaking changes
        run: |
          ./scripts/check-breaking-changes.sh

      - name: Generate OpenAPI schemas
        run: |
          python scripts/generate-openapi.py

      - name: Lint contracts
        run: |
          cd shared/contracts
          pylint --disable=all --enable=E,W *.py */*.py

  protobuf-validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install protoc
        run: |
          sudo apt-get update
          sudo apt-get install -y protobuf-compiler

      - name: Validate Protobuf
        run: |
          protoc --python_out=/tmp \
            shared/contracts/graphops/v1/*.proto
```

---

## Breaking Change Detection

### scripts/check-breaking-changes.sh

```bash
#!/bin/bash
set -e

echo "🔍 Checking for breaking changes in v1 contracts..."

# Get changed files in v1 directories
CHANGED_V1=$(git diff --name-only origin/main -- 'shared/contracts/*/v1/')

if [ -z "$CHANGED_V1" ]; then
    echo "✅ No v1 contracts changed"
    exit 0
fi

echo "📝 Changed v1 files:"
echo "$CHANGED_V1"

# Check for breaking patterns
BREAKING_PATTERNS=(
    "^-.*Field.*required"
    "^-.*class.*Response"
    "^-.*class.*Request"
    "^-.*def "
)

for pattern in "${BREAKING_PATTERNS[@]}"; do
    if git diff origin/main -- shared/contracts/*/v1/ | grep -E "$pattern"; then
        echo "❌ Breaking change detected: $pattern"
        echo "🚫 v1 contracts are immutable. Create v2 instead."
        exit 1
    fi
done

# Check for field removals
if git diff origin/main -- shared/contracts/*/v1/ | grep -E "^-\s+\w+:\s"; then
    echo "❌ Field removal detected in v1"
    echo "🚫 Create v2 for breaking changes"
    exit 1
fi

echo "✅ No breaking changes detected"
```

---

## Pre-commit Hooks

### .pre-commit-config.yaml

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-contracts
        name: Validate Contract Imports
        entry: bash -c 'cd shared/contracts && python -c "from ninaivalaigal_contracts.auth.v1 import *"'
        language: system
        pass_filenames: false
        files: ^shared/contracts/

      - id: check-contract-syntax
        name: Check Pydantic Syntax
        entry: python -m py_compile
        language: system
        files: ^shared/contracts/.*\.py$

      - id: format-contracts
        name: Format with Black
        entry: black
        language: system
        files: ^shared/contracts/.*\.py$
        args: ['--line-length=100']
```

### Setup
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Local Testing Workflow

### Before Committing

```bash
# 1. Install contracts
cd shared/contracts/
pip install -e .

# 2. Test imports
python -c "from ninaivalaigal_contracts.my_service.v1 import *"

# 3. Run tests
pytest tests/ -v

# 4. Check breaking changes
../scripts/check-breaking-changes.sh

# 5. Format code
black .

# 6. Commit
git add .
git commit -m "Add new contract"
```

---

## Service Integration CI

### Validating service uses contracts

```yaml
# .github/workflows/service-ci.yml
name: Service CI

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install contracts
        run: |
          cd shared/contracts
          pip install -e .

      - name: Install service dependencies
        run: |
          cd services/my-service
          pip install -r requirements.txt

      - name: Run service tests
        run: |
          cd services/my-service
          pytest tests/ -v

      - name: Verify contract compliance
        run: |
          python scripts/verify-service-contracts.py my-service
```

---

## Monitoring

### Metrics to Track

```yaml
# In CI, emit metrics
- name: Track contract changes
  run: |
    echo "contracts_changed=$CHANGED_COUNT" >> $GITHUB_ENV
    echo "breaking_changes=$BREAKING_COUNT" >> $GITHUB_ENV

    # Send to monitoring
    curl -X POST https://metrics.internal/api/track \
      -d "metric=contracts.changed&value=$CHANGED_COUNT"
```

---

## Troubleshooting CI Failures

### Import Error in CI
```
ModuleNotFoundError: No module named 'ninaivalaigal_contracts'
```

**Fix:** Ensure `pip install -e .` ran in contracts directory

### Breaking Change Detected
```
❌ Breaking change detected: ^-.*Field.*required
```

**Fix:** Create v2 instead of modifying v1

### Protobuf Validation Failed
```
Error: unknown type
```

**Fix:** Check `.proto` syntax, ensure imports are correct

---

## References

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Pre-commit Docs](https://pre-commit.com/)
- [VALIDATION.md](./VALIDATION.md)
