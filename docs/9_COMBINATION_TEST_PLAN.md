# 9-Combination Test Plan

**Date**: 2025-09-30
**Purpose**: Validate all 9 runtime/environment combinations
**Status**: 🔄 **RUNNING**

---

## 🎯 **Test Objectives**

1. **Validate all 9 combinations start successfully**
2. **Confirm PostgreSQL and Redis work in each combination**
3. **Verify data sharing across runtimes within same environment**
4. **Ensure different environments remain isolated**

---

## 📊 **Test Matrix**

### **The 9 Combinations**

| # | Runtime | Environment | Postgres Port | Redis Port | API Port | Data Directory |
|---|---------|-------------|---------------|------------|----------|----------------|
| 1 | Docker | dev | 5432 | 6379 | 13370 | `./data/postgres_dev` |
| 2 | Colima | dev | 5442 | 6389 | 13380 | `./data/postgres_dev` |
| 3 | Apple CLI | dev | 5452 | 6399 | 13390 | `./data/postgres_dev` |
| 4 | Docker | test | 5532 | 6479 | 13470 | `./data/postgres_test` |
| 5 | Colima | test | 5542 | 6489 | 13480 | `./data/postgres_test` |
| 6 | Apple CLI | test | 5552 | 6499 | 13490 | `./data/postgres_test` |
| 7 | Docker | prod | 5632 | 6579 | 13570 | `./data/postgres_prod` |
| 8 | Colima | prod | 5642 | 6589 | 13580 | `./data/postgres_prod` |
| 9 | Apple CLI | prod | 5652 | 6599 | 13590 | `./data/postgres_prod` |

---

## 🧪 **Test Phases**

### **Phase 1: Individual Combination Tests**

For each of the 9 combinations, test:

1. **Stack Startup**
   - ✅ Compose file exists
   - ✅ Services start successfully
   - ✅ No port conflicts

2. **PostgreSQL Health**
   - ✅ Container running
   - ✅ `pg_isready` returns success
   - ✅ Can create table
   - ✅ Can insert data
   - ✅ Data written to bind mount directory

3. **Redis Health**
   - ✅ Container running
   - ✅ `PING` returns `PONG`
   - ✅ Can SET key
   - ✅ Can GET key
   - ✅ Data persisted to bind mount directory

4. **API Health**
   - ✅ Container running
   - ✅ `/health` endpoint responds
   - ✅ Returns `{"status":"ok"}`

5. **Data Directory**
   - ✅ Directory exists
   - ✅ Directory populated with data
   - ✅ Correct permissions

### **Phase 2: Cross-Runtime Data Sharing**

For each environment (dev, test, prod), test:

1. **Docker → Apple CLI**
   - Start Docker, create test data
   - Stop Docker
   - Start Apple CLI
   - ✅ Apple CLI sees Docker's data

2. **Apple CLI → Docker**
   - Apple CLI adds more data
   - Stop Apple CLI
   - Start Docker
   - ✅ Docker sees Apple CLI's data

3. **Data Persistence**
   - ✅ Data survives runtime switches
   - ✅ Row counts match
   - ✅ No data loss

---

## ✅ **Success Criteria**

### **Individual Combinations**
- All 9 combinations start successfully
- All PostgreSQL instances healthy
- All Redis instances healthy
- All API instances responding
- All data directories populated

### **Data Sharing**
- Dev: Docker ↔ Colima ↔ Apple CLI share data
- Test: Docker ↔ Colima ↔ Apple CLI share data
- Prod: Docker ↔ Colima ↔ Apple CLI share data

### **Environment Isolation**
- Dev data ≠ Test data
- Test data ≠ Prod data
- Prod data ≠ Dev data

---

## 📋 **Test Script**

**Location**: `scripts/test-all-9-combinations.sh`

**Features**:
- Automated testing of all 9 combinations
- Cross-runtime data sharing validation
- Detailed pass/fail reporting
- Summary statistics
- Log file generation

