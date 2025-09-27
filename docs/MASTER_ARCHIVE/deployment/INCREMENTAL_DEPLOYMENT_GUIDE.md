# Incremental Deployment Guide - Mac Studio Apple Container CLI

This guide documents the incremental deployment strategy for ninaivalaigal on Mac Studio using Apple Container CLI.

## 🎯 **Deployment Strategy**

### **Phase 1: Database Foundation** ✅ **COMPLETE**
- PostgreSQL 15 + pgvector
- Validated performance and functionality
- Production-ready scripts

### **Phase 2: Connection Pooling** 🚧 **READY TO DEPLOY**
- PgBouncer for connection management
- Improved database performance under load
- Connection pooling and query routing

### **Phase 3: API Server** 🚧 **READY TO DEPLOY**
- FastAPI application server
- Complete ninaivalaigal functionality
- RESTful API with documentation

### **Phase 4: Full Stack** 🎯 **FUTURE**
- Redis for caching
- Monitoring and observability
- Load balancing and scaling

## 📋 **Available Scripts**

### **Individual Service Management**
```bash
# Database (Phase 1) - VALIDATED
./scripts/nv-db-start.sh          # Start PostgreSQL + pgvector
./scripts/nv-db-stop.sh           # Stop database
./scripts/nv-db-status.sh         # Check database health

# PgBouncer (Phase 2) - READY
./scripts/nv-pgbouncer-start.sh   # Start connection pooler
./scripts/nv-pgbouncer-stop.sh    # Stop PgBouncer

# API Server (Phase 3) - READY
./scripts/nv-api-start.sh          # Start FastAPI server
./scripts/nv-api-stop.sh           # Stop API server
```

### **Stack Management**
```bash
# Full stack operations
./scripts/nv-stack-start.sh        # Start complete stack
./scripts/nv-stack-stop.sh         # Stop complete stack
./scripts/nv-stack-status.sh       # Comprehensive status

# Incremental options
./scripts/nv-stack-start.sh --db-only          # Database only
./scripts/nv-stack-start.sh --skip-api         # DB + PgBouncer only
./scripts/nv-stack-start.sh --skip-pgbouncer   # DB + API (direct connection)
```

## 🚀 **Deployment Workflow**

### **Phase 1: Database (Current)**
```bash
# Already validated and working
./scripts/nv-db-start.sh
./scripts/nv-db-status.sh
```

### **Phase 2: Add PgBouncer**
```bash
# Start database first
./scripts/nv-db-start.sh

# Add PgBouncer
./scripts/nv-pgbouncer-start.sh

# Verify stack
./scripts/nv-stack-status.sh
```

### **Phase 3: Add API Server**
```bash
# Start full stack
./scripts/nv-stack-start.sh

# Or add API to existing DB + PgBouncer
./scripts/nv-api-start.sh

# Test API
curl http://localhost:13370/health
curl http://localhost:13370/docs
```

## 🔧 **Configuration**

### **Environment Setup**
```bash
# Copy and customize environment
cp .env.example .env

# Key settings to review:
# - POSTGRES_PASSWORD (change from default)
# - NINAIVALAIGAL_JWT_SECRET (generate secure secret)
# - Port configurations if conflicts exist
```

### **Port Allocation**
- **5433**: PostgreSQL (direct access)
- **6432**: PgBouncer (pooled access)
- **13370**: FastAPI API server

### **Connection Strings**
```bash
# Direct database (Phase 1)
DATABASE_URL=postgresql://nina:password  # pragma: allowlist secret@localhost:5433/nina

# Via PgBouncer (Phase 2+)
DATABASE_URL=postgresql://nina:password  # pragma: allowlist secret@localhost:6432/nina

# API endpoints (Phase 3+)
API_BASE=http://localhost:13370
```

## 🎯 **Validation & Testing**

### **Phase 2 Validation (PgBouncer)**
```bash
# Start DB + PgBouncer
./scripts/nv-db-start.sh
./scripts/nv-pgbouncer-start.sh

# Test direct connection
psql "postgresql://nina:password  # pragma: allowlist secret@localhost:5433/nina" -c "SELECT 'direct';"

# Test pooled connection
psql "postgresql://nina:password  # pragma: allowlist secret@localhost:6432/nina" -c "SELECT 'pooled';"

# Check PgBouncer stats
psql "postgresql://nina:password  # pragma: allowlist secret@localhost:6432/pgbouncer" -c "SHOW STATS;"
```

### **Phase 3 Validation (API)**
```bash
# Start full stack
./scripts/nv-stack-start.sh

# Test API health
curl http://localhost:13370/health

# Test API documentation
open http://localhost:13370/docs

# Test with existing test suite
export DATABASE_URL="postgresql://nina:password  # pragma: allowlist secret@localhost:6432/nina"
pytest tests/
```

## 🔍 **Monitoring & Troubleshooting**

### **Stack Status**
```bash
# Comprehensive status check
./scripts/nv-stack-status.sh

# Individual service logs
container logs nv-db
container logs nv-pgbouncer
container logs nv-api
```

### **Common Issues**

#### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :5433
lsof -i :6432
lsof -i :13370

# Change ports in .env if needed
```

#### **Database Connection Issues**
```bash
# Test database directly
./scripts/nv-db-status.sh

# Test PgBouncer connectivity
nc -z localhost 6432

# Check container networking
container list
```

#### **API Build Issues**
```bash
# Check API container logs
container logs nv-api

# Rebuild API image
./scripts/nv-api-stop.sh
./scripts/nv-api-start.sh
```

## 📊 **Performance Expectations**

### **Phase 1 (Database Only)**
- Container startup: ~2-3 seconds
- Database ready: ~10 seconds
- Query performance: ~0.111s for complex operations

### **Phase 2 (+ PgBouncer)**
- Additional startup: ~5-10 seconds
- Connection pooling: 20 default connections
- Reduced connection overhead

### **Phase 3 (+ API)**
- API startup: ~15-30 seconds (includes build)
- Health check response: <100ms
- Full stack ready: ~45-60 seconds

## 🎉 **Success Criteria**

### **Phase 2 Complete When:**
- ✅ PgBouncer accepts connections on port 6432
- ✅ Can query database through PgBouncer
- ✅ Connection pooling stats available
- ✅ Performance improved under concurrent load

### **Phase 3 Complete When:**
- ✅ API responds to health checks
- ✅ API documentation accessible
- ✅ All existing tests pass via API
- ✅ Full stack manageable via scripts

This incremental approach ensures each phase is solid before adding complexity! 🚀
