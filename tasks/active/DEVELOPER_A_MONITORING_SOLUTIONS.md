# Developer A: Resource Monitoring Solutions for Apple Container CLI

**Date:** October 21, 2025, 2:18 PM
**Task:** US #86 - GraphOps Benchmarking
**Issue:** Apple Container CLI monitoring constraints

---

## 🎯 Excellent Progress!

✅ Graph seeded via GraphOps gRPC
✅ Readiness check confirmed (perf_user nodes accessible)
⚠️ Monitoring script needs adaptation for Apple Container CLI

**You've correctly identified the constraints!**

---

## 🚧 The Issues

### **1. macOS bash v3.2 Limitations**
- No `mapfile` builtin (added in bash 4.0+)
- Solution: Use `while read` loop instead

### **2. Apple Container CLI - No `stats` Command**
- Docker has: `docker stats`
- Apple CLI has: `container list`, `container inspect` (no real-time stats)
- Solution: Alternative monitoring approach

---

## ✅ **SOLUTION 1: Simplified Monitoring (RECOMMENDED)**

Use `container inspect` + process monitoring for lightweight resource tracking.

### **Create: `scripts/monitor-resources-apple.sh`**

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Resource monitoring for Apple Container CLI
# Adapted for containers that don't have stats command

set -euo pipefail

OUTPUT_FILE=${1:-"benchmarks/results/resources_$(date +%Y%m%d_%H%M%S).csv"}
INTERVAL=${2:-10}  # seconds between samples

# Container names to monitor
CONTAINERS=(
    "ninaivalaigal-dev-graphops"
    "ninaivalaigal-dev-db"
    "ninaivalaigal-dev-redis"
)

echo "📊 Starting resource monitoring (Apple Container CLI mode)"
echo "   Output: $OUTPUT_FILE"
echo "   Interval: ${INTERVAL}s"
echo ""

# Create CSV header
echo "timestamp,container,status,pid" > "$OUTPUT_FILE"

# Monitor loop
while true; do
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    for container in "${CONTAINERS[@]}"; do
        # Get container status and PID
        if container inspect "$container" >/dev/null 2>&1; then
            status=$(container inspect "$container" --format '{{.State.Status}}' 2>/dev/null || echo "unknown")
            pid=$(container inspect "$container" --format '{{.State.Pid}}' 2>/dev/null || echo "0")

            # Write to CSV
            echo "$timestamp,$container,$status,$pid" >> "$OUTPUT_FILE"
        else
            echo "$timestamp,$container,not_found,0" >> "$OUTPUT_FILE"
        fi
    done

    sleep "$INTERVAL"
done
```

**Usage:**
```bash
# Start monitoring in background
./scripts/monitor-resources-apple.sh benchmarks/results/resources.csv 10 &
MONITOR_PID=$!

# Run your benchmark
python3 scripts/mcp_mix_run.py ...

# Stop monitoring
kill $MONITOR_PID
```

**Output:** Basic container status tracking (running/stopped)

---

## ✅ **SOLUTION 2: Host-Level Process Monitoring (ACCURATE)**

Use macOS `ps` to track actual CPU/memory of container processes.

### **Create: `scripts/monitor-resources-macos.sh`**

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# macOS-native resource monitoring using ps command

set -euo pipefail

OUTPUT_FILE=${1:-"benchmarks/results/resources_$(date +%Y%m%d_%H%M%S).csv"}
INTERVAL=${2:-10}

CONTAINERS=(
    "ninaivalaigal-dev-graphops"
    "ninaivalaigal-dev-db"
    "ninaivalaigal-dev-redis"
)

echo "📊 Starting macOS process monitoring"
echo "   Output: $OUTPUT_FILE"
echo "   Interval: ${INTERVAL}s"
echo ""

# CSV header
echo "timestamp,container,pid,cpu_percent,mem_mb,vsz_mb,rss_mb" > "$OUTPUT_FILE"

while true; do
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    for container in "${CONTAINERS[@]}"; do
        # Get PID from container
        pid=$(container inspect "$container" --format '{{.State.Pid}}' 2>/dev/null || echo "0")

        if [ "$pid" != "0" ] && [ "$pid" != "" ]; then
            # Use ps to get resource usage
            # Format: PID %CPU %MEM VSZ RSS
            ps_output=$(ps -p "$pid" -o pid=,%cpu=,%mem=,vsz=,rss= 2>/dev/null || echo "$pid 0.0 0.0 0 0")

            # Parse output
            read -r p_pid cpu mem vsz rss <<< "$ps_output"

            # Convert to MB (VSZ and RSS are in KB on macOS)
            vsz_mb=$(awk "BEGIN {printf \"%.2f\", $vsz/1024}")
            rss_mb=$(awk "BEGIN {printf \"%.2f\", $rss/1024}")

            echo "$timestamp,$container,$p_pid,$cpu,$rss_mb,$vsz_mb,$rss_mb" >> "$OUTPUT_FILE"
        else
            echo "$timestamp,$container,0,0.0,0.0,0.0,0.0" >> "$OUTPUT_FILE"
        fi
    done

    sleep "$INTERVAL"
done
```

