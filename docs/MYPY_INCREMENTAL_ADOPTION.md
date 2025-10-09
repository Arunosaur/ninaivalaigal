# MyPy Incremental Adoption Plan

## 📊 Current Status

**MyPy Errors**: ~1,103
**Target**: <100 in 4 weeks
**Strategy**: Incremental, phased adoption
**Effort**: 40-60 hours (3-4 weeks, moderate pace)

---

## 🎯 Goals

### Short-term (Week 1-2)
- ✅ Enable MyPy for new code only
- ✅ Fix critical type errors in core modules (10% coverage)
- ✅ Establish type annotation patterns

### Medium-term (Week 3-4)
- ✅ Reach 35% type coverage
- ✅ Type-annotate all public interfaces
- ✅ Enable pre-commit MyPy checks (non-blocking)

### Long-term (Next Quarter)
- ✅ Achieve 80%+ type coverage
- ✅ Enable strict mode for new modules
- ✅ Full IDE autocomplete benefits

---

## 📋 4-Phase Rollout Plan

### Phase 1: Foundation (Week 1) - **10% coverage**

**Goal**: New files must have type hints

**Actions**:
1. Update `mypy.ini` with incremental settings ✅ (Done)
2. Enable MyPy in pre-commit for new files only
3. Add type hints to all new code

**Target Modules** (start here):
```
server/health/
server/observability/
server/security/logging/
```

**Expected Errors to Fix**: ~100

**Time**: 1 week (8-10 hours)

---

### Phase 2: Core & Database (Weeks 2-3) - **35% coverage**

**Goal**: Type-annotate interfaces and data models

**Priority Modules**:
```
server/core/
server/database/models.py
server/spec_kit.py (Pydantic models)
server/security/rbac/
```

**Common Patterns to Fix**:
```python
# Before
def get_user(user_id):
    return db.query(User).filter_by(id=user_id).first()

# After
def get_user(user_id: int) -> User | None:
    return db.query(User).filter_by(id=user_id).first()
```

**Expected Errors to Fix**: ~400

**Time**: 1-2 weeks (15-20 hours)

---

### Phase 3: Business Logic (Week 3-4) - **60% coverage**

**Goal**: Type complex modules with subsystem interactions

**Modules**:
```
server/graph/
server/agent/
server/memory/
```

**Complex Type Patterns**:
```python
from typing import TypedDict, Protocol

class MemoryRecord(TypedDict):
    id: str
    content: str
    metadata: dict[str, Any]

class MemoryStore(Protocol):
    async def write(self, record: MemoryRecord) -> str: ...
    async def query(self, q: str) -> list[MemoryRecord]: ...
```

**Expected Errors to Fix**: ~400

**Time**: 1-2 weeks (15-20 hours)

---

### Phase 4: Cleanup & Strict (Ongoing) - **80%+ coverage**

**Goal**: Progressive strictness, gradual migration

**Actions**:
1. Add stub files (`.pyi`) for complex modules
2. Enable `disallow_untyped_defs` per module
3. Fix remaining union type issues
4. Enable strict mode for new code

**Tools**:
- `stubgen` for auto-generating stubs
- `monkeytype` for runtime type collection
- `pyre infer` for type inference

**Expected Errors to Fix**: ~200

**Time**: Ongoing (10 hours/week)

---

## 🛠️ Tooling Setup

### Enable MyPy in Pre-commit

Already configured but **commented out**. To enable incrementally:

```yaml
# In .pre-commit-config.yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.2
  hooks:
    - id: mypy
      args: ["--config-file=mypy.ini"]
      additional_dependencies: [types-requests, types-redis, types-python-dateutil]
      # Phase 1: Only check new/modified files
      files: ^server/(health|observability|security/logging)/.*\.py$
```

### Run MyPy Incrementally

```bash
# Check specific module
mypy server/health/ --config-file=mypy.ini

# Check only modified files
git diff --name-only --diff-filter=AM | grep '\.py$' | xargs mypy --config-file=mypy.ini

# Cache results for speed
mypy --cache-dir=.mypy_cache server/
```

