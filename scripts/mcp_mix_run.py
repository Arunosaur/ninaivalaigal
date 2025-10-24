#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""GraphOps mix workload orchestrator.

Launches the Go load tester with a weighted set of ExecuteQuery payloads,
collects resource samples (when psutil is available), and writes a summary
report for benchmarking runs associated with US-86.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dep
    psutil = None

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover - optional dep
    requests = None


DEFAULT_LOAD_TESTER = Path("go-services/load-tester/bin/load-tester")
DEFAULT_TARGET = "localhost:13398"
DEFAULT_SERVICE = "ninaivalaigal.graphops.v1.GraphOpsService"
DEFAULT_METHOD = "ExecuteQuery"


@dataclass
class QueryEntry:
    """Weighted query definition for the mix run."""

    name: str
    template: str
    weight: float
    expected_shape: str | None = None
    headers: List[str] = field(default_factory=list)

    def resolved_template(self, repo_root: Path) -> Path:
        path = Path(self.template)
        if not path.is_absolute():
            path = repo_root / path
        return path


@dataclass
class WorkloadConfig:
    """Full workload description combined with runtime overrides."""

    description: str = ""
    queries: List[QueryEntry] = field(default_factory=list)
    ramp_up_seconds: int = 30
    steady_state_seconds: int = 300
    cooldown_seconds: int = 30
    target_rps: int = 1000
    parallel_workers: int = 10
    snapshot_interval_seconds: int = 10
    prometheus_url: str = ""

    def total_weight(self) -> float:
        return sum(entry.weight for entry in self.queries)

    def total_duration(self) -> int:
        return self.ramp_up_seconds + self.steady_state_seconds + self.cooldown_seconds


@dataclass
class QueryLaunch:
    entry: QueryEntry
    rps: int
    concurrency: int
    log_path: Path
    process: Optional[object] = None
    log_handle: Optional[object] = None
    return_code: Optional[int] = None


def load_workload_config(path: Path, repo_root: Path) -> WorkloadConfig:
    with path.open() as handle:
        payload = json.load(handle)

    queries = [
        QueryEntry(
            name=item["name"],
            template=item["template"],
            weight=float(item["weight"]),
            expected_shape=item.get("expected_shape"),
            headers=item.get("headers", []),
        )
        for item in payload.get("queries", [])
    ]

    if not queries:
        raise ValueError(f"No queries defined in {path}")

    config = WorkloadConfig(
        description=payload.get("description", ""),
        queries=queries,
        ramp_up_seconds=int(payload.get("ramp_up_seconds", 30)),
        steady_state_seconds=int(payload.get("steady_state_seconds", 300)),
        cooldown_seconds=int(payload.get("cooldown_seconds", 30)),
        target_rps=int(payload.get("target_rps", 1000)),
        parallel_workers=int(payload.get("parallel_workers", 10)),
        snapshot_interval_seconds=int(payload.get("snapshot_interval_seconds", 10)),
        prometheus_url=payload.get("prometheus_url", ""),
    )

    weight = config.total_weight()
    if weight <= 0:
        raise ValueError("Configured query weights must be positive")

    return config


def default_workload(repo_root: Path) -> WorkloadConfig:
    return WorkloadConfig(
        description="Default GraphOps mix (auto-generated)",
        queries=[
            QueryEntry(
                name="memory_feed",
                template="benchmarks/graphops/queries/memory_feed.request.json",
                weight=0.4,
                expected_shape="map",
            ),
            QueryEntry(
                name="context_similarity",
                template="benchmarks/graphops/queries/context_similarity.request.json",
                weight=0.3,
                expected_shape="map",
            ),
            QueryEntry(
                name="team_collaboration",
                template="benchmarks/graphops/queries/team_collaboration.request.json",
                weight=0.2,
                expected_shape="map",
            ),
            QueryEntry(
                name="memory_feed_topics",
                template="benchmarks/graphops/queries/memory_feed.topics.json",
                weight=0.1,
                expected_shape="map",
            ),
        ],
    )


