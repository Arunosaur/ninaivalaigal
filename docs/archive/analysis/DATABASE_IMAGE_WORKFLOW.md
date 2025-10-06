# Database Image Workflow - Proper Way

## 🎯 Problem Statement

**Issue:** The database image that worked yesterday now has segmentation faults.
**Root Cause:** Using unstable/unversioned images leads to unpredictable behavior.

**Solution:** Create a **stable, versioned, multi-arch database image** that includes all required extensions.

---

## 📋 Required Extensions

Based on your platform requirements:

### Immediate Enable (Core - Must Have)
- ✅ pg_stat_statements
- ✅ auto_explain
- ✅ pg_repack
- ✅ pg_cron
- ✅ citext
- ✅ pgcrypto
- ✅ pgAudit
- ✅ pgvector

### Future-Ready
- ⏳ pg_partman (Phase 3 - Production scale)
- ⏳ postgres_fdw (Future federation)
- ⏳ TimescaleDB (Analytics cluster)

### Optional Advanced
- 🔬 pg_similarity (RAG/GraphOps)
- 🔬 pg_jsonschema (Development DB)

---

## ✅ Proper Workflow

### Step 1: Build Stable Image Locally
```bash
cd containers/ninaivalaigal-db

# Build for ARM64 (Apple Silicon / ARM servers)
docker build --platform linux/arm64 \
  -t ninaivalaigal-db:1.0.0 \
  -t ninaivalaigal-db:latest \
  .

# Build for AMD64 (Intel/AMD servers)
docker build --platform linux/amd64 \
  -t ninaivalaigal-db:1.0.0-amd64 \
  .
```

### Step 2: Test Locally
```bash
# Test the image
docker run --rm ninaivalaigal-db:1.0.0 postgres --version

# Test extensions
docker run --rm ninaivalaigal-db:1.0.0 \
  bash -c "ls -la /usr/lib/postgresql/15/lib/ | grep -E 'vector|age|cron'"

# Start with compose
docker compose -f compose.colima.yml up -d postgres

# Verify extensions
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "\dx"
```

### Step 3: Push to Registry (One-Time Setup)
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u arunosaur --password-stdin

# Build and push multi-arch image
cd containers/ninaivalaigal-db
./build-and-push.sh 1.0.0

# This creates:
# - ghcr.io/arunosaur/ninaivalaigal-db:1.0.0 (multi-arch)
# - ghcr.io/arunosaur/ninaivalaigal-db:latest (multi-arch)
```

### Step 4: Use in All Environments
```yaml
# compose.colima.yml
services:
  postgres:
    image: ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
    platform: linux/arm64

# compose.docker.yml
services:
  postgres:
    image: ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
    platform: linux/arm64

# compose.apple.yml
# Uses Apple Container CLI with same image concepts
```

---

## 🔄 Version Management

### When to Bump Versions

**Patch (1.0.x):**
- Configuration changes
- Minor script updates
- No extension version changes

**Minor (1.x.0):**
- Add new extensions
- Update extension versions
- PostgreSQL minor updates

**Major (x.0.0):**
- PostgreSQL major version upgrade
- Breaking changes to extensions
- Architecture changes

### Version Workflow
```bash
# 1. Update version in multiple files
VERSION=1.1.0

# 2. Build and tag
docker build --platform linux/arm64 \
  -t ninaivalaigal-db:${VERSION} \
  -t ninaivalaigal-db:latest \
  .

# 3. Test thoroughly
docker compose -f compose.colima.yml up -d
# Run all tests...

# 4. Push to registry
./build-and-push.sh ${VERSION}

# 5. Update all compose files
sed -i '' "s/ninaivalaigal-db:[0-9.]\+/ninaivalaigal-db:${VERSION}/g" compose.*.yml

# 6. Commit and tag
git add .
git commit -m "chore(db): upgrade database image to v${VERSION}"
git tag "db-v${VERSION}"
git push origin main --tags
```

---

## 🚨 Troubleshooting Yesterday's Segmentation Fault

### Why It Happened
1. **No version pinning** - Used `latest` tag which changed
2. **Registry corruption** - GitHub registry image got corrupted/rebuilt
3. **Platform mismatch** - Wrong architecture pulled
4. **Extension conflict** - pgvector version incompatible with PostgreSQL

### How We Fixed It
1. ✅ Created **versioned, controlled Dockerfile**
2. ✅ Built **locally first** to verify
3. ✅ **Pinned all extension versions** (pgvector v0.5.1, AGE v1.5.0-rc0)
4. ✅ Added **platform-specific builds**
5. ✅ Included **health checks**

### Prevention Going Forward
```bash
# ALWAYS use versioned images
image: ninaivalaigal-db:1.0.0  ✅
image: ninaivalaigal-db:latest ❌

# ALWAYS specify platform
platform: linux/arm64           ✅
# (platform auto-detect)        ❌

# ALWAYS test before pushing
docker build && docker run      ✅
./build-and-push.sh            ❌ (without testing)
```

---

## 📦 Multi-Environment Strategy

### Development (Local)
```bash
# Use local build
export NINA_DB_IMAGE=ninaivalaigal-db:local
make colima-dev-up
```

### Staging
```bash
# Use versioned registry image
export NINA_DB_IMAGE=ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
docker compose -f compose.staging.yml up -d
```

### Production
```bash
# Use specific version (never :latest)
export NINA_DB_IMAGE=ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
docker compose -f compose.production.yml up -d
```

---

## 🔐 Security Best Practices

1. **Image Scanning**
```bash
# Scan for vulnerabilities before pushing
docker scout cves ninaivalaigal-db:1.0.0
```

2. **Signed Images**
```bash
# Sign images (production)
docker trust sign ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
```

3. **Private Registry**
```bash
# For sensitive environments
# Push to private AWS ECR / Azure ACR instead of public GHCR
```

---

## 📚 Key Takeaways

1. **Never use `:latest` in production** - Always pin versions
2. **Test locally before pushing** - Catch issues early
3. **Version everything** - Database images, extensions, configs
4. **Document changes** - Keep README.md updated with each version
5. **Multi-arch from day 1** - Support ARM64 and AMD64

---

**Current Status:** ✅ Building stable v1.0.0 image with all extensions
**Next Step:** Test locally, then push to registry for team use
**Timeline:** One-time 30min setup → Stable forever