**Usage:** Same as above

**Output:** Real CPU% and memory usage from macOS `ps`

---

## ✅ **SOLUTION 3: Python-Based Monitoring (MOST ACCURATE)**

Use `psutil` library for detailed process metrics.

### **Create: `scripts/monitor-resources-psutil.py`**

```python
#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Resource monitoring using psutil for accurate metrics
"""

import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("❌ psutil not installed")
    print("   Install with: pip3 install psutil")
    sys.exit(1)


def get_container_pid(container_name: str) -> int:
    """Get PID of a container."""
    try:
        result = subprocess.run(
            ["container", "inspect", container_name, "--format", "{{.State.Pid}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0


def get_process_metrics(pid: int) -> dict:
    """Get detailed metrics for a process."""
    try:
        process = psutil.Process(pid)

        # Get CPU and memory info
        cpu_percent = process.cpu_percent(interval=0.1)
        mem_info = process.memory_info()

        # Get children processes (container often spawns children)
        children = process.children(recursive=True)
        total_cpu = cpu_percent + sum(c.cpu_percent(interval=0) for c in children)
        total_mem = mem_info.rss + sum(c.memory_info().rss for c in children)

        return {
            "cpu_percent": round(total_cpu, 2),
            "memory_mb": round(total_mem / (1024 * 1024), 2),
            "num_threads": process.num_threads(),
            "num_children": len(children)
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "num_threads": 0,
            "num_children": 0
        }


def monitor_containers(output_file: str, interval: int = 10):
    """Monitor container resource usage."""
    containers = [
        "ninaivalaigal-dev-graphops",
        "ninaivalaigal-dev-db",
        "ninaivalaigal-dev-redis"
    ]

    print(f"📊 Starting psutil-based monitoring")
    print(f"   Output: {output_file}")
    print(f"   Interval: {interval}s")
    print("")

    # Create output file with header
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "container", "pid", "cpu_percent",
            "memory_mb", "num_threads", "num_children"
        ])

    try:
        while True:
            timestamp = datetime.utcnow().isoformat() + "Z"

            for container in containers:
                pid = get_container_pid(container)

                if pid > 0:
                    metrics = get_process_metrics(pid)

                    with open(output_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            timestamp,
                            container,
                            pid,
                            metrics["cpu_percent"],
                            metrics["memory_mb"],
                            metrics["num_threads"],
                            metrics["num_children"]
                        ])

                    print(f"✓ {container}: CPU {metrics['cpu_percent']}%, "
                          f"Mem {metrics['memory_mb']:.2f}MB")
                else:
                    with open(output_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, container, 0, 0.0, 0.0, 0, 0])

            print("")  # Blank line between samples
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "benchmarks/results/resources.csv"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    monitor_containers(output, interval)
```

**Usage:**
```bash
# Requires psutil
pip3 install psutil

# Run monitoring
python3 scripts/monitor-resources-psutil.py benchmarks/results/resources.csv 10 &
MONITOR_PID=$!

# Your benchmark
python3 scripts/mcp_mix_run.py ...

# Stop
kill $MONITOR_PID
```

