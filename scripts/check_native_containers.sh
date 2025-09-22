#!/bin/bash

echo "=== macOS Native Container Exploration ==="
echo "macOS Version:"
sw_vers

echo -e "\n=== Checking for native container tools ==="
which podman 2>/dev/null && echo "✅ Podman found" || echo "❌ Podman not found"
which lima 2>/dev/null && echo "✅ Lima found" || echo "❌ Lima not found"
which colima 2>/dev/null && echo "✅ Colima found" || echo "❌ Colima not found"

echo -e "\n=== Checking system container support ==="
ls /usr/bin/*container* 2>/dev/null || echo "No native container binaries in /usr/bin"
ls /System/Library/Frameworks/*Container* 2>/dev/null || echo "No Container frameworks found"

echo -e "\n=== Checking for OCI runtime ==="
which runc 2>/dev/null && echo "✅ runc found" || echo "❌ runc not found"
which crun 2>/dev/null && echo "✅ crun found" || echo "❌ crun not found"

echo -e "\n=== Docker Desktop status ==="
docker --version 2>/dev/null && echo "✅ Docker available" || echo "❌ Docker not available"
docker info 2>/dev/null | head -5 || echo "Docker not running"

echo -e "\n=== Homebrew container options ==="
brew list | grep -E "(podman|lima|colima|docker)" || echo "No container tools via Homebrew"

echo -e "\n=== System container processes ==="
ps aux | grep -E "(container|docker|podman)" | grep -v grep || echo "No container processes running"
