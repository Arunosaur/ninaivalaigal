#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Check for unapproved files in project root

untracked=$(git ls-files --others --exclude-standard | grep -E "^[^/]+$" | grep -vE "^(README\.md|CHANGELOG\.md|CONTRIBUTING\.md|SECURITY\.md|LICENSE|Makefile|Makefile\.(compose|dev)|Dockerfile|pyproject\.toml|requirements(-dev)?\.txt|package(-lock)?\.json|alembic\.ini|\.pre-commit-config.*\.yaml|\.gitignore)$")

if [ -n "$untracked" ]; then
  echo "❌ Unapproved files detected in project root:"
  echo "$untracked"
  echo ""
  echo "Only these files are allowed in root:"
  echo "  - Documentation: README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, LICENSE"
  echo "  - Build: Makefile*, Dockerfile"
  echo "  - Config: pyproject.toml, requirements*.txt, package*.json, alembic.ini"
  echo ""
  echo "Please move other files to appropriate subdirectories (src/, scripts/, docs/, etc.)"
  exit 1
fi

echo "✅ Root directory is clean"
exit 0
