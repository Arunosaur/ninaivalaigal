// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Prometheus Metrics Registry for GraphOps
// SPEC-099 Phase 1: Metrics Integration

use lazy_static::lazy_static;
use prometheus::{
    Encoder, Histogram, HistogramOpts, IntCounterVec, IntGaugeVec, Opts, Registry, TextEncoder,
};
use std::time::Instant;

lazy_static! {
    pub static ref REGISTRY: Registry = Registry::new();

    // Request duration histogram (required by Grafana dashboard)
    pub static ref REQUEST_DURATION: Histogram = {
        let opts = HistogramOpts::new(
            "graphops_request_duration_seconds",
            "GraphOps request latency in seconds"
        )
        .buckets(vec![0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]);

        let histogram = Histogram::with_opts(opts).unwrap();
        REGISTRY.register(Box::new(histogram.clone())).unwrap();
        histogram
    };

    // Total requests counter
    pub static ref REQUESTS_TOTAL: IntCounterVec = {
        let counter = IntCounterVec::new(
            Opts::new("graphops_requests_total", "Total GraphOps requests"),
            &["runtime", "operation", "status"]
        ).unwrap();
        REGISTRY.register(Box::new(counter.clone())).unwrap();
        counter
    };

    // Cache hits counter
    pub static ref CACHE_HITS_TOTAL: IntCounterVec = {
        let counter = IntCounterVec::new(
            Opts::new("graphops_cache_hits_total", "GraphOps cache hits"),
            &["runtime", "cache_type"]
        ).unwrap();
        REGISTRY.register(Box::new(counter.clone())).unwrap();
        counter
    };

    // Active database connections
    pub static ref DB_CONNECTIONS_ACTIVE: IntGaugeVec = {
        let gauge = IntGaugeVec::new(
            Opts::new("graphops_db_connections_active", "Active database connections"),
            &["runtime", "pool"]
        ).unwrap();
        REGISTRY.register(Box::new(gauge.clone())).unwrap();
        gauge
    };

    // Error counter
    pub static ref ERRORS_TOTAL: IntCounterVec = {
        let counter = IntCounterVec::new(
            Opts::new("graphops_errors_total", "Total errors by type"),
            &["runtime", "error_type", "operation"]
        ).unwrap();
        REGISTRY.register(Box::new(counter.clone())).unwrap();
        counter
    };

    // Memory usage (optional but recommended)
    pub static ref MEMORY_BYTES: IntGaugeVec = {
        let gauge = IntGaugeVec::new(
            Opts::new("graphops_memory_bytes", "Current memory usage"),
            &["runtime", "type"]
        ).unwrap();
        REGISTRY.register(Box::new(gauge.clone())).unwrap();
        gauge
    };
}

/// Timer for measuring request duration
pub struct RequestTimer {
    start: Instant,
}

impl Default for RequestTimer {
    fn default() -> Self {
        Self::new()
    }
}

impl RequestTimer {
    pub fn new() -> Self {
        Self {
            start: Instant::now(),
        }
    }

    pub fn observe(self) {
        let duration = self.start.elapsed();
        REQUEST_DURATION.observe(duration.as_secs_f64());
    }
}

/// Gather all metrics in Prometheus text format
pub fn gather_metrics() -> String {
    let encoder = TextEncoder::new();
    let metric_families = REGISTRY.gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer).unwrap();
    String::from_utf8(buffer).unwrap()
}

/// Get current memory usage (RSS)
pub fn get_memory_usage() -> u64 {
    use sysinfo::{ProcessRefreshKind, RefreshKind, System};

    let mut sys =
        System::new_with_specifics(RefreshKind::new().with_processes(ProcessRefreshKind::new()));

    sys.refresh_process(sysinfo::get_current_pid().unwrap());

    if let Some(process) = sys.process(sysinfo::get_current_pid().unwrap()) {
        return process.memory();
    }

    0 // Fallback
}

/// Update memory metrics
pub fn update_memory_metrics() {
    let rss = get_memory_usage();
    MEMORY_BYTES
        .with_label_values(&["rust", "rss"])
        .set(rss as i64);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrics_registration() {
        // Prime counters so they emit samples in the gathered output.
        REQUEST_DURATION.observe(0.0);
        REQUESTS_TOTAL
            .with_label_values(&["rust", "test", "success"])
            .inc();

        // Verify metrics are registered
        let metrics = gather_metrics();
        assert!(metrics.contains("graphops_request_duration_seconds"));
        assert!(metrics.contains("graphops_requests_total"));
    }

    #[test]
    fn test_request_timer() {
        let timer = RequestTimer::new();
        std::thread::sleep(std::time::Duration::from_millis(10));
        timer.observe();

        // Verify duration was recorded
        let metrics = gather_metrics();
        assert!(metrics.contains("graphops_request_duration_seconds"));
    }
}
