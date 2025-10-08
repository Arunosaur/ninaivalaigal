# Uniform Architecture Design - The Right Way

**Created:** 2024-10-06
**Status:** 🏗️ Architecture Design (Day 4)
**Principle:** One consistent architecture across ALL runtimes and environments

---

## 🎯 Core Principle

**Every environment should have UNIFORM architecture:**
- Same component stack
- Same connection patterns
- Same configuration approach
- Only runtime/environment-specific values differ

---

## 🏗️ Uniform Architecture

### Component Stack (Identical Everywhere)

```
┌─────────────────────────────────────────┐
│  Presentation Layer                      │
│  • Customer App (external users)        │
│  • Admin Console (internal staff)       │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Application Layer                       │
│  • FastAPI Backend                       │
│  • Business Logic                        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Connection Pooling Layer (MANDATORY)   │
│  • PgBouncer                            │
│  ⚠️  ALL apps connect through here      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Data Layer                              │
│  • PostgreSQL (pgvector + Apache AGE)   │
│  • Redis (cache + sessions)             │
└─────────────────────────────────────────┘
```

**This architecture is IDENTICAL in:**
- Docker runtime
- Colima runtime
- Apple CLI runtime
- Dev environment
- Test environment
- Prod environment

**Only differences:** Ports, IPs, resource limits

---

## 📐 Configuration Hierarchy

### 1. Global Defaults (Source of Truth)

**File:** `configs/defaults.env`

```bash
# Stack Architecture (NEVER changes)
STACK_COMPONENTS="db,pgbouncer,redis,api,customer-app,admin-console"

# Naming Convention (SPEC-086)
CONTAINER_PREFIX="ninaivalaigal"
NAMING_PATTERN="${CONTAINER_PREFIX}-${RUNTIME}-${ENV}-${COMPONENT}"

# SPEC-086 Base Ports
BASE_DB_PORT=5432
BASE_PGBOUNCER_PORT=6432
BASE_REDIS_PORT=6379
BASE_API_PORT=13370
BASE_CUSTOMER_UI_PORT=8081
BASE_ADMIN_UI_PORT=8181

# Runtime Offsets (SPEC-086)
DOCKER_OFFSET=0
COLIMA_OFFSET=10
APPLE_OFFSET=20

# Environment Offsets (SPEC-086)
DEV_OFFSET=0
TEST_OFFSET=100
PROD_OFFSET=200

# Default Resource Limits
DEFAULT_DB_MEMORY=1024m
DEFAULT_REDIS_MEMORY=512m
DEFAULT_API_MEMORY=512m

# Default Images
DEFAULT_DB_IMAGE="ghcr.io/arunosaur/ninaivalaigal-db:latest"
DEFAULT_PGBOUNCER_IMAGE="bitnami/pgbouncer:1.22.1"
DEFAULT_REDIS_IMAGE="redis:7-alpine"
DEFAULT_API_IMAGE="ghcr.io/arunosaur/ninaivalaigal-api:latest"
```

### 2. Runtime-Specific Configs

**File:** `configs/runtime-docker.env`

```bash
NINA_RUNTIME=docker
RUNTIME_OFFSET=0
CONTAINER_COMMAND=docker
PLATFORM=linux/arm64  # or linux/amd64
```

**File:** `configs/runtime-colima.env`

```bash
NINA_RUNTIME=colima
RUNTIME_OFFSET=10
CONTAINER_COMMAND=docker
PLATFORM=linux/arm64
```

**File:** `configs/runtime-apple.env`

```bash
NINA_RUNTIME=apple
RUNTIME_OFFSET=20
CONTAINER_COMMAND=container
PLATFORM=linux/arm64
```

### 3. Environment-Specific Configs

**File:** `configs/env-dev.env`

```bash
NINA_ENV=dev
ENV_OFFSET=0
LOG_LEVEL=debug
ENABLE_DEBUG=true
ENABLE_HOT_RELOAD=true
```

**File:** `configs/env-test.env`

```bash
NINA_ENV=test
ENV_OFFSET=100
LOG_LEVEL=info
ENABLE_DEBUG=false
ENABLE_HOT_RELOAD=false
```

**File:** `configs/env-prod.env`

