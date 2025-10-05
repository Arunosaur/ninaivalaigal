# Database Image Management Guide

## 🎯 Overview

The ninaivalaigal database uses a custom PostgreSQL image with:
- **PostgreSQL 15**
- **pgvector v0.5.1** (for embeddings)
- **Apache AGE v1.5.0-rc0** (for graph queries)

This image is **persistent across system restarts** once built or pulled.

---

## 🏗️ Building the Database Image

### **One-Time Build (Local Development):**
```bash
make build-db
```

This creates: `ghcr.io/arunosaur/ninaivalaigal-db:latest`

**Build time:** ~3-5 minutes (ARM64), ~5-8 minutes (x86_64)

---

## 📦 Pulling from GitHub Container Registry

### **Pull Pre-Built Image (Recommended):**
```bash
docker pull ghcr.io/arunosaur/ninaivalaigal-db:latest
```

**Prerequisites:**
- GitHub Container Registry authentication (for private repos)
- Or use public workflow to publish images

### **Authenticate with GHCR:**
```bash
# Create a GitHub Personal Access Token with read:packages
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

---

## 🔄 Automatic Image Management

The `compose.docker.yml` is configured to:

1. **Try to pull** from GHCR first
2. **Build locally** if pull fails
3. **Use cached image** if already exists locally

```yaml
postgres:
  image: ${NINA_DB_IMAGE:-ghcr.io/arunosaur/ninaivalaigal-db:latest}
  build:
    context: ./containers/consolidated-db
  pull_policy: missing  # Only pull if not available locally
```

---

## 🚀 Publishing Images to GHCR

### **Manual Push:**
```bash
# Build if not already built
make build-db

# Tag for GHCR (if not already tagged)
docker tag nina-intelligence-db:arm64 ghcr.io/arunosaur/ninaivalaigal-db:latest

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u arunosaur --password-stdin

# Push to registry
docker push ghcr.io/arunosaur/ninaivalaigal-db:latest
```

### **Automated Push via GitHub Actions:**

The workflow `.github/workflows/build-and-push-db.yml` automatically builds and pushes when:
- Manually triggered via workflow_dispatch
- Changes detected in `containers/consolidated-db/`
- Push to main branch

**Trigger manually:**
1. Go to GitHub Actions
2. Select "Build and Push Database Image"
3. Click "Run workflow"

---

## 🛡️ Preventing Image Loss

### **Why Images Disappear After Restart:**

1. **Docker Desktop "Resource Saver"** - Auto-cleans when idle
2. **Manual cleanup** - `docker system prune -a`
3. **Disk space cleanup** - macOS/Docker auto-cleanup
4. **GitHub Actions cleanup** - Workflow cleanup steps

### **Solutions Implemented:**

#### ✅ **1. GitHub Actions Cleanup Removed**
- Removed `docker image prune -f` from workflows
- Only removes temporary containers, keeps images

#### ✅ **2. Automatic Build on Missing**
- Compose file rebuilds if image not found
- No manual intervention needed

#### ✅ **3. GHCR Registry Storage**
- Images stored in GitHub Container Registry
- Pull instead of rebuild (seconds vs minutes)

#### ✅ **4. Pull Policy Optimized**
- `pull_policy: missing` - Only downloads if needed
- Uses local cache when available

---

## 📊 Image Verification

### **Check if Image Exists:**
```bash
docker images | grep ninaivalaigal-db
```

**Expected output:**
```
ghcr.io/arunosaur/ninaivalaigal-db   latest       95401910c9f0   4 hours ago    2.04GB
nina-intelligence-db                 arm64        79cf6445ca74   4 hours ago    2.04GB
```

### **Verify Extensions Installed:**
```bash
docker run --rm ghcr.io/arunosaur/ninaivalaigal-db:latest \
  psql --version
```

```bash
docker run --rm ghcr.io/arunosaur/ninaivalaigal-db:latest \
  ls -la /usr/share/postgresql/15/extension/ | grep -E "vector|age"
```

---

## 🔧 Troubleshooting

### **Image Not Found Error:**
```bash
Error: pull access denied for nina-intelligence-db
```

**Solution:**
```bash
# Option 1: Build locally
make build-db

# Option 2: Authenticate with GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u arunosaur --password-stdin
docker pull ghcr.io/arunosaur/ninaivalaigal-db:latest
```

### **Image Lost After Restart:**
```bash
# Check Docker Desktop settings:
# 1. Open Docker Desktop → Settings
# 2. Resources → Advanced
# 3. Disable "Remove unused images"
# 4. General → Disable "Use resource saver"
```

### **Rebuild Takes Too Long:**
```bash
# Use multi-core builds
docker buildx build --load \
  -t nina-intelligence-db:arm64 \
  ./containers/consolidated-db
```

---

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NINA_DB_IMAGE` | `ghcr.io/arunosaur/ninaivalaigal-db:latest` | Database image to use |
| `POSTGRES_DB` | `ninaivalaigal_dev` | Database name |
| `POSTGRES_USER` | `nina` | Database user |
| `POSTGRES_PASSWORD` | `dev_password_change_in_production` | Database password |

**Override image:**
```bash
NINA_DB_IMAGE=nina-intelligence-db:arm64 docker-compose up
```

---

## 🎯 Best Practices

### **For Local Development:**
1. Build once: `make build-db`
2. Disable Docker Desktop auto-cleanup
3. Images persist across restarts

### **For CI/CD:**
1. Use GHCR images: `docker pull ghcr.io/...`
2. GitHub Actions builds automatically
3. No manual builds needed

### **For Production:**
1. Always use tagged versions (not `:latest`)
2. Pin to specific SHA: `ghcr.io/.../ninaivalaigal-db@sha256:...`
3. Implement image scanning
4. Regular security updates

---

## 📚 Related Documentation

- [Docker Compose Configuration](../compose.docker.yml)
- [Database Dockerfile](../containers/consolidated-db/Dockerfile)
- [Build Workflow](../.github/workflows/build-and-push-db.yml)
- [Makefile Targets](../Makefile)

---

## ✅ Quick Reference

```bash
# Build database image
make build-db

# Start stack (auto-builds if needed)
docker-compose -f compose.docker.yml up -d

# Check if image exists
docker images | grep ninaivalaigal-db

# Pull from GHCR
docker pull ghcr.io/arunosaur/ninaivalaigal-db:latest

# Push to GHCR
docker push ghcr.io/arunosaur/ninaivalaigal-db:latest

# Rebuild from scratch
docker-compose -f compose.docker.yml build --no-cache postgres
```

---

**Last Updated:** October 4, 2025
**Status:** ✅ Production Ready
