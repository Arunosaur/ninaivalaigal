# Environment Management Guide

## 🎯 **Triple-Layer Detection System**

Ninaivalaigal uses a sophisticated triple-layer detection system to prevent environment conflicts and enable parallel development workflows.

### **Architecture Overview**

```
Environment (dev/test/prod) × Runtime (docker/colima/apple) × Service Isolation
```

This creates **9 unique combinations** with completely isolated:
- Port assignments
- Database names
- Container names
- Volume storage
- Network namespaces

---

## 🏗️ **Core Services & Architecture**

### **Service Stack**
1. **PostgreSQL Database** (includes Apache AGE graph extension + pgvector)
2. **Redis Cache** (memory caching and session storage)
3. **FastAPI Server** (Python backend)
4. **Frontend UI** (React/Next.js interface)
5. **PgBouncer** (connection pooling - production only)

### **Database Features**
- **Apache AGE**: Graph database capabilities within PostgreSQL
- **pgvector**: Vector similarity search for AI/ML features
- **Full ACID compliance**: Transactions, constraints, indexes
- **Automatic migrations**: Alembic-managed schema updates

---

## 📊 **Port Assignment Matrix**

| Environment | Runtime | Postgres | Redis | API   | UI   | PgBouncer | Database Name |
|-------------|---------|----------|-------|-------|------|-----------|---------------|
| **dev**     | docker  | 5432     | 6379  | 13370 | 8081 | 6432      | nina_dev      |
| **dev**     | colima  | 5442     | 6389  | 13380 | 8091 | 6442      | nina_dev      |
| **dev**     | apple   | 5452     | 6399  | 13390 | 8101 | 6452      | nina_dev      |
| **test**    | docker  | 5532     | 6479  | 13470 | 8181 | 6532      | nina_test     |
| **test**    | colima  | 5542     | 6489  | 13480 | 8191 | 6542      | nina_test     |
| **test**    | apple   | 5552     | 6499  | 13490 | 8201 | 6552      | nina_test     |
| **prod**    | docker  | 5632     | 6579  | 13570 | 8281 | 6632      | nina_prod     |
| **prod**    | colima  | 5642     | 6589  | 13580 | 8291 | 6642      | nina_prod     |
| **prod**    | apple   | 5652     | 6599  | 13590 | 8301 | 6652      | nina_prod     |

### **Port Calculation Formula**
```
Final Port = Base Port + Environment Offset + Runtime Offset

Environment Offsets:
- dev: +0
- test: +100
- prod: +200

Runtime Offsets:
- docker: +0
- colima: +10
- apple: +20
```

---

## 💾 **Data Persistence Strategy**

### **Volume Management**
Each environment maintains **separate data volumes**:

```bash
# Development
postgres_data_dev/     # PostgreSQL data (includes Apache AGE graphs)
redis_data_dev/        # Redis persistence

# Test
postgres_data_test/    # Isolated test database
redis_data_test/       # Isolated test cache

# Production
postgres_data_prod/    # Production database
redis_data_prod/       # Production cache
```

### **Persistence Guarantees**
- ✅ **Full Persistence**: All data survives container restarts
- ✅ **Environment Isolation**: No data leakage between environments
- ✅ **Apache AGE Graphs**: Graph data persisted with PostgreSQL
- ✅ **Redis Snapshots**: Cache data persisted to disk
- ✅ **Backup Compatible**: Standard PostgreSQL backup tools work

### **Data Safety**
- **Atomic Operations**: All database operations are ACID-compliant
- **Crash Recovery**: PostgreSQL WAL ensures data integrity
- **Graph Consistency**: Apache AGE maintains graph ACID properties
- **Redis Durability**: Configurable persistence (RDB + AOF)

---

## 🚀 **Usage Examples**

### **Basic Operations**
```bash
# Start development environment with Docker
NINA_ENV=dev NINA_RUNTIME=docker make stack-up

# Start test environment with Colima
NINA_ENV=test NINA_RUNTIME=colima make stack-up

# Start production with Apple Container CLI
NINA_ENV=prod NINA_RUNTIME=apple make stack-up
```

