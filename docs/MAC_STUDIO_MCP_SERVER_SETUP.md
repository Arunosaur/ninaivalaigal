# Mac Studio MCP Server Setup Guide

**Purpose**: Set up your Mac Studio as a centralized MCP server that colleagues can access via Tailscale Funnel
**Date**: 2025-09-30
**Status**: Production Ready

---

## 🎯 Overview

This guide sets up your Mac Studio to run:
1. **Ninaivalaigal API** - Memory management backend
2. **MCP Server** - Model Context Protocol server for Copilot integration
3. **Tailscale Funnel** - Public URL for colleague access

**Colleagues will**:
- Access your Mac Studio via a Tailscale Funnel URL
- Configure their Copilot to use your MCP server
- Store and recall memories without local setup

---

## 📋 Prerequisites

### **1. Install Tailscale**
```bash
# Install via Homebrew
brew install tailscale

# Or download from https://tailscale.com/download

# Start Tailscale
sudo tailscaled
tailscale up
```

### **2. Verify Docker**
```bash
# Check Docker is running
docker ps

# If not installed:
# Download from https://www.docker.com/products/docker-desktop
```

### **3. Clone Repository** (if not already done)
```bash
cd /Users/swami/WorkSpace/ninaivalaigal
git pull origin main
```

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Start the Production Stack**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Start all services (API, Redis, PostgreSQL, MCP)
docker-compose -f compose.production.yml up -d

# Wait for services to be healthy (30s)
sleep 30

# Verify all services are running
docker-compose -f compose.production.yml ps
```

**Expected output**:
```
NAME                      STATUS
ninaivalaigal-prod-api    Up (healthy)
ninaivalaigal-prod-db     Up (healthy)
ninaivalaigal-prod-redis  Up (healthy)
ninaivalaigal-prod-mcp    Up (healthy)
```

### **Step 2: Set Up Tailscale Funnel**

```bash
# Run the setup script
./scripts/setup-tailscale-funnel.sh
```

**This will**:
- Enable Tailscale Funnel on port 3000 (MCP server)
- Generate a public URL (e.g., `https://your-mac.ts.net:3000`)
- Test the connection
- Save the URL to `.tailscale-funnel-url`

### **Step 3: Get Your MCP URL**

```bash
# Your MCP server URL
cat .tailscale-funnel-url

# Example output:
# https://mac-studio-swami.ts.net:3000
```

**Share this URL with colleagues!**

---

## 🧪 Verify Everything Works

### **Test 1: Local Health Check**
```bash
# Test API
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Test MCP server
curl http://localhost:3000/health
# Expected: {"status":"healthy","api_connected":true,...}
```

### **Test 2: Funnel Access (Public URL)**
```bash
# Get your Funnel URL
FUNNEL_URL=$(cat .tailscale-funnel-url)

# Test from your Mac
curl ${FUNNEL_URL}/health

# Expected: {"status":"healthy",...}
```

### **Test 3: MCP Endpoints**
```bash
# Test memory storage
curl -X POST ${FUNNEL_URL}/mcp/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test memory from MCP",
    "context": "test",
    "tags": ["test", "mcp"]
  }'

# Expected: {"success":true,"memory_id":"..."}

# Test memory recall
curl -X POST ${FUNNEL_URL}/mcp/memory/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test memory",
    "context": "test",
    "limit": 10
  }'

# Expected: [{"id":"...","content":"Test memory from MCP",...}]
```

---

## 📝 Colleague Instructions

### **What to Share with Colleagues**

Send them this information:

```
🎉 Ninaivalaigal MCP Server is Ready!

MCP Server URL: https://your-mac.ts.net:3000

To use with Copilot:
1. Configure your Copilot MCP settings
2. Add MCP Server URL: https://your-mac.ts.net:3000
3. Test connection: https://your-mac.ts.net:3000/health

Available Endpoints:
- POST /mcp/memory/store - Store memories
- POST /mcp/memory/recall - Recall memories
- GET /mcp/contexts - List available contexts
- POST /mcp/memory/tokenize - Tokenize text

Documentation: [Link to your docs]

Questions? Contact me!
```

### **Copilot Configuration Example**

Colleagues should configure their Copilot with:

```json
{
  "mcp_servers": {
    "ninaivalaigal": {
      "url": "https://your-mac.ts.net:3000",
      "endpoints": {
        "store": "/mcp/memory/store",
        "recall": "/mcp/memory/recall",
        "contexts": "/mcp/contexts",
        "tokenize": "/mcp/memory/tokenize"
      }
    }
  }
}
```

---

## 🔧 Management Commands

### **View Logs**
```bash
# All services
docker-compose -f compose.production.yml logs -f

# Specific service
docker-compose -f compose.production.yml logs -f mcp
docker-compose -f compose.production.yml logs -f api
```

