#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
set -e

echo "🔄 Running database migrations..."
echo "  📦 Public schema (main application)..."
alembic -c alembic/public/alembic.ini upgrade head

echo "  📦 GraphOps schema (ag_catalog)..."
alembic -c alembic/graphops/alembic.ini upgrade head

echo "  📦 Memory schema..."
alembic -c alembic/memory/alembic.ini upgrade head

echo "  📦 Intelligence schema..."
alembic -c alembic/intelligence/alembic.ini upgrade head

echo "✅ All migrations complete"

echo "🚀 Starting Core API with gunicorn..."
# SPEC-107: Use gunicorn + uvicorn workers for runtime parity across dev/test/prod
exec gunicorn main:app -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py
