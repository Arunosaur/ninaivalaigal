# Testing Configuration Guide

**Created:** October 13, 2025  
**Purpose:** Centralized test configuration management

---

## 🎯 **Problem Solved**

**Before:** API URLs and ports were hardcoded in multiple test files, creating:
- Maintenance nightmare (update 10+ files for one port change)
- Configuration drift between test suites
- No environment-specific overrides

**After:** Single source of truth in `tests/conftest.py` with environment variable support.

---

## ⚙️ **Centralized Configuration**

### **Location**
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def api_config() -> Dict:
    """Centralized API configuration for all tests."""
    return {
        "base_url": os.getenv("TEST_API_BASE_URL", "http://localhost:13390"),
        "concurrent_limit": int(os.getenv("TEST_CONCURRENT_LIMIT", "50")),
        "test_timeout": int(os.getenv("TEST_API_TIMEOUT", "30")),
        "rate_limit_threshold": 100,
        "session_timeout_minutes": 30,
    }
```

### **Usage**
```python
@pytest.fixture
def rbac_engine(api_config) -> RBACTestEngine:
    """Use centralized config instead of hardcoded values."""
    return RBACTestEngine(api_config)
```

---

## 🌍 **Environment Variables**

### **`.env.test` (Default Values)**
```bash
TEST_API_BASE_URL=http://localhost:13390
TEST_API_TIMEOUT=30
TEST_CONCURRENT_LIMIT=50
```

### **Override for CI/CD**
```bash
# GitHub Actions
export TEST_API_BASE_URL=http://api:8080
pytest tests/
```

### **Override for Local Dev**
```bash
# Testing against staging
export TEST_API_BASE_URL=https://staging-api.nina.com
pytest tests/integration/
```

---

## 📊 **Port Reference**

| Port | Service | Usage |
|------|---------|-------|
| **13390** | Backend API | Default for tests |
| **3000** | Frontend Dev | Developer A |
| **3500** | Docs Dashboard | Documentation |
| **8080** | Legacy | (deprecated) |

---

## 🔧 **Migration Guide**

### **Before (Anti-pattern)**
```python
# ❌ Hardcoded in multiple files
@pytest.fixture
def auth_test_config():
    return {
        "base_url": "http://localhost:8080",  # Hardcoded!
        ...
    }
```

### **After (Correct)**
```python
# ✅ Use centralized fixture
@pytest.fixture
def rbac_engine(api_config):  # Inject api_config
    return RBACTestEngine(api_config)
```

---

## 📝 **Files Updated**

### **Centralized Config**
- ✅ `tests/conftest.py` - Added `api_config` fixture

### **Files Migrated**
- ✅ `tests/auth_aware/test_rbac_validation.py`
- ✅ `tests/auth_aware/test_fixtures.py`
- ✅ `.env.test` - Added TEST_API_* variables

### **Files Using Defaults (fallback)**
- `tests/auth_aware/multi_user_manager.py` - Uses `config.get("base_url", "...")`
- `tests/auth_aware/rbac_engine.py` - Uses `config.get("base_url", "...")`
- `tests/auth_aware/security_scenarios.py` - Uses `config.get("base_url", "...")`

---

## ✅ **Benefits**

1. **Single Source of Truth**
   - Change port in ONE place (.env.test)
   - All tests automatically use new value

2. **Environment-Specific**
   - Local dev: http://localhost:13390
   - CI/CD: http://api:8080
   - Staging: https://staging.nina.com

3. **Type-Safe**
   - Centralized fixture provides Dict type
   - IDE autocompletion works

4. **Testable**
   - Mock `api_config` fixture for unit tests
   - No need to mock environment variables everywhere

---

## 🚨 **Rules**

### **DO:**
- ✅ Use `api_config` fixture in all new tests
- ✅ Override via environment variables
- ✅ Add new config keys to `api_config` fixture

### **DON'T:**
- ❌ Hardcode URLs/ports in test files
- ❌ Create duplicate config fixtures
- ❌ Use different port numbers across tests

---

## 🔍 **Verification**

### **Check Current Config**
```bash
# See what tests will use
python3 -c "
import os
print('Base URL:', os.getenv('TEST_API_BASE_URL', 'http://localhost:13390'))
print('Timeout:', os.getenv('TEST_API_TIMEOUT', '30'))
"
```

### **Test with Override**
```bash
# Test against different port
TEST_API_BASE_URL=http://localhost:8000 pytest tests/auth_aware/
```

---

## 📚 **Related Documentation**

- `PORT_ALLOCATION.md` - Port assignment guide
- `TESTING_GUIDE.md` - General testing practices
- `TESTING_PATTERNS.md` - Common test patterns
- `.env.test` - Default test environment variables

---

## 🎯 **Example: Adding New Config**

```python
# 1. Add to tests/conftest.py
@pytest.fixture(scope="session")
def api_config() -> Dict:
    return {
        ...
        "new_setting": os.getenv("TEST_NEW_SETTING", "default"),
    }

# 2. Add to .env.test
TEST_NEW_SETTING=value

# 3. Use in tests
def test_something(api_config):
    setting = api_config["new_setting"]
    assert setting == "value"
```

---

**Status:** ✅ Implemented  
**Migration:** ✅ Complete (TD-001)  
**Coverage:** Core test suites

---

**Last Updated:** October 13, 2025  
**By:** Developer C (TD-001 Resolution)
