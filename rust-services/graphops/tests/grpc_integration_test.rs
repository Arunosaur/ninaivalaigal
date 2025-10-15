// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// gRPC integration tests exercising the GraphOps service contract end-to-end.

use graphops_service::proto::graphops::v1::graph_ops_service_client::GraphOpsServiceClient;
use graphops_service::proto::graphops::v1::graph_ops_service_server::GraphOpsServiceServer;
use graphops_service::proto::graphops::v1::{
    CypherBatchRequest, CypherRequest, HealthCheckRequest, MetricsRequest,
};
use graphops_service::{DbPool, GraphOpsService};
use std::env;
use std::net::TcpListener;
use std::time::Duration;
use tokio::sync::oneshot;
use tonic::transport::{Channel, Endpoint, Server};

async fn spawn_test_client() -> Option<(GraphOpsServiceClient<Channel>, oneshot::Sender<()>)> {
    // Load local environment overrides if present.
    let _ = dotenvy::dotenv();

    let database_url = match env::var("DATABASE_URL") {
        Ok(url) => url,
        Err(_) => {
            eprintln!("Skipping test: DATABASE_URL not set");
            return None;
        }
    };

    let graph_name =
        env::var("GRAPHOPS_GRAPH").unwrap_or_else(|_| "ninaivalaigal_intelligence".to_string());

    let pool = match DbPool::new(&database_url) {
        Ok(pool) => pool,
        Err(error) => {
            eprintln!("Skipping test: failed to create DbPool ({error})");
            return None;
        }
    };

    let service = GraphOpsService::new(pool, graph_name);

    // Bind to an ephemeral port so tests can run in parallel without conflicts.
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind test listener");
    let addr = listener.local_addr().expect("listener addr");
    drop(listener); // Release the port so tonic can bind to it.

    let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();

    let grpc_service = GraphOpsServiceServer::new(service);

    tokio::spawn(async move {
        if let Err(error) = Server::builder()
            .add_service(grpc_service)
            .serve_with_shutdown(addr, async {
                let _ = shutdown_rx.await;
            })
            .await
        {
            eprintln!("Test gRPC server error: {error}");
        }
    });

    // Give the server a brief moment to start listening before we connect a client.
    tokio::time::sleep(Duration::from_millis(200)).await;

    let endpoint = match Endpoint::from_shared(format!("http://{}", addr)) {
        Ok(endpoint) => endpoint
            .connect_timeout(Duration::from_secs(3))
            .timeout(Duration::from_secs(5)),
        Err(error) => {
            eprintln!("Skipping test: invalid endpoint ({error})");
            let _ = shutdown_tx.send(());
            return None;
        }
    };

    let channel = match endpoint.connect().await {
        Ok(channel) => channel,
        Err(error) => {
            eprintln!("Skipping test: failed to connect to GraphOps gRPC server ({error})");
            let _ = shutdown_tx.send(());
            return None;
        }
    };

    Some((GraphOpsServiceClient::new(channel), shutdown_tx))
}

#[tokio::test]
async fn execute_query_roundtrip() {
    let Some((mut client, shutdown)) = spawn_test_client().await else {
        return;
    };

    let request = CypherRequest {
        query: "MATCH (n) RETURN n LIMIT 1".to_string(),
        parameters: Default::default(),
        timeout_ms: 0,
        trace_id: "it-execute-query".to_string(),
        span_id: String::new(),
    };

    let response = client
        .execute_query(request)
        .await
        .expect("ExecuteQuery RPC should return");
    let payload = response.into_inner();

    assert_eq!(
        payload.status,
        graphops_service::proto::graphops::v1::ExecutionStatus::Success as i32
    );
    assert!(payload.row_count >= 0);

    let _ = shutdown.send(());
}

#[tokio::test]
async fn execute_query_batch_roundtrip() {
    let Some((mut client, shutdown)) = spawn_test_client().await else {
        return;
    };

    let request = CypherBatchRequest {
        queries: vec![
            CypherRequest {
                query: "MATCH (n) RETURN n LIMIT 1".to_string(),
                parameters: Default::default(),
                timeout_ms: 0,
                trace_id: "it-batch-1".to_string(),
                span_id: String::new(),
            },
            CypherRequest {
                query: "MATCH (n) RETURN n LIMIT 1".to_string(),
                parameters: Default::default(),
                timeout_ms: 0,
                trace_id: "it-batch-2".to_string(),
                span_id: String::new(),
            },
        ],
        fail_fast: false,
        trace_id: "batch-trace".to_string(),
    };

    let response = client
        .execute_query_batch(request)
        .await
        .expect("ExecuteQueryBatch RPC should return");
    let payload = response.into_inner();

    assert_eq!(
        payload.batch_status,
        graphops_service::proto::graphops::v1::ExecutionStatus::Success as i32
    );
    assert_eq!(payload.responses.len(), 2);
    assert_eq!(payload.success_count, 2);
    assert_eq!(payload.failure_count, 0);

    let _ = shutdown.send(());
}

#[tokio::test]
async fn health_check_roundtrip() {
    let Some((mut client, shutdown)) = spawn_test_client().await else {
        return;
    };

    let response = client
        .health_check(HealthCheckRequest {
            service: "graphops".to_string(),
        })
        .await
        .expect("HealthCheck RPC should return");
    let payload = response.into_inner();

    assert_eq!(
        payload.status,
        graphops_service::proto::graphops::v1::HealthStatus::Healthy as i32
    );
    assert!(payload.uptime_seconds >= 0);

    let _ = shutdown.send(());
}

#[tokio::test]
async fn get_metrics_roundtrip() {
    let Some((mut client, shutdown)) = spawn_test_client().await else {
        return;
    };

    let response = client
        .get_metrics(MetricsRequest { window_seconds: 60 })
        .await
        .expect("GetMetrics RPC should return");
    let payload = response.into_inner();

    assert!(payload.total_queries >= 0);
    assert!(payload.memory_usage_bytes >= 0);

    let _ = shutdown.send(());
}
