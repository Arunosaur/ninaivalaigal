# Ninaivalaigal Development Setup

Simple, clean development environment using Colima + Docker.

## Quick Start

```bash
# Start Colima (if not running)
colima start --arch aarch64 --runtime docker

# Start development stack
make -f Makefile.dev dev-up

# Test auth endpoints
make -f Makefile.dev login-test

# View logs
make -f Makefile.dev dev-logs
```

## What You Get

- **Live Code Reloading**: Edit files, see changes instantly
- **Multi-arch Support**: Build for ARM64 + x86_64
- **Clean Development**: No file sync issues
- **Free Forever**: No Docker Desktop licensing

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:13370 | FastAPI backend |
| UI | http://localhost:8081 | Frontend interface |
| Database | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | Cache & queues |

## Development Commands

```bash
# Stack management
make -f Makefile.dev dev-up        # Start everything
make -f Makefile.dev dev-down      # Stop everything
make -f Makefile.dev dev-status    # Check status

# Testing
make -f Makefile.dev login-test    # Test auth endpoints
make -f Makefile.dev test-endpoints # Test all endpoints

# Database
make -f Makefile.dev db-shell      # Connect to database
make -f Makefile.dev db-reset      # Reset database

# Multi-arch builds
make -f Makefile.dev multiarch-push # Build & push images
```

## File Structure

```
ninaivalaigal/
├── server/              # Python FastAPI code (live mounted)
├── ui/                  # Frontend code (live mounted)
├── docker-compose.dev.yml # Development stack
├── Makefile.dev         # Development commands
└── .github/workflows/   # CI/CD
```

## Troubleshooting

**Auth endpoint hanging?**
```bash
# Check if services are running
make -f Makefile.dev dev-status

# Test backup endpoint
curl -X POST http://localhost:13370/simple-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@ninaivalaigal.com", "password": "test"}'
```

**File changes not reflecting?**
- Colima provides live mounts - changes should appear instantly
- If not, restart: `make -f Makefile.dev restart`

**Multi-arch build issues?**
```bash
# Verify buildx
docker buildx ls

# Recreate builder
docker buildx create --use --name ninaivalaigal-builder
```

## Architecture

- **Local Development**: Colima + Docker Compose
- **CI/CD**: GitHub Actions with x86_64 runners
- **Production**: Multi-arch containers on any platform
- **No Vendor Lock-in**: Standard Docker everywhere

## Migration from Apple Container CLI

The old `container` commands are replaced with standard `docker`:

| Old | New |
|-----|-----|
| `container exec nv-api` | `docker exec ninaivalaigal_dev_api` |
| `container logs nv-api` | `docker logs ninaivalaigal_dev_api` |
| `container stop nv-api` | `make -f Makefile.dev dev-down` |

## Why This Setup?

✅ **Live file sync** - No more injection hacks
✅ **Multi-arch builds** - ARM64 + x86_64 support
✅ **Open source** - No licensing issues
✅ **CI compatible** - GitHub Actions work perfectly
✅ **Simple** - Standard Docker commands

---

**Ready to develop!** 🚀