def query_prometheus(prometheus_url: str, prom_query: str) -> Dict[str, object] | None:
    if not prometheus_url or requests is None:
        return None

    try:
        endpoint = prometheus_url.rstrip("/")
        if not endpoint.endswith("/api/v1/query"):
            endpoint = f"{endpoint}/api/v1/query"

        response = requests.get(  # type: ignore[arg-type]
            endpoint,
            params={"query": prom_query},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data
    except Exception:
        return None


def collect_resource_snapshot(prometheus_url: str = "") -> Dict[str, object]:
    snapshot: Dict[str, object] = {
        "timestamp": time.time(),
    }

    if psutil is not None:
        disk_stats: Dict[str, object] = {}
        net_stats: Dict[str, object] = {}
        try:
            counters = psutil.disk_io_counters()
            if counters:
                disk_stats = counters._asdict()  # type: ignore[assignment]
        except Exception:
            disk_stats = {}

        try:
            net_counters = psutil.net_io_counters()
            if net_counters:
                net_stats = net_counters._asdict()  # type: ignore[assignment]
        except Exception:
            net_stats = {}

        snapshot.update(
            {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_mb": psutil.virtual_memory().used / (1024**2),
                "disk": disk_stats,
                "network": net_stats,
            }
        )
    else:
        snapshot["cpu_percent"] = None
        snapshot["memory_mb"] = None

    prom_result = query_prometheus(
        prometheus_url, 'rate(container_cpu_usage_seconds_total{name="ninaivalaigal-dev-graphops"}[5m])'
    )
    if prom_result is not None:
        snapshot["graphops_cpu_timeseries"] = prom_result

    prom_memory = query_prometheus(prometheus_url, 'container_memory_usage_bytes{name="ninaivalaigal-dev-graphops"}')
    if prom_memory is not None:
        snapshot["graphops_memory_timeseries"] = prom_memory

    return snapshot


def sample_resources(
    stop_event: threading.Event, interval: int, prometheus_url: str, sink: List[Dict[str, object]]
) -> None:
    # First call to psutil.cpu_percent should set baseline
    if psutil is not None:
        psutil.cpu_percent(interval=None)

    while not stop_event.is_set():
        sink.append(collect_resource_snapshot(prometheus_url))
        for _ in range(interval):
            if stop_event.is_set():
                break
            time.sleep(1)


def ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Load tester binary not found: {path}")
    if not os.access(path, os.X_OK):
        raise PermissionError(f"Load tester binary is not executable: {path}")


def launch_queries(
    load_tester: Path,
    repo_root: Path,
    config: WorkloadConfig,
    target: str,
    service: str,
    method: str,
    duration: int,
    timeout: int,
    headers: List[str],
    proto: Optional[Path],
    dry_run: bool,
    output_dir: Path,
) -> List[QueryLaunch]:
    launches: List[QueryLaunch] = []
    total_weight = config.total_weight()

    for entry in config.queries:
        weight_fraction = entry.weight / total_weight
        rps = max(1, round(config.target_rps * weight_fraction))
        concurrency = max(1, math.ceil(config.parallel_workers * weight_fraction))
        data_file = entry.resolved_template(repo_root)

        if not data_file.exists():
            raise FileNotFoundError(f"Data file for query '{entry.name}' not found: {data_file}")

        log_path = output_dir / f"{entry.name}.log"

        cmd = [
            str(load_tester),
            "grpc",
            target,
            "--service",
            service,
            "--method",
            method,
            "--data-file",
            str(data_file),
            "--duration",
            f"{duration}s",
            "--concurrency",
            str(concurrency),
            "--rps",
            str(rps),
            "--timeout",
            f"{timeout}s",
        ]

        if proto is not None:
            cmd.extend(["--proto", str(proto)])

        combined_headers = headers + entry.headers
        for header in combined_headers:
            cmd.extend(["--header", header])

        launch = QueryLaunch(entry=entry, rps=rps, concurrency=concurrency, log_path=log_path)

        if dry_run:
            print("DRY RUN:", " ".join(cmd))
            launches.append(launch)
            continue

        log_handle = log_path.open("w")
        process = subprocess.Popen(cmd, stdout=log_handle, stderr=subprocess.STDOUT)  # noqa: S603
        launch.process = process
        launch.log_handle = log_handle
        launches.append(launch)

    return launches


def wait_for_launches(launches: List[QueryLaunch]) -> None:
    for launch in launches:
        process = launch.process
        if process is None:
            continue
        try:
            launch.return_code = process.wait()
        finally:
            if launch.log_handle is not None:
                try:
                    launch.log_handle.close()
                except Exception:
                    pass


def summarise_launches(launches: List[QueryLaunch]) -> List[Dict[str, object]]:
    summary = []
    for launch in launches:
        if launch.return_code is None:
            status = "pending"
        elif launch.return_code == 0:
            status = "success"
        else:
            status = "failed"

        summary.append(
            {
                "query": launch.entry.name,
                "template": launch.entry.template,
                "weight": launch.entry.weight,
                "rps": launch.rps,
                "concurrency": launch.concurrency,
                "log_path": str(launch.log_path),
                "status": status,
                "return_code": launch.return_code,
            }
        )
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(description="Run GraphOps mix workloads via load tester")
    parser.add_argument("--config", type=Path, help="JSON workload configuration (defaults to realistic mix)")
    parser.add_argument("--load-tester", type=Path, default=DEFAULT_LOAD_TESTER, help="Path to load tester binary")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="GraphOps gRPC endpoint")
    parser.add_argument("--service", default=DEFAULT_SERVICE, help="Fully-qualified GraphOps service name")
    parser.add_argument("--method", default=DEFAULT_METHOD, help="GraphOps method (ExecuteQuery)")
    parser.add_argument("--duration", type=int, help="Override total duration in seconds")
    parser.add_argument("--steady", type=int, help="Override steady-state duration (seconds)")
    parser.add_argument("--target-rps", type=int, help="Override total target RPS")
    parser.add_argument("--parallel", type=int, help="Override total parallel workers")
    parser.add_argument("--timeout", type=int, default=5, help="Per-request timeout in seconds")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("benchmarks/results"), help="Directory for logs/results"
    )
    parser.add_argument("--header", action="append", default=[], help="Additional gRPC metadata header (Key: Value)")
    parser.add_argument("--proto", type=Path, help="Optional proto file for load tester")
    parser.add_argument("--no-snapshots", action="store_true", help="Disable psutil-based resource sampling")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")

    args = parser.parse_args(argv)

    config = load_workload_config(args.config, repo_root) if args.config else default_workload(repo_root)

    if args.steady is not None:
        config.steady_state_seconds = args.steady
    if args.target_rps is not None:
        config.target_rps = args.target_rps
    if args.parallel is not None:
        config.parallel_workers = args.parallel
    if args.duration is not None:
        override = max(1, args.duration)
        # Preserve ramp/cooldown ratios when overriding total duration
        steady_ratio = config.steady_state_seconds / max(1, config.total_duration())
        ramp_ratio = config.ramp_up_seconds / max(1, config.total_duration())
        cool_ratio = config.cooldown_seconds / max(1, config.total_duration())
        config.ramp_up_seconds = max(0, round(override * ramp_ratio))
        config.steady_state_seconds = max(1, round(override * steady_ratio))
        config.cooldown_seconds = max(0, override - config.ramp_up_seconds - config.steady_state_seconds)

    if not args.dry_run:
        ensure_executable(args.load_tester)

    output_dir = (repo_root / args.output_dir).resolve()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"graphops_mix_{timestamp}"
    if not args.dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)

    total_duration = config.total_duration()

    launches = launch_queries(
        load_tester=args.load_tester,
        repo_root=repo_root,
        config=config,
        target=args.target,
        service=args.service,
        method=args.method,
        duration=total_duration,
        timeout=args.timeout,
        headers=args.header,
        proto=args.proto,
        dry_run=args.dry_run,
        output_dir=run_dir,
    )

    if args.dry_run:
        return 0

    snapshots: List[Dict[str, object]] = []
    stop_event = threading.Event()
    sampler_thread: Optional[threading.Thread] = None

    if not args.no_snapshots:
        sampler_thread = threading.Thread(
            target=sample_resources,
            args=(stop_event, config.snapshot_interval_seconds, config.prometheus_url, snapshots),
            daemon=True,
        )
        sampler_thread.start()

    wait_for_launches(launches)

    stop_event.set()
    if sampler_thread is not None:
        sampler_thread.join(timeout=5)

    summary = {
        "started_at": timestamp,
        "target": args.target,
        "service": args.service,
        "method": args.method,
        "duration_seconds": total_duration,
        "config": asdict(config),
        "queries": summarise_launches(launches),
        "resource_samples": snapshots,
        "psutil_available": psutil is not None,
        "prometheus_enabled": bool(config.prometheus_url),
    }

    summary_path = run_dir / "mix_summary.json"
    with summary_path.open("w") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Mix run complete. Summary -> {summary_path}")
    print(f"Logs -> {run_dir}")

    failures = [entry for entry in summary["queries"] if entry.get("status") == "failed"]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
