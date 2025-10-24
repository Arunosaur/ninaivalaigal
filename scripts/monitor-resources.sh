#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
#
# Periodically capture docker resource metrics for the core GraphOps stack.

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker CLI is required on PATH" >&2
  exit 1
fi

OUTPUT_FILE=${1:-"results/resources_$(date -u +%Y%m%d_%H%M%SZ).csv"}
INTERVAL_SECONDS=${INTERVAL_SECONDS:-10}
CONTAINERS_ENV=${CONTAINERS:-"ninaivalaigal-dev-graphops ninaivalaigal-dev-db ninaivalaigal-dev-redis"}
IFS=' ' read -r -a CONTAINERS <<< "$CONTAINERS_ENV"

mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "timestamp,container,cpu_percent,mem_usage_mb,mem_limit_mb,net_in_mb,net_out_mb" > "$OUTPUT_FILE"

echo "📊 Streaming docker stats every ${INTERVAL_SECONDS}s -> $OUTPUT_FILE"

convert_to_mb() {
  local value=$1
  local number unit
  number=${value%[A-Za-z]*}
  unit=${value#${number}}
  case "$unit" in
    GiB|G|GB) awk -v n="$number" 'BEGIN { printf "%.2f", n * 1024 }' ;;
    MiB|M|MB) awk -v n="$number" 'BEGIN { printf "%.2f", n }' ;;
    KiB|K|KB) awk -v n="$number" 'BEGIN { printf "%.4f", n / 1024 }' ;;
    B) awk -v n="$number" 'BEGIN { printf "%.6f", n / (1024*1024) }' ;;
    *) echo "$number" ;;
  esac
}

trap 'echo "\n⏹️  Stopping resource monitor"' INT TERM

while true; do
  # Capture stats for all containers in one invocation to avoid skew
  mapfile -t STATS < <(docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}}" "${CONTAINERS[@]}")

  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  for line in "${STATS[@]}"; do
    IFS=',' read -r name cpu mem net <<< "$line"
    # mem format: "<usage> / <limit>"
    usage_part=${mem%/*}
    limit_part=${mem#*/ }
    usage_mb=$(convert_to_mb "${usage_part//[[:space:]]/}")
    limit_mb=$(convert_to_mb "${limit_part//[[:space:]]/}")

    # net format: "<in> / <out>"
    net_in_part=${net%/*}
    net_out_part=${net#*/ }
    net_in_mb=$(convert_to_mb "${net_in_part//[[:space:]]/}")
    net_out_mb=$(convert_to_mb "${net_out_part//[[:space:]]/}")

    echo "$timestamp,$name,$cpu,$usage_mb,$limit_mb,$net_in_mb,$net_out_mb" >> "$OUTPUT_FILE"
  done

  sleep "$INTERVAL_SECONDS"
done
