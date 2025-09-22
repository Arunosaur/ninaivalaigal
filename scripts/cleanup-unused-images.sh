#!/usr/bin/env bash
# Clean up unused container images to reduce confusion
# This script removes images that are not used by the current ninaivalaigal stack

set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; NC=$'\033[0m'

ok(){ echo "${GRN}✅${NC} $*"; }
warn(){ echo "${YLW}⚠️${NC} $*"; }
error(){ echo "${RED}❌${NC} $*"; }

echo "🧹 Cleaning up unused container images"
echo ""

# Images currently used by ninaivalaigal stack
USED_IMAGES=(
    "pgvector/pgvector:pg15"              # nv-db
    "nina-pgbouncer:arm64"                # nv-pgbouncer
    "nina-api:arm64"                      # nv-api
    "redis:7-alpine"                      # nv-redis
    "ninaivalaigal-graph-db:arm64"        # graph-db (separate system)
)

# OUR BUILT IMAGES that are safe to remove (not used by current stack)
UNUSED_IMAGES=(
    "ninaivalaigal-api:latest"            # Old/different API image we built
    "test-age-build:latest"               # Test image we built
)

# Base images that might be needed for builds (keep these)
BASE_IMAGES=(
    "python:3.11-slim"                    # Used in Dockerfile.api
    "alpine:latest"                       # Commonly used base
    "alpine:3.20"                         # Specific alpine version
)

echo "📋 Current images in use by ninaivalaigal:"
for img in "${USED_IMAGES[@]}"; do
    if container images list | grep -q "$img"; then
        ok "$img (KEEP - actively used)"
    else
        warn "$img (MISSING - may need to build)"
    fi
done

echo ""
echo "📋 Base images (keeping for builds):"
for img in "${BASE_IMAGES[@]}"; do
    if container images list | grep -q "$img"; then
        ok "$img (KEEP - build dependency)"
    fi
done

echo ""
echo "🗑️  OUR BUILT images that can be removed:"
IMAGES_TO_REMOVE=()
for img in "${UNUSED_IMAGES[@]}"; do
    if container images list | grep -q "$img"; then
        # Get image details including creation date
        echo ""
        echo "📋 Image: $img"
        container images inspect "$img" --format '  Created: {{.Created}}' 2>/dev/null || echo "  Created: Unknown"
        container images inspect "$img" --format '  Size: {{.Size}}' 2>/dev/null || echo "  Size: Unknown"
        IMAGES_TO_REMOVE+=("$img")
    fi
done

if [[ ${#IMAGES_TO_REMOVE[@]} -eq 0 ]]; then
    ok "No unused images found to remove."
    REMOVED_COUNT=0
else
    echo ""
    echo "⚠️  The above ${#IMAGES_TO_REMOVE[@]} image(s) will be removed."
    read -p "Do you want to proceed with removal? (y/N): " -r
    echo ""

    REMOVED_COUNT=0
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for img in "${IMAGES_TO_REMOVE[@]}"; do
            echo "  Removing: $img"
            if container images rm "$img" 2>/dev/null; then
                ok "Removed $img"
                ((REMOVED_COUNT++))
            else
                warn "Failed to remove $img (may be in use)"
            fi
        done
    else
        warn "Cleanup cancelled by user"
    fi
fi

# Check for dangling images (images with <none> tag)
echo ""
echo "🧹 Checking for dangling images..."
DANGLING_IMAGES=()
while IFS= read -r image_line; do
    if [[ -n "$image_line" ]]; then
        image_id=$(echo "$image_line" | awk '{print $1":"$2}')
        echo ""
        echo "📋 Dangling Image: $image_id"
        echo "$image_line" | awk '{print "  Size: " $3}'
        DANGLING_IMAGES+=("$image_id")
    fi
done < <(container images list | grep '<none>' || true)

DANGLING_COUNT=0
if [[ ${#DANGLING_IMAGES[@]} -eq 0 ]]; then
    ok "No dangling images found."
else
    echo ""
    echo "⚠️  Found ${#DANGLING_IMAGES[@]} dangling image(s) that can be removed."
    read -p "Do you want to remove dangling images? (y/N): " -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for image_id in "${DANGLING_IMAGES[@]}"; do
            echo "  Removing dangling image: $image_id"
            if container images rm "$image_id" 2>/dev/null; then
                ok "Removed dangling image"
                ((DANGLING_COUNT++))
            else
                warn "Failed to remove dangling image $image_id"
            fi
        done
    else
        warn "Dangling image cleanup cancelled by user"
    fi
fi

echo ""
echo "📊 Cleanup Summary:"
echo "  Our unused images removed: $REMOVED_COUNT"
echo "  Dangling images removed: $DANGLING_COUNT"
echo ""

if [[ $((REMOVED_COUNT + DANGLING_COUNT)) -gt 0 ]]; then
    ok "Cleanup completed! Container image list is now cleaner."
else
    ok "No unused images found to remove."
fi

echo ""
echo "📋 Remaining images:"
container images list

echo ""
echo "💡 To rebuild core images if needed:"
echo "  make build-api              # Rebuild API image"
echo "  make build-pgbouncer        # Rebuild PgBouncer image"
echo "  make build-graph-db-arm64   # Rebuild Graph DB image"
