#!/bin/bash

# setup-persistent-postgres.sh - Persistent PostgreSQL setup for Ninaivalaigal
# Creates a persistent Docker PostgreSQL container with correct credentials

set -e

echo "🐘 Ninaivalaigal PostgreSQL Persistent Setup"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - matches our security architecture
CONTAINER_NAME="ninaivalaigal_postgres"
POSTGRES_DB="ninaivalaigal_db"
POSTGRES_USER="ninaivalaigal_app"
POSTGRES_PASSWORD="ninaivalaigal_secure_password_2024"
POSTGRES_PORT="5432"
VOLUME_NAME="ninaivalaigal_postgres_data"

# Helper functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Check if Docker is running
check_docker() {
    log_step "Checking Docker status..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    log_info "Docker is running"
}

# Stop and remove existing container if it exists
cleanup_existing() {
    log_step "Cleaning up existing PostgreSQL container..."
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Stopping existing container: ${CONTAINER_NAME}"
        docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
        docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
        log_info "Existing container removed"
    else
        log_info "No existing container found"
    fi
}

# Create persistent volume
create_volume() {
    log_step "Creating persistent volume..."
    
    if docker volume ls --format '{{.Name}}' | grep -q "^${VOLUME_NAME}$"; then
        log_info "Volume ${VOLUME_NAME} already exists"
    else
        docker volume create ${VOLUME_NAME}
        log_info "Created volume: ${VOLUME_NAME}"
    fi
}

# Start PostgreSQL container
start_postgres() {
    log_step "Starting persistent PostgreSQL container..."
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -e POSTGRES_DB=${POSTGRES_DB} \
        -e POSTGRES_USER=${POSTGRES_USER} \
        -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
        -e POSTGRES_HOST_AUTH_METHOD=md5 \
        -p ${POSTGRES_PORT}:5432 \
        -v ${VOLUME_NAME}:/var/lib/postgresql/data \
        postgres:15
    
    log_info "PostgreSQL container started: ${CONTAINER_NAME}"
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log_step "Waiting for PostgreSQL to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec ${CONTAINER_NAME} pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} >/dev/null 2>&1; then
            log_info "PostgreSQL is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL failed to start within 60 seconds"
    exit 1
}

# Create database schema
setup_schema() {
    log_step "Setting up database schema..."
    
    # Check if schema files exist
    if [ -f "/Users/asrajag/Workspace/mem0/scripts/create-postgresql-schema.sql" ]; then
        docker exec -i ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < /Users/asrajag/Workspace/mem0/scripts/create-postgresql-schema.sql
        log_info "Main schema created"
    else
        log_warn "Main schema file not found, skipping"
    fi
    
    if [ -f "/Users/asrajag/Workspace/mem0/scripts/create-team-merger-schema.sql" ]; then
        docker exec -i ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < /Users/asrajag/Workspace/mem0/scripts/create-team-merger-schema.sql
        log_info "Team merger schema created"
    else
        log_warn "Team merger schema file not found, skipping"
    fi
}

# Update configuration files
update_config() {
    log_step "Updating configuration files..."
    
    # Database URL for the application
    DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
    
    # Update .env file if it exists
    if [ -f "/Users/asrajag/Workspace/mem0/.env" ]; then
        sed -i '' "s|NINAIVALAIGAL_DATABASE_URL=.*|NINAIVALAIGAL_DATABASE_URL=${DATABASE_URL}|" /Users/asrajag/Workspace/mem0/.env
        log_info "Updated .env file"
    else
        # Create .env file
        cat > /Users/asrajag/Workspace/mem0/.env << EOF
NINAIVALAIGAL_DATABASE_URL=${DATABASE_URL}
NINAIVALAIGAL_JWT_SECRET=ninaivalaigal-super-secret-jwt-signing-key-min-32-chars-2024
NINAIVALAIGAL_DEBUG=true
EOF
        log_info "Created .env file"
    fi
    
    # Update VS Code MCP configuration
    cat > /Users/asrajag/Workspace/mem0/.vscode/mcp.json << EOF
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "${DATABASE_URL}",
        "NINAIVALAIGAL_JWT_SECRET": "ninaivalaigal-super-secret-jwt-signing-key-min-32-chars-2024",
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYXJ1biIsIm9yZ2FuaXphdGlvbl9pZCI6ImFjbWVfY29ycCIsInRlYW1zIjpbeyJ0ZWFtX2lkIjoiZW5naW5lZXJpbmciLCJyb2xlIjoibGVhZCJ9XSwiZXhwIjoxNzU3NjQ5NjAwfQ.example_signature_replace_with_real"
      }
    }
  }
}
EOF
    log_info "Updated VS Code MCP configuration"
}

# Test database connection
test_connection() {
    log_step "Testing database connection..."
    
    if docker exec ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT version();" >/dev/null 2>&1; then
        log_info "Database connection successful"
        
        # Show database info
        echo ""
        echo "📊 Database Information:"
        echo "  Container: ${CONTAINER_NAME}"
        echo "  Database: ${POSTGRES_DB}"
        echo "  User: ${POSTGRES_USER}"
        echo "  Port: ${POSTGRES_PORT}"
        echo "  Volume: ${VOLUME_NAME}"
        echo "  URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
    else
        log_error "Database connection failed"
        exit 1
    fi
}

# Show container management commands
show_management_commands() {
    echo ""
    echo "🔧 Container Management Commands:"
    echo "  Start:   docker start ${CONTAINER_NAME}"
    echo "  Stop:    docker stop ${CONTAINER_NAME}"
    echo "  Restart: docker restart ${CONTAINER_NAME}"
    echo "  Logs:    docker logs ${CONTAINER_NAME}"
    echo "  Shell:   docker exec -it ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
    echo ""
    echo "💾 Data Persistence:"
    echo "  Volume: ${VOLUME_NAME}"
    echo "  Backup: docker run --rm -v ${VOLUME_NAME}:/data -v \$(pwd):/backup alpine tar czf /backup/postgres-backup-\$(date +%Y%m%d).tar.gz -C /data ."
    echo ""
}

# Main execution
main() {
    echo "Starting PostgreSQL setup for Ninaivalaigal..."
    echo ""
    
    check_docker
    cleanup_existing
    create_volume
    start_postgres
    wait_for_postgres
    setup_schema
    update_config
    test_connection
    show_management_commands
    
    echo ""
    log_info "PostgreSQL setup completed successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Restart your VS Code to reload MCP configuration"
    echo "  2. Test with: @e^m remember 'PostgreSQL is working' --context test"
    echo "  3. Check with: @e^m recall --context test"
    echo ""
}

# Run main function
main "$@"
