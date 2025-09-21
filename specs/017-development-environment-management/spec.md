# SPEC-017: Development Environment Management

## Overview

This specification defines the development environment management system for ninaivalaigal, providing comprehensive local development stack management, health monitoring, backup/restore capabilities, and developer experience optimization.

## Motivation

- **Consistent Development Environment**: Standardized local development setup across team members
- **Rapid Development Iteration**: Fast startup, teardown, and reset of development stack
- **Data Management**: Backup, restore, and migration capabilities for development data
- **Health Monitoring**: Real-time status monitoring and diagnostics for all services
- **Developer Experience**: Simple commands for complex operations

## Specification

### 1. Development Stack Architecture

#### 1.1 Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   PgBouncer     │    │   FastAPI       │
│   + pgvector     │◄───│   Connection    │◄───│   Application   │
│   (Port 5433)   │    │   Pooler        │    │   (Port 13370)  │
│                 │    │   (Port 6432)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Volume   │    │   Config Files  │    │   Health Checks │
│   Persistence   │    │   Templates     │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 1.2 Service Dependencies
```yaml
Startup Order:
  1. PostgreSQL Database (nv-db)
  2. PgBouncer Connection Pooler (nv-pgbouncer)
  3. FastAPI Application (nv-api)

Shutdown Order:
  1. FastAPI Application (nv-api)
  2. PgBouncer Connection Pooler (nv-pgbouncer)
  3. PostgreSQL Database (nv-db)
```

### 2. Makefile Interface

#### 2.1 Primary Development Commands
```makefile
# Development stack management
dev-up:         # Start complete development stack
dev-down:       # Stop complete development stack
dev-status:     # Show status of all services
dev-logs:       # Show logs from all services
dev-restart:    # Restart all services

# Health monitoring
health:         # Show comprehensive health summary
metrics:        # Display performance metrics

# Data management
backup:         # Create database backup
restore:        # Restore from backup
cleanup-backups: # Clean old backup files
```

#### 2.2 Individual Service Management
```makefile
# Database operations
db-start:       # Start PostgreSQL only
db-stop:        # Stop PostgreSQL only
db-status:      # PostgreSQL status and logs
db-stats:       # Database performance statistics

# Connection pooler operations
pgb-start:      # Start PgBouncer only
pgb-stop:       # Stop PgBouncer only
pgb-status:     # PgBouncer status and logs
pgb-stats:      # Connection pool statistics

# API operations
api-start:      # Start FastAPI only
api-stop:       # Stop FastAPI only
api-status:     # API status and logs
api-logs:       # API application logs
```

### 3. Script Architecture

#### 3.1 Core Management Scripts
```bash
scripts/
├── nv-stack-start.sh      # Orchestrated stack startup
├── nv-stack-stop.sh       # Orchestrated stack shutdown
├── nv-stack-status.sh     # Comprehensive status display
├── nv-db-start.sh         # Database startup with health checks
├── nv-db-stop.sh          # Database shutdown
├── nv-pgbouncer-start.sh  # PgBouncer startup with config generation
├── nv-pgbouncer-stop.sh   # PgBouncer shutdown
├── nv-api-start.sh        # API startup with dependency checks
├── nv-api-stop.sh         # API shutdown
└── nv-health-check.sh     # Health monitoring script
```

#### 3.2 Utility Scripts
```bash
scripts/
├── backup-database.sh     # Database backup automation
├── restore-database.sh    # Database restore automation
├── cleanup-backups.sh     # Backup file management
├── generate-test-data.sh  # Test data generation
├── reset-development.sh   # Complete environment reset
└── system-info.sh         # System diagnostics
```

### 4. Health Monitoring System

#### 4.1 Health Check Endpoints
```yaml
Database Health:
  - Connection: pg_isready check
  - Performance: Query response time
  - Storage: Disk usage and availability
  - Extensions: pgvector availability

PgBouncer Health:
  - Process: Service running status
  - Connections: Pool utilization
  - Configuration: Config file validity
  - Backend: Database connectivity

API Health:
  - HTTP: /health endpoint response
  - Database: Connection pool status
  - Memory: Memory provider health
  - Performance: Response time metrics
```

#### 4.2 Status Display Format
```bash
# Example health output
🏥 NINAIVALAIGAL HEALTH SUMMARY
═══════════════════════════════════════

📊 SYSTEM STATUS
├─ 🗄️  Database (nv-db): ✅ HEALTHY (192.168.65.200:5432)
├─ 🔄 PgBouncer (nv-pgbouncer): ✅ HEALTHY (192.168.65.206:6432)
└─ 🚀 API Server (nv-api): ✅ HEALTHY (localhost:13370)

📈 PERFORMANCE METRICS
├─ API Response Time: 45ms (target: <100ms)
├─ Database Connections: 3/100 active
└─ Memory Usage: 256MB/512MB allocated

🔗 ENDPOINTS
├─ API: http://localhost:13370
├─ Health: http://localhost:13370/health
├─ Metrics: http://localhost:13370/metrics
└─ Database: postgresql://nina:***@localhost:5433/nina
```

### 5. Data Management

#### 5.1 Backup Strategy
```yaml
Backup Types:
  - Full Database: Complete PostgreSQL dump
  - Schema Only: Structure without data
  - Data Only: Data without structure
  - Incremental: Changes since last backup (future)

Backup Locations:
  - Local: ./backups/ directory
  - Timestamped: backup-YYYYMMDD-HHMMSS.sql
  - Compressed: gzip compression for storage efficiency
```

