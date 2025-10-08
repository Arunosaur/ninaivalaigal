# Runtime Management Guide

## 🎯 Overview

Ninaivalaigal supports three container runtimes:
- **Docker** - Standard Docker Desktop
- **Colima** - Lightweight Docker alternative
- **Apple Container CLI** - Native Apple Silicon container runtime (3-5x faster)

Only **one runtime** should be active at a time to prevent conflicts.

## 🚀 Quick Start

### 1. Check Current Runtime
```bash
make runtime-status
```

### 2. Switch Runtimes

```bash
# Switch to Apple Container CLI (recommended for M1/M2/M3)
make runtime-apple

# Switch to Docker
make runtime-docker

# Switch to Colima
make runtime-colima
```

### 3. Start Stack
```bash
# For Apple Container CLI
./start-apple-container-stack.sh

# For Docker/Colima
make docker-dev-up
# or
make colima-dev-up
```

### 4. Health Check
```bash
make health-check
```

## ⚙️ Configuration

Runtime config is stored in `.runtime-config` (gitignored):

```bash
ACTIVE_RUNTIME=apple              # docker | colima | apple
HEALTH_MONITORING_ENABLED=true    # Enable health checks
AUTO_RESTART_ENABLED=false        # Auto-restart unhealthy containers
```

### Enable Auto-Restart
```bash
make runtime-auto-restart-on
```

### Disable Auto-Restart
```bash
make runtime-auto-restart-off
```

## 🔄 Runtime-Aware Health Monitoring

The health check script (`scripts/runtime-aware-health-check.sh`) automatically:
- Detects active runtime from `.runtime-config`
- Uses correct container commands (`container` vs `docker`)
- Only monitors containers for the active runtime
- Optionally restarts unhealthy containers

**Benefits:**
- ✅ No conflicts between runtimes
- ✅ Automatic runtime detection
- ✅ Prevents Docker from interfering with Apple Container CLI
- ✅ Clean runtime switching

## 🛠️ Manual Runtime Management

### Stop All Containers (All Runtimes)
```bash
# Docker/Colima
docker-compose -f compose.docker.yml down
docker stop $(docker ps -q)

# Apple Container CLI
container list | grep nv- | awk '{print $1}' | xargs -I {} container stop {}
```

### Disable LaunchAgents (Prevents Auto-Restart)
```bash
# Rename to .disabled to prevent auto-start
mv ~/Library/LaunchAgents/com.ninaivalaigal.*.plist \
   ~/Library/LaunchAgents/com.ninaivalaigal.*.plist.disabled
```

### Re-enable LaunchAgents
```bash
# Remove .disabled suffix
for f in ~/Library/LaunchAgents/com.ninaivalaigal.*.plist.disabled; do
    mv "$f" "${f%.disabled}"
done
```

## 📊 Comparison

| Feature | Docker | Colima | Apple Container CLI |
|---------|--------|--------|---------------------|
| **Performance** | Baseline | 1.5x faster | 3-5x faster |
| **Memory Usage** | High | Medium | Low |
| **Startup Time** | Slow | Medium | Fast |
| **ARM64 Native** | Emulated | Native | Native |
| **Maturity** | Stable | Stable | Experimental |

## 🐛 Troubleshooting

### Containers Keep Restarting
```bash
# Check for health monitors
ps aux | grep -E "comprehensive-health|nina-intelligence-health"

# Kill them
killall comprehensive-health-monitor.sh
killall nina-intelligence-health-monitor.sh

# Disable LaunchAgents
make runtime-auto-restart-off
```

### Can't Switch Runtimes
```bash
# Force stop all containers
docker stop $(docker ps -q) 2>/dev/null || true
container list | awk 'NR>1 {print $1}' | xargs -I {} container stop {} 2>/dev/null || true

# Then switch
make runtime-apple
```

### Health Check Fails
```bash
# Verify runtime config
cat .runtime-config

# Manually run health check with debug
bash -x scripts/runtime-aware-health-check.sh
```

## 📝 Best Practices

1. **Choose one runtime** and stick with it during development
2. **Disable auto-restart** during active development (set `AUTO_RESTART_ENABLED=false`)
3. **Use `make runtime-status`** before starting work to verify configuration
4. **Switch runtimes cleanly** using `make runtime-<name>` (stops old containers first)
5. **Enable auto-restart** only in production/staging environments

## 🎓 Examples

### Development Workflow
```bash
# Morning: Check what's running
make runtime-status
docker ps
container list

# Switch to Apple CLI for fast iteration
make runtime-apple

# Start stack
./start-apple-container-stack.sh

# Work, make changes, rebuild...

# End of day: Check health
make health-check
```

### Production Deployment
```bash
# Production uses Docker for stability
make runtime-docker

# Enable auto-restart
make runtime-auto-restart-on

# Deploy
make docker-dev-up

# Verify
make health-check
```

---

**Created:** October 7, 2025
**Last Updated:** October 7, 2025
