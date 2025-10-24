# Contract Validation

**Purpose:** How to validate contracts in CI and locally
**Audience:** All developers

---

## Local Validation

### Install Contracts
```bash
cd shared/contracts/
pip install -e .
```

### Test Imports
```bash
python -c "from ninaivalaigal_contracts.my_service.v1 import *"
```

### Run Tests
```bash
pytest shared/contracts/tests/
```

---

## CI Validation

### GitHub Actions
```yaml
name: Validate Contracts

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Python
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

      - name: Run contract tests
        run: pytest shared/contracts/tests/ -v
```

---

## Pre-commit Hooks

### Install pre-commit
```bash
pip install pre-commit
```

### .pre-commit-config.yaml
```yaml
repos:
  - repo: local
    hooks:
      - id: validate-contracts
        name: Validate Contracts
        entry: python -c "from ninaivalaigal_contracts.my_service.v1 import *"
        language: system
        pass_filenames: false
```

```bash
pre-commit install
pre-commit run --all-files
```

---

## Breaking Change Detection

### Script: scripts/check-breaking-changes.sh
```bash
#!/bin/bash
# Detect breaking changes in contracts

echo "Checking for breaking changes..."

# Compare v1 contracts with previous version
git diff origin/main -- shared/contracts/*/v1/ | grep -E "^-.*Field|^-.*class" && {
    echo "❌ Breaking changes detected in v1!"
    echo "Create a new version (v2) instead."
    exit 1
}

echo "✅ No breaking changes in v1"
```

---

## Contract Tests

### Example Test Suite
```python
# shared/contracts/tests/test_my_service.py
import pytest
from ninaivalaigal_contracts.my_service.v1 import (
    CreateItemRequest,
    ItemResponse,
)
from pydantic import ValidationError

def test_create_request_valid():
    """Test valid create request"""
    request = CreateItemRequest(
        name="Test Item",
        description="Test description",
        tags=["test"]
    )
    assert request.name == "Test Item"

def test_create_request_missing_name():
    """Test request fails without required name"""
    with pytest.raises(ValidationError):
        CreateItemRequest(
            description="Test",
            tags=[]
        )

def test_response_serialization():
    """Test response can be serialized"""
    from uuid import uuid4
    from datetime import datetime

    response = ItemResponse(
        id=uuid4(),
        name="Test",
        description="Test",
        tags=[],
        created_at=datetime.utcnow(),
    )

    # Can serialize to JSON
    json_data = response.json()
    assert json_data

    # Can deserialize from JSON
    restored = ItemResponse.parse_raw(json_data)
    assert restored.name == "Test"
```

---

## References
- [CI/CD Integration](./CICD_INTEGRATION.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
