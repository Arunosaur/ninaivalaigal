#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# macOS-native resource monitoring using ps command
# Compatible with macOS bash 3.2 (no mapfile required)

set -euo pipefail

OUTPUT_FILE=${1:-"benchmarks/results/resources_$(date +%Y%m%d_%H%M%S).csv"}
INTERVAL=${2:-10}

CONTAINERS=(
    "ninaivalaigal-dev-graphops"
    "ninaivalaigal-dev-db"
    "ninaivalaigal-dev-redis"
)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resource Monitoring (macOS ps)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Output: $OUTPUT_FILE"
echo "   Interval: ${INTERVAL}s"
echo ""

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT_FILE")"

# CSV header
echo "timestamp,container,pid,cpu_percent,mem_mb,vsz_mb,rss_mb" > "$OUTPUT_FILE"

SAMPLE_COUNT=0

# Trap SIGINT for clean exit
trap 'echo ""; echo "✅ Monitoring stopped ($SAMPLE_COUNT samples)"; exit 0' INT

while true; do
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    SAMPLE_COUNT=$((SAMPLE_COUNT + 1))

    echo "Sample $SAMPLE_COUNT @ $timestamp"

    for container in "${CONTAINERS[@]}"; do
        # Get PID from container
        pid=$(container inspect "$container" --format '{{.State.Pid}}' 2>/dev/null || echo "0")

        if [ "$pid" != "0" ] && [ -n "$pid" ]; then
            # Use ps to get resource usage
            # Format: PID %CPU %MEM VSZ RSS
            if ps_output=$(ps -p "$pid" -o pid=,%cpu=,%mem=,vsz=,rss= 2>/dev/null); then
                # Parse output (bash 3.2 compatible)
                read -r p_pid cpu mem vsz rss <<< "$ps_output"

                # Convert KB to MB (VSZ and RSS are in KB on macOS)
                vsz_mb=$(awk "BEGIN {printf \"%.2f\", $vsz/1024}")
                rss_mb=$(awk "BEGIN {printf \"%.2f\", $rss/1024}")

                # Write to CSV
                echo "$timestamp,$container,$p_pid,$cpu,$rss_mb,$vsz_mb,$rss_mb" >> "$OUTPUT_FILE"

                # Display
                printf "  ✓ %-30s | CPU: %6s%% | Mem: %8sMB\n" "$container" "$cpu" "$rss_mb"
            else
                echo "$timestamp,$container,$pid,0.0,0.0,0.0,0.0" >> "$OUTPUT_FILE"
                echo "  ⚠ $container | Process $pid not found"
            fi
        else
            echo "$timestamp,$container,0,0.0,0.0,0.0,0.0" >> "$OUTPUT_FILE"
            echo "  ⚠ $container | Not running"
        fi
    done

    echo ""
    sleep "$INTERVAL"
done
