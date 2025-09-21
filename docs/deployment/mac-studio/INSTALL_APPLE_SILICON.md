# Installation Guide for Apple Silicon (M1/M2/M3)

This guide helps you set up Ninaivalaigal on Apple Silicon Macs using Apple Container CLI for optimal ARM64 performance.

## Prerequisites

### 1. Install Apple Container CLI

```bash
# Install via Homebrew (recommended)
brew install container

# Verify installation
container --version
```

### 2. Install Development Tools

```bash
# Install required tools
brew install jq curl git make

# Install Python 3.11+ (if not already installed)
brew install python@3.11
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ninaivalaigal.git
cd ninaivalaigal
```

### 2. Start the Development Environment

```bash
# One-command startup
make dev-up
```

This will:
- ✅ Start PostgreSQL 15.14 + pgvector (port 5433)
- ✅ Start custom PgBouncer ARM64 (port 6432)
- ✅ Start FastAPI server with observability (port 13370)
- ✅ Run health checks and display status

### 3. Verify Installation

```bash
# Check all services
make health

# View detailed status
make dev-status

# View metrics
make metrics
```

Expected output:
```json
{
  "status": "ok",
  "uptime_s": 45,
  "db": {
    "connected": true,
    "active_connections": 1,
    "max_connections": 100
  }
}
```

## Available Commands

### Development Workflow
```bash
make dev-up      # Start development environment
make dev-down    # Stop development environment
make dev-logs    # Follow logs for all containers
make dev-status  # Show container status
```

### Health & Monitoring
```bash
make health      # Quick health check
make metrics     # View Prometheus metrics
make stack-status # Detailed stack status
```

### Production Commands
```bash
make start       # Start full production stack
make stop        # Stop all services
make validate-production  # Run comprehensive checks
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    PgBouncer     │    │   FastAPI       │
│   + pgvector     │◄───┤  Connection Pool │◄───┤   + Observability│
│   (port 5433)   │    │   (port 6432)    │    │   (port 13370)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Performance Benefits

Compared to Docker Desktop on Apple Silicon:

- **3-5x faster** container startup
- **Native ARM64** performance (no emulation)
- **Lower memory usage** (no Docker Desktop overhead)
- **Better battery life** (more efficient resource usage)

## Troubleshooting

### Container Issues
```bash
# List all containers
container list

# View container logs
container logs nv-db
container logs nv-api

# Restart specific service
make stop && make dev-up
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :5433
lsof -i :13370

# Kill conflicting processes
sudo kill -9 <PID>
```

### Database Connection Issues
```bash
# Test direct database connection
container exec nv-db psql -U nina -d nina -c "SELECT version();"

# Check database logs
container logs nv-db
```

## Development Tips

### 1. Hot Reload Development
The API container supports hot reload for development:

```bash
# Mount local code for development
make dev-up
# Edit files locally, changes reflect immediately
```

### 2. Database Management
```bash
# Connect to database
container exec -it nv-db psql -U nina -d nina

# Run migrations
make db-migrate

# Backup database
make backup
```

### 3. Monitoring & Debugging
```bash
# View real-time metrics
open http://localhost:13370/metrics

# Health dashboard
open http://localhost:13370/health/detailed

# Memory system status
open http://localhost:13370/memory/health
```

## Next Steps

1. **Explore the API**: Visit http://localhost:13370/docs for interactive API documentation
2. **Set up CI/CD**: See `.github/workflows/` for Apple Container CLI GitHub Actions
3. **Production Deployment**: Follow the production deployment guide
4. **Contribute**: Check `CONTRIBUTING.md` for development guidelines

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/ninaivalaigal/issues)
- **Apple Container CLI**: [Official Documentation](https://developer.apple.com/documentation/container)

---

**Note**: This installation method is optimized for Apple Silicon Macs. For Intel Macs or other platforms, see the standard Docker installation guide.
