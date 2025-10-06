# 🗄️ Database Access Patterns

**Last Updated:** October 3, 2025
**Status:** Production Guide

---

## 🎯 TL;DR

**Simple auth/CRUD?** → Use `get_staff_db()`
**Need graph/context/async?** → Use `get_db()` (with pool)

---

## 📊 Decision Tree

```
┌─────────────────────────────────────┐
│  What does your endpoint need?     │
└─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Just basic SQL?     │
    │ (SELECT/INSERT/     │
    │  UPDATE/DELETE)     │
    └─────────────────────┘
         │         │
         │ YES     │ NO
         ▼         ▼
    ┌─────────┐   ┌──────────────────┐
    │ Use:    │   │ Need any of:     │
    │ get_    │   │ • Context ops    │
    │ staff_  │   │ • Graph queries  │
    │ db()    │   │ • Memory ops     │
    └─────────┘   │ • Async pool     │
                  └──────────────────┘
                         │
                         ▼
                    ┌─────────┐
                    │ Use:    │
                    │ get_db()│
                    │ (needs  │
                    │  pool)  │
                    └─────────┘
```

---

## 🔧 The Core Problem

### **DatabaseOperations Is Doing Too Much**

```python
class DatabaseOperations(
    DatabaseUtilities,      # ✅ Basic CRUD
    MemoryOperations,       # 🤔 Memory-specific
    UserOperations,         # ✅ User management
    ContextOperations,      # ⚠️ Requires asyncpg.Pool
    RBACOperations,         # ✅ Authorization
    VendorAdminOperations,  # 🤔 Vendor-specific
    OrganizationOperations, # 🤔 Org-specific
):
    pass
```

**The Issue:**
- `ContextOperations.__init__()` requires `asyncpg.Pool`
- But staff auth doesn't need context operations
- Staff auth doesn't need async pool
- **Why force it to load everything?**

---

## ✅ Solution 1: Separate Session (Current)

### **For Simple Use Cases:**

```python
# server/staff_auth_api.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nina:password@postgres:5432/ninaivalaigal_dev"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_staff_db():
    """Simple database session for staff auth"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage:**
```python
@router.post("/login")
async def staff_login(
    login_data: StaffLoginRequest,
    db: Session = Depends(get_staff_db)
):
    # Simple SQL queries only
    staff = db.execute(text("SELECT ...")).fetchone()
    return response
```

### **When to Use get_staff_db():**

✅ **Authentication endpoints**
- Login
- Logout
- Password reset
- Token refresh

✅ **Simple CRUD operations**
- Create staff
- Read staff list
- Update staff
- Delete staff

✅ **Basic queries**
- No context switching
- No graph traversal
- No async operations

### **Benefits:**
- ✅ **Lightweight** - No heavy imports
- ✅ **Fast** - No pool initialization
- ✅ **Simple** - Standard FastAPI pattern
- ✅ **Independent** - No complex dependencies

---

## 🔄 Solution 2: Full Operations (Complex)

### **For Advanced Use Cases:**

```python
# server/database.py or imports
from database.operations import DatabaseOperations

async def get_db():
    """Full database operations with async pool"""
    # Initialize pool (expensive operation)
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20
    )

    db = DatabaseOperations(pool=pool)
    try:
        yield db
    finally:
        await pool.close()
```

**Usage:**
```python
@router.post("/memory")
async def create_memory(
    memory_data: MemoryCreate,
    db = Depends(get_db)
):
    # Complex operations with context
    db.set_active_context("user_context")
    memory = await db.create_memory_with_graph(memory_data)
    return memory
```

### **When to Use get_db():**

✅ **Context operations**
- Set active context
- Switch contexts
- Context-aware queries

✅ **Graph operations**
- Create graph nodes
- Traverse relationships
- Run Cypher queries

✅ **Memory operations**
- Create memories with embeddings
- Search similar memories
- Memory graph relationships

✅ **Async operations**
- Need connection pooling
- High concurrency
- Background tasks

### **Benefits:**
- ✅ **Powerful** - Full feature set
- ✅ **Integrated** - All operations available
- ✅ **Optimized** - Connection pooling
- ✅ **Async** - Non-blocking operations

---

## 📋 Examples

### **Example 1: Staff Login (Simple)**

```python
# server/staff_auth_api.py

@router.post("/login", response_model=StaffLoginResponse)
async def staff_login(
    login_data: StaffLoginRequest,
    request: Request,
    db: Session = Depends(get_staff_db)  # ✅ Simple session
):
    """Staff login - just needs basic SQL"""

    # Simple query
    query = text("""
        SELECT id, name, email, password_hash, role
        FROM staff
        WHERE email = :email
    """)
    staff = db.execute(query, {"email": login_data.email}).fetchone()

    # Verify password
    if not verify_password(login_data.password, staff.password_hash):
        raise HTTPException(status_code=401)

    # Create JWT token
    token = create_access_token({"sub": staff.email})

    return StaffLoginResponse(access_token=token, role=staff.role)
```

**Why Simple?**
- ✅ Single table query
- ✅ No context switching
- ✅ No graph operations
- ✅ Fast and lightweight

---

### **Example 2: Memory with Context (Complex)**

```python
# server/memory_api.py

