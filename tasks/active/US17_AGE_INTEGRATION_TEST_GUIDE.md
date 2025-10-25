# US #17: AGE Integration Test Execution Guide

**Date:** October 24, 2025
**Developer:** Developer A
**Status:** Tests Ready - Awaiting Environment Configuration

---

## ✅ Current Progress

### Completed:
- ✅ Activated `nina` conda environment
- ✅ AGE integration tests collected successfully
- ✅ Test structure validated (2 tests, properly skipped)
- ✅ All containers running (DB, PgBouncer, Redis, Graph Service)
- ✅ Fixed pytest-asyncio deprecation warning

### Test Files:
- `/Users/swami/WorkSpace/ninaivalaigal/tests/integration/age_integration_test.py`
  - `test_age_health_check_reports_status`
  - `test_age_graph_list_contains_configured_graph`

---

## 🎯 To Run Integration Tests Successfully

### Option 1: Using PgBouncer Transaction Mode (Recommended)

```bash
# In conda environment: nina
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.66.119:6432/ninaivalaigal_dev"  # pragma: allowlist secret
export REDIS_URL="redis://:dev_redis_password@192.168.66.89:6379/0"

# Run AGE integration tests
conda run -n nina pytest tests/integration/age_integration_test.py -v
```

### Option 2: Direct Database Connection (Alternative)

```bash
# In conda environment: nina
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.66.88:5432/ninaivalaigal_dev"  # pragma: allowlist secret
export REDIS_URL="redis://:dev_redis_password@192.168.66.89:6379/0"

# Run AGE integration tests
conda run -n nina pytest tests/integration/age_integration_test.py -v
```

---

## 📊 Container Mapping Reference

| Service | Container IP | Port | Purpose |
|---------|-------------|------|---------|
| PostgreSQL (direct) | 192.168.66.88 | 5432 | ninaivalaigal_dev DB with AGE extension |
| PgBouncer TX | 192.168.66.119 | 6432 | Transaction mode pool (stateless services) |
| PgBouncer SESS | 192.168.66.120 | 6433 | Session mode pool (Rust/SQLx services) |
| Redis | 192.168.66.89 | 6379 | Cache and session storage |
| Graph Service | 192.168.66.94 | 13398 | GraphOps service under test |

---

## 🔍 Expected Test Results

### When AGE Extension is Available:

```bash
tests/integration/age_integration_test.py::test_age_health_check_reports_status PASSED
tests/integration/age_integration_test.py::test_age_graph_list_contains_configured_graph PASSED

======================== 2 passed in 0.45s ========================
```

### Test Validations:

**Test 1: Health Check**
- ✅ Returns `type: "postgresql+age"`
- ✅ Reports database name
- ✅ Status is "healthy" or "unhealthy"
- ✅ When healthy, lists available graphs
- ✅ Configured graph name present in list

**Test 2: Graph List**
- ✅ Returns list of graphs from AGE catalog
- ✅ Configured graph name is present

---

## 🛠️ Troubleshooting

### If Tests Still Skip:

**Check 1: AGE Extension Installed**
```bash
# Connect to database
container exec -it ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev

# Verify AGE extension
\dx

# Should show:
# age | 1.5.0 | ag_catalog | Apache AGE graph database extension
```

**Check 2: Graph Service Config**
```bash
# Check if graph service config loads
conda run -n nina python -c "
import sys
sys.path.insert(0, 'services/graph-service')
sys.path.insert(0, 'services/graph-service/lib')
from config import get_config
config = get_config()
print(f'Database URL: {config.database_url}')
print(f'DB Name: {config.db_name}')
print(f'Graph Name: {config.graph_name}')
"
```

**Check 3: Network Connectivity**
```bash
# Test PgBouncer connection
conda run -n nina python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        'postgresql://nina:dev_password_change_in_production@192.168.66.119:6432/ninaivalaigal_dev'  # pragma: allowlist secret
    )
    result = await conn.fetchval('SELECT version()')
    print(f'PostgreSQL: {result}')
    await conn.close()

asyncio.run(test())
"
```

---

## 📋 Graph Service Configuration

### Expected Config (services/graph-service/lib/config.py):

```python
from typing import Optional
import os

class Config:
    """Graph service configuration"""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev"  # pragma: allowlist secret
    )

    db_name: str = os.getenv("NINA_DB_NAME", "ninaivalaigal_dev")
    graph_name: str = os.getenv("GRAPH_NAME", "ninaivalaigal_graph")

    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Service configuration
    service_port: int = int(os.getenv("GRAPHOPS_PORT", "13398"))
```

---

## 🎯 Success Criteria

### US #17 Integration Tests PASS When:

1. ✅ AGE extension loaded in `ninaivalaigal_dev` database
2. ✅ Graph service can connect via PgBouncer (port 6432)
3. ✅ ApacheAGEClient initializes successfully
4. ✅ Health check returns valid status
5. ✅ Configured graph exists in AGE catalog
6. ✅ Both integration tests pass (not skipped)

---

## 📝 Next Steps After Tests Pass

1. Update Taiga US #17 status with test results
2. Document AGE integration in graph service README
3. Add CI workflow to run AGE tests
4. Create graph service health endpoint using AGE client
5. Wire real AGE queries into GraphOps API endpoints

---

## 🚨 Known Issues & Resolutions

### Issue 1: pytest-asyncio Deprecation Warning ✅ FIXED
**Solution:** Updated `tests/conftest.py` and `tests/foundation/conftest.py` to use `asyncio_event_loop_policy` instead of custom `event_loop` fixture.

### Issue 2: Tests Skipped - No DB Connection ⏳ PENDING
**Solution:** Set `DATABASE_URL` environment variable to point to running PgBouncer container.

### Issue 3: AGE Extension Not Found ⏳ TO VERIFY
**Solution:** Verify AGE extension is installed in `ninaivalaigal_dev` database.

---

**Developer A:** Tests are ready to run. Set the environment variables above and execute the pytest command to validate AGE integration! 🚀
