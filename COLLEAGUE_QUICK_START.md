# 🚀 Colleague Quick Start Guide

**Welcome to ninaivalaigal!** This guide will get you up and running in minutes.

---

## 📋 Prerequisites

- **Docker** OR **Colima** OR **Apple Container CLI** (pick one)
- **Make** (comes with macOS/Linux)
- **Git**

---

## 🎯 Quick Start (3 Commands)

```bash
# 1. Clone the repo
git clone https://github.com/Arunosaur/ninaivalaigal.git
cd ninaivalaigal

# 2. Choose your runtime and start the stack
make docker-dev-up      # If using Docker
# OR
make colima-dev-up      # If using Colima
# OR
make apple-dev-up       # If using Apple Container CLI

# 3. Verify everything is running
make health
```

**That's it!** Your development environment is ready.

---

## 🎮 Essential Make Commands

### **Start/Stop Stack**

```bash
# Docker
make docker-dev-up          # Start dev environment
make docker-dev-down        # Stop dev environment

# Colima
make colima-dev-up          # Start dev environment
make colima-dev-down        # Stop dev environment

# Apple Container CLI
make apple-dev-up           # Start dev environment
make apple-dev-down         # Stop dev environment
```

### **Health Checks**

```bash
make health                 # Check all services
make logs                   # View container logs
```

### **Access Services**

```bash
# API Documentation
open http://localhost:13370/docs

# UI (if running)
open http://localhost:8081

# Health endpoint
curl http://localhost:13370/health
```

---

## 🗺️ Port Matrix Reference

### **Development Environment (dev)**

| Runtime | PostgreSQL | Redis | API | UI |
|---------|-----------|-------|-----|-----|
| **Docker** | 5432 | 6379 | 13370 | 8081 |
| **Colima** | 5442 | 6389 | 13380 | 8091 |
| **Apple CLI** | 5452 | 6399 | 13390 | 8101 |

### **Test Environment (test)**

| Runtime | PostgreSQL | Redis | API | UI |
|---------|-----------|-------|-----|-----|
| **Docker** | 5532 | 6479 | 13470 | - |
| **Colima** | 5542 | 6489 | 13480 | - |
| **Apple CLI** | 5552 | 6499 | 13490 | - |

### **Production Environment (prod)**

| Runtime | PostgreSQL | Redis | API | UI |
|---------|-----------|-------|-----|-----|
| **Docker** | 5632 | 6579 | 13570 | - |
| **Colima** | 5642 | 6589 | 13580 | - |
| **Apple CLI** | 5652 | 6599 | 13590 | - |

---

## 🔑 Default Credentials (Development Only)

```bash
# Database
User: nina
Password: secure_nina_password
Database: ninaivalaigal_dev

# Redis
Password: secure_nina_password

# API
JWT Secret: dev_jwt_secret (development only)
```

**⚠️ Never use these in production!**

---

## 🧪 Running Tests

```bash
# Smoke tests (quick validation)
make smoke-tests

# Full test suite
make test

# Specific test file
pytest tests/smoke/test_api.py -v
```

---

## 🐛 Troubleshooting

### **Port Already in Use**

```bash
# Find what's using the port
lsof -i :13370

# Kill the process
kill -9 <PID>

# Or use a different runtime (different ports)
make colima-dev-up  # Uses 13380 instead of 13370
```

### **Containers Not Starting**

```bash
# Check logs
make logs

# Restart everything
make docker-dev-down
make docker-dev-up
```

### **Database Connection Issues**

```bash
# Check database is running
docker ps | grep postgres

# Test connection
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT 1;"
```

---

## 📚 Important Files

```
ninaivalaigal/
├── compose.docker.yml      # Docker runtime config
├── compose.colima.yml      # Colima runtime config
├── compose.apple.yml       # Apple CLI runtime config
├── Makefile               # All make commands
├── server/                # API source code
├── ui/                    # Frontend source code
└── tests/                 # Test suite
```

---

## 🎓 Next Steps

1. **Explore the API**: http://localhost:13370/docs
2. **Read the docs**: Check `docs/` directory
3. **Run tests**: `make smoke-tests`
4. **Join the team**: Ask questions in Slack/Teams

---

## 💡 Pro Tips

### **Data Sharing Across Runtimes**

All runtimes share data within the same environment:
```bash
# Start with Docker
make docker-dev-up
# Create some data...

# Switch to Apple CLI (sees same data!)
make docker-dev-down
make apple-dev-up
```

### **Multiple Environments Simultaneously**

Run dev, test, and prod at the same time:
```bash
make docker-dev-up          # Dev on ports 5432, 6379, 13370
make docker-test-up         # Test on ports 5532, 6479, 13470
make docker-prod-up         # Prod on ports 5632, 6579, 13570
```

### **Quick Health Check**

```bash
# One-liner to check everything
curl -s http://localhost:13370/health | jq
```

---

## 🆘 Getting Help

- **Documentation**: `docs/` directory
- **Issues**: GitHub Issues
- **Slack**: #ninaivalaigal channel
- **Email**: team@ninaivalaigal.com

---

## ✅ Validation Checklist

Before starting development, verify:

- [ ] Stack is running: `make health`
- [ ] API responds: `curl http://localhost:13370/health`
- [ ] Database connected: `docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT 1;"`
- [ ] Redis connected: `docker exec ninaivalaigal-dev-redis redis-cli -a secure_nina_password ping`
- [ ] Tests pass: `make smoke-tests`

**All green? You're ready to code!** 🎉

---

**Questions?** Check `CROSS_RUNTIME_HANDOFF.md` for more details or ask the team!
