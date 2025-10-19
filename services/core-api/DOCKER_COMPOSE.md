
# Docker Compose Integration for Core API

Complete Docker Compose setup for the ninaivalaigal Core API with PostgreSQL, PgBouncer, and Redis.

## 📁 Available Compose Files

### 1. `docker-compose.yml` (Development)
Lightweight setup for local development:
- PostgreSQL with pgvector
- Redis for caching
- Core API with hot-reload

**Use case**: Local development, quick testing

### 2. `docker-compose.prod.yml` (Production)
Production-ready stack with all components:
- PostgreSQL with pgvector
- PgBouncer for connection pooling
- Redis for caching
- Core API with production optimizations

**Use case**: Production deployments, staging environments

---

## 🚀 Quick Start

### Development Environment

```bash
# Copy environment template
cp .env.docker .env

# Start the stack
docker-compose up -d

# View logs
docker-compose logs -f nv-core-api-dev

# Check health
curl http://localhost:8000/health

# Stop the stack
docker-compose down
```

### Production Environment

```bash
# Copy and edit production environment
cp .env.docker .env.production
vim .env.production  # Edit with production values

# Start production stack
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f nv-core-api

# Check health
curl http://localhost:8000/health

# Stop
docker-compose -f docker-compose.prod.yml down
```

---

## 🏗️ Architecture

### Development Stack
```
┌─────────────────┐
│  nv-core-api-dev│  (Port 8000)
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌─▼──────┐
│nv-db   │ │nv-redis│
│-dev    │ │-dev    │
│(5432)  │ │(6379)  │
└────────┘ └────────┘
```

### Production Stack
```
┌─────────────────┐
│   nv-core-api   │  (Port 8000)
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴──────────┐
    │               │
┌───▼──────┐   ┌───▼──────┐
│nv-pgbouncer│  │nv-redis  │
│  (6432)    │  │  (6379)  │
└─────┬──────┘  └──────────┘
      │
┌─────▼──────┐
│   nv-db    │
│   (5432)   │
└────────────┘
```

---

## 🔧 Configuration

### Environment Variables

#### Database
- `POSTGRES_USER`: Database username (default: `ninauser`)
- `POSTGRES_PASSWORD`: Database password (default: `ninapass`)
- `POSTGRES_DB`: Database name (default: `ninaivalaigal`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)

#### PgBouncer (Production only)
- `PGBOUNCER_PORT`: PgBouncer port (default: `6432`)
- `PGBOUNCER_POOL_MODE`: Pooling mode (`transaction`, `session`, `statement`)
- `PGBOUNCER_MAX_CLIENT_CONN`: Max client connections (default: `1000`)
- `PGBOUNCER_DEFAULT_POOL_SIZE`: Default pool size (default: `25`)

#### Redis
- `REDIS_PASSWORD`: Redis password (default: `redispass`)
- `REDIS_PORT`: Redis port (default: `6379`)
- `REDIS_CACHE_TTL`: Cache TTL in seconds (default: `3600`)

#### API
- `API_PORT`: API port (default: `8000`)
- `API_HOST`: API host (default: `0.0.0.0`)
- `ENVIRONMENT`: Environment (`development`, `production`)
- `LOG_LEVEL`: Logging level (`debug`, `info`, `warning`, `error`)

#### JWT
- `JWT_SECRET_KEY`: **REQUIRED** - Secret key for JWT signing
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_EXPIRATION_MINUTES`: Token expiration (default: `30`)

#### CORS
- `CORS_ORIGINS`: Comma-separated allowed origins

---

## 📊 Service Management

### Health Checks

All services include health checks:

```bash
# Check individual services
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Test database
docker-compose exec nv-db-dev pg_isready -U ninauser

# Test Redis
docker-compose exec nv-redis-dev redis-cli ping
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f nv-core-api-dev

# Last 100 lines
docker-compose logs --tail=100 nv-core-api-dev
```

### Scaling

```bash
# Scale API instances (requires load balancer)
docker-compose -f docker-compose.prod.yml up -d --scale nv-core-api=3
```

---

## 🗄️ Data Persistence

### Volumes

Development:
- `postgres_dev_data`: PostgreSQL data

Production:
- `ninaivalaigal-postgres-data`: PostgreSQL data
- `ninaivalaigal-redis-data`: Redis persistence
- `ninaivalaigal-api-logs`: API logs

### Backup

```bash
# Backup PostgreSQL
docker-compose exec nv-db pg_dump -U ninauser ninaivalaigal > backup.sql

# Restore PostgreSQL
cat backup.sql | docker-compose exec -T nv-db psql -U ninauser ninaivalaigal
```

---

## 🔒 Security Best Practices

### Production Checklist

- [ ] Change all default passwords in `.env.production`
- [ ] Generate strong JWT secret: `openssl rand -hex 32`
- [ ] Use environment-specific CORS origins
- [ ] Enable rate limiting (`ENABLE_RATE_LIMITING=true`)
- [ ] Set proper log levels (`LOG_LEVEL=warning` or `LOG_LEVEL=error`)
- [ ] Use TLS/SSL for database connections
- [ ] Restrict network access (firewall rules)
- [ ] Regular security updates

### Secrets Management

**DO NOT** commit `.env` files to git!

```bash
# Add to .gitignore
echo ".env*" >> .gitignore
echo "!.env.example" >> .gitignore
```

---

## 🧪 Testing

### Integration Tests

```bash
# Start test environment
docker-compose up -d

# Run tests
docker-compose exec nv-core-api-dev python -m pytest tests/

# Run specific test
docker-compose exec nv-core-api-dev python -m pytest tests/test_integration.py -v
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/health
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
API_PORT=8001 docker-compose up -d
```

#### 2. Database Connection Failed

```bash
# Check database is running
docker-compose ps nv-db-dev

# Check database logs
docker-compose logs nv-db-dev

# Test connection
docker-compose exec nv-db-dev psql -U ninauser -d ninaivalaigal
```

#### 3. Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps nv-redis-dev

# Test Redis
docker-compose exec nv-redis-dev redis-cli ping
```

#### 4. API Not Starting

```bash
# Check logs
docker-compose logs -f nv-core-api-dev

# Rebuild image
docker-compose build --no-cache nv-core-api-dev
docker-compose up -d
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
docker-compose up -d --build
```

---

## 📈 Monitoring

### Resource Usage

```bash
# Container stats
docker stats

# Specific service
docker stats nina-core-api-dev
```

### Performance Metrics

```bash
# API metrics endpoint
curl http://localhost:8000/metrics

# Database connections
docker-compose exec nv-db-dev psql -U ninauser -d ninaivalaigal -c "SELECT count(*) FROM pg_stat_activity;"

# Redis info
docker-compose exec nv-redis-dev redis-cli info stats
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Core API

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy with Docker Compose
        run: |
          docker-compose -f services/core-api/docker-compose.prod.yml pull
          docker-compose -f services/core-api/docker-compose.prod.yml up -d
```

---

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [PgBouncer Documentation](https://www.pgbouncer.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 🎯 Next Steps

1. Configure environment variables for your environment
2. Start the stack: `docker-compose up -d`
3. Run migrations if needed
4. Test endpoints: `curl http://localhost:8000/health`
5. Monitor logs: `docker-compose logs -f`
6. Scale as needed for production

---

**Last Updated**: October 2025
**Maintainer**: Developer C
**Status**: Production Ready ✅
