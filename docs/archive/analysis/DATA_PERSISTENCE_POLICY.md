# 🔒 Data Persistence Policy

**Version:** 1.0
**Date:** October 5, 2025
**Status:** MANDATORY

---

## ❌ **NEVER DO THIS:**

```bash
# DANGER: This deletes ALL data volumes
docker-compose down -v  # ❌ FORBIDDEN

# DANGER: This deletes specific volumes
docker volume rm ninaivalaigal_dev_postgres_data  # ❌ FORBIDDEN
```

---

## ✅ **SAFE COMMANDS:**

### **Stop Stack (Data Preserved):**
```bash
docker-compose -f compose.docker.yml --env-file .env.dev down
make docker-dev-down
```

### **Restart Stack:**
```bash
docker-compose -f compose.docker.yml --env-file .env.dev restart
docker restart ninaivalaigal-dev-db ninaivalaigal-dev-redis
```

### **Rebuild Without Data Loss:**
```bash
# Stop containers
docker-compose -f compose.docker.yml --env-file .env.dev down

# Rebuild
docker-compose -f compose.docker.yml --env-file .env.dev build

# Start
make docker-dev-up
```

---

## 📂 **Data Storage Locations:**

### **Docker Runtime:**
- PostgreSQL: `./data/postgres_dev/`
- Redis: `./data/redis_dev/`
- Backups: `./backups/`

### **Apple Container CLI:**
- PostgreSQL: `./data/postgres_dev/`
- Redis: `./data/redis_dev/`
- Backups: `./backups/`

### **Colima Runtime:**
- PostgreSQL: `./data/postgres_dev/`
- Redis: `./data/redis_dev/`
- Backups: `./backups/`

---

## 🔄 **Data Sharing Across Runtimes:**

All runtimes share the **SAME data directories** within the same environment:

```
data/
├── postgres_dev/     # Shared by docker-dev, apple-dev, colima-dev
├── postgres_test/    # Shared by docker-test, apple-test, colima-test
├── postgres_prod/    # Shared by docker-prod, apple-prod, colima-prod
├── redis_dev/        # Shared by docker-dev, apple-dev, colima-dev
├── redis_test/       # Shared by docker-test, apple-test, colima-test
└── redis_prod/       # Shared by docker-prod, apple-prod, colima-prod
```

**This means:**
- Migrations run in Docker are visible in Apple Container CLI ✅
- Data seeded in Colima is accessible from Docker ✅
- **One environment = One database**, regardless of runtime ✅

---

## 🛡️ **Backup Policy:**

### **Manual Backup:**
```bash
make backup-db  # Creates timestamped backup in ./backups/
```

### **Automatic Backups:**
- Daily backups at 2 AM (if configured)
- Kept for 7 days
- Stored in `./backups/`

### **Restore:**
```bash
make restore-db BACKUP_FILE=./backups/backup-2025-10-05.sql
```

---

## 🚨 **Emergency Recovery:**

If data is accidentally deleted:

1. **Stop all containers:**
   ```bash
   docker-compose -f compose.docker.yml --env-file .env.dev down
   ```

2. **Check for backups:**
   ```bash
   ls -lh ./backups/
   ```

3. **Restore from backup:**
   ```bash
   make restore-db BACKUP_FILE=./backups/latest-backup.sql
   ```

4. **If no backup exists:**
   - Run migrations: `DATABASE_URL="..." alembic upgrade head`
   - Seed initial data: `DATABASE_URL="..." python scripts/seed_initial_staff.py`

---

## 📋 **Pre-Deployment Checklist:**

Before any stack operation:

- [ ] Backup exists and is recent (< 24 hours old)
- [ ] Data directories exist: `ls ./data/postgres_dev/ ./data/redis_dev/`
- [ ] Using correct command (no `-v` flag)
- [ ] Environment variable is set correctly: `echo $NINA_ENV`

---

## 🔐 **Access Control:**

### **Default Admin Credentials:**
- Email: `admin@ninaivalaigal.com`
- Password: `ChangeMe123!@#`
- **⚠️ Change immediately in production!**

### **Database Access:**
```bash
# Through PgBouncer (recommended):
psql "postgresql://nina:password@localhost:6432/ninaivalaigal_dev"

# Direct to PostgreSQL (debugging only):
psql "postgresql://nina:password@localhost:5432/ninaivalaigal_dev"
```

---

## 📊 **Data Verification:**

### **Check if database is populated:**
```bash
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "\dt"
```

### **Check staff accounts:**
```bash
docker exec -e PGPASSWORD=dev_password_change_in_production \
  ninaivalaigal-dev-db \
  psql -U nina -d ninaivalaigal_dev \
  -c "SELECT email, role, is_active FROM staff;"
```

### **Check data size:**
```bash
du -sh ./data/postgres_dev/
du -sh ./data/redis_dev/
```

---

## ⚠️ **Critical Rules:**

1. **NEVER** use `docker-compose down -v` in dev/test/prod
2. **ALWAYS** backup before major operations
3. **ALL** runtimes share the same environment data
4. **DATA** directories are in `.gitignore` (never commit data)
5. **BACKUPS** directory should be backed up to external storage

---

**Violation of this policy will result in data loss and development delays.**
**When in doubt, make a backup first!**

---

**Last Updated:** October 5, 2025
**Reviewed By:** Development Team
**Next Review:** January 2026
