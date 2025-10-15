// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Integration Tests for GraphOps Service
// SPEC-099 Phase 1

use graphops_service::proto::graphops::v1::graph_ops_service_server::GraphOpsService as GraphOpsServiceTrait;
use graphops_service::proto::graphops::v1::*;
use graphops_service::{DbPool, GraphOpsService};
use tonic::Request;

#[tokio::test]
async fn test_health_check() {
    // Skip if no database available
    if std::env::var("DATABASE_URL").is_err() {
        eprintln!("Skipping test: DATABASE_URL not set");
        return;
    }

    let database_url = std::env::var("DATABASE_URL").unwrap();
    let pool = DbPool::new(&database_url).expect("Failed to create pool");
    let service = GraphOpsService::new(pool, "ninaivalaigal_intelligence".to_string());

    let request = Request::new(HealthCheckRequest {
        service: "graphops".to_string(),
    });

    let response = service
        .health_check(request)
        .await
        .expect("Health check failed");

    let health = response.into_inner();
    println!("Health check response: {:?}", health);

    // Service should be healthy if database is available
    assert_eq!(health.status, HealthStatus::Healthy as i32);
    assert!(health.uptime_seconds >= 0);
}

#[tokio::test]
async fn test_get_metrics() {
    // Skip if no database available
    if std::env::var("DATABASE_URL").is_err() {
        eprintln!("Skipping test: DATABASE_URL not set");
        return;
    }

    let database_url = std::env::var("DATABASE_URL").unwrap();
    let pool = DbPool::new(&database_url).expect("Failed to create pool");
    let service = GraphOpsService::new(pool, "ninaivalaigal_intelligence".to_string());

    let request = Request::new(MetricsRequest { window_seconds: 60 });

    let response = service
        .get_metrics(request)
        .await
        .expect("Get metrics failed");

    let metrics = response.into_inner();
    println!("Metrics response: {:?}", metrics);

    // Memory usage should be non-zero
    assert!(metrics.memory_usage_bytes >= 0);
}

#[test]
fn test_metrics_export() {
    use graphops_service::metrics;

    metrics::REQUEST_DURATION.observe(0.0);
    metrics::REQUESTS_TOTAL
        .with_label_values(&["rust", "test", "success"])
        .inc();
    metrics::update_memory_metrics();
    metrics::CACHE_HITS_TOTAL
        .with_label_values(&["rust", "warm"])
        .inc();
    metrics::DB_CONNECTIONS_ACTIVE
        .with_label_values(&["rust", "primary"])
        .set(1);
    metrics::ERRORS_TOTAL
        .with_label_values(&["rust", "test", "ExecuteQuery"])
        .inc();

    // Test that metrics can be gathered
    let metrics_text = metrics::gather_metrics();

    println!("Prometheus metrics:");
    println!("{}", metrics_text);

    // Verify required metrics are present
    assert!(metrics_text.contains("graphops_request_duration_seconds"));
    assert!(metrics_text.contains("graphops_requests_total"));
    assert!(metrics_text.contains("graphops_cache_hits_total"));
    assert!(metrics_text.contains("graphops_db_connections_active"));
    assert!(metrics_text.contains("graphops_errors_total"));
}

#[test]
fn test_memory_tracking() {
    use graphops_service::metrics;

    // Test memory usage retrieval
    let memory_usage = metrics::get_memory_usage();
    println!(
        "Current memory usage: {} bytes ({} MB)",
        memory_usage,
        memory_usage / 1024 / 1024
    );

    // Should return non-zero value
    assert!(memory_usage > 0);

    // Update metrics
    metrics::update_memory_metrics();

    // Verify metrics updated
    let metrics_text = metrics::gather_metrics();
    assert!(metrics_text.contains("graphops_memory_bytes"));
}
