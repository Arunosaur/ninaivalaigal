# Mac Studio Quick Reference Guide

## 🚀 **Deployment Commands**

### Initial Setup (Run Once)
```bash
# 1. Deploy the full stack
./deploy_mac_studio.sh

# 2. Setup GitHub Actions runner
./setup_github_runner.sh https://github.com/Arunosaur/ninaivalaigal YOUR_RUNNER_TOKEN
```

### Daily Operations
```bash
# Check service status
docker compose -f /srv/medhasys/docker-compose.prod.yml ps

# View logs
docker compose -f /srv/medhasys/docker-compose.prod.yml logs -f api
docker compose -f /srv/medhasys/docker-compose.prod.yml logs -f postgres

# Restart services
docker compose -f /srv/medhasys/docker-compose.prod.yml restart

# Update application
cd /Users/medhasys/ninaivalaigal
git pull origin main
docker compose -f /srv/medhasys/docker-compose.prod.yml up -d --build api
```

## 🌐 **Service URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **API Server** | http://localhost:13370 | Main application API |
| **API Health** | http://localhost:13370/healthz | Health monitoring |
| **API Docs** | http://localhost:13370/docs | Interactive API documentation |
| **Memory Health** | http://localhost:13370/healthz/memory | Memory substrate status |
| **PostgreSQL** | localhost:5433 | Database (with pgvector) |
| **PgBouncer** | localhost:6432 | Connection pooling |
| **Redis** | localhost:6379 | Caching layer |

## 📁 **Important Paths**

| Path | Purpose |
|------|---------|
| `/Users/medhasys/ninaivalaigal` | Application repository |
| `/srv/medhasys/.env` | Environment configuration |
| `/srv/medhasys/docker-compose.prod.yml` | Production stack definition |
| `/srv/medhasys/volumes/db` | PostgreSQL data |
| `/srv/medhasys/logs` | Application logs |
| `/srv/medhasys/backups` | Database backups |
| `/opt/actions-runner` | GitHub Actions runner |

## 🔧 **Troubleshooting**

### Service Won't Start
```bash
# Check Docker status
docker info

# Check service logs
docker compose -f /srv/medhasys/docker-compose.prod.yml logs service_name

# Restart specific service
docker compose -f /srv/medhasys/docker-compose.prod.yml restart service_name
```

### Database Issues
```bash
# Check database connectivity
pg_isready -h localhost -p 5433 -U medhasys

# Connect to database
psql -h localhost -p 5433 -U medhasys -d medhasys

# Check database logs
docker compose -f /srv/medhasys/docker-compose.prod.yml logs postgres
```

### GitHub Runner Issues
```bash
# Check runner status
sudo /opt/actions-runner/svc.sh status

# Restart runner
sudo /opt/actions-runner/svc.sh stop
sudo /opt/actions-runner/svc.sh start

# View runner logs
tail -f /opt/actions-runner/_diag/Runner_*.log
```

## 📊 **Performance Monitoring**

### System Resources
```bash
# CPU and memory usage
htop

# Docker resource usage
docker stats

# Disk usage
df -h
du -sh /srv/medhasys/volumes/*
```

### Database Performance
```bash
# Connect to database
psql -h localhost -p 5433 -U medhasys -d medhasys

# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Check database size
SELECT pg_size_pretty(pg_database_size('medhasys'));

# Check table sizes
SELECT schemaname,tablename,pg_size_pretty(size) as size
FROM (
  SELECT schemaname,tablename,pg_relation_size(schemaname||'.'||tablename) as size
  FROM pg_tables WHERE schemaname NOT IN ('information_schema','pg_catalog')
) s ORDER BY size DESC;
```

## 🔐 **Security**

### Environment Variables
```bash
# View current environment (passwords hidden)
grep -v PASSWORD /srv/medhasys/.env

# Rotate passwords (requires service restart)
# Edit /srv/medhasys/.env
# Then: docker compose -f /srv/medhasys/docker-compose.prod.yml up -d --force-recreate
```

### Backup & Restore
```bash
# Create backup
docker exec medhasys-production-postgres-1 pg_dump -U medhasys medhasys > /srv/medhasys/backups/backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
psql -h localhost -p 5433 -U medhasys -d medhasys < /srv/medhasys/backups/backup-file.sql
```

## ⚡ **Performance Benefits**

**Mac Studio Advantages:**
- **20-core M2 Ultra**: Parallel test execution across multiple Python versions
- **128GB RAM**: Large dataset processing, extensive caching
- **Native ARM64**: No emulation overhead, maximum performance
- **Always-on**: Dedicated CI runner, no cold starts
- **Local Storage**: Fast SSD access for databases and caches

**Expected Performance:**
- **CI Pipeline**: 3-5x faster than cloud runners
- **Database Operations**: Sub-millisecond queries with proper indexing
- **Memory Substrate**: Handle 100K+ memory records efficiently
- **Concurrent Users**: Support 1000+ concurrent API requests

## 🎯 **Development Workflow**

### Laptop Development
```bash
# Point CLI to Mac Studio
export NINAIVALAIGAL_SERVER_URL="http://mac-studio-ip:13370"

# Use remote database for development
export DATABASE_URL="postgresql://medhasys:password@mac-studio-ip:5433/medhasys"

# Quick local testing with InMemory store
unset DATABASE_URL
./utils/eM.py contexts  # Uses InMemory store
```

### Mac Studio Production
- Heavy services (Postgres, API, Redis)
- All CI/CD workloads
- Database backups and monitoring
- Production-grade logging and observability

This setup gives you the perfect balance: **fast local development** with **powerful remote infrastructure**! 🚀
