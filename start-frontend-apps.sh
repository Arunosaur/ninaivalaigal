#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

echo "🚀 Starting Nina Frontend Apps..."

# Kill any existing processes
pkill -f "vite.*8101" 2>/dev/null
pkill -f "vite.*8102" 2>/dev/null
sleep 1

# Start customer app
cd /Users/swami/WorkSpace/ninaivalaigal/apps/customer
nohup npm run dev > /tmp/nina-customer.log 2>&1 &
CUSTOMER_PID=$!
echo "✅ Customer app starting (PID: $CUSTOMER_PID) - http://localhost:8101"

# Start admin console
cd /Users/swami/WorkSpace/ninaivalaigal/apps/admin-console
nohup npm run dev > /tmp/nina-admin.log 2>&1 &
ADMIN_PID=$!
echo "✅ Admin console starting (PID: $ADMIN_PID) - http://localhost:8102"

# Wait for startup
echo "⏳ Waiting for apps to start..."
sleep 5

# Check if they're running
if lsof -i :8101 >/dev/null 2>&1; then
    echo "✅ Customer app is running on http://localhost:8101"
else
    echo "❌ Customer app failed to start. Check /tmp/nina-customer.log"
fi

if lsof -i :8102 >/dev/null 2>&1; then
    echo "✅ Admin console is running on http://localhost:8102"
else
    echo "❌ Admin console failed to start. Check /tmp/nina-admin.log"
fi

echo ""
echo "📝 Logs:"
echo "   Customer: tail -f /tmp/nina-customer.log"
echo "   Admin:    tail -f /tmp/nina-admin.log"