**Usage**:
```bash
cd /Users/swami/WorkSpace/ninaivalaigal
./scripts/test-all-9-combinations.sh
```

**Output**:
- Console output with color-coded results
- Log file: `test-results-YYYYMMDD-HHMMSS.log`

---

## 🎯 **Expected Results**

### **Phase 1: Individual Tests**
```
✅ Docker/dev - Stack started
✅ Docker/dev - PostgreSQL healthy
✅ Docker/dev - PostgreSQL write successful
✅ Docker/dev - Redis healthy
✅ Docker/dev - Redis write successful
✅ Docker/dev - API responding
✅ Docker/dev - Data directory populated

... (repeat for all 9 combinations)
```

### **Phase 2: Data Sharing Tests**
```
✅ Data sharing dev - Apple CLI sees Docker's data
✅ Data sharing dev - Docker sees Apple CLI's data
✅ Data sharing test - Apple CLI sees Docker's data
✅ Data sharing test - Docker sees Apple CLI's data
✅ Data sharing prod - Apple CLI sees Docker's data
✅ Data sharing prod - Docker sees Apple CLI's data
```

### **Summary**
```
Total Tests:  60+
Passed:       60+
Failed:       0

✅ ALL TESTS PASSED!
All 9 combinations validated successfully
Cross-runtime data sharing confirmed
```

---

## ⏱️ **Estimated Duration**

- **Phase 1** (9 combinations × 30s wait): ~5 minutes
- **Phase 2** (3 environments × 3 switches × 30s): ~5 minutes
- **Total**: ~10 minutes

---

## 🔍 **What We're Validating**

### **1. Port Matrix Correctness**
- Each combination uses unique ports
- No port conflicts when running different environments
- Ports follow the formula: `Base + EnvOffset + RuntimeOffset`

### **2. Bind Mount Architecture**
- All runtimes in same environment share same directory
- Data persists across runtime switches
- No data loss or corruption

### **3. Container Orchestration**
- Docker Compose works with all runtimes
- Environment variables properly substituted
- Dependencies correctly configured

### **4. Database Functionality**
- PostgreSQL accepts connections
- Tables can be created
- Data can be inserted and queried
- Transactions work correctly

### **5. Cache Functionality**
- Redis accepts connections
- Keys can be set and retrieved
- Data persists to disk
- Password authentication works

---

## 📊 **Test Coverage**

### **Runtimes**
- ✅ Docker (native)
- ✅ Colima (lightweight alternative)
- ✅ Apple Container CLI (ARM-optimized)

### **Environments**
- ✅ Development (dev)
- ✅ Testing (test)
- ✅ Production (prod)

### **Services**
- ✅ PostgreSQL
- ✅ Redis
- ✅ API
- ✅ UI (startup only)

### **Data Operations**
- ✅ CREATE TABLE
- ✅ INSERT
- ✅ SELECT
- ✅ Redis SET
- ✅ Redis GET

---

## 🎊 **Success Indicators**

If all tests pass, we confirm:

1. ✅ **All 9 combinations are functional**
2. ✅ **Data sharing works across all runtimes**
3. ✅ **Environment isolation is maintained**
4. ✅ **Port matrix is correct**
5. ✅ **Bind mounts work as designed**
6. ✅ **System is ready for production use**

---

## 📝 **Post-Test Actions**

### **If All Tests Pass**
1. Create baseline release (v0.9.0)
2. Update documentation
3. Create colleague handoff package
4. Celebrate! 🎉

### **If Any Tests Fail**
1. Review failure details in log file
2. Identify root cause
3. Fix the issue
4. Re-run tests
5. Repeat until all pass

---

**Status**: Test in progress
**Started**: 2025-09-30 23:30
**Expected Completion**: 2025-09-30 23:40
**Log File**: `test-results-YYYYMMDD-HHMMSS.log`

---

*This is the final validation before declaring the system production-ready!* 🚀
