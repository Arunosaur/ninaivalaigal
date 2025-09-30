# 🏷️ Naming Conventions & Dynamic Discovery

## 🎯 **Consistent Naming Convention**

### **Container Names**
```
ninaivalaigal-{environment}-{service}

Examples:
- ninaivalaigal-dev-db
- ninaivalaigal-test-redis
- ninaivalaigal-prod-api
- ninaivalaigal-dev-ui
```

### **Database Names**
```
ninaivalaigal_{environment}

Examples:
- ninaivalaigal_dev
- ninaivalaigal_test
- ninaivalaigal_prod
```

### **Database User**
```
ninaivalaigal_app (consistent across all environments)
```

### **Network Names**
```
ninaivalaigal_{environment}_network

Examples:
- ninaivalaigal_dev_network
- ninaivalaigal_test_network
- ninaivalaigal_prod_network
```

---

## 🔍 **Dynamic Discovery System**

### **How API/UI Discovers Database Connection**

The system uses **environment-aware dynamic discovery** in `server/config.py`:

```python
def get_dynamic_database_url() -> str:
    # 1. Check environment variables first
    env_db_url = os.getenv("NINAIVALAIGAL_DATABASE_URL")
    if env_db_url:
        return env_db_url

    # 2. Get current environment and runtime
    nina_env = os.getenv("NINA_ENV", "dev")           # dev/test/prod
    nina_runtime = os.getenv("NINA_RUNTIME", "docker") # docker/colima/apple

    # 3. Calculate dynamic ports using get-port.sh
    postgres_port = get_port("postgres", nina_env, nina_runtime)

    # 4. Construct database name and connection
    db_name = f"ninaivalaigal_{nina_env}"
    db_user = "ninaivalaigal_app"

    # 5. Try container discovery, fallback to localhost
    return f"postgresql://{db_user}:{password}@localhost:{postgres_port}/{db_name}"
```

### **Discovery Priority**
1. **Environment Variable Override** (`NINAIVALAIGAL_DATABASE_URL`)
2. **PgBouncer Container** (production environments)
3. **PostgreSQL Container** (direct connection)
4. **Localhost Fallback** (calculated ports)

---

## 📊 **Complete Environment Matrix**

| Environment | Runtime | Container Names | Database | Ports | Network |
|-------------|---------|----------------|----------|-------|---------|
| **dev** | docker | ninaivalaigal-dev-* | ninaivalaigal_dev | 5432,6379,13370,8081 | ninaivalaigal_dev_network |
| **dev** | colima | ninaivalaigal-dev-* | ninaivalaigal_dev | 5442,6389,13380,8091 | ninaivalaigal_dev_network |
| **dev** | apple | ninaivalaigal-dev-* | ninaivalaigal_dev | 5452,6399,13390,8101 | ninaivalaigal_dev_network |
| **test** | docker | ninaivalaigal-test-* | ninaivalaigal_test | 5532,6479,13470,8181 | ninaivalaigal_test_network |
| **test** | colima | ninaivalaigal-test-* | ninaivalaigal_test | 5542,6489,13480,8191 | ninaivalaigal_test_network |
| **test** | apple | ninaivalaigal-test-* | ninaivalaigal_test | 5552,6499,13490,8201 | ninaivalaigal_test_network |
| **prod** | docker | ninaivalaigal-prod-* | ninaivalaigal_prod | 5632,6579,13570,8281 | ninaivalaigal_prod_network |
| **prod** | colima | ninaivalaigal-prod-* | ninaivalaigal_prod | 5642,6589,13580,8291 | ninaivalaigal_prod_network |
| **prod** | apple | ninaivalaigal-prod-* | ninaivalaigal_prod | 5652,6599,13590,8301 | ninaivalaigal_prod_network |

---

## 🔧 **How Services Connect**

### **API Server Connection Logic**
```bash
# Environment variables automatically set by docker-compose
NINA_ENV=test
NINA_RUNTIME=colima
NINAIVALAIGAL_DATABASE_URL=postgresql://ninaivalaigal_app:password@postgres:5432/ninaivalaigal_test

# API discovers:
# - Container: ninaivalaigal-test-db
# - Database: ninaivalaigal_test
# - Port: 5542 (calculated)
# - Network: ninaivalaigal_test_network
```

