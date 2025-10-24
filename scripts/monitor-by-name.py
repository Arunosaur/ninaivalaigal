#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Monitor processes by name (workaround for Apple Container CLI PID 0 issue)
"""

import csv
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


def find_processes_by_name(name_pattern):
    """Find all processes matching name pattern."""
    matching_pids = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            # Check if pattern in process name
            if name_pattern.lower() in proc.info["name"].lower():
                matching_pids.append((proc.pid, proc.info["name"]))
                continue

            # Check if pattern in command line
            if proc.info["cmdline"]:
                cmdline = " ".join(proc.info["cmdline"]).lower()
                if name_pattern.lower() in cmdline:
                    matching_pids.append((proc.pid, " ".join(proc.info["cmdline"][:2])))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return matching_pids


def get_process_metrics(pid):
    """Get CPU and memory metrics for a process."""
    try:
        proc = psutil.Process(pid)

        # Get main process metrics
        cpu = proc.cpu_percent(interval=0.1)
        mem = proc.memory_info().rss / (1024 * 1024)  # MB

        # Include children
        children = proc.children(recursive=True)
        for child in children:
            try:
                cpu += child.cpu_percent(interval=0)
                mem += child.memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {"cpu_percent": round(cpu, 2), "memory_mb": round(mem, 2), "num_children": len(children)}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"cpu_percent": 0.0, "memory_mb": 0.0, "num_children": 0}


def monitor_by_name(name_pattern, output_file, interval=10):
    """Monitor processes matching name pattern."""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Process Name Monitoring (Apple Container CLI Workaround)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Pattern: {name_pattern}")
    print(f"   Output: {output_file}")
    print(f"   Interval: {interval}s")
    print("")

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Create CSV with header
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "process_name", "pid", "cpu_percent", "memory_mb", "num_children"])

    sample_count = 0

    try:
        while True:
            timestamp = datetime.utcnow().isoformat() + "Z"
            sample_count += 1

            print(f"Sample {sample_count} @ {timestamp}")

            # Find matching processes
            processes = find_processes_by_name(name_pattern)

            if not processes:
                print(f"  ⚠ No processes matching '{name_pattern}' found")
                with open(output_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, name_pattern, 0, 0.0, 0.0, 0])
            else:
                # Aggregate metrics across all matching processes
                total_cpu = 0.0
                total_mem = 0.0
                total_children = 0

                for pid, proc_name in processes:
                    metrics = get_process_metrics(pid)
                    total_cpu += metrics["cpu_percent"]
                    total_mem += metrics["memory_mb"]
                    total_children += metrics["num_children"]

                    print(
                        f"  ✓ {proc_name:40s} | PID: {pid:6d} | "
                        f"CPU: {metrics['cpu_percent']:6.2f}% | "
                        f"Mem: {metrics['memory_mb']:8.2f}MB | "
                        f"Children: {metrics['num_children']:2d}"
                    )

                # Write aggregated metrics
                with open(output_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            timestamp,
                            f"{name_pattern} (aggregated)",
                            len(processes),  # Number of processes found
                            round(total_cpu, 2),
                            round(total_mem, 2),
                            total_children,
                        ]
                    )

                if len(processes) > 1:
                    print(
                        f"  📊 TOTAL: {len(processes)} processes | " f"CPU: {total_cpu:.2f}% | Mem: {total_mem:.2f}MB"
                    )

            print("")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Monitoring stopped ({sample_count} samples collected)")
        print(f"   Output: {output_file}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: monitor-by-name.py <process_pattern> [output_file] [interval]")
        print("")
        print("Examples:")
        print("  monitor-by-name.py graphops benchmarks/results/resources.csv 10")
        print("  monitor-by-name.py postgres benchmarks/results/pg_resources.csv 5")
        print("  monitor-by-name.py redis")
        sys.exit(1)

    pattern = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else f"benchmarks/results/{pattern}_resources.csv"
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    # Find processes first to verify pattern works
    print(f"🔍 Searching for processes matching '{pattern}'...")
    found = find_processes_by_name(pattern)

    if not found:
        print(f"❌ No processes found matching '{pattern}'")
        print("\nTry one of these patterns:")
        print("  - graphops")
        print("  - postgres")
        print("  - redis")
        print("  - container")
        sys.exit(1)

    print(f"✅ Found {len(found)} matching process(es):")
    for pid, name in found:
        print(f"   - PID {pid}: {name}")
    print("")

    monitor_by_name(pattern, output, interval)