---

## 📝 Type Annotation Patterns

### Pattern 1: Function Signatures

```python
# Simple
def add_user(name: str, email: str) -> int:
    ...

# With Optional
def get_user(user_id: int) -> User | None:
    ...

# Async
async def fetch_data(url: str) -> dict[str, Any]:
    ...
```

### Pattern 2: Generic Collections

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Store(Generic[T]):
    def add(self, item: T) -> None: ...
    def get(self, id: str) -> T | None: ...
```

### Pattern 3: Complex Types

```python
from typing import TypedDict, Literal, Protocol

# Structured dicts
class Config(TypedDict):
    host: str
    port: int
    ssl: bool

# Literal types
Status = Literal["active", "inactive", "pending"]

# Protocols (structural typing)
class Closeable(Protocol):
    def close(self) -> None: ...
```

---

## 🔍 Common Error Fixes

### Error: `Missing type annotation`

```python
# Before
data = {}  # Error: Need type annotation for "data"

# Fix
data: dict[str, Any] = {}
```

### Error: `Incompatible return value type`

```python
# Before
def get_user(id: int) -> User:
    return db.get(id)  # Error: might return None

# Fix
def get_user(id: int) -> User | None:
    return db.get(id)
```

### Error: `Call overload variant doesn't match`

```python
# Before
result = session.query(User).get(user_id)  # Error: ambiguous type

# Fix
result: User | None = session.query(User).get(user_id)
```

---

## 📊 Progress Tracking

### Week 1 Checklist
- [ ] MyPy runs without crashes
- [ ] `server/health/` fully typed
- [ ] `server/observability/` fully typed
- [ ] Type errors < 1,000

### Week 2 Checklist
- [ ] All Pydantic models typed
- [ ] Database models annotated
- [ ] Type errors < 700

### Week 3 Checklist
- [ ] Core business logic typed
- [ ] 35% coverage achieved
- [ ] Type errors < 500

### Week 4 Checklist
- [ ] Graph and agent modules typed
- [ ] 60% coverage achieved
- [ ] Type errors < 200

---

## 💡 Quick Wins

Start with these **high-value, low-effort** modules:

1. **server/health/config_hash_guard.py** (~26 lines)
   - Simple functions, easy to type
   - Immediate benefit for health checks

2. **server/observability/metrics_labels.py** (~22 lines)
   - Clear function signatures
   - No complex types

3. **server/security/logging/scrubber.py** (~59 lines)
   - Straightforward dict operations
   - Good learning example

**Total**: ~100 lines, ~30 minutes, immediate 3% coverage boost!

---

## 🚀 Commands Reference

```bash
# Run full type check
mypy server/ --config-file=mypy.ini

# Check specific module
mypy server/health/ --config-file=mypy.ini

# Show error codes
mypy server/ --show-error-codes

# Generate coverage report
mypy server/ --html-report mypy-report/

# Incremental check (fast)
mypy server/ --cache-dir=.mypy_cache

# Strict check for module
mypy server/health/ --strict

# Generate stubs
stubgen -p server.health -o stubs/
```

---

## 🎯 Success Metrics

| Week | Coverage Target | Error Count | Modules Typed |
|------|----------------|-------------|---------------|
| 1    | 10%            | <1,000      | 3-5           |
| 2    | 25%            | <700        | 10-15         |
| 3    | 40%            | <400        | 20-25         |
| 4    | 60%            | <200        | 30-40         |

**End Goal**: 80%+ coverage, <100 errors, strict mode for new code

---

## 📚 Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [typing Module Docs](https://docs.python.org/3/library/typing.html)
- [Real Python - Type Checking](https://realpython.com/python-type-checking/)

---

**Next Action**: Run `mypy server/health/ --config-file=mypy.ini` and fix the first module! 🚀

---

**Last Updated**: 2025-10-09
**Status**: Ready to Start
**Current Errors**: ~1,103
**Target**: <100 in 4 weeks
