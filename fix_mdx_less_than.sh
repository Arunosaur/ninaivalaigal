#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Fix MDX compilation errors: Escape < before numbers
# Prevents "Unexpected character" JSX errors in Docusaurus

echo "Fixing MDX '<' symbols before numbers in all spec files..."

# Find all .md files in specs/ and replace <NUMBER with &lt;NUMBER
find specs -name "*.md" -type f -exec sed -i '' 's/<\([0-9]\)/\&lt;\1/g' {} \;

echo "✅ Fixed all '<NUMBER' patterns to '&lt;NUMBER'"
echo "Files affected:"
git diff --name-only specs/ | grep "\.md$" | wc -l

echo ""
echo "Review changes with: git diff specs/"
echo "Commit with: git add specs/ && git commit -m 'fix(docs): Escape MDX < symbols before numbers'"
