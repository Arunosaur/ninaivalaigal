#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
#
# fix_postgres_lock.sh
# Safely clears stale Docker file locks on Postgres bind mount (macOS / Apple Container)
# Author: Medhasys – Ninaivalaigal Stack Recovery Utility
#

set -e

DATA_DIR="./data/postgres_dev"
COMPOSE_FILE="compose.docker.yml"
ENV_FILE=".env.dev"
SERVICE="postgres"

echo "🔍 Checking for file locks on: $DATA_DIR"
LOCKS=$(sudo lsof +D "$DATA_DIR" 2>/dev/null || true)

if [[ -n "$LOCKS" ]]; then
  echo "⚠️  Found active file locks:"
  echo "$LOCKS" | head -20
  echo ""
  echo "Attempting to kill Docker-related locking processes..."
  PIDS=$(echo "$LOCKS" | awk '/com\.docker|Docker|hyperkit|vpnkit/ {print $2}' | sort -u)

  if [[ -n "$PIDS" ]]; then
    echo "$PIDS" | while read -r pid; do
      echo "➡️  Killing PID $pid ..."
      sudo kill -9 "$pid" || true
    done
  else
    echo "No obvious Docker PIDs found — proceeding anyway."
  fi
else
  echo "✅ No file locks found."
fi

echo ""
echo "🌀 Restarting Docker Desktop..."
osascript -e 'quit app "Docker"'
sleep 3
open -a Docker

# Wait for Docker engine to be ready
echo -n "⏳ Waiting for Docker to be ready "
until docker info >/dev/null 2>&1; do
  echo -n "."
  sleep 2
done
echo " ✅"

echo ""
echo "🔁 Verifying that locks are gone..."
if sudo lsof +D "$DATA_DIR" >/dev/null 2>&1; then
  echo "❌ Locks still present! Please reboot manually."
  exit 1
else
  echo "✅ Lock directory is clear."
fi

echo ""
echo "🚀 Restarting Ninaivalaigal stack..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d "$SERVICE" redis

echo ""
echo "⏳ Waiting 20 seconds for Postgres to start..."
sleep 20

echo ""
echo "🧪 Testing database connectivity..."
PGPASSWORD=dev_password_change_in_production \
psql -h localhost -p 5432 -U nina -d ninaivalaigal_dev \
-c "SELECT 'DB ✅ restored' AS status;" || echo "❌ Could not connect yet — check docker logs $SERVICE"

echo ""
echo "🎉 Done! If you see 'DB ✅ restored', your system is healthy again."
