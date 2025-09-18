#!/bin/bash
# Make script executable
chmod +x "$0"
set -e

echo "🚀 Mac Studio Deployment Script"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running on Mac Studio
if [[ $(uname -m) != "arm64" ]] || [[ $(sysctl -n hw.memsize) -lt 137438953472 ]]; then
    log_warning "This script is optimized for Mac Studio (ARM64 + 128GB+)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. System Setup
log_step "Setting up system accounts and directories..."

# Create medhasys user if doesn't exist
if ! id "medhasys" &>/dev/null; then
    sudo dscl . -create /Users/medhasys
    sudo dscl . -create /Users/medhasys UserShell /bin/zsh
    sudo dscl . -create /Users/medhasys RealName "Medhasys Service"
    sudo dscl . -create /Users/medhasys UniqueID 510
    sudo dscl . -create /Users/medhasys PrimaryGroupID 20
    sudo dscl . -create /Users/medhasys NFSHomeDirectory /Users/medhasys
    sudo mkdir -p /Users/medhasys && sudo chown -R medhasys:staff /Users/medhasys
    log_success "Created medhasys service user"
else
    log_success "medhasys user already exists"
fi

# Create service directories
sudo mkdir -p /srv/medhasys/{volumes/db,volumes/redis,logs,artifacts,caches,backups}
sudo chown -R medhasys:staff /srv/medhasys
log_success "Service directories created"

# 2. Install Docker Desktop if not present
log_step "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_step "Installing Docker Desktop..."
    brew install --cask docker
    log_success "Docker Desktop installed - please start it manually once"
    echo "Press any key after Docker Desktop is running..."
    read -n 1 -s
else
    log_success "Docker is available"
fi

# Verify Docker is running
if ! docker info &>/dev/null; then
    log_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# 3. Clone repository if not present
log_step "Setting up repository..."
REPO_PATH="/Users/medhasys/ninaivalaigal"
if [ ! -d "$REPO_PATH" ]; then
    sudo -u medhasys git clone https://github.com/Arunosaur/ninaivalaigal.git "$REPO_PATH"
    sudo chown -R medhasys:staff "$REPO_PATH"
    log_success "Repository cloned to $REPO_PATH"
else
    log_success "Repository already exists at $REPO_PATH"
    # Update repository
    cd "$REPO_PATH"
    sudo -u medhasys git pull origin main
    log_success "Repository updated"
fi

# 4. Create environment configuration
log_step "Setting up environment configuration..."
ENV_FILE="/srv/medhasys/.env"
if [ ! -f "$ENV_FILE" ]; then
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-32)
    
    sudo tee "$ENV_FILE" > /dev/null << EOF
# Generated on $(date)
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
JWT_SECRET=$JWT_SECRET
ENVIRONMENT=production
DATABASE_URL=postgresql://medhasys:$POSTGRES_PASSWORD@localhost:5433/medhasys
NINAIVALAIGAL_DATABASE_URL=postgresql://medhasys:$POSTGRES_PASSWORD@localhost:5433/medhasys
NINAIVALAIGAL_JWT_SECRET=$JWT_SECRET
NINAIVALAIGAL_JWT_EXPIRATION_HOURS=168
EOF
    
    sudo chmod 600 "$ENV_FILE"
    sudo chown medhasys:staff "$ENV_FILE"
    log_success "Environment configuration created"
    log_warning "Passwords generated and stored in $ENV_FILE"
else
    log_success "Environment configuration already exists"
fi

