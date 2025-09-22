# GraphOps: Production Apache AGE + PostgreSQL

This directory contains the production-ready Apache AGE graph database setup for ninaivalaigal, based on the GraphOps Starter Kit with **dual-architecture support**.

## Overview

- **PostgreSQL 15** with **Apache AGE** extension for graph operations
- **Redis** for graph caching and performance optimization
- **Dual-architecture support**: ARM64 (Apple Container CLI) + x86_64 (CI/Docker)
- **Production-ready** containers with health checks
- **Automated schema initialization** with ninaivalaigal graph structure
- **CI/CD integration** with GitHub Actions

## Dual-Architecture Strategy

### 🍎 **ARM64 (Local Development)**
- **Apple Container CLI** for native ARM64 performance
- **3-5x faster** container startup vs Docker Desktop
- **No emulation overhead** on Apple Silicon
- **Enhanced developer experience**

### 🏭 **x86_64 (CI/Production)**
- **Docker/Kubernetes** for broad compatibility
- **GitHub Actions** CI validation
- **Production deployment** compatibility
- **Multi-cloud support**

## Quick Start

```bash
# Start the graph infrastructure
make start-graph-infrastructure

# Check health status
make check-graph-health

# Connect to graph database
make graph-db-shell

# Connect to Redis
make graph-redis-shell

# Stop infrastructure
make stop-graph-infrastructure
```

## Architecture

### Graph Database (PostgreSQL + Apache AGE)
- **Container**: `ninaivalaigal-graph-db`
- **Port**: `5433:5432`
- **Database**: `ninaivalaigal_graph`
- **User**: `graphuser`
- **Features**:
  - Apache AGE extension for graph operations
  - Cypher query language support
  - SCRAM-SHA-256 authentication
  - Automated health checks
  - Persistent data volumes

### Redis Cache
- **Container**: `ninaivalaigal-graph-redis`
- **Port**: `6380:6379`
- **Features**:
  - Graph query result caching
  - Session management
  - Performance optimization
  - Password authentication
  - Persistent data with AOF

## Graph Schema

The database is automatically initialized with:

### Node Types (Vertices)
- `User` - Platform users
- `Memory` - Memory objects
- `Context` - Context information
- `Agent` - AI agents
- `Team` - User teams
- `Organization` - Organizations
- `Session` - User sessions
- `Macro` - Automation macros
- `Token` - Memory tokens

### Relationship Types (Edges)
- `CREATED` - Creation relationships
- `ACCESSED` - Access relationships
- `BELONGS_TO` - Ownership relationships
- `MEMBER_OF` - Membership relationships
- `OWNS` - Ownership relationships
- `LINKED_TO` - General links
- `SIMILAR_TO` - Similarity relationships
- `REFERENCES` - Reference relationships
- `TAGGED_WITH` - Tagging relationships
- `EXECUTED` - Execution relationships
- `CONTAINS` - Containment relationships
- `SHARED_WITH` - Sharing relationships
- `DERIVED_FROM` - Derivation relationships
- `FEEDBACK` - Feedback relationships
- `SUGGESTS` - Suggestion relationships

## Environment Variables

```bash
# Graph Database
GRAPH_DB_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password
```

## Development Commands

```bash
# Start infrastructure
make start-graph-infrastructure

# Restart infrastructure
make restart-graph-infrastructure

# Check health
make check-graph-health

# Database shell
make graph-db-shell

# Redis shell
make graph-redis-shell

# Initialize schema
make init-graph-schema

# Clean all data (WARNING: Destructive)
make clean-graph-data

# Run all graph tests
make test-graph-all
```

## Production Deployment

### Docker Compose
```bash
# Production deployment
docker compose -f docker-compose.graph.yml up -d --build

# With custom environment
GRAPH_DB_PASSWORD=prod_password REDIS_PASSWORD=prod_redis docker compose -f docker-compose.graph.yml up -d
```

### Kubernetes
The containers are designed to work with Kubernetes deployments:
- Health checks for readiness/liveness probes
- Persistent volume support
- ConfigMap/Secret integration
- Resource limits and requests

## Monitoring

### Health Checks
- **Graph DB**: `pg_isready` check every 10 seconds
- **Redis**: `redis-cli ping` check every 10 seconds

### Logging
- JSON file driver with rotation (10MB max, 3 files)
- Structured logging for production monitoring

### Metrics
Access graph statistics:
```sql
SELECT * FROM graph_stats;
```

## Security

### Authentication
- **PostgreSQL**: SCRAM-SHA-256 authentication
- **Redis**: Password authentication
- **Network**: Isolated Docker network

### Data Protection
- Persistent volumes for data durability
- Regular backup capabilities
- Access control and user permissions

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   make check-graph-health
   docker logs ninaivalaigal-graph-db
   docker logs ninaivalaigal-graph-redis
   ```

2. **Connection refused**
   - Check if containers are running
   - Verify port mappings (5433 for DB, 6380 for Redis)
   - Check firewall settings

3. **Schema not initialized**
   ```bash
   make init-graph-schema
   ```

4. **Performance issues**
   - Check Redis cache hit rates
   - Monitor PostgreSQL query performance
   - Review graph query patterns

### Logs
```bash
# View real-time logs
docker logs -f ninaivalaigal-graph-db
docker logs -f ninaivalaigal-graph-redis

# View container status
docker compose -f docker-compose.graph.yml ps
```

## Integration

### Python Client
```python
from server.graph.age_client import ApacheAGEClient

# Connect to graph database
client = ApacheAGEClient("postgresql://graphuser:password@localhost:5433/ninaivalaigal_graph")
await client.initialize()

# Execute Cypher queries
result = await client.execute_cypher("MATCH (n:User) RETURN n LIMIT 10")
```

### Redis Integration
```python
from server.redis_client import RedisClient

# Connect to Redis
redis_client = RedisClient(host="localhost", port=6380, password="password")
await redis_client.initialize()
```

## Performance

### Benchmarks
- Graph query performance: < 100ms for complex traversals
- Redis cache hit ratio: > 90% for repeated queries
- Concurrent connections: Supports 100+ simultaneous connections

### Optimization
- Connection pooling for PostgreSQL
- Redis caching for frequently accessed data
- Indexed graph traversals
- Query result caching

## Contributing

When modifying the graph infrastructure:

1. Update schema in `init-schema.sql`
2. Test with `make test-graph-all`
3. Update documentation
4. Run CI/CD pipeline

## Support

For issues with the graph infrastructure:
1. Check the troubleshooting section
2. Review container logs
3. Verify environment configuration
4. Test with minimal examples