### **Environment Management**
```bash
# Check status of any environment
NINA_ENV=test NINA_RUNTIME=colima make stack-status

# Stop specific environment
NINA_ENV=dev NINA_RUNTIME=docker make stack-down

# View logs for specific environment
NINA_ENV=prod NINA_RUNTIME=apple make stack-logs
```

### **Database Access**
```bash
# Connect to development database
NINA_ENV=dev NINA_RUNTIME=docker make db-shell

# Connect to test database
NINA_ENV=test NINA_RUNTIME=colima make db-shell

# Connect to production database
NINA_ENV=prod NINA_RUNTIME=apple make db-shell
```

### **Parallel Development**
```bash
# Run all environments simultaneously
NINA_ENV=dev NINA_RUNTIME=docker make stack-up &
NINA_ENV=test NINA_RUNTIME=colima make stack-up &
NINA_ENV=prod NINA_RUNTIME=apple make stack-up &

# Each runs on different ports - no conflicts!
```

---

## 🔧 **Runtime Characteristics**

### **Docker Runtime**
- **Best for**: CI/CD, Linux development, cross-platform compatibility
- **Performance**: Standard container performance
- **Memory**: Moderate overhead
- **Compatibility**: Works everywhere

### **Colima Runtime**
- **Best for**: macOS development, Docker Desktop alternative
- **Performance**: Optimized for macOS, lower memory usage
- **Memory**: Efficient resource usage
- **Compatibility**: macOS only

### **Apple Container CLI Runtime**
- **Best for**: Production, Apple Silicon optimization
- **Performance**: 3-5x faster on Apple Silicon
- **Memory**: Minimal overhead
- **Compatibility**: macOS Apple Silicon only

---

## 🛡️ **Safety Features**

### **Conflict Prevention**
- ✅ **Unique Ports**: No port conflicts between environments
- ✅ **Isolated Containers**: Separate container names
- ✅ **Separate Networks**: Independent network namespaces
- ✅ **Volume Isolation**: No shared data volumes

### **Production Safety**
- ✅ **Environment Detection**: Automatic prod/dev differentiation
- ✅ **Connection Pooling**: PgBouncer for production workloads
- ✅ **Resource Limits**: Environment-specific resource allocation
- ✅ **Health Monitoring**: Comprehensive health checks

---

## 🔍 **Troubleshooting**

### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :5432

# Validate port assignments
./scripts/validate-all-combinations.sh
```

### **Database Issues**
```bash
# Check database health
NINA_ENV=dev NINA_RUNTIME=docker make db-health

# Reset database (⚠️ DESTRUCTIVE)
NINA_ENV=dev NINA_RUNTIME=docker make db-reset
```

### **Container Issues**
```bash
# View container logs
NINA_ENV=test NINA_RUNTIME=colima make logs

# Restart specific environment
NINA_ENV=test NINA_RUNTIME=colima make restart
```

---

## 📋 **Quick Reference**

### **Environment Variables**
```bash
export NINA_ENV=dev          # dev, test, prod
export NINA_RUNTIME=docker   # docker, colima, apple
```

### **Key Commands**
```bash
make stack-up       # Start environment
make stack-down     # Stop environment
make stack-status   # Check status
make stack-logs     # View logs
make db-shell       # Database access
```

### **Configuration Files**
- `.env.sample` - Environment configuration template
- `compose.docker.yml` - Docker runtime configuration
- `compose.colima.yml` - Colima runtime configuration
- `compose.apple.yml` - Apple Container CLI configuration
- `scripts/get-port.sh` - Dynamic port assignment logic

---

## ⚡ **Performance Notes**

### **Development (dev)**
- **Live Reload**: Enabled for rapid development
- **Debug Mode**: Full logging and error details
- **Resource Limits**: Relaxed for development convenience

### **Testing (test)**
- **Isolated Data**: Clean slate for each test run
- **Parallel Safe**: Multiple test suites can run simultaneously
- **Fast Startup**: Optimized for quick test cycles

### **Production (prod)**
- **Connection Pooling**: PgBouncer for high concurrency
- **Resource Optimization**: Production-tuned memory/CPU limits
- **Health Monitoring**: Comprehensive monitoring and alerting
- **Security Hardening**: Production security configurations
