#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# organize_root_final.sh - Final root directory organization
# shellcheck disable=SC2010,SC2035  # One-time organization script

set -euo pipefail

echo "🗂️  FINAL ROOT ORGANIZATION"
echo "============================"
echo ""

# Create organized subdirectories
mkdir -p legal
mkdir -p build/{makefiles,docker}
mkdir -p python-config
mkdir -p node-config
mkdir -p db-config

echo "📁 Creating directory structure..."
echo ""

# Move LICENSE to legal/
echo "⚖️  Moving legal files..."
if [ -f LICENSE ]; then
    mv LICENSE legal/
    echo "  ✅ LICENSE → legal/"
fi

# Create a symlink in root for GitHub/common tools to find it
ln -sf legal/LICENSE LICENSE
echo "  🔗 Created symlink: LICENSE → legal/LICENSE"

# Move licensing documentation
if [ -f docs/Ninaivalaigal_Licensing_Map.pdf ]; then
    mv docs/Ninaivalaigal_Licensing_Map.* legal/
    echo "  ✅ Licensing maps → legal/"
fi

echo ""
echo "🐳 Moving container/build files..."
# Move Makefiles to build/makefiles/
if [ -f Makefile ]; then
    mv Makefile build/makefiles/
    mv Makefile.* build/makefiles/ 2>/dev/null
    echo "  ✅ Makefiles → build/makefiles/"
fi

# Create symlink for main Makefile
ln -sf build/makefiles/Makefile Makefile
echo "  🔗 Created symlink: Makefile → build/makefiles/Makefile"

# Move Dockerfile to build/docker/
if [ -f Dockerfile ]; then
    mv Dockerfile build/docker/
    echo "  ✅ Dockerfile → build/docker/"
fi

# Create symlink for Dockerfile
ln -sf build/docker/Dockerfile Dockerfile
echo "  🔗 Created symlink: Dockerfile → build/docker/Dockerfile"

echo ""
echo "🐍 Moving Python config files..."
# Move Python configs to python-config/
mv pyproject.toml python-config/ 2>/dev/null
mv requirements*.txt python-config/ 2>/dev/null
mv pytest.ini python-config/ 2>/dev/null
mv mypy.ini python-config/ 2>/dev/null
echo "  ✅ Python configs → python-config/"

# Create symlinks for commonly accessed Python files
ln -sf python-config/pyproject.toml pyproject.toml
ln -sf python-config/requirements.txt requirements.txt
ln -sf python-config/requirements-dev.txt requirements-dev.txt
echo "  🔗 Created symlinks for pyproject.toml, requirements.txt"

echo ""
echo "📦 Moving Node.js config files..."
# Move Node configs to node-config/
mv package*.json node-config/ 2>/dev/null
echo "  ✅ Node.js configs → node-config/"

# Create symlinks for package.json
ln -sf node-config/package.json package.json
ln -sf node-config/package-lock.json package-lock.json
echo "  🔗 Created symlinks for package.json, package-lock.json"

echo ""
echo "🗄️  Moving database config..."
# Move database config to db-config/
mv alembic.ini db-config/ 2>/dev/null
echo "  ✅ Alembic config → db-config/"

# Create symlink for alembic
ln -sf db-config/alembic.ini alembic.ini
echo "  🔗 Created symlink: alembic.ini → db-config/alembic.ini"

echo ""
echo "✅ ORGANIZATION COMPLETE"
echo "========================"
echo ""
echo "📊 Root directory now contains:"
echo "  - README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md"
echo "  - Symlinks to: LICENSE, Makefile, Dockerfile, pyproject.toml, etc."
echo "  - All actual files organized in subdirectories"
echo ""
echo "Files in root (excluding directories):"
# shellcheck disable=SC2010  # Complex pattern, needs review
ls -p | grep -v / | wc -l
echo ""
ls -lh | grep -v "^d"
