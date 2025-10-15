#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

# GraphOps Rust Service - One-time setup script

set -e

echo "🚀 Setting up GraphOps Rust Service..."

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Skipping creation."
    echo "   If you want to recreate it, delete .env and run this script again."
else
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created!"
fi

# Make env.sh executable
chmod +x env.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Verify credentials in .env (should be ready to use)"
echo "  2. Run tests:       cargo test -- --nocapture"
echo "  3. Run benchmarks:  cargo bench"
echo ""
echo "📖 See README.md for more details"