### **UI Connection Logic**
```bash
# UI connects to API via calculated port
API_URL=http://localhost:13480  # test+colima = 13480

# UI discovers API automatically based on:
# - NINA_ENV=test
# - NINA_RUNTIME=colima
# - Calculated API port: 13480
```

---

## 🎯 **Apache AGE Integration**

### **Graph Database Access**
Apache AGE is **integrated within PostgreSQL**, not a separate service:

```sql
-- Connect to any environment's PostgreSQL
psql postgresql://ninaivalaigal_app:password@localhost:5542/ninaivalaigal_test

-- Apache AGE is available as extension
SELECT * FROM ag_catalog.create_graph('ninaivalaigal_intelligence');

-- Graph operations work within the same database
SELECT * FROM cypher('ninaivalaigal_intelligence', $$
  MATCH (n) RETURN n LIMIT 10
$$) AS (result agtype);
```

### **Graph Schema**
- **Graph Name**: `ninaivalaigal_intelligence` (consistent across environments)
- **Node Types**: User, Memory, Context, Agent, Team, Organization, Session, Macro, Token
- **Relationships**: CREATED, ACCESSED, BELONGS_TO, MEMBER_OF, etc.
- **Storage**: Within PostgreSQL data directory (fully persistent)

---

## 🔄 **Environment Variables**

### **Required Variables**
```bash
# Core environment selection
NINA_ENV=dev|test|prod
NINA_RUNTIME=docker|colima|apple

# Database credentials
NINA_DB_PASSWORD=secure_password
NINA_JWT_SECRET=jwt_secret

# Optional overrides
NINAIVALAIGAL_DATABASE_URL=postgresql://...  # Skip auto-discovery
```

### **Auto-Generated Variables**
```bash
# Calculated by system
POSTGRES_PORT=5542      # Based on env+runtime
REDIS_PORT=6489         # Based on env+runtime
API_PORT=13480          # Based on env+runtime
UI_PORT=8191            # Based on env+runtime
```

---

## 🚀 **Usage Examples**

### **Start Environment with Auto-Discovery**
```bash
# Set environment
export NINA_ENV=test
export NINA_RUNTIME=colima

# Start stack - everything auto-configured
make stack-up

# API automatically connects to:
# - Database: ninaivalaigal_test
# - Container: ninaivalaigal-test-db
# - Port: 5542
# - Apache AGE: Available within same DB
```

### **Manual Database Connection**
```bash
# Connect to any environment
NINA_ENV=test NINA_RUNTIME=colima ./scripts/get-port.sh postgres test colima
# Returns: 5542

# Connect directly
psql postgresql://ninaivalaigal_app:password@localhost:5542/ninaivalaigal_test
```

### **Override Auto-Discovery**
```bash
# Skip auto-discovery with explicit URL
export NINAIVALAIGAL_DATABASE_URL="postgresql://custom_user:custom_pass@custom_host:5432/custom_db"
make stack-up
# API uses explicit URL instead of auto-discovery
```

---

## 🛡️ **Data Persistence & Safety**

### **Volume Persistence**
- **PostgreSQL Data**: Includes Apache AGE graphs, pgvector indexes, all tables
- **Redis Data**: Cache persistence with RDB snapshots
- **Environment Isolation**: Completely separate data per environment
- **Container Restart Safe**: All data survives container restarts

### **Backup Strategy**
```bash
# Backup any environment
NINA_ENV=prod NINA_RUNTIME=apple make db-backup

# Restore to different environment
NINA_ENV=test NINA_RUNTIME=docker make db-restore
```

---

## 🎉 **Benefits Achieved**

✅ **Consistent Naming**: All components follow `ninaivalaigal_*` convention
✅ **Auto-Discovery**: API/UI automatically find correct database/ports
✅ **Environment Isolation**: Zero conflicts between dev/test/prod
✅ **Apache AGE Integration**: Graph capabilities within main database
✅ **Runtime Flexibility**: Works with Docker, Colima, Apple Container CLI
✅ **Production Ready**: PgBouncer support, connection pooling, monitoring
✅ **Developer Friendly**: Simple commands, automatic configuration
