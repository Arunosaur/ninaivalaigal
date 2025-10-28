#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
set -e

echo "🔄 Running database migrations..."
alembic upgrade head

echo "🚀 Starting Core API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
