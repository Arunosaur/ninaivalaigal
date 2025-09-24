#!/usr/bin/env bash
# Setup automated health monitoring via cron and systemd-like service
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
HEALTH_MONITOR="$SCRIPT_DIR/comprehensive-health-monitor.sh"
SERVICE_NAME="ninaivalaigal-health-monitor"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [setup] $*"
}

setup_cron_monitoring() {
    log "Setting up cron-based health monitoring..."

    # Create cron job that runs every 5 minutes
    local cron_entry="*/5 * * * * cd $ROOT_DIR && $HEALTH_MONITOR monitor >> /tmp/ninaivalaigal-cron.log 2>&1"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "ninaivalaigal-health-monitor"; then
        log "Cron job already exists, updating..."
        # Remove old entry and add new one
        (crontab -l 2>/dev/null | grep -v "ninaivalaigal-health-monitor"; echo "$cron_entry") | crontab -
    else
        log "Adding new cron job..."
        (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    fi

    log "✅ Cron monitoring setup complete"
    log "📋 Cron job: $cron_entry"
}

setup_launchd_service() {
    log "Setting up macOS LaunchAgent for persistent monitoring..."

    local plist_path="$HOME/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist"

    cat > "$plist_path" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ninaivalaigal.health-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$HEALTH_MONITOR</string>
        <string>monitor</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$ROOT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ninaivalaigal-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ninaivalaigal-launchd-error.log</string>
    <key>ThrottleInterval</key>
    <integer>60</integer>
</dict>
</plist>
EOF

    # Load the service
    launchctl unload "$plist_path" 2>/dev/null || true
    launchctl load "$plist_path"

    log "✅ LaunchAgent setup complete"
    log "📋 Service file: $plist_path"
}

setup_github_actions_monitoring() {
    log "Setting up GitHub Actions workflow for monitoring..."

    local workflow_dir="$ROOT_DIR/.github/workflows"
    mkdir -p "$workflow_dir"

    cat > "$workflow_dir/health-monitoring.yml" << 'EOF'
name: Health Monitoring & Auto-Recovery

on:
  schedule:
    # Run every 10 minutes
    - cron: '*/10 * * * *'
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        default: 'status'
        type: choice
        options:
        - status
        - restart
        - logs

jobs:
  health-check:
    runs-on: self-hosted
    if: github.event_name == 'schedule' || github.event.inputs.action == 'status'

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run health check
      run: |
        cd ${{ github.workspace }}
        ./scripts/comprehensive-health-monitor.sh status

    - name: Check container status
      run: |
        make stack-status || echo "Stack status check failed"

    - name: Auto-recovery if needed
      run: |
        if ! make stack-status | grep -q "✅.*All systems healthy"; then
          echo "🚨 Issues detected, attempting auto-recovery..."
          ./scripts/comprehensive-health-monitor.sh test
        fi

  manual-restart:
    runs-on: self-hosted
    if: github.event.inputs.action == 'restart'

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Restart stack
      run: |
        make stack-down || true
        sleep 10
        make stack-up

    - name: Verify restart
      run: |
        sleep 30
        make stack-status

  show-logs:
    runs-on: self-hosted
    if: github.event.inputs.action == 'logs'

    steps:
    - name: Show health monitor logs
      run: |
        echo "=== Recent Health Monitor Logs ==="
        tail -50 /tmp/ninaivalaigal-health-fixed.log || echo "No logs found"
        echo ""
        echo "=== Container Status ==="
        container list || echo "Container CLI not available"
EOF

    log "✅ GitHub Actions workflow created"
    log "📋 Workflow file: $workflow_dir/health-monitoring.yml"
}

show_status() {
    log "📊 Current monitoring status:"

    echo ""
    echo "🔍 Active processes:"
    ps aux | grep -E "(health-monitor|container.*monitor)" | grep -v grep || echo "  No health monitors running"

    echo ""
    echo "📋 Cron jobs:"
    crontab -l 2>/dev/null | grep ninaivalaigal || echo "  No cron jobs found"

    echo ""
    echo "🍎 LaunchAgents:"
    launchctl list | grep ninaivalaigal || echo "  No LaunchAgents found"

    echo ""
    echo "📁 Log files:"
    ls -la /tmp/ninaivalaigal-health* 2>/dev/null || echo "  No log files found"
}

case "${1:-setup}" in
    "setup")
        log "🚀 Setting up comprehensive health monitoring..."
        setup_launchd_service
        setup_github_actions_monitoring
        log "✅ Setup complete!"
        show_status
        ;;
    "cron")
        setup_cron_monitoring
        ;;
    "launchd")
        setup_launchd_service
        ;;
    "github")
        setup_github_actions_monitoring
        ;;
    "status")
        show_status
        ;;
    "stop")
        log "🛑 Stopping all health monitoring..."
        # Stop LaunchAgent
        launchctl unload "$HOME/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist" 2>/dev/null || true
        # Remove cron job
        crontab -l 2>/dev/null | grep -v "ninaivalaigal-health-monitor" | crontab - || true
        # Kill any running processes
        pkill -f "comprehensive-health-monitor" || true
        log "✅ All monitoring stopped"
        ;;
    *)
        echo "Usage: $0 [setup|cron|launchd|github|status|stop]"
        echo "  setup:   Setup LaunchAgent + GitHub Actions (default)"
        echo "  cron:    Setup cron-based monitoring only"
        echo "  launchd: Setup macOS LaunchAgent only"
        echo "  github:  Setup GitHub Actions workflow only"
        echo "  status:  Show current monitoring status"
        echo "  stop:    Stop all monitoring"
        exit 1
        ;;
esac
