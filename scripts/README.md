# Scripts Directory

This directory contains automation scripts for the ninaivalaigal project, with a focus on Mac Studio deployment using Apple Container CLI.

## Apple Container CLI Scripts (Mac Studio)

### Database Management
- **`nv-db-start.sh`** - Start PostgreSQL + pgvector container
- **`nv-db-stop.sh`** - Stop and remove database container  
- **`nv-db-status.sh`** - Check database container health
- **`nv-test-db.sh`** - Run tests against database container

### Usage Examples

```bash
# Start database
./scripts/nv-db-start.sh

# Check status
./scripts/nv-db-status.sh

# Run tests
./scripts/nv-test-db.sh

# Stop database
./scripts/nv-db-stop.sh
```

## Container Performance Testing
- **`check_native_containers.sh`** - Check Apple Container CLI availability
- **`test_colima_postgres.sh`** - Test Colima performance (legacy)
- **`compare_container_performance.sh`** - Benchmark different runtimes

## Development & CI Scripts
- **`setup-persistent-postgres.sh`** - Set up persistent PostgreSQL
- **`db_snapshot_key.py`** - Generate database snapshot keys for CI
- **`generate_jwt_token.py`** - Generate JWT tokens for testing

## MCP (Model Context Protocol) Scripts
- **`start_mcp_server.sh`** - Start MCP server for VSCode integration
- **`start_mcp_for_vscode.sh`** - VSCode-specific MCP startup
- **`mcp_client.py`** - MCP client for testing

## Project Management
- **`create-new-feature.sh`** - Create new feature branches
- **`check-task-prerequisites.sh`** - Validate task prerequisites
- **`update-agent-context.sh`** - Update AI agent context

## Security & RBAC
- **`rbac_policy_snapshot_gate.py`** - RBAC policy validation
- **`policy_snapshot_gate.py`** - Policy change detection
- **`multipart_policy_snapshot_gate.py`** - Multi-part policy validation

## System Validation
- **`test-shell-integration.sh`** - Test shell integration
- **`setup-plan.sh`** - System setup planning

## Common Utilities
- **`common.sh`** - Shared functions and utilities
- **`get-feature-paths.sh`** - Get feature-related file paths

## Apple Container CLI Syntax Reference

Key differences from Docker:

| Operation | Docker | Apple Container CLI |
|-----------|--------|-------------------|
| List containers | `docker ps` | `container list` |
| Remove container | `docker rm` | `container delete` |
| List images | `docker images` | `container images list` |
| Pull image | `docker pull` | `container images pull` |

## Environment Setup

Copy and edit the environment template:
```bash
cp .env.example .env
# Edit .env to set POSTGRES_PASSWORD and other values
```

## Validation Status

✅ **Apple Container CLI**: Validated on Mac Studio M1 Ultra  
✅ **PostgreSQL + pgvector**: Working perfectly  
✅ **Performance**: Excellent native ARM64 optimization  
✅ **Scripts**: Production-ready with correct syntax  

For detailed validation results, see `docs/APPLE_CONTAINER_CLI_SETUP.md`.
