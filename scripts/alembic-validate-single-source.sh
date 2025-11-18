#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Validate single source of truth for Alembic migrations

set -euo pipefail

echo "🔍 Validating single source of truth for Alembic migrations..."
echo

# Check for duplicate table names across schemas
echo "Checking for duplicate table names across schemas..."

# Extract table names from all migration files
temp_dir=$(mktemp -d)
find alembic -name "*.py" -path "*/versions/*" -exec grep -l "create_table" {} \; | while read file; do
    schema=$(echo "$file" | sed 's|.*/\([^/]*\)/versions/.*|\1|')
    grep "create_table" "$file" -A 1 | grep '"' | sed 's/.*"\([^"]*\)".*/\1/' | while read table; do
        echo "$schema:$table" >> "$temp_dir/tables.txt"
    done
done

# Check for duplicates
if [ -f "$temp_dir/tables.txt" ]; then
    duplicates=$(cut -d: -f2 "$temp_dir/tables.txt" | sort | uniq -d)
    if [ -n "$duplicates" ]; then
        echo "❌ DUPLICATE TABLE NAMES FOUND:"
        for table in $duplicates; do
            echo "   $table:"
            grep ":$table$" "$temp_dir/tables.txt" | sed 's/^/     - /'
        done
        echo
        echo "🚨 This violates single source of truth principle!"
        rm -rf "$temp_dir"
        exit 1
    else
        echo "✅ No duplicate table names found"
    fi
else
    echo "⚠️  No migration files found"
fi

# Check schema consistency
echo
echo "Checking schema consistency..."

# Check if public schema migrations target core_api
public_files=$(find alembic/public/versions -name "*.py" 2>/dev/null || true)
if [ -n "$public_files" ]; then
    schema_usage=$(grep -c "schema=" alembic/public/versions/*.py 2>/dev/null || echo "0")
    if [ "$schema_usage" -gt 0 ]; then
        echo "✅ Public schema migrations use explicit schema targeting"
    else
        echo "⚠️  Public schema migrations should use explicit schema targeting"
    fi
fi

# Clean up
rm -rf "$temp_dir"

echo
echo "✅ Single source of truth validation complete"