#### 5.2 Restore Capabilities
```yaml
Restore Options:
  - Latest Backup: Most recent backup file
  - Specific Backup: Choose from available backups
  - Clean Restore: Drop and recreate database
  - Merge Restore: Add to existing data
```

#### 5.3 Backup Automation
```bash
# Automated backup scheduling
Frequency: Daily (configurable)
Retention: 7 days (configurable)
Cleanup: Automatic old backup removal
Verification: Backup integrity checking
```

### 6. Configuration Management

#### 6.1 Environment Variables
```bash
# Core configuration
NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@localhost:5433/nina"
NINAIVALAIGAL_JWT_SECRET="development-jwt-secret-key"
MEMORY_PROVIDER="native"

# Development-specific
NINAIVALAIGAL_DEBUG=1
LOG_LEVEL="DEBUG"
RELOAD_ON_CHANGE=true
```

#### 6.2 Service Configuration
```yaml
PostgreSQL:
  - Port: 5433 (avoid conflicts with system PostgreSQL)
  - Database: nina
  - User: nina
  - Extensions: pgvector, uuid-ossp

PgBouncer:
  - Port: 6432
  - Pool Mode: session
  - Max Connections: 100
  - Auth Type: SCRAM-SHA-256

FastAPI:
  - Port: 13370
  - Host: 0.0.0.0
  - Reload: true (development)
  - Workers: 1 (development)
```

### 7. Developer Experience Features

#### 7.1 Quick Start
```bash
# One-command development setup
make dev-up

# Verify everything is working
make health

# Start development
# Application available at http://localhost:13370
```

#### 7.2 Troubleshooting Support
```bash
# Comprehensive diagnostics
make system-info        # System requirements check
make dev-logs          # View all service logs
make dev-status        # Detailed service status

# Service-specific debugging
make db-logs           # Database logs only
make api-logs          # API logs only
make pgb-logs          # PgBouncer logs only
```

#### 7.3 Development Workflow
```bash
# Daily development workflow
make dev-up            # Start development environment
# ... development work ...
make backup            # Backup current state
make dev-down          # Stop environment

# Reset environment
make dev-down
make cleanup-backups
make dev-up
```

## Implementation

### 1. Script Standards
```bash
# All scripts follow these standards
set -euo pipefail      # Strict error handling
# Colored output for better UX
# Comprehensive error messages
# Health check integration
# Logging to both console and files
```

### 2. Container Management
```bash
# Container naming convention
nv-db          # PostgreSQL database
nv-pgbouncer   # PgBouncer connection pooler
nv-api         # FastAPI application

# Volume management
nv-db-data     # PostgreSQL data persistence
./backups/     # Backup file storage
./logs/        # Application logs
```

### 3. Port Management
```yaml
Port Allocation:
  5433: PostgreSQL (avoids conflict with system PostgreSQL:5432)
  6432: PgBouncer (standard PgBouncer port)
  13370: FastAPI API (distinctive port for ninaivalaigal)
```

## Testing Strategy

### 1. Environment Testing
```bash
# Test complete stack startup
make dev-up
make health
make dev-down

# Test individual services
make db-start && make db-status && make db-stop
make pgb-start && make pgb-status && make pgb-stop
make api-start && make api-status && make api-stop
```

### 2. Data Management Testing
```bash
# Test backup and restore
make dev-up
make backup
make dev-down
make restore
make health
```

### 3. Error Handling Testing
```bash
# Test error scenarios
# - Port conflicts
# - Missing dependencies
# - Configuration errors
# - Service failures
```

## Security Considerations

### 1. Development Security
```yaml
Security Measures:
  - Non-production secrets only
  - Local network binding only
  - Development-specific JWT secrets
  - No external network exposure by default
```

### 2. Data Protection
```yaml
Data Safety:
  - Automatic backups before major operations
  - Backup verification
  - Safe restore procedures
  - Development data isolation
```

## Success Criteria

### 1. Functional Requirements
- ✅ Complete stack starts with single command
- ✅ All services pass health checks
- ✅ Backup and restore work reliably
- ✅ Status monitoring provides clear information
- ✅ Error messages are helpful and actionable

### 2. Performance Requirements
- ✅ Stack startup time < 60 seconds
- ✅ Health check response time < 5 seconds
- ✅ Backup creation time < 30 seconds
- ✅ Service restart time < 10 seconds

### 3. Developer Experience Requirements
- ✅ Simple, memorable commands
- ✅ Clear status and error messages
- ✅ Comprehensive documentation
- ✅ Troubleshooting support
- ✅ Consistent behavior across environments

## Future Enhancements

1. **Hot Reload**: Automatic service restart on code changes
2. **Test Data Management**: Automated test data generation and seeding
3. **Performance Profiling**: Built-in performance monitoring and profiling
4. **Multi-Environment**: Support for multiple development environments
5. **IDE Integration**: VS Code tasks and debugging configuration
6. **Docker Compose**: Alternative Docker Compose setup for non-Apple Container CLI users

## Dependencies

- Apple Container CLI (primary container runtime)
- PostgreSQL client tools (psql, pg_dump, pg_restore)
- curl (health check testing)
- jq (JSON processing)
- Make (build automation)
- Bash (script execution)

This specification ensures ninaivalaigal has a professional, developer-friendly local development environment with comprehensive management capabilities.
