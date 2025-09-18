# GitHub Runner Setup for Mac Studio

Quick reference for setting up GitHub Actions self-hosted runner on Mac Studio.

## GitHub Runner Service (on the Studio)

From the GitHub UI: Settings → Actions → Runners → New self-hosted runner → macOS

```bash
# Configure runner with Mac Studio labels
./config.sh --labels "self-hosted,macstudio"

# Install as service
sudo ./svc.sh install

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

## Workflow Snippets

### Cache block for pip

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

### Concurrency + artifact for logs

```yaml
concurrency:
  group: macstudio-stack
  cancel-in-progress: true

# ... in steps:
- name: Collect logs
  if: always()
  run: |
    mkdir -p artifacts
    container logs nv-db > artifacts/db.log || true
    container logs nv-pgbouncer > artifacts/pgbouncer.log || true
    container logs nv-api > artifacts/api.log || true

- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: stack-logs
    path: artifacts/
```

## Environment Setup

### Required Environment Variables

```bash
# In .env file
POSTGRES_USER=nina
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=nina
POSTGRES_HOST=<mac-studio-lan-ip>  # Important for container networking
```

### GitHub Secrets

Set these in your repository settings:

- `POSTGRES_PASSWORD` - Database password for CI runs

## Troubleshooting

### Container Networking

If API container cannot reach localhost services:

```bash
# Set POSTGRES_HOST to your Mac Studio LAN or Tailscale IP in .env
export POSTGRES_HOST=$(ipconfig getifaddr en0)
```

### Runner Service Issues

```bash
# Stop service
sudo ./svc.sh stop

# Uninstall service
sudo ./svc.sh uninstall

# Check logs
tail -f ~/actions-runner/_diag/Runner_*.log
```

### Container Cleanup

```bash
# Force cleanup all ninaivalaigal containers
container stop nv-db nv-pgbouncer nv-api 2>/dev/null || true
container delete nv-db nv-pgbouncer nv-api 2>/dev/null || true

# Clean temporary files
rm -rf /tmp/pgbouncer-* /tmp/ninaivalaigal-api-* 2>/dev/null || true
```

## Performance Monitoring

### Basic Metrics

```bash
# Container resource usage
container stats

# System resources
top -l 1 | grep -E "(CPU|PhysMem)"

# Disk usage
df -h
```

### Benchmark Commands

```bash
# Time full stack startup
time make stack-up

# Test database performance
time psql "postgresql://nina:password@localhost:6432/nina" -c "SELECT version();"

# Test API response time
time curl -f http://localhost:13370/health
```
