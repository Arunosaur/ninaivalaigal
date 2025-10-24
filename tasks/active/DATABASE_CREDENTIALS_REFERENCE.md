# Database Credentials Reference

**Date:** October 21, 2025
**Environment:** Development

---

## 🔐 **Standard Credentials Pattern**

All ninaivalaigal databases use **consistent credentials** across the platform:

```
User:     nina
Password: dev_password_change_in_production
```

**⚠️ IMPORTANT:** As the password name indicates, this **MUST be changed** in production!

---

## 📊 **Database Endpoints**

### **1. Main Application Database**

```
Host:     localhost
Port:     5432 (direct) or 6432 (via PgBouncer - RECOMMENDED)
Database: ninaivalaigal_dev
User:     nina
Password: dev_password_change_in_production
```

**Connection Strings:**

```bash
# Direct to PostgreSQL (not recommended)
postgresql://nina:dev_password_change_in_production@localhost:5432/ninaivalaigal_dev

# Via PgBouncer (recommended - connection pooling)
postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev
```

**Used by:**
- Core API
- Business Service
- Admin/Vendor Service
- All Python services

---

### **2. GraphOps Database (Apache AGE)**

```
Host:     localhost
Port:     5433 (separate from main DB)
Database: ninaivalaigal-graph-db
User:     nina
Password: dev_password_change_in_production
```

**Connection String:**

```bash
postgresql://nina:dev_password_change_in_production@localhost:5433/ninaivalaigal-graph-db
```

**Used by:**
- GraphOps Service (Rust)
- Graph Intelligence features
- Apache AGE Cypher queries
- Alembic migrations for graph schema

---

## 🔧 **psql Access**

### **Main Database:**

```bash
# Via PgBouncer (recommended)
psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev

# Direct (not recommended)
psql -h localhost -p 5432 -U nina -d ninaivalaigal_dev

# With password inline
PGPASSWORD=dev_password_change_in_production psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev
```

### **GraphOps Database:**

```bash
# Direct access (no PgBouncer for GraphOps)
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db

# With password inline
PGPASSWORD=dev_password_change_in_production psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db
```

---

## 🐳 **Container Environment Variables**

### **For Python Services:**

```bash
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev"
export NINA_DB_USER="nina"
export NINA_DB_PASSWORD="dev_password_change_in_production"
```

### **For GraphOps (Rust):**

```bash
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@localhost:5433/ninaivalaigal-graph-db"
```

---

## 🔑 **Other Credentials**

### **JWT Secret (Development):**

```bash
NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production
```

⚠️ **Also must be changed in production!**

---

## ⚠️ **Security Notes**

### **Development:**
- ✅ These credentials are acceptable
- ✅ Clear naming indicates they need changing
- ✅ Documented in code with `# pragma: allowlist secret`

### **Production:**
- ❌ **NEVER use these credentials in production**
- ✅ Use strong, randomly-generated passwords
- ✅ Store in secrets management (e.g., AWS Secrets Manager, Vault)
- ✅ Rotate regularly
- ✅ Use different credentials per environment

---

## 📋 **Quick Reference Table**

| Database | Port | User | Database Name | PgBouncer? |
|----------|------|------|---------------|------------|
| **Main** | 5432 | nina | ninaivalaigal_dev | No |
| **Main (via PgBouncer)** | 6432 | nina | ninaivalaigal_dev | Yes ✅ |
| **GraphOps** | 5433 | nina | ninaivalaigal-graph-db | No |

**Password for all:** `dev_password_change_in_production`

---

## 🚀 **For Developer A - GraphOps Work**

### **Alembic Migrations:**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# Default (uses nina user)
alembic upgrade head

# Or with explicit URL
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@localhost:5433/ninaivalaigal-graph-db"
alembic upgrade head
```

### **Direct Database Access:**

```bash
# Check indexes
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db -c "\di ninaivalaigal_graph.*"

# Run Cypher query
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db -c "
SELECT * FROM cypher('ninaivalaigal_graph', \$\$
  MATCH (u:User) RETURN u LIMIT 5
\$\$) AS (u agtype);
"
```

---

## ❓ **FAQ**

### **Q: Is the user `nina` or `postgres`?**

**A:** The user is `nina` across the entire platform for consistency.

The `postgres` superuser exists but is not used by applications.

### **Q: Why `dev_password_change_in_production`?**

**A:** Clear naming convention that:
1. Works fine for development
2. Clearly indicates it's not production-safe
3. Prevents accidental production use
4. Documents intent directly in the credential

### **Q: Do all services use the same credentials?**

**A:** Yes, all services use:
- User: `nina`
- Password: `dev_password_change_in_production`

But they may connect to different databases or ports depending on their needs.

### **Q: What about Redis?**

**A:** Redis credentials are separate:
- Main Redis (port 6379): No password in dev
- GraphOps Redis (port 6380): No password in dev
- Production: Use `requirepass` configuration

---

## 📝 **For Production Deployment**

**Before going to production, change:**

1. **Database Password**
   ```bash
   # Generate strong password
   openssl rand -base64 32

   # Update PostgreSQL
   ALTER USER nina WITH PASSWORD '<new-password>';

   # Update all service configurations
   ```

2. **JWT Secret**
   ```bash
   # Generate strong secret
   openssl rand -base64 64

   # Update all service environment variables
   ```

3. **Store in Secrets Manager**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - GCP Secret Manager

---

**Updated:** October 21, 2025
**Environment:** Development
**Status:** Credentials corrected and documented
