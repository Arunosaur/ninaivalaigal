#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail
NAME="${1:-nv-db}"
echo "== container =="
container list | grep "$NAME" || echo "No container named ${NAME}"
echo "== readiness =="
container exec "$NAME" pg_isready -h 127.0.0.1 -p 5432 -U "${POSTGRES_USER:-nina}" -d "${POSTGRES_DB:-nina}" || true
echo "== last logs =="
container logs "$NAME" | tail -20 || true
