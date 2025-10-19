# Environment Files Guide

## 📁 File Structure (Consolidated)

### Root Level (Primary)
- **`.env.example`** - Master template with all variables and documentation
- **`.env.ci`** - CI/CD pipeline configuration (GitHub Actions)
- **`.env.test`** - Test environment configuration
- **`.env.ghcr`** - GitHub Container Registry credentials
- **`.env.monitoring`** - Monitoring/observability configuration

### Configs Directory (Deployment Specific)
- **`env-dev.env`** - Development environment overrides
- **`env-prod.env`** - Production environment settings
- **`env-test.env`** - Test environment overrides
- **`secrets-apple-dev.env`** - Apple Container CLI specific secrets

### Docker Directory
- **`docker/.env.example`** - Docker-specific variables

### Frontend Directories
- **`frontend-nextjs/.env.example`** - Next.js template
- **`frontend-nextjs-customer/.env.local`** - Customer portal local config

## 🔐 Secret Management (SPEC-054)

### Setup New Environment
```bash
# Generate secure secrets
./scripts/setup-secrets.sh

# This creates .env with cryptographically secure values:
# - DB_PASSWORD (24 chars)
# - REDIS_PASSWORD (24 chars)
# - JWT_SECRET (48 chars)
# - MEMORY_SECRET (32 chars)
```

### Usage Pattern
1. **Copy template**: `cp .env.example .env`
2. **Generate secrets**: `./scripts/setup-secrets.sh`
3. **Customize**: Edit `.env` for your environment
4. **Never commit**: `.env` is gitignored

## 🎯 Which File to Use?

| Scenario | File to Copy | Notes |
|----------|--------------|-------|
| Local development | `.env.example` → `.env` | Use setup-secrets.sh |
| CI/CD | `.env.ci` | Used by GitHub Actions |
| Testing | `.env.test` | Used by pytest |
| Production | `configs/env-prod.env` | Merge with secrets |
| Docker Compose | `docker/.env.example` → `docker/.env` | Container-specific |

## ⚠️ Security Rules

1. **NEVER commit** actual `.env` files (gitignored)
2. **NEVER hardcode** secrets in code or docs
3. **ALWAYS use** `${VARIABLE}` syntax in configs
4. **REFERENCE env vars** in documentation examples:
   ```bash
   # ✅ GOOD - Documentation
   export TAIGA_URL=${TAIGA_URL:-http://localhost:9000}
   export TAIGA_USERNAME=${TAIGA_USERNAME}
   export TAIGA_PASSWORD=${TAIGA_PASSWORD}

   # ❌ BAD - Don't do this
   export TAIGA_PASSWORD="admin123"
   ```

## 🔄 Migration Complete

**Removed** (duplicates/empty):
- `configs/.env.apple.dev` (empty)
- `configs/.env.colima.dev` (empty)
- `configs/.env.docker.dev` (empty)
- `.env.colima.dev` (duplicate of .env.example)
- `.env.dev` (duplicate of .env.example)
- `.env.backup` (backup file)
- `.env.sample` (duplicate of .env.example)

**Kept** (single source of truth):
- Root: Master templates and CI/CD configs
- Configs: Deployment-specific overrides
- Docker: Container-specific variables
- Frontend: UI-specific variables

## 📚 Related Documentation

- **SPEC-054**: Secret Management & Environment Hygiene
- **Taiga Setup**: See `~/WorkSpace/taiga/docs/` (external project management)
- **Deployment Guides**: `docs/guides/` (reference env vars, not values)
