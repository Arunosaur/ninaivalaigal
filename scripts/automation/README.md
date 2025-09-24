# 🤖 Ninaivalaigal Automation Suite

This directory contains comprehensive automation for container health monitoring and graph intelligence validation.

## 📋 Overview

| Component | Purpose | Frequency | Platform |
|-----------|---------|-----------|----------|
| **Health Monitor** | Container lifecycle management | Every 60s | macOS LaunchAgent |
| **Graph Validator** | API endpoint testing | Every 10min | macOS LaunchAgent |
| **CI/CD Pipeline** | Automated testing & recovery | Every 10min | GitHub Actions |
| **Container Guard** | Protection from CI interference | Continuous | Background Process |

## 🚀 Quick Start

### Option 1: macOS LaunchAgent (Recommended for Local Dev)

```bash
# 1. Install health monitor
cp com.ninaivalaigal.health-monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist

# 2. Install graph validator
cp com.ninaivalaigal.graph-test.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.graph-test.plist

# 3. Start container guard
nohup ../guard-docker.sh monitor > /tmp/container-guard-monitor.log 2>&1 &

# 4. Check status
launchctl list | grep ninaivalaigal
```

### Option 2: GitHub Actions (CI/CD)

```bash
# 1. Copy workflow to GitHub Actions
cp self-healing.yml ../.github/workflows/

# 2. Commit and push
git add .github/workflows/self-healing.yml
git commit -m "Add automated health monitoring workflow"
git push
```

## 🔧 Configuration

### Environment Setup

Ensure your conda environment is properly configured:

```bash
# Check conda environment
conda env list | grep nina

# If missing, create it
conda create -n nina python=3.11
conda activate nina
pip install requests matplotlib seaborn pandas networkx
```

### Token Configuration

Update tokens in your test files:

```python
# In simple_enhanced_graph_test.py
TOKENS = [
    "GuruR5gh5v3ndr5",  # Primary token
    "backup_token_here"  # Add backup tokens
]
```

## 📊 Monitoring & Logs

### Log Locations

| Service | Log File | Purpose |
|---------|----------|---------|
| Health Monitor | `/tmp/ninaivalaigal-health-fixed.log` | Container health events |
| Container Guard | `/tmp/container-guard.log` | Protection events |
| Graph Tests | `/tmp/graph-test.log` | API validation results |
| LaunchAgent | `/tmp/ninaivalaigal-launchd.log` | System daemon logs |

### Check Status

```bash
# Health monitor status
launchctl list com.ninaivalaigal.health-monitor

# Graph test status
launchctl list com.ninaivalaigal.graph-test

# Container guard status
ps aux | grep guard-docker

# Recent logs
tail -f /tmp/ninaivalaigal-health-fixed.log
tail -f /tmp/graph-test.log
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Redis Ping Error
```
'RedisClient' object has no attribute 'ping'
```

**Fix:**
```bash
# Run the Redis fix script
python ../fix-redis-ping.py
```

#### 2. Authentication 401 Error
```
/graph-intelligence/metrics endpoint fails with 401
```

**Fix:**
- Check token format in test files
- Verify metrics endpoint requires special scope
- Add logging to metrics route

#### 3. Container Guard Not Working
```bash
# Check if guard is running
ps aux | grep guard-docker

# Restart guard
pkill -f guard-docker
nohup ../guard-docker.sh monitor > /tmp/container-guard-monitor.log 2>&1 &
```

#### 4. LaunchAgent Not Starting
```bash
# Check for errors
launchctl list com.ninaivalaigal.health-monitor
cat /tmp/ninaivalaigal-launchd-error.log

# Reload agent
launchctl unload ~/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist
launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist
```

## 🎯 Advanced Features

### Slack Notifications

Add to GitHub Actions workflow:

```yaml
- name: Notify Slack on Failure
  if: failure()
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"🚨 Ninaivalaigal health check failed"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Custom Metrics Dashboard

Create a simple dashboard:

```python
# dashboard.py
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta

def generate_health_dashboard():
    # Read logs and generate charts
    # Implementation in separate file
    pass
```

### Email Alerts

```bash
# Add to health monitor script
if [ "$FAILURES" -gt "3" ]; then
    echo "Multiple failures detected" | mail -s "Ninaivalaigal Alert" admin@example.com
fi
```

## 🔄 Maintenance

### Weekly Tasks

```bash
# Rotate logs
find /tmp -name "*ninaivalaigal*" -mtime +7 -delete

# Update tokens if needed
# Check GitHub Actions artifacts for patterns
```

### Monthly Tasks

```bash
# Review automation effectiveness
grep "CRITICAL\|ERROR" /tmp/ninaivalaigal-health-fixed.log | tail -50

# Update dependencies
conda activate nina
pip list --outdated
```

## 📈 Metrics & KPIs

Track these key metrics:

- **Container Uptime**: % time containers are healthy
- **Recovery Time**: Time from failure detection to recovery
- **False Positives**: Unnecessary restarts
- **API Response Times**: Graph intelligence performance
- **Token Rotation Events**: Authentication health

## 🎛️ Manual Controls

### Emergency Commands

```bash
# Emergency stop all automation
launchctl unload ~/Library/LaunchAgents/com.ninaivalaigal.*
pkill -f guard-docker

# Emergency restart stack
make stack-down && sleep 10 && make stack-up

# Emergency re-enable automation
launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.*
nohup ../guard-docker.sh monitor > /tmp/container-guard-monitor.log 2>&1 &
```

### Testing Commands

```bash
# Test health monitor once
../comprehensive-health-monitor.sh status

# Test graph validation once
conda run -n nina python /Users/swami/Downloads/simple_enhanced_graph_test.py

# Test container guard
../guard-docker.sh status
```

---

## 🎉 Success Indicators

Your automation is working correctly when you see:

- ✅ All LaunchAgents loaded and running
- ✅ Container guard protecting dev containers
- ✅ GitHub Actions passing regularly
- ✅ Logs showing regular health checks
- ✅ Quick recovery from container failures
- ✅ Graph intelligence endpoints responding

This setup provides **enterprise-grade container resiliency** with automated recovery, comprehensive monitoring, and multi-platform automation! 🚀