@router.post("/memories", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    db = Depends(get_db),  # ✅ Full operations
    current_user: User = Depends(get_current_user)
):
    """Create memory with context and graph"""

    # Set context
    await db.set_active_context(
        context_name=memory_data.context,
        user_id=current_user.id
    )

    # Create memory with graph
    memory = await db.create_memory_with_graph(
        content=memory_data.content,
        metadata=memory_data.metadata,
        context_id=db.active_context_id
    )

    # Create relationships
    await db.create_graph_relationship(
        from_node=memory.id,
        to_node=current_user.id,
        relationship_type="CREATED_BY"
    )

    return memory
```

**Why Complex?**
- ⚠️ Context operations
- ⚠️ Graph relationships
- ⚠️ Async operations
- ⚠️ Connection pooling needed

---

### **Example 3: Staff Management (Simple)**

```python
# server/staff_management_api.py

@router.get("/staff", response_model=List[StaffResponse])
async def list_staff(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_staff_db)  # ✅ Simple session
):
    """List all staff - just basic query"""

    query = text("""
        SELECT id, name, email, role, is_active
        FROM staff
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)

    staff = db.execute(query, {"limit": limit, "skip": skip}).fetchall()

    return [StaffResponse(**dict(s)) for s in staff]
```

**Why Simple?**
- ✅ Single table
- ✅ No context
- ✅ Straightforward query

---

## 🔮 Future: The Proper Fix

### **Long-term Architecture**

```python
# Future: Refactor DatabaseOperations

class CoreOps:
    """Basic CRUD - no dependencies"""
    def __init__(self):
        pass

    # Basic queries that everyone needs

class ContextOps:
    """Context operations - requires pool"""
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # Context-specific operations

class GraphOps:
    """Graph operations - requires pool"""
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # Graph-specific operations

# Then get_db() can provide what's needed
def get_basic_db():
    """For simple operations"""
    return CoreOps()

def get_full_db(pool):
    """For complex operations"""
    return DatabaseOperations(pool=pool)
```

**See:** `PROPER_FIX_PLAN.md` for detailed refactoring plan.

---

## 🚨 Common Mistakes

### ❌ **Mistake 1: Using get_db() Everywhere**

```python
# BAD - Staff login doesn't need full operations
@router.post("/login")
async def login(db = Depends(get_db)):  # ❌ Overkill
    # Just checking password...
```

**Fix:** Use `get_staff_db()` for simple operations.

### ❌ **Mistake 2: Using get_staff_db() for Complex Ops**

```python
# BAD - Memory operations need context
@router.post("/memories")
async def create_memory(db = Depends(get_staff_db)):  # ❌ Missing features
    # Need context operations...
    db.set_active_context(...)  # ❌ Method doesn't exist!
```

**Fix:** Use `get_db()` for operations needing context/graph.

### ❌ **Mistake 3: Mixing Patterns**

```python
# BAD - Inconsistent dependencies
@router.post("/endpoint1")
async def func1(db = Depends(get_db)):
    pass

@router.post("/endpoint2")
async def func2(db = Depends(get_staff_db)):
    pass

@router.post("/endpoint3")
async def func3(db: Session = Depends(get_db)):  # Different type hint!
    pass
```

**Fix:** Be consistent within each router module.

---

## 📚 Best Practices

### ✅ **1. Choose by Complexity**
- Simple → `get_staff_db()`
- Complex → `get_db()`

### ✅ **2. Be Consistent Per Module**
```python
# staff_auth_api.py - ALL use get_staff_db()
# memory_api.py - ALL use get_db()
# staff_management_api.py - ALL use get_staff_db()
```

### ✅ **3. Document Your Choice**
```python
def get_staff_db():
    """
    Simple database session for staff operations.

    Use this for:
    - Authentication
    - Basic CRUD on staff table
    - Operations that don't need context/graph

    DO NOT use for:
    - Memory operations
    - Graph queries
    - Context switching
    """
```

### ✅ **4. Type Hints Help**
```python
from sqlalchemy.orm import Session

# Clear what you're getting
async def func(db: Session = Depends(get_staff_db)):
    # Everyone knows it's a simple session
```

---

## 🔍 When in Doubt

**Ask yourself:**

1. **Do I need context operations?**
   - YES → `get_db()`
   - NO → Continue

2. **Do I need graph queries?**
   - YES → `get_db()`
   - NO → Continue

3. **Do I need async pool?**
   - YES → `get_db()`
   - NO → Continue

4. **Just basic SQL?**
   - YES → `get_staff_db()` ✅

---

## 📖 Related Documentation

- **`PROPER_FIX_PLAN.md`** - Is this a shortcut? (No!)
- **`TODO_TRACKER.md`** - Task #5: Fix ContextOps properly
- **`BREAKTHROUGH_SUCCESS.md`** - How we solved this
- **FastAPI Docs** - [SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)

---

## ❓ FAQ

### **Q: Is get_staff_db() a shortcut?**
**A:** No! It's proper separation of concerns. See your screenshot analysis - we agree 100%.

### **Q: Will we fix DatabaseOperations?**
**A:** Yes, in next sprint. See Task #5 in TODO_TRACKER.md.

### **Q: Can I use get_staff_db() for other endpoints?**
**A:** Yes! Any endpoint that doesn't need context/graph/async can use it.

### **Q: What about performance?**
**A:** `get_staff_db()` is actually FASTER - no pool initialization overhead.

### **Q: Is this FastAPI best practice?**
**A:** Yes! This is literally from FastAPI official documentation.

---

**Remember:** Keep simple things simple. Use the right tool for the job.