**Output:** Most accurate CPU/memory metrics including child processes

---

## 📋 **RECOMMENDED APPROACH**

### **Option A: Skip Detailed Monitoring (FASTEST)**

If you just want to validate performance without resource metrics:

```bash
# No monitoring - focus on benchmark results
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results \
  --no-snapshots  # Skip resource sampling
```

**Pros:**
- Fastest path to results
- RPS, latency, success rate still captured
- Can add monitoring later

**Cons:**
- No CPU/memory data for cost model

---

### **Option B: Python psutil Monitoring (RECOMMENDED)**

Best accuracy for resource tracking:

```bash
# Install psutil
pip3 install psutil

# Start monitoring
python3 scripts/monitor-resources-psutil.py benchmarks/results/resources.csv 10 &
MONITOR_PID=$!

# Run baseline
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results

# Stop monitoring
kill $MONITOR_PID

# Review
cat benchmarks/results/resources.csv
```

**Pros:**
- Accurate CPU/memory tracking
- Works with Apple Container CLI
- Child process aggregation
- CSV output for analysis

**Cons:**
- Requires psutil dependency

---

### **Option C: Simplified Bash Monitoring**

If you want to avoid Python dependencies:

```bash
# Use macOS native monitoring
./scripts/monitor-resources-macos.sh benchmarks/results/resources.csv 10 &
MONITOR_PID=$!

# Run benchmark
python3 scripts/mcp_mix_run.py ...

# Stop
kill $MONITOR_PID
```

**Pros:**
- No dependencies
- Works with macOS bash 3.2
- Lightweight

**Cons:**
- Less accurate than psutil
- Doesn't track child processes

---

## 🎯 **MY RECOMMENDATION**

**Use Option B (Python psutil)** because:

1. ✅ Most accurate metrics
2. ✅ Tracks child processes (important for containers)
3. ✅ Clean CSV output
4. ✅ Easy to analyze later
5. ✅ Works perfectly with Apple Container CLI

**Quick Start:**
```bash
# 1. Install psutil (one-time)
pip3 install psutil

# 2. Create the monitoring script (I'll do this if you want)

# 3. Run your baseline test
python3 scripts/monitor-resources-psutil.py benchmarks/results/baseline_resources.csv 10 &
MONITOR_PID=$!

python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results

kill $MONITOR_PID

# 4. Review results
cat benchmarks/results/baseline_resources.csv
cd benchmarks/results/graphops_mix_*
cat mix_summary.json | jq '.'
```

---

## ✅ **NEXT STEPS**

**Choose your path:**

### **Path 1: Skip Monitoring (Fastest)**
```bash
python3 scripts/mcp_mix_run.py --config realistic_mix.json --target localhost:13398 --target-rps 100 --parallel 5 --no-snapshots
```
→ Report back: RPS, latency, success rate

### **Path 2: Python Monitoring (Recommended)**
```bash
pip3 install psutil
# I'll create monitor-resources-psutil.py for you
# Then run with monitoring
```
→ Report back: Full metrics including CPU/memory

### **Path 3: Bash Monitoring (Lightweight)**
```bash
# I'll create monitor-resources-macos.sh for you
# Then run with monitoring
```
→ Report back: Basic metrics

---

## 📝 **What I Need From You**

**Choose one:**
1. **"Skip monitoring for now"** - I'll guide baseline run without metrics
2. **"Create psutil script"** - I'll create the Python monitoring script
3. **"Create bash script"** - I'll create the macOS-native script

Then you can proceed immediately with the baseline test!

---

## 🎯 **For Cost Model**

If you skip monitoring now, you can always:
1. Run benchmark for performance numbers (RPS, latency)
2. Add monitoring later for cost model
3. Re-run one test with monitoring to get CPU/memory

The performance data (RPS, P95 latency, success rate) is more important than resource metrics for initial validation.

---

**Excellent progress! You're doing this exactly right by identifying the constraints upfront.** 👏

Let me know which path you'd like, and I'll get you unblocked immediately!
