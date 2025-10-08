#!/usr/bin/env bash
echo "🔍 Verifying hook coverage by directory..."
for dir in server tests scripts utils; do
  echo "📁 Checking $dir..."
  flake8 $dir --count --select=E9,F63,F7,F82 --show-source --statistics
  echo ""
done
