// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// GraphOps Service Main
// SPEC-099 Phase 1: gRPC + Metrics Endpoint

use graphops_service::metrics;
use graphops_service::proto::graphops::v1::graph_ops_service_server::GraphOpsServiceServer;
use graphops_service::{DbPool, GraphOpsService};
use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Method, Request, Response, Server as HyperServer, StatusCode};
use std::convert::Infallible;
use std::env;
use std::net::SocketAddr;
use tonic::transport::Server;
use tracing::{error, info};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Initialize tracing
    tracing_subscriber::fmt::try_init().ok();

    // Load configuration from environment
    let database_url = env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://nina:dev_password_change_in_production@192.168.64.135:5432/ninaivalaigal_dev".to_string()); // pragma: allowlist secret

    let grpc_addr: SocketAddr = env::var("GRAPHOPS_GRPC_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:50051".to_string())
        .parse()?;

    let metrics_addr: SocketAddr = env::var("GRAPHOPS_METRICS_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:9090".to_string())
        .parse()?;

    let graph_name =
        env::var("GRAPHOPS_GRAPH").unwrap_or_else(|_| "ninaivalaigal_intelligence".to_string());

    info!("Starting GraphOps Service");
    info!("Database: {}", database_url);
    info!("gRPC listening on: {}", grpc_addr);
    info!("Metrics listening on: {}", metrics_addr);
    info!("Graph name: {}", graph_name);

    // Initialize database pool
    let pool = DbPool::new(&database_url)?;
    let service = GraphOpsService::new(pool, graph_name);

    // Start gRPC server in background
    let grpc_server = Server::builder()
        .add_service(GraphOpsServiceServer::new(service))
        .serve(grpc_addr);

    info!("✅ gRPC server started on {}", grpc_addr);

    // Start metrics HTTP server in background
    let metrics_server = HyperServer::bind(&metrics_addr).serve(make_service_fn(|_conn| async {
        Ok::<_, Infallible>(service_fn(handle_metrics_request))
    }));

    info!("✅ Metrics server started on {}", metrics_addr);
    info!("📊 Metrics available at http://{}/metrics", metrics_addr);
    info!("💚 Health check at http://{}/health", metrics_addr);

    // Run both servers concurrently
    tokio::select! {
        result = grpc_server => {
            if let Err(e) = result {
                error!("gRPC server error: {}", e);
            }
        }
        result = metrics_server => {
            if let Err(e) = result {
                error!("Metrics server error: {}", e);
            }
        }
    }

    Ok(())
}

/// Handle HTTP requests for metrics endpoint
async fn handle_metrics_request(req: Request<Body>) -> Result<Response<Body>, Infallible> {
    match (req.method(), req.uri().path()) {
        (&Method::GET, "/metrics") => {
            // Update memory metrics before gathering
            metrics::update_memory_metrics();

            // Gather all Prometheus metrics
            let metrics_text = metrics::gather_metrics();

            Ok(Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "text/plain; version=0.0.4")
                .body(Body::from(metrics_text))
                .unwrap())
        }
        (&Method::GET, "/health") => {
            // Simple health check endpoint
            let health_response = r#"{"status":"healthy","service":"graphops"}"#;

            Ok(Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "application/json")
                .body(Body::from(health_response))
                .unwrap())
        }
        _ => {
            // 404 for unknown paths
            Ok(Response::builder()
                .status(StatusCode::NOT_FOUND)
                .body(Body::from("Not Found"))
                .unwrap())
        }
    }
}
