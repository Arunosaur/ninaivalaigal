# Module Shim Pattern - Shared Contracts + Local Implementation

**Problem**: Services need both shared contract models (for API consistency) AND local implementation functions (for business logic).

**Example**:
```python
# Need BOTH of these to work:
from auth.v1.models import Token, UserLogin  # Shared contracts
from auth import create_refresh_token, authenticate_user  # Local implementation
```

---

## Solution: Module Merging Shim

### **What `local_run.py` Does**

1. **Load shared contracts first** - Makes `auth.v1.models` available
2. **Load local implementation** - Gets service-specific functions
3. **Merge them** - Combines into single `auth` module
4. **Preserve package metadata** - Keeps `__path__`, `__spec__` for submodule imports

### **Key Code Pattern**

```python
import importlib
import importlib.util
import sys
from pathlib import Path

# 1. Setup paths
SHARED_CONTRACTS = Path(__file__).parent.parent.parent / "shared" / "contracts"
SERVICE_PATH = Path(__file__).parent

sys.path.insert(0, str(SHARED_CONTRACTS))
sys.path.insert(1, str(SERVICE_PATH))

# 2. Load shared contracts (has submodules like auth.v1)
contracts_auth = importlib.import_module("auth")

# 3. Load local implementation
local_auth_spec = importlib.util.spec_from_file_location(
    "_service_auth",
    SERVICE_PATH / "auth.py"
)
local_auth = importlib.util.module_from_spec(local_auth_spec)

# 4. Temporarily set contracts as 'auth' during load (so local auth.py can import from auth.v1)
sys.modules["auth"] = contracts_auth
local_auth_spec.loader.exec_module(local_auth)

# 5. Merge: Copy contracts attributes to local module (if not already present)
for name, value in contracts_auth.__dict__.items():
    if not name.startswith("__") or name in {"__path__", "__package__", "__spec__"}:
        if not hasattr(local_auth, name):
            setattr(local_auth, name, value)

# 6. Preserve package metadata for submodule resolution
if hasattr(contracts_auth, "__path__"):
    local_auth.__path__ = contracts_auth.__path__
if hasattr(contracts_auth, "__spec__"):
    local_auth.__spec__ = contracts_auth.__spec__

# 7. Register merged module
sys.modules["auth"] = local_auth
```

---

## When to Use This Pattern

**Use When**:
- ✅ You have shared API contracts in `/shared/contracts/`
- ✅ You have service-specific implementation in `/services/{service}/`
- ✅ You need both to be importable as the same module name
- ✅ Running locally (not in Docker with pre-configured paths)

**Don't Need When**:
- ❌ Running in Docker (paths pre-configured in Dockerfile)
- ❌ Only using shared contracts (no local implementation)
- ❌ Only using local implementation (no shared contracts)

---

## Alternative: Reusable Helper

See `module_shim.py` for a reusable implementation:

```python
# In local_run.py or test setup
from module_shim import setup_service_modules

setup_service_modules()  # Merges auth + any other modules

# Now both work:
from auth.v1.models import Token
from auth import create_refresh_token
```

---

## Testing the Shim

```bash
# Test that both import styles work
python -c "
from auth.v1.models import Token
from auth import create_refresh_token
print('✅ Shim working correctly')
"
```

---

## Common Issues

### Issue 1: ImportError for auth.v1

**Symptom**: `ModuleNotFoundError: No module named 'auth.v1'`

**Cause**: Package metadata (`__path__`, `__spec__`) not preserved

**Fix**: Ensure you copy these attributes:
```python
local_auth.__path__ = contracts_auth.__path__
local_auth.__spec__ = contracts_auth.__spec__
```

### Issue 2: Local functions override contract models

**Symptom**: `Token` model not available after merge

**Cause**: Merging in wrong direction

**Fix**: Copy TO local, not FROM local:
```python
# Correct: Copy contracts to local (preserves contracts)
if not hasattr(local_auth, name):
    setattr(local_auth, name, value)

# Wrong: Would override contracts
setattr(local_auth, name, value)  # No check!
```

### Issue 3: Circular import during merge

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Cause**: Local auth.py imports from auth.v1 before merge completes

**Fix**: Temporarily set contracts as 'auth' during exec:
```python
sys.modules["auth"] = contracts_auth  # Before exec
local_auth_spec.loader.exec_module(local_auth)  # Now imports work
sys.modules["auth"] = local_auth  # After exec
```

---

## Performance Considerations

**Overhead**: ~10ms startup time (negligible for web services)

**Memory**: No duplication (merged module shares references)

**Runtime**: Zero overhead after startup (normal imports)

---

## Future Improvements

**Option 1: Namespace Packages**
- Use Python namespace packages (PEP 420)
- Both shared and local contribute to same namespace
- Pro: Standard Python feature
- Con: Requires restructuring imports

**Option 2: Explicit Imports**
```python
# Instead of merging, use explicit paths
from shared.contracts.auth.v1.models import Token
from services.core_api.auth_impl import create_refresh_token
```
- Pro: Explicit is better than implicit
- Con: Verbose, breaks existing code

**Option 3: Build-Time Merge**
- Pre-merge during Docker build
- Pro: No runtime overhead
- Con: More complex build process

---

## Credit

**Implementation**: Developer A
**Date**: October 23, 2025
**Context**: US#79 local development setup

---

## Related Files

- `local_run.py` - Current implementation (working)
- `module_shim.py` - Reusable helper (optional)
- `/shared/contracts/python/auth/` - Shared contracts
- `auth.py` - Local implementation