```bash
NINA_ENV=prod
ENV_OFFSET=200
LOG_LEVEL=warning
ENABLE_DEBUG=false
ENABLE_HOT_RELOAD=false
```

### 4. Secrets (NEVER in Git)

**File:** `configs/secrets-{runtime}-{env}.env` (gitignored)

```bash
# configs/secrets-apple-dev.env
NINA_DB_PASSWORD=secure_db_password_here
NINA_REDIS_PASSWORD=secure_redis_password_here
NINA_JWT_SECRET=secure_jwt_secret_here
```

---

## 🔧 Unified Script Architecture

### Master Configuration Loader

**File:** `scripts/lib/config-loader.sh`

```bash
#!/usr/bin/env bash
# Unified Configuration Loader
# Loads config in proper hierarchy: defaults → runtime → env → secrets

load_config() {
    local runtime=${1:-apple}
    local env=${2:-dev}

    # 1. Load defaults (required)
    source "${ROOT_DIR}/configs/defaults.env"

    # 2. Load runtime config (required)
    source "${ROOT_DIR}/configs/runtime-${runtime}.env"

    # 3. Load environment config (required)
    source "${ROOT_DIR}/configs/env-${env}.env"

    # 4. Load secrets (required for non-dev)
    local secrets_file="${ROOT_DIR}/configs/secrets-${runtime}-${env}.env"
    if [ -f "$secrets_file" ]; then
        source "$secrets_file"
    else
        if [ "$env" != "dev" ]; then
            echo "ERROR: Secrets file required for ${env}: ${secrets_file}"
            exit 1
        fi
        # Dev fallback to defaults
        NINA_DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
        NINA_REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"
        NINA_JWT_SECRET="${NINA_JWT_SECRET:-dev_jwt_secret}"
    fi

    # 5. Calculate ports using SPEC-086 formula
    calculate_ports

    # 6. Validate configuration
    validate_config
}

calculate_ports() {
    # Final Port = Base Port + Environment Offset + Runtime Offset
    export DB_PORT=$((BASE_DB_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export PGBOUNCER_PORT=$((BASE_PGBOUNCER_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export REDIS_PORT=$((BASE_REDIS_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export API_PORT=$((BASE_API_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export CUSTOMER_UI_PORT=$((BASE_CUSTOMER_UI_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export ADMIN_UI_PORT=$((BASE_ADMIN_UI_PORT + ENV_OFFSET + RUNTIME_OFFSET))

    # Container names
    export DB_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-db"
    export PGBOUNCER_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-pgbouncer"
    export REDIS_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-redis"
    export API_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-api"
    export CUSTOMER_APP_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-customer-app"
    export ADMIN_CONSOLE_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-admin-console"
}

validate_config() {
    # Ensure all required variables are set
    local required_vars=(
        "NINA_RUNTIME"
        "NINA_ENV"
        "DB_PORT"
        "PGBOUNCER_PORT"
        "REDIS_PORT"
        "NINA_DB_PASSWORD"
        "NINA_REDIS_PASSWORD"
        "NINA_JWT_SECRET"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required variable $var is not set"
            exit 1
        fi
    done
}
```

### Unified Stack Start Script

**File:** `scripts/stack-start-unified.sh`

