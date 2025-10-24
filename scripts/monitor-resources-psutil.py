#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Resource monitoring using psutil for accurate metrics
Works with Apple Container CLI and macOS
"""

import csv
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
            check=True,
        )
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str and pid_str != "0" else 0
    except (subprocess.CalledProcessError, ValueError):
        return 0


def get_process_metrics(pid: int) -> dict:
    """Get detailed metrics for a process including children."""
    try:
        process = psutil.Process(pid)

        # Get CPU and memory info (interval=0.1 for responsive measurement)
        cpu_percent = process.cpu_percent(interval=0.1)
        mem_info = process.memory_info()

        # Get children processes (container often spawns children)
        children = process.children(recursive=True)

        # Aggregate metrics from children
        children_cpu = 0.0
        children_mem = 0
        for child in children:
            try:
                children_cpu += child.cpu_percent(interval=0)
                children_mem += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        total_cpu = cpu_percent + children_cpu
        total_mem = mem_info.rss + children_mem

        return {
            "cpu_percent": round(total_cpu, 2),
            "memory_mb": round(total_mem / (1024 * 1024), 2),
            "num_threads": process.num_threads(),
            "num_children": len(children),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"cpu_percent": 0.0, "memory_mb": 0.0, "num_threads": 0, "num_children": 0}


def monitor_containers(output_file: str, interval: int = 10):
    """Monitor container resource usage."""
    containers = ["ninaivalaigal-dev-graphops", "ninaivalaigal-dev-db", "ninaivalaigal-dev-redis"]

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Resource Monitoring (psutil)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Output: {output_file}")
    print(f"   Interval: {interval}s")
    print(f"   Containers: {', '.join(containers)}")
    print("")

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Create output file with header
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "container", "pid", "cpu_percent", "memory_mb", "num_threads", "num_children"])

    sample_count = 0
    try:
        while True:
            timestamp = datetime.utcnow().isoformat() + "Z"
            sample_count += 1

            print(f"Sample {sample_count} @ {timestamp}")

            for container in containers:
                pid = get_container_pid(container)

                if pid > 0:
                    metrics = get_process_metrics(pid)

                    with open(output_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            [
                                timestamp,
                                container,
                                pid,
                                metrics["cpu_percent"],
                                metrics["memory_mb"],
                                metrics["num_threads"],
                                metrics["num_children"],
                            ]
                        )

                    print(
                        f"  ✓ {container:30s} | CPU: {metrics['cpu_percent']:6.2f}% | "
                        f"Mem: {metrics['memory_mb']:8.2f}MB | "
                        f"Threads: {metrics['num_threads']:3d} | "
                        f"Children: {metrics['num_children']:2d}"
                    )
                else:
                    # Container not running
                    with open(output_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, container, 0, 0.0, 0.0, 0, 0])

                    print(f"  ⚠ {container:30s} | Not running")

            print("")  # Blank line between samples
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Monitoring stopped ({sample_count} samples collected)")
        print(f"   Output: {output_file}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "benchmarks/results/resources.csv"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    monitor_containers(output, interval)
