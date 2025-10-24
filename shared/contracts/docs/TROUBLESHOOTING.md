# Troubleshooting Guide

**Purpose:** Common issues and solutions
**Audience:** All developers using contracts

---

## Import Errors

### Problem: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'ninaivalaigal_contracts'
```

**Solution:**
```bash
cd shared/contracts/
pip install -e .
```

---

## Validation Errors

### Problem: Field Required
```
ValidationError: field required (type=value_error.missing)
```

**Solution:** Ensure all required fields are provided, or make field optional:
```python
optional_field: Optional[str] = None
```

### Problem: Type Mismatch
```
ValidationError: value is not a valid email address
```

**Solution:** Use correct Pydantic type:
```python
from pydantic import EmailStr
email: EmailStr  # Not just str
```

---

## CI/CD Failures

### Problem: Contract Validation Failed
**Solution:** Run locally: `./scripts/validate-contracts.sh`

### Problem: Breaking Change Detected
**Solution:** Create new version (v2) instead of modifying v1

---

## References
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
- [VERSIONING.md](./VERSIONING.md)