### **Restart Services**
```bash
# Restart all
docker-compose -f compose.production.yml restart

# Restart specific service
docker-compose -f compose.production.yml restart mcp
```

### **Stop Services**
```bash
# Stop all (keeps data)
docker-compose -f compose.production.yml stop

# Stop and remove containers (keeps data)
docker-compose -f compose.production.yml down

# Stop Tailscale Funnel
tailscale funnel off
```

### **Update Code**
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f compose.production.yml up -d --build
```

---

## 📊 Monitoring

### **Check Service Status**
```bash
# Docker containers
docker-compose -f compose.production.yml ps

# Tailscale Funnel status
tailscale funnel status

# Resource usage
docker stats
```

### **Check Funnel Traffic**
```bash
# View Funnel logs
tailscale funnel status

# Monitor API requests
docker-compose -f compose.production.yml logs -f api | grep "POST\|GET"
```

### **Health Checks**
```bash
# Create a monitoring script
cat > check-health.sh << 'EOF'
#!/bin/bash
echo "Checking services..."
curl -s http://localhost:8000/health | jq
curl -s http://localhost:3000/health | jq
curl -s $(cat .tailscale-funnel-url)/health | jq
EOF

chmod +x check-health.sh
./check-health.sh
```

---

## 🔒 Security Considerations

### **1. Tailscale Funnel Security**
- Funnel URLs are public but require HTTPS
- Consider adding authentication to MCP endpoints
- Monitor access logs regularly

### **2. Production Secrets**
Create `.env.production` file:
```bash
# .env.production
NINA_DB_PASSWORD=your_secure_db_password_here
NINA_REDIS_PASSWORD=your_secure_redis_password_here
NINA_JWT_SECRET=your_secure_jwt_secret_here
```

Load it:
```bash
# Add to docker-compose command
docker-compose -f compose.production.yml --env-file .env.production up -d
```

### **3. Firewall Rules**
```bash
# Only Tailscale Funnel needs external access
# Local ports (5432, 6379, 8000) should not be exposed externally
```

---

## 🐛 Troubleshooting

### **Issue: Funnel URL Not Accessible**

```bash
# Check Tailscale status
tailscale status

# Check Funnel status
tailscale funnel status

# Restart Funnel
tailscale funnel off
tailscale funnel 3000
```

### **Issue: MCP Server Not Responding**

```bash
# Check MCP container
docker logs ninaivalaigal-prod-mcp

# Restart MCP
docker-compose -f compose.production.yml restart mcp

# Check if port 3000 is available
lsof -i :3000
```

### **Issue: API Connection Failed**

```bash
# Check API health
curl http://localhost:8000/health

# Check API logs
docker logs ninaivalaigal-prod-api

# Restart API
docker-compose -f compose.production.yml restart api
```

### **Issue: Database Connection Failed**

```bash
# Check PostgreSQL
docker exec ninaivalaigal-prod-db psql -U nina -d ninaivalaigal_prod -c "SELECT 1;"

# Check logs
docker logs ninaivalaigal-prod-db

# Restart database
docker-compose -f compose.production.yml restart postgres
```

---

## 📈 Performance Tuning

### **For Mac Studio (M2 Max/Ultra)**

Update `compose.production.yml` for better performance:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  postgres:
    command: >
      postgres
      -c shared_buffers=2GB
      -c effective_cache_size=6GB
      -c maintenance_work_mem=512MB
      -c max_connections=200

  redis:
    command: redis-server
      --requirepass ${NINA_REDIS_PASSWORD:-secure_nina_password}
      --maxmemory 4gb
      --maxmemory-policy allkeys-lru
```

---

## 🎯 Success Criteria

Your setup is ready when:

- ✅ All 4 containers running and healthy
- ✅ Tailscale Funnel URL accessible
- ✅ MCP health check returns "healthy"
- ✅ Colleagues can access Funnel URL
- ✅ Memory store/recall works via MCP

---

## 📞 Quick Reference

```bash
# Start everything
docker-compose -f compose.production.yml up -d
./scripts/setup-tailscale-funnel.sh

# Get MCP URL
cat .tailscale-funnel-url

# Check health
curl $(cat .tailscale-funnel-url)/health

# View logs
docker-compose -f compose.production.yml logs -f

# Stop everything
docker-compose -f compose.production.yml down
tailscale funnel off
```

---

**Setup Time**: ~5 minutes
**Colleague Setup Time**: ~2 minutes (just configure Copilot)
**Maintenance**: Minimal (restart on Mac reboot)

---

*Last Updated: 2025-09-30*
*Status: Production Ready*
*Next Review: After colleague feedback*
