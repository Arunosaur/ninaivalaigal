// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// GraphOps Service Main
// SPEC-099 Phase 1: gRPC + Metrics Endpoint

use clap::Parser;
use graphops_service::metrics;
use graphops_service::proto::graphops::v1::graph_ops_service_server::GraphOpsServiceServer;
use graphops_service::{DbPool, GraphOpsService};
use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Method, Request, Response, Server as HyperServer, StatusCode};
use std::convert::Infallible;
use std::env;
use std::net::SocketAddr;
use std::process;
use tonic::transport::Server;
use tracing::{error, info};

#[derive(Parser, Debug, Clone)]
#[command(name = "graphops", about = "GraphOps gRPC Service", long_about = None)]
struct Cli {
    /// Perform a lightweight health check and exit
    #[arg(long)]
    health_check: bool,

    /// PostgreSQL connection string (overrides DATABASE_URL)
    #[arg(long, env = "DATABASE_URL")]
    database_url: Option<String>,

    /// Graph name to target (overrides GRAPHOPS_GRAPH)
    #[arg(long, env = "GRAPHOPS_GRAPH")]
    graph: Option<String>,

    /// gRPC bind address (overrides GRAPHOPS_GRPC_ADDR)
    #[arg(long, env = "GRAPHOPS_GRPC_ADDR")]
    grpc_addr: Option<String>,

    /// Metrics bind address (overrides GRAPHOPS_METRICS_ADDR)
    #[arg(long, env = "GRAPHOPS_METRICS_ADDR")]
    metrics_addr: Option<String>,
}

fn resolve_config(value: &Option<String>, key: &str, default: &str) -> String {
    value
        .clone()
        .or_else(|| env::var(key).ok())
        .unwrap_or_else(|| default.to_string())
}

fn run_health_check(cli: &Cli) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    println!("🏥 Running GraphOps health check...");

    if let Some(url) = cli
        .database_url
        .clone()
        .or_else(|| env::var("DATABASE_URL").ok())
    {
        DbPool::new(&url)?;
        println!("  ✅ DATABASE_URL detected");
    } else {
        println!("  ℹ️  DATABASE_URL not set (skipping database readiness)");
    }

    if let Some(graph) = cli
        .graph
        .clone()
        .or_else(|| env::var("GRAPHOPS_GRAPH").ok())
    {
        println!("  ✅ GRAPHOPS_GRAPH set to {graph}");
    } else {
        println!("  ℹ️  GRAPHOPS_GRAPH not provided (defaults apply)");
    }

    println!("✅ GraphOps health check passed");
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    tracing_subscriber::fmt::try_init().ok();

    let cli = Cli::parse();

    if cli.health_check {
        if let Err(error) = run_health_check(&cli) {
            eprintln!("❌ GraphOps health check failed: {error}");
            process::exit(1);
        }
        process::exit(0);
    }

    let database_url = resolve_config(
        &cli.database_url,
        "DATABASE_URL",
        "postgresql://nina:dev_password_change_in_production@192.168.64.135:5432/ninaivalaigal_dev", // pragma: allowlist secret
    );

    let grpc_addr: SocketAddr =
        resolve_config(&cli.grpc_addr, "GRAPHOPS_GRPC_ADDR", "0.0.0.0:50051").parse()?;

    let metrics_addr: SocketAddr =
        resolve_config(&cli.metrics_addr, "GRAPHOPS_METRICS_ADDR", "0.0.0.0:9090").parse()?;

    let graph_name = resolve_config(&cli.graph, "GRAPHOPS_GRAPH", "ninaivalaigal_intelligence");

    info!("Starting GraphOps Service");
    info!("Database: {}", database_url);
    info!("gRPC listening on: {}", grpc_addr);
    info!("Metrics listening on: {}", metrics_addr);
    info!("Graph name: {}", graph_name);

    let pool = DbPool::new(&database_url)?;
    let service = GraphOpsService::new(pool, graph_name);

    let grpc_server = Server::builder()
        .add_service(GraphOpsServiceServer::new(service))
        .serve(grpc_addr);

    info!("✅ gRPC server started on {}", grpc_addr);

    let metrics_server = HyperServer::bind(&metrics_addr).serve(make_service_fn(|_conn| async {
        Ok::<_, Infallible>(service_fn(handle_metrics_request))
    }));

    info!("✅ Metrics server started on {}", metrics_addr);
    info!("📊 Metrics available at http://{}/metrics", metrics_addr);
    info!("💚 Health check at http://{}/health", metrics_addr);

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
            metrics::update_memory_metrics();
            let metrics_text = metrics::gather_metrics();

            Ok(Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "text/plain; version=0.0.4")
                .body(Body::from(metrics_text))
                .unwrap())
        }
        (&Method::GET, "/health") => {
            let health_response = r#"{"status":"healthy","service":"graphops"}"#;

            Ok(Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "application/json")
                .body(Body::from(health_response))
                .unwrap())
        }
        _ => Ok(Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Body::from("Not Found"))
            .unwrap()),
    }
}
