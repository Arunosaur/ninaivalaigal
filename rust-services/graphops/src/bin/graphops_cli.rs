// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Lightweight CLI helper for invoking the GraphOps gRPC service during manual validation.
// The tool provides a simple way to hit the HealthCheck, ExecuteQuery, ExecuteQueryBatch,
// and GetMetrics RPCs without requiring external dependencies like `grpcurl`.

use std::env;
use std::error::Error;

use graphops_service::proto::graphops::v1::graph_ops_service_client::GraphOpsServiceClient;
use graphops_service::proto::graphops::v1::{
    CypherBatchRequest, CypherRequest, HealthCheckRequest, MetricsRequest,
};
use tonic::transport::Channel;

const DEFAULT_ENDPOINT: &str = "http://localhost:50051";

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    let mode = args.get(1).map(|arg| arg.as_str()).unwrap_or("all");

    let endpoint = env::var("GRAPHOPS_ENDPOINT").unwrap_or_else(|_| DEFAULT_ENDPOINT.to_string());

    match mode {
        "health" => {
            let mut client = connect(&endpoint).await?;
            run_health_check(&mut client).await?;
        }
        "execute" => {
            let mut client = connect(&endpoint).await?;
            run_execute_query(&mut client).await?;
        }
        "metrics" => {
            let mut client = connect(&endpoint).await?;
            run_get_metrics(&mut client).await?;
        }
        "batch" => {
            let mut client = connect(&endpoint).await?;
            run_execute_batch(&mut client).await?;
        }
        "all" => {
            let mut client = connect(&endpoint).await?;
            run_health_check(&mut client).await?;
            run_execute_query(&mut client).await?;
            run_get_metrics(&mut client).await?;
            run_execute_batch(&mut client).await?;
        }
        other => {
            eprintln!(
                "Unknown mode '{}'. Use one of: all, health, execute, batch, metrics.",
                other
            );
            std::process::exit(2);
        }
    }

    Ok(())
}

async fn connect(endpoint: &str) -> Result<GraphOpsServiceClient<Channel>, Box<dyn Error>> {
    println!("Connecting to {}...", endpoint);
    let client = GraphOpsServiceClient::connect(endpoint.to_string()).await?;
    Ok(client)
}

async fn run_health_check(
    client: &mut GraphOpsServiceClient<Channel>,
) -> Result<(), Box<dyn Error>> {
    println!("\n== HealthCheck ==");
    let response = client
        .health_check(HealthCheckRequest {
            service: "graphops".to_string(),
        })
        .await?;
    println!("{:?}", response.into_inner());
    Ok(())
}

async fn run_execute_query(
    client: &mut GraphOpsServiceClient<Channel>,
) -> Result<(), Box<dyn Error>> {
    println!("\n== ExecuteQuery ==");
    let response = client
        .execute_query(CypherRequest {
            query: "MATCH (n) RETURN count(n)".to_string(),
            parameters: Default::default(),
            timeout_ms: 30_000,
            trace_id: "graphops-cli-execute".to_string(),
            span_id: String::new(),
        })
        .await?;
    println!("{:?}", response.into_inner());
    Ok(())
}

async fn run_get_metrics(
    client: &mut GraphOpsServiceClient<Channel>,
) -> Result<(), Box<dyn Error>> {
    println!("\n== GetMetrics ==");
    let response = client
        .get_metrics(MetricsRequest { window_seconds: 60 })
        .await?;
    println!("{:?}", response.into_inner());
    Ok(())
}

async fn run_execute_batch(
    client: &mut GraphOpsServiceClient<Channel>,
) -> Result<(), Box<dyn Error>> {
    println!("\n== ExecuteQueryBatch ==");
    let response = client
        .execute_query_batch(CypherBatchRequest {
            queries: vec![
                CypherRequest {
                    query: "MATCH (n:User) RETURN count(n)".to_string(),
                    parameters: Default::default(),
                    timeout_ms: 30_000,
                    trace_id: "graphops-cli-batch-1".to_string(),
                    span_id: String::new(),
                },
                CypherRequest {
                    query: "MATCH (m:Memory) RETURN count(m)".to_string(),
                    parameters: Default::default(),
                    timeout_ms: 30_000,
                    trace_id: "graphops-cli-batch-2".to_string(),
                    span_id: String::new(),
                },
            ],
            fail_fast: false,
            trace_id: "graphops-cli-batch".to_string(),
        })
        .await?;
    println!("{:?}", response.into_inner());
    Ok(())
}