# 5. Create production docker-compose file
log_step "Creating production Docker Compose configuration..."
COMPOSE_FILE="/srv/medhasys/docker-compose.prod.yml"
sudo tee "$COMPOSE_FILE" > /dev/null << 'EOF'
name: medhasys-production
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: medhasys
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: medhasys
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=en_US.UTF-8"
    ports: ["5433:5432"]
    volumes:
      - /srv/medhasys/volumes/db:/var/lib/postgresql/data
      - /srv/medhasys/backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medhasys -d medhasys"]
      interval: 5s
      timeout: 5s
      retries: 20
    restart: unless-stopped
    shm_size: 1gb
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4.0'

  pgbouncer:
    image: bitnami/pgbouncer:latest
    depends_on: 
      postgres: { condition: service_healthy }
    environment:
      POSTGRESQL_HOST: postgres
      POSTGRESQL_PORT_NUMBER: "5432"
      POSTGRESQL_USERNAME: medhasys
      POSTGRESQL_PASSWORD: ${POSTGRES_PASSWORD}
      PGBOUNCER_DATABASE: medhasys
      PGBOUNCER_POOL_MODE: transaction
      PGBOUNCER_MAX_CLIENT_CONN: 1000
      PGBOUNCER_DEFAULT_POOL_SIZE: 25
    ports: ["6432:6432"]
    restart: unless-stopped

  api:
    build:
      context: /Users/medhasys/ninaivalaigal
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://medhasys:${POSTGRES_PASSWORD}@pgbouncer:6432/medhasys
      NINAIVALAIGAL_JWT_SECRET: ${JWT_SECRET}
      NINAIVALAIGAL_JWT_EXPIRATION_HOURS: "168"
      PYTHONUNBUFFERED: "1"
      ENVIRONMENT: production
    command: >
      bash -c "
        echo 'Waiting for database...' &&
        sleep 10 &&
        echo 'Running migrations...' &&
        cd /app &&
        alembic upgrade head &&
        echo 'Starting API server...' &&
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
      "
    ports: ["13370:8000"]
    depends_on:
      pgbouncer: { condition: service_started }
    volumes:
      - /Users/medhasys/ninaivalaigal:/app:ro
      - /srv/medhasys/logs:/app/logs:rw
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/healthz"]
      interval: 10s
      timeout: 3s
      retries: 12
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '8.0'

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes:
      - /srv/medhasys/volumes/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20
    restart: unless-stopped
EOF

sudo chown medhasys:staff "$COMPOSE_FILE"
log_success "Production Docker Compose configuration created"

# 6. Create Dockerfile if it doesn't exist
log_step "Creating Dockerfile..."
DOCKERFILE="$REPO_PATH/Dockerfile"
if [ ! -f "$DOCKERFILE" ]; then
    sudo tee "$DOCKERFILE" > /dev/null << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path
ENV PYTHONPATH="/app/server:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    sudo chown medhasys:staff "$DOCKERFILE"
    log_success "Dockerfile created"
else
    log_success "Dockerfile already exists"
fi

# 7. Deploy the stack
log_step "Deploying the production stack..."
cd /srv/medhasys

# Source environment variables
set -a
source .env
set +a

# Build and start services
sudo -u medhasys docker compose -f docker-compose.prod.yml --env-file .env up -d --build

log_success "Production stack deployed!"

# 8. Wait for services to be healthy
log_step "Waiting for services to be healthy..."
sleep 30

# Check service health
if curl -f http://localhost:13370/healthz > /dev/null 2>&1; then
    log_success "API server is healthy"
else
    log_warning "API server health check failed - check logs"
fi

if pg_isready -h localhost -p 5433 -U medhasys > /dev/null 2>&1; then
    log_success "PostgreSQL is healthy"
else
    log_warning "PostgreSQL health check failed - check logs"
fi

# 9. Display status
log_step "Deployment Status:"
echo ""
echo "🐳 Docker Services:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "🌐 Service URLs:"
echo "  API Server: http://localhost:13370"
echo "  API Health: http://localhost:13370/healthz"
echo "  API Docs: http://localhost:13370/docs"
echo "  PostgreSQL: localhost:5433"
echo "  Redis: localhost:6379"

echo ""
echo "📁 Important Paths:"
echo "  Repository: $REPO_PATH"
echo "  Environment: $ENV_FILE"
echo "  Logs: /srv/medhasys/logs"
echo "  Data: /srv/medhasys/volumes"
echo "  Backups: /srv/medhasys/backups"

echo ""
echo "🔧 Management Commands:"
echo "  View logs: docker compose -f /srv/medhasys/docker-compose.prod.yml logs -f"
echo "  Restart: docker compose -f /srv/medhasys/docker-compose.prod.yml restart"
echo "  Stop: docker compose -f /srv/medhasys/docker-compose.prod.yml down"
echo "  Update: cd $REPO_PATH && git pull && docker compose -f /srv/medhasys/docker-compose.prod.yml up -d --build"

echo ""
log_success "Mac Studio deployment complete! 🎉"
