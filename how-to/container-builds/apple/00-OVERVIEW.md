# Apple Container CLI - Overview
**Runtime**: Apple Container CLI (built-in macOS Sequoia+)
**Architecture**: ARM64 (Apple Silicon)
**Status**: ✅ Production-ready for development

---

## System Requirements

### macOS Version
- **Minimum**: macOS Sequoia 15.0+
- **Recommended**: macOS Sequoia 15.1+
- **Hardware**: Mac with Apple Silicon (M1/M2/M3/M4)

### Installation
```bash
# Apple Container CLI is built-in, no installation needed
container version

# If not available, update macOS to Sequoia or later
```

---

## Architecture Support

### Native ARM64
- **Primary**: All containers built and run natively on ARM64
- **Performance**: Optimal, no emulation overhead
- **Compatibility**: Some packages require ARM64-specific builds

### x86_64 via Rosetta
- ⚠️ **Not Recommended**: Use native ARM64 images
- ⚠️ **Performance**: Significant overhead
- ⚠️ **Issues**: May have compatibility problems

---

## Command Reference

### Image Management
```bash
# Build image
container build -t {name}:{tag} -f {dockerfile} {context}

# List images
container image list

# Remove image
container image rm {name}:{tag}

# Load from tar
container image load --input {file}.tar

# Save to tar (not directly supported, use Docker)
docker save {name}:{tag} -o {file}.tar
# Then: container image load --input {file}.tar
```

### Container Management
```bash
# Run container
container run -d --name {name} \
  -p {host}:{container} \
  -e {VAR}={value} \
  {image}:{tag}

# List containers
container list
container list --all  # Include stopped

# Stop container
container stop {name}

# Start container
container start {name}

# Remove container
container delete {name}

# Logs
container logs {name}
container logs -f {name}  # Follow

# Execute command
container exec {name} {command}
container exec -it {name} bash
```

### Networking
```bash
# Inspect container network
container inspect {name} | jq -r '.[0].networks[0].address'

# Get container IP
CONTAINER_IP=$(container inspect {name} | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

---

## File Locations

### Containers
```
/Users/{user}/Library/Application Support/com.apple.container/containers/{container-name}/
```

### Images
```
/Users/{user}/Library/Application Support/com.apple.container/images/
```

### Volumes
```
/Users/{user}/Library/Application Support/com.apple.container/volumes/
```

---

## Known Limitations

### DNS Resolution
**Issue**: Build containers may fail to resolve DNS during `apt-get update`
```
Error: Temporary failure resolving 'apt.postgresql.org'
```

**Solutions**:
1. **Wait and retry**: Often a temporary network issue
2. **Check network**: `ping apt.postgresql.org`
3. **Build with Docker, transfer to Apple**:
   ```bash
   docker build -t {name}:{tag} .
   docker save {name}:{tag} -o /tmp/{name}.tar
   container image load --input /tmp/{name}.tar
   ```

### Image Load Performance
**Issue**: Large images (>2GB) may take time to load
- **Expected**: 2-3 minutes for 2GB image
- **If hangs**: Check available disk space, restart terminal

### Registry Access
**Issue**: No direct `container push` to registries
**Workaround**: Build with Docker, push, then pull with Apple Container CLI

---

## Best Practices

### Development Workflow
1. **Build**: Use Apple Container CLI for local builds
2. **Test**: Verify locally
3. **Transfer**: If needed for CI/CD:
   ```bash
   docker save {name}:arm64 -o /tmp/{name}.tar
   # Upload tar to CI/CD or registry
   ```

### Image Tagging
```bash
# Always tag with architecture
container build -t {service}:arm64 .

# For multi-arch support
container build -t {service}:latest .
```

### Resource Management
```bash
# Clean up stopped containers
container list --all | grep -v running | awk '{print $1}' | xargs container delete

# Clean up unused images
container image list | grep '<none>' | awk '{print $2}' | xargs container image rm
```

---

## Performance

### Build Time (Approximate)
- **Database (with AGE + pgvector)**: 2-3 minutes
- **API (with dependencies)**: 1-2 minutes
- **Redis**: <1 minute (pre-built)
- **PgBouncer**: <1 minute
- **UI**: 1-2 minutes

### Container Startup
- **Database**: 15-30 seconds (including init scripts)
- **Redis**: <5 seconds
- **PgBouncer**: <5 seconds
- **API**: 10-15 seconds

---

## Troubleshooting

### Container won't start
```bash
# Check logs
container logs {name}

# Check if port is in use
lsof -i :{port}

# Check container state
container inspect {name}
```

### Build fails
```bash
# Check disk space
df -h

# Clean build cache
container system prune

# Try with --no-cache
container build --no-cache -t {name}:{tag} .
```

### Network issues
```bash
# Check DNS
ping apt.postgresql.org
ping deb.debian.org

# Restart container runtime (if needed)
# No direct command - restart Mac or wait for automatic restart
```

---

## Migration from Docker

### Import Docker image
```bash
# Save from Docker
docker save {image}:{tag} -o /tmp/{image}.tar

# Load to Apple Container CLI
container image load --input /tmp/{image}.tar

# Verify
container image list | grep {image}
```

### Update scripts
```bash
# Replace all 'docker' commands with 'container'
docker run    → container run
docker build  → container build
docker ps     → container list
docker stop   → container stop
docker rm     → container delete
```

---

## Next Steps

1. Review [STANDARDS.md](./STANDARDS.md) for naming conventions
2. Read [DO-NOT-DOS.md](./DO-NOT-DOS.md) to avoid common mistakes
3. Check [CONNECTIVITY.md](./CONNECTIVITY.md) for network configuration
4. Start with [01-database.md](./01-database.md) to build your first container

---

## Quick Reference Card

```bash
# Build
container build --no-cache -t {service}:arm64 -f Dockerfile .

# Run
container run -d --name ninaivalaigal-dev-{service} \
  -p {port}:{port} \
  -e VAR=value \
  {service}:arm64

# Manage
container list                    # List running
container stop {name}             # Stop
container delete {name}           # Remove
container logs {name}             # View logs

# Network
container inspect {name} | jq -r '.[0].networks[0].address' | cut -d'/' -f1

# Cleanup
container list --all | grep Exited | awk '{print $1}' | xargs container delete
```