```bash
#!/usr/bin/env bash
# Unified Stack Startup - Works with ANY runtime/environment
# Usage: ./stack-start-unified.sh [runtime] [environment]
#   runtime: docker|colima|apple (default: apple)
#   environment: dev|test|prod (default: dev)

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration library
source "${SCRIPT_DIR}/lib/config-loader.sh"

# Parse arguments
RUNTIME=${1:-${NINA_RUNTIME:-apple}}
ENVIRONMENT=${2:-${NINA_ENV:-dev}}

# Load configuration (single source of truth)
load_config "$RUNTIME" "$ENVIRONMENT"

# Now start the stack using loaded configuration
# All components use the SAME startup logic
# Only ports/IPs differ based on config

start_database() {
    log_info "Starting Database: $DB_CONTAINER on port $DB_PORT"

    $CONTAINER_COMMAND run -d --name "$DB_CONTAINER" \
        -p "$DB_PORT:5432" \
        -e POSTGRES_DB="ninaivalaigal_${NINA_ENV}" \
        -e POSTGRES_USER=nina \
        -e POSTGRES_PASSWORD="$NINA_DB_PASSWORD" \
        -e POSTGRES_HOST_AUTH_METHOD=md5 \
        -v "ninaivalaigal_${NINA_ENV}_db_data:/var/lib/postgresql/data" \
        "$DEFAULT_DB_IMAGE"

    # Health check (same for all runtimes)
    wait_for_database
}

start_pgbouncer() {
    log_info "Starting PgBouncer: $PGBOUNCER_CONTAINER on port $PGBOUNCER_PORT"

    local db_ip=$(get_container_ip "$DB_CONTAINER")

    $CONTAINER_COMMAND run -d --name "$PGBOUNCER_CONTAINER" \
        -p "$PGBOUNCER_PORT:6432" \
        -e POSTGRESQL_HOST="$db_ip" \
        -e POSTGRESQL_PORT=5432 \
        -e POSTGRESQL_DATABASE="ninaivalaigal_${NINA_ENV}" \
        -e POSTGRESQL_USERNAME=nina \
        -e POSTGRESQL_PASSWORD="$NINA_DB_PASSWORD" \
        -e PGBOUNCER_POOL_MODE=transaction \
        "$DEFAULT_PGBOUNCER_IMAGE"

    # Health check (same for all runtimes)
    wait_for_pgbouncer
}

# ... same pattern for Redis, API, UIs

main() {
    log_info "Starting Ninaivalaigal Stack"
    log_info "Runtime: $RUNTIME | Environment: $ENVIRONMENT"
    log_info "Ports: DB=$DB_PORT, PgBouncer=$PGBOUNCER_PORT, Redis=$REDIS_PORT, API=$API_PORT"

    # Same startup sequence for ALL runtimes
    start_database
    start_pgbouncer
    start_redis
    start_api
    start_customer_ui
    start_admin_console

    show_stack_info
}

main "$@"
```

---

## 📋 Usage Examples

### Start Any Runtime/Environment Combo

```bash
# Apple CLI + Dev (default)
./scripts/stack-start-unified.sh

# Docker + Dev
./scripts/stack-start-unified.sh docker dev

# Colima + Test
./scripts/stack-start-unified.sh colima test

# Apple CLI + Prod
./scripts/stack-start-unified.sh apple prod
```

### Makefile Integration

```makefile
# Start with runtime/env detection
stack-start:
	@./scripts/stack-start-unified.sh ${NINA_RUNTIME} ${NINA_ENV}

# Specific combinations
stack-start-docker-dev:
	@./scripts/stack-start-unified.sh docker dev

stack-start-apple-dev:
	@./scripts/stack-start-unified.sh apple dev

stack-start-colima-test:
	@./scripts/stack-start-unified.sh colima test
```

---

## 🔐 Secrets Management

### Development (Local)

```bash
# Create dev secrets (gitignored)
cat > configs/secrets-apple-dev.env <<EOF
NINA_DB_PASSWORD=dev_password_123
NINA_REDIS_PASSWORD=dev_redis_456
NINA_JWT_SECRET=dev_jwt_789
EOF
```

### Production (Recommended Approach)

**Option 1: External Secrets Manager**
```bash
# Fetch from 1Password/Vault/AWS Secrets Manager
./scripts/fetch-secrets.sh prod
```

**Option 2: Environment Variables**
```bash
# Set in shell or CI/CD
export NINA_DB_PASSWORD=$(op read "op://production/db/password")
export NINA_REDIS_PASSWORD=$(op read "op://production/redis/password")
export NINA_JWT_SECRET=$(op read "op://production/jwt/secret")
```

**Option 3: Kubernetes Secrets**
```yaml
# k8s/secrets/prod-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ninaivalaigal-prod-secrets
type: Opaque
stringData:
  db-password: "..."
  redis-password: "..."
  jwt-secret: "..."
```

---

## 📊 SPEC-086 Port Matrix (Auto-Calculated)

