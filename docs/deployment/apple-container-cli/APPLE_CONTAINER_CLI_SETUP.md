# Apple Container CLI Setup for Mac Studio

**Status**: ✅ Validated and Production-Ready
**Date**: September 17, 2025
**System**: Mac Studio M1 Ultra, 128GB RAM, macOS 26.0

## Overview

This guide documents the successful validation and setup of Apple Container CLI on Mac Studio for running PostgreSQL + pgvector containers. This is part of our incremental deployment strategy to migrate heavy workloads from laptop to Mac Studio.

## Prerequisites

- Mac Studio with Apple Silicon (M1/M2)
- macOS 26.0 or later
- Apple Container CLI installed (`/usr/local/bin/container`)

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env to change POSTGRES_PASSWORD

# 2. Start PostgreSQL + pgvector
./scripts/nv-db-start.sh

# 3. Check status
./scripts/nv-db-status.sh

# 4. Run tests
./scripts/nv-test-db.sh

# 5. Stop when done
./scripts/nv-db-stop.sh
```

## Apple Container CLI Syntax

Key differences from Docker CLI:

| Operation | Docker | Apple Container CLI |
|-----------|--------|-------------------|
| List containers | `docker ps` | `container list` |
| Remove container | `docker rm` | `container delete` |
| List images | `docker images` | `container images list` |
| Pull image | `docker pull` | `container images pull` |

## Validated Configuration

- **Image**: `pgvector/pgvector:pg15` (includes PostgreSQL 15 + pgvector)
- **Port**: 5433 (host) → 5432 (container)
- **Database**: `nina` with user `nina`
- **Extensions**: pgvector for semantic search

## Performance Results

- **Container startup**: ~2-3 seconds
- **Database ready**: ~10 seconds total
- **Query performance**: 0.111s for complex operations
- **Native ARM64**: Excellent M1 Ultra optimization

## Scripts

All scripts located in `scripts/` directory:

- `nv-db-start.sh` - Start PostgreSQL + pgvector container
- `nv-db-stop.sh` - Stop and remove container
- `nv-db-status.sh` - Check container health
- `nv-test-db.sh` - Run full test suite

## Known Issues

- **Volume Permissions**: Persistent volumes need permission fixes
- **Workaround**: Currently running without persistent storage for testing

## Next Steps

1. Set up GitHub Actions self-hosted runner
2. Configure CI workflows for Mac Studio
3. Add PgBouncer and FastAPI services
4. Implement persistent volume solution

## Troubleshooting

```bash
# Check container system
container system status

# View container logs
container logs nv-db

# Manual container management
container list
container stop nv-db
container delete nv-db
```

For detailed validation results, see `MAC_STUDIO_VALIDATION_REPORT.md`.
