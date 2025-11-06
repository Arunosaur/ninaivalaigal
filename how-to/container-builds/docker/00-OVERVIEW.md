# Docker - Overview
**Runtime**: Docker Desktop / Docker Engine
**Architectures**: ARM64 (Apple Silicon) + x86-64 (AMD64)
**Status**: ✅ Production-ready for multi-architecture builds

---

## System Requirements

### Docker Installation
```bash
# macOS (Docker Desktop)
brew install --cask docker

# Linux (Docker Engine)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify installation
docker --version
docker buildx version  # Required for multi-arch builds
```

### Docker Buildx Setup
```bash
# Enable buildx (usually enabled by default in Docker Desktop)
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Verify multi-arch support
docker buildx ls
```

---

## Architecture Support

### ARM64 (Apple Silicon)
- **Primary**: Native builds on Apple Silicon Macs
- **Performance**: Optimal, no emulation
- **Use Case**: Development, local testing, ARM64 production (AWS Graviton)

### x86-64 (AMD64)
- **Primary**: Standard Linux/cloud deployments
- **Performance**: Native on x86-64 systems
- **Use Case**: Cloud VMs, CI/CD, production deployments

### Multi-Architecture Builds
- **Method**: Docker buildx with multi-platform support
- **Output**: Single manifest pointing to architecture-specific images
- **Push**: Can push to registry with single manifest

---

## Command Reference

### Image Management
```bash
# Build single architecture
docker build --platform linux/arm64 -t {name}:{tag} -f {dockerfile} {context}
docker build --platform linux/amd64 -t {name}:{tag} -f {dockerfile} {context}

# Build multi-arch manifest (recommended)
docker buildx build --platform linux/arm64,linux/amd64 \
  -t {name}:{tag} \
  -f {dockerfile} \
  {context}

# List images
docker images
docker images | grep {name}

# Remove image
docker rmi {name}:{tag}

# Save to tar
docker save {name}:{tag} -o {file}.tar

# Load from tar
docker load -i {file}.tar
```

### Container Management
```bash
# Run container
docker run -d --name {name} \
  -p {host}:{container} \
  -e {VAR}={value} \
  {image}:{tag}

# List containers
docker ps
docker ps -a  # Include stopped

# Stop container
docker stop {name}

# Start container
docker start {name}

# Remove container
docker rm {name}
docker rm -f {name}  # Force remove

# Logs
docker logs {name}
docker logs -f {name}  # Follow

# Execute command
docker exec {name} {command}
docker exec -it {name} bash
```

### Networking
```bash
# Inspect container network
docker inspect {name} | jq -r '.[0].NetworkSettings.Networks'

# Get container IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {name}

# List networks
docker network ls

# Create network
docker network create {name}
```

---

## Multi-Architecture Builds

### Using build-docker-service.sh (Recommended)
```bash
# Build both architectures separately
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context .

# Build only ARM64
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context . \
  --arch arm64

# Build only x86-64
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context . \
  --arch amd64

# Build multi-arch manifest
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context . \
  --multi-arch
```

### Manual buildx Commands
```bash
# Build multi-arch without manifest (separate images)
docker buildx build --platform linux/arm64 \
  -t {name}:arm64 \
  -f {dockerfile} \
  {context} \
  --load

docker buildx build --platform linux/amd64 \
  -t {name}:amd64 \
  -f {dockerfile} \
  {context} \
  --load

# Build multi-arch manifest (single tag, multiple architectures)
docker buildx build --platform linux/arm64,linux/amd64 \
  -t {name}:{tag} \
  -f {dockerfile} \
  {context} \
  --push  # Push to registry

# Or save locally (requires --load per platform or --output)
docker buildx build --platform linux/arm64,linux/amd64 \
  -t {name}:{tag} \
  -f {dockerfile} \
  {context} \
  --output type=docker,dest=- | docker load
```

---

## Port Allocation

All ports follow `config/ports.nv.yaml`:

### Docker Dev Environment
- **core-api**: 13370
- **business-service**: 13371
- **admin-vendor-service**: 13372
- **memory-service**: 13373
- **graph-service**: 13374
- **grpc-gateway**: 13375

### Docker Test Environment
- **core-api**: 13470
- **business-service**: 13471
- **admin-vendor-service**: 13472
- **memory-service**: 13473
- **graph-service**: 13474
- **grpc-gateway**: 13475

### Docker Prod Environment
- **core-api**: 13570
- **business-service**: 13571
- **admin-vendor-service**: 13572
- **memory-service**: 13573
- **graph-service**: 13574
- **grpc-gateway**: 13575

See `config/ports.nv.yaml` for complete port matrix.

---

## Best Practices

### Build Performance
- ✅ Use `--no-cache` only when dependencies change
- ✅ Leverage Docker layer caching
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Build context should be minimal

### Security
- ✅ Use non-root user in containers
- ✅ Scan images for vulnerabilities: `docker scan {image}`
- ✅ Use specific tags, avoid `latest` in production
- ✅ Keep base images updated

### Multi-Architecture
- ✅ Test both ARM64 and x86-64 before deploying
- ✅ Use multi-arch manifests for registry pushes
- ✅ Verify platform-specific dependencies
- ✅ Test cross-platform compatibility

### Resource Management
- ✅ Set memory limits: `docker run -m 2g {image}`
- ✅ Set CPU limits: `docker run --cpus="2.0" {image}`
- ✅ Monitor resource usage: `docker stats`
- ✅ Clean up unused images: `docker image prune`

---

## Troubleshooting

### Build Issues
```bash
# Clear build cache
docker builder prune

# Check buildx status
docker buildx ls

# Inspect build process
docker buildx build --progress=plain ...
```

### Platform Issues
```bash
# Verify platform
docker inspect {image} | jq -r '.[0].Architecture'

# Check if image supports your platform
docker manifest inspect {image}:{tag}
```

### Networking Issues
```bash
# Check container network
docker network inspect bridge

# Test connectivity
docker exec {container} ping {target}
docker exec {container} curl {url}
```

---

## Quick Reference

### Build Service
```bash
./scripts/build-docker-service.sh {service} \
  --dockerfile {path} \
  --context {context} \
  --arch arm64,amd64
```

### Run Container
```bash
docker run -d --name ninaivalaigal-dev-{service} \
  -p {port}:8000 \
  -e NINA_ENV=dev \
  nina-{service}:{arch}
```

### Verify Health
```bash
curl http://localhost:{port}/health
docker logs ninaivalaigal-dev-{service}
```

---

**Last Updated**: 2025-01-31
**Part of**: SPEC-145 Multi-Runtime Multi-Architecture Builds
