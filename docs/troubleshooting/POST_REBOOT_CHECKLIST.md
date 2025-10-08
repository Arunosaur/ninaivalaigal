# Post-Reboot Validation Checklist

## After Mac Reboot - 3-Step Verification

### ✅ Step 1: Verify Docker Daemon (30 seconds)

```bash
# Open Terminal in a clean directory (~/Desktop or ~/Dev)
cd ~/Desktop

# Test Docker daemon
docker version
docker info | head -20
```

**Expected Output:**
```
Client: Docker Engine - Community
 Version:           24.x.x
...
Server: Docker Engine - Community
 Version:           24.x.x
...
```

**If you see both Client AND Server sections → ✅ Docker is healthy**

---

### ✅ Step 2: Quick Filesystem Test (5 seconds)

```bash
# Test filesystem responsiveness
echo "test" > /tmp/testfile && cat /tmp/testfile && rm /tmp/testfile
chmod +x /tmp/testfile2 2>/dev/null || true
```

**If commands return instantly → ✅ Filesystem is unlocked**

---

### ✅ Step 3: Run API Integration Script (3-5 minutes)

```bash
# Navigate to repo (use new location if you moved it)
cd ~/WorkSpace/ninaivalaigal
# OR if you moved it during recovery:
# cd ~/Dev/ninaivalaigal

# Make script executable
chmod +x scripts/nv-api-diagnose-repair-v3.1-autoheal-fscheck.sh

# Run the full integration
./scripts/nv-api-diagnose-repair-v3.1-autoheal-fscheck.sh
```

**Script will automatically:**
1. Check filesystem responsiveness
2. Verify Docker daemon
3. Build API image (2-3 min)
4. Verify sys.path fix in image
5. Start API container
6. Check PgBouncer/Redis connectivity
7. Probe API health endpoint

---

## Expected Final Output

```
🎉 Full API integration complete!
   • Build:      Docker ✅
   • Runtime:    Docker ✅
   • Health:     http://localhost:13390/health ✅
   • API Docs:   http://localhost:13390/docs ✅
   • PgBouncer:  localhost:6452 ✅
   • Redis:      localhost:6399 ✅

💡 Next: Disable 'Use Virtualization.framework' in Docker settings
   to prevent future filesystem deadlocks.
```

---

## If Something Fails

### Filesystem Still Frozen
```bash
# Check for remaining locks
sudo lsof +D ~/WorkSpace/ninaivalaigal | grep -E 'Docker|container|fuse'

# Force kill any remaining processes
sudo kill -9 <pid>

# Consider moving repo to clean location
mv ~/WorkSpace/ninaivalaigal ~/Dev/ninaivalaigal
```

### Docker Daemon Still Unresponsive
```bash
# Complete Docker reset
sudo pkill -9 -f docker
sudo rm -f /var/run/docker.sock
sudo launchctl remove com.docker.vmnetd 2>/dev/null || true

# Reinstall Docker Desktop
open https://docs.docker.com/desktop/release-notes/mac/

# After fresh install, verify both Client + Server appear
docker version
```

### API Build Fails
```bash
# Check build context size (should be <100 MB)
du -sh .
du -sh containers/api/

# If >500 MB, create .dockerignore:
cat > .dockerignore <<'EOF'
.git
__pycache__
*.pyc
.env
venv
node_modules/
.data/
backups/
tests/
EOF

# Retry build
docker build --no-cache -t nina-api:arm64 -f containers/api/Dockerfile .
```

---

## Permanent Prevention

After successful validation, prevent future deadlocks:

### Disable Apple Virtualization in Docker

**Docker Desktop → Settings → Advanced:**
- ☑️ Disable "Use Virtualization.framework"
- ☑️ Enable "Use Rosetta for x86/arm64" (optional)
- Click "Apply & Restart"

This routes Docker through its own hypervisor, avoiding APFS deadlocks.

---

## Quick Sanity Test Commands

```bash
# Test filesystem I/O (should return instantly)
time ls -la ~/WorkSpace/ninaivalaigal/scripts

# Test Docker socket (should show listening socket)
sudo lsof -i -P | grep docker | grep LISTEN

# Test API endpoints
curl -v http://localhost:13390/health
curl -s http://localhost:13390/docs | grep "<title>"

# Test stack connectivity
nc -zv localhost 6452  # PgBouncer
nc -zv localhost 6399  # Redis
nc -zv localhost 13390 # API
```

---

## Success Criteria

All of the following should be true:

- [ ] ✅ `docker version` shows both Client and Server
- [ ] ✅ `docker info` returns within 2 seconds
- [ ] ✅ Filesystem operations (`touch`, `ls`, `chmod`) are instant
- [ ] ✅ API image builds in 2-3 minutes (not 15+ or hang)
- [ ] ✅ API container starts and logs appear
- [ ] ✅ `/health` endpoint returns `200 OK`
- [ ] ✅ PgBouncer and Redis ports are reachable
- [ ] ✅ No processes holding locks in project directory

---

## Monitoring Commands (Keep in Terminal Tab)

```bash
# Watch Docker containers
watch -n 2 'docker ps | grep ninaivalaigal'

# Watch API logs live
docker logs -f ninaivalaigal-dev-api

# Monitor system for locks
watch -n 5 'sudo lsof +D ~/WorkSpace/ninaivalaigal 2>/dev/null | wc -l'
```

---

**Once all checks pass, your environment is stable and you can continue development!**
