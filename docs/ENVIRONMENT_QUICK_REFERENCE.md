# 🚀 Environment Management - Quick Reference

## **One-Line Commands**

```bash
# 🔥 MOST COMMON COMMANDS
NINA_ENV=dev NINA_RUNTIME=docker make stack-up     # Start dev with Docker
NINA_ENV=test NINA_RUNTIME=colima make stack-up    # Start test with Colima
NINA_ENV=prod NINA_RUNTIME=apple make stack-up     # Start prod with Apple CLI

# 📊 CHECK STATUS
NINA_ENV=dev NINA_RUNTIME=docker make stack-status

# 🛑 STOP ENVIRONMENT
NINA_ENV=dev NINA_RUNTIME=docker make stack-down
```

---

## **🎯 Port Quick Lookup**

| Env+Runtime | Postgres | Redis | API   | UI   | Database Name |
|-------------|----------|-------|-------|------|---------------|
| dev+docker | 5432     | 6379  | 13370 | 8081 | nina_dev      |
| dev+colima | 5442     | 6389  | 13380 | 8091 | nina_dev      |
| test+docker | 5532     | 6479  | 13470 | 8181 | nina_test     |
| prod+apple  | 5652     | 6599  | 13590 | 8301 | nina_prod     |

**🔍 Get any port**: `./scripts/get-port.sh postgres dev docker`

---

## **💾 Database Access**

```bash
# 🐘 PostgreSQL Shell (includes Apache AGE)
NINA_ENV=dev NINA_RUNTIME=docker make db-shell

# 🔴 Redis CLI
NINA_ENV=dev NINA_RUNTIME=docker make redis-shell

# 🌐 Direct Connection
psql postgresql://nina:password@localhost:5432/nina_dev
redis-cli -h localhost -p 6379
```

---

## **🔧 Troubleshooting**

```bash
# ❓ What's running?
docker ps

# 🔍 Check port usage
lsof -i :5432

# 🧪 Validate all combinations
./scripts/validate-all-combinations.sh

# 📋 View logs
NINA_ENV=dev NINA_RUNTIME=docker make logs
```

---

## **⚡ Pro Tips**

### **🔄 Parallel Development**
```bash
# Run multiple environments simultaneously
NINA_ENV=dev NINA_RUNTIME=docker make stack-up &
NINA_ENV=test NINA_RUNTIME=colima make stack-up &
# No conflicts! Different ports automatically assigned
```

### **🎛️ Environment Switching**
```bash
# Quick environment variables
export NINA_ENV=test NINA_RUNTIME=colima
make stack-up    # Uses your exported settings
```

### **🛡️ Safety First**
- ✅ **dev** = Development data (safe to reset)
- ⚠️ **test** = Testing data (isolated)
- 🚨 **prod** = Production data (NEVER reset)

---

## **🏗️ Architecture Summary**

```
┌─────────────────────────────────────────────────────────┐
│                 Triple-Layer Isolation                  │
├─────────────────────────────────────────────────────────┤
│ Environment: dev/test/prod                              │
│ Runtime: docker/colima/apple                            │
│ Services: postgres+redis+api+ui                         │
├─────────────────────────────────────────────────────────┤
│ Result: 9 unique combinations, zero conflicts           │
└─────────────────────────────────────────────────────────┘
```

**🎯 Key Benefits:**
- No database conflicts
- Parallel environments
- Runtime flexibility
- Production safety

---

## **📞 Emergency Commands**

```bash
# 🚨 Stop everything
docker stop $(docker ps -q)

# 🧹 Clean restart
NINA_ENV=dev NINA_RUNTIME=docker make stack-down
NINA_ENV=dev NINA_RUNTIME=docker make stack-up

# 🔄 Reset development database (⚠️ DESTRUCTIVE)
NINA_ENV=dev NINA_RUNTIME=docker make db-reset
```

---

**📚 Full Documentation**: `docs/ENVIRONMENT_MANAGEMENT.md`