| Runtime | Env  | DB   | PgBouncer | Redis | API   | Customer | Admin |
|---------|------|------|-----------|-------|-------|----------|-------|
| Docker  | Dev  | 5432 | 6432      | 6379  | 13370 | 8081     | 8181  |
| Docker  | Test | 5532 | 6532      | 6479  | 13470 | 8181     | 8281  |
| Docker  | Prod | 5632 | 6632      | 6579  | 13570 | 8281     | 8381  |
| Colima  | Dev  | 5442 | 6442      | 6389  | 13380 | 8091     | 8191  |
| Colima  | Test | 5542 | 6542      | 6489  | 13480 | 8191     | 8291  |
| Colima  | Prod | 5642 | 6642      | 6589  | 13580 | 8291     | 8391  |
| Apple   | Dev  | 5452 | 6452      | 6399  | 13390 | 8101     | 8201  |
| Apple   | Test | 5552 | 6552      | 6499  | 13490 | 8201     | 8301  |
| Apple   | Prod | 5652 | 6652      | 6599  | 13590 | 8301     | 8401  |

**All calculated automatically - NO hardcoding!**

---

## ✅ Benefits of Uniform Architecture

### 1. **Consistency**
- Same stack everywhere
- Same debugging process
- Same monitoring approach

### 2. **Maintainability**
- One set of scripts
- One configuration approach
- Easy to understand

### 3. **Flexibility**
- Switch runtimes easily
- Add new environments
- No code duplication

### 4. **Safety**
- Single source of truth
- Validation at load time
- No accidental misconfigurations

### 5. **Scalability**
- Easy to add new components
- Easy to add new runtimes
- Easy to add new environments

---

## 🗂️ File Structure

```
ninaivalaigal/
├── configs/
│   ├── defaults.env              # Global defaults (committed)
│   ├── runtime-docker.env        # Docker-specific (committed)
│   ├── runtime-colima.env        # Colima-specific (committed)
│   ├── runtime-apple.env         # Apple CLI-specific (committed)
│   ├── env-dev.env               # Dev environment (committed)
│   ├── env-test.env              # Test environment (committed)
│   ├── env-prod.env              # Prod environment (committed)
│   ├── secrets-apple-dev.env     # Secrets (gitignored)
│   ├── secrets-apple-test.env    # Secrets (gitignored)
│   └── secrets-apple-prod.env    # Secrets (gitignored)
├── scripts/
│   ├── lib/
│   │   ├── config-loader.sh      # Config hierarchy loader
│   │   ├── health-checks.sh      # Reusable health checks
│   │   └── logging.sh            # Logging utilities
│   ├── stack-start-unified.sh    # Universal startup
│   ├── stack-stop-unified.sh     # Universal shutdown
│   ├── stack-status-unified.sh   # Universal status
│   └── stack-validate.sh         # Config validation
└── .gitignore                     # Ignore secrets-*.env
```

---

## 🚀 Implementation Plan (Day 4)

### Phase 1: Configuration System
1. Create `configs/` directory structure
2. Create all `.env` files with proper values
3. Create `config-loader.sh` library
4. Update `.gitignore` for secrets

### Phase 2: Unified Scripts
1. Create `stack-start-unified.sh`
2. Create `stack-stop-unified.sh`
3. Create `stack-status-unified.sh`
4. Test all runtime/env combinations

### Phase 3: Migration
1. Update Makefile to use unified scripts
2. Deprecate old scripts (keep for reference)
3. Update documentation
4. Test complete workflows

### Phase 4: Validation
1. Test Docker + Dev
2. Test Colima + Dev
3. Test Apple + Dev
4. Test all combinations
5. Document any issues

---

## 🎯 Success Criteria

✅ **One script works for ALL runtimes**
✅ **One config system for ALL environments**
✅ **No hardcoded ports or passwords**
✅ **SPEC-086 compliant automatically**
✅ **Easy to add new runtimes/environments**
✅ **Production-ready secrets management**
✅ **Complete validation and error handling**

---

## 📝 Migration Path from Current State

```bash
# Current (Day 3)
./scripts/stack-start-complete.sh  # Hardcoded for Apple CLI

# Future (Day 4)
./scripts/stack-start-unified.sh apple dev  # Explicit runtime/env
./scripts/stack-start-unified.sh docker dev  # Same script!
./scripts/stack-start-unified.sh colima test  # Same script!!
```

**Same architecture, different runtime - as it should be!**

---

**This is the RIGHT way - uniform architecture everywhere.**
