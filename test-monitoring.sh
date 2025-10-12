#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Test monitoring integration

echo "🧪 Testing Foundation Test Monitoring..."

# Load environment
if [ -f ".env.monitoring" ]; then
    set -a
    source .env.monitoring
    set +a
fi

# Test Slack notification
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "📱 Testing Slack notification..."
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🧪 Foundation Test Monitoring - Manual Test"}' \
        "$SLACK_WEBHOOK_URL"
    echo "✅ Slack test sent"
fi

# Test HealthChecks.io ping
if [ -n "${HEALTHCHECK_UUID:-}" ]; then
    echo "🏥 Testing HealthChecks.io ping..."
    curl -fsS -m 10 --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID"
    echo "✅ HealthChecks.io ping sent"
fi

echo "🎉 Monitoring test complete!"
