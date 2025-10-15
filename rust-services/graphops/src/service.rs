// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

use crate::handlers::CypherExecutor;
use crate::metrics::{
    self, RequestTimer, CACHE_HITS_TOTAL, DB_CONNECTIONS_ACTIVE, ERRORS_TOTAL, REQUESTS_TOTAL,
};
use crate::proto::graphops::v1::graph_ops_service_server::GraphOpsService as GraphOpsServiceTrait;
use crate::proto::graphops::v1::{
    ComponentStatus, CypherBatchRequest, CypherBatchResponse, CypherRequest, CypherResponse,
    ErrorDetails, ExecutionStatus, HealthCheckRequest, HealthCheckResponse, HealthStatus,
    MetricsRequest, MetricsResponse, QueryMetrics,
};
use crate::DbPool;
use std::collections::HashMap;
use std::time::{Instant, SystemTime, UNIX_EPOCH};
use tonic::{Request, Response, Status};
use tracing::{error, info};

const RUNTIME_LABEL: &str = "rust";

#[derive(Clone)]
pub struct GraphOpsService {
    pool: DbPool,
    graph_name: String,
    service_start_time: SystemTime,
}

impl GraphOpsService {
    pub fn new(pool: DbPool, graph_name: String) -> Self {
        Self {
            pool,
            graph_name,
            service_start_time: SystemTime::now(),
        }
    }

    async fn execute_single_query(
        &self,
        request: CypherRequest,
        operation: &'static str,
    ) -> Result<CypherResponse, Status> {
        let trimmed_query = request.query.trim().to_string();
        let mut timer = Some(RequestTimer::new());

        if trimmed_query.is_empty() {
            REQUESTS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, operation, "error"])
                .inc();
            ERRORS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, "invalid_argument", operation])
                .inc();
            if let Some(metric_timer) = timer.take() {
                metric_timer.observe();
            }
            return Err(Status::invalid_argument("query must not be empty"));
        }

        if !request.parameters.is_empty() {
            REQUESTS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, operation, "error"])
                .inc();
            ERRORS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, "unimplemented", operation])
                .inc();
            if let Some(metric_timer) = timer.take() {
                metric_timer.observe();
            }
            return Err(Status::unimplemented(
                "parameterised queries are not supported yet",
            ));
        }

        let gauge = DB_CONNECTIONS_ACTIVE.with_label_values(&[RUNTIME_LABEL, "primary"]);

        let client = match self.pool.get_client().await {
            Ok(client) => {
                gauge.inc();
                client
            }
            Err(error) => {
                error!(?error, "failed to obtain database client");
                REQUESTS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, operation, "error"])
                    .inc();
                ERRORS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "connection", operation])
                    .inc();
                if let Some(metric_timer) = timer.take() {
                    metric_timer.observe();
                }
                return Err(Status::unavailable(format!(
                    "database unavailable: {error}"
                )));
            }
        };

        let executor = CypherExecutor::new(self.graph_name.clone(), client);
        let query_start = Instant::now();
        let result = executor.execute_query(&trimmed_query).await;
        gauge.dec();

        match result {
            Ok(rows) => {
                let execution_time_ms = query_start.elapsed().as_millis() as i32;
                let results: Vec<String> = rows.iter().map(|value| value.to_string()).collect();

                REQUESTS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, operation, "success"])
                    .inc();
                CACHE_HITS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "plan_cache"])
                    .inc_by(0);
                if let Some(metric_timer) = timer.take() {
                    metric_timer.observe();
                }

                Ok(CypherResponse {
                    status: ExecutionStatus::Success as i32,
                    results,
                    execution_time_ms,
                    row_count: rows.len() as i32,
                    error: None,
                    metrics: Some(QueryMetrics {
                        parse_time_ms: 0.0, // populated once EXPLAIN integration lands
                        plan_time_ms: 0.0,
                        execution_time_ms: execution_time_ms as f64,
                        rows_scanned: 0,
                        rows_returned: rows.len() as i64,
                        memory_used_bytes: 0,
                        cache_hit: false,
                    }),
                })
            }
            Err(error) => {
                error!(?error, "cypher execution failed");
                REQUESTS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, operation, "error"])
                    .inc();
                ERRORS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "query_execution", operation])
                    .inc();
                if let Some(metric_timer) = timer.take() {
                    metric_timer.observe();
                }
                Err(Status::internal(format!("query failed: {error}")))
            }
        }
    }

    fn status_to_error_details(status: &Status) -> ErrorDetails {
        let mut context = HashMap::new();
        context.insert("status_code".to_string(), status.code().to_string());
        ErrorDetails {
            code: status.code().to_string(),
            message: status.message().to_string(),
            stack_trace: String::new(),
            sql_state: String::new(),
            context,
        }
    }
}

#[tonic::async_trait]
impl GraphOpsServiceTrait for GraphOpsService {
    async fn execute_query(
        &self,
        request: Request<CypherRequest>,
    ) -> Result<Response<CypherResponse>, Status> {
        info!(trace_id = %request.get_ref().trace_id, "ExecuteQuery request");
        let response = self
            .execute_single_query(request.into_inner(), "ExecuteQuery")
            .await?;
        Ok(Response::new(response))
    }

    async fn execute_query_batch(
        &self,
        request: Request<CypherBatchRequest>,
    ) -> Result<Response<CypherBatchResponse>, Status> {
        let payload = request.into_inner();
        info!(
            batch_size = payload.queries.len(),
            trace_id = %payload.trace_id,
            "ExecuteQueryBatch request"
        );

        let mut batch_timer = Some(RequestTimer::new());
        let batch_start = Instant::now();

        let mut responses = Vec::with_capacity(payload.queries.len());
        let mut success_count = 0;
        let mut failure_count = 0;

        for query_request in payload.queries {
            match self
                .execute_single_query(query_request, "ExecuteQuery")
                .await
            {
                Ok(response) => {
                    success_count += 1;
                    responses.push(response);
                }
                Err(status) => {
                    failure_count += 1;
                    responses.push(CypherResponse {
                        status: ExecutionStatus::Error as i32,
                        results: Vec::new(),
                        execution_time_ms: 0,
                        row_count: 0,
                        error: Some(Self::status_to_error_details(&status)),
                        metrics: None,
                    });

                    if payload.fail_fast {
                        break;
                    }
                }
            }
        }

        let batch_status = if failure_count == 0 {
            ExecutionStatus::Success
        } else if success_count == 0 {
            ExecutionStatus::Error
        } else {
            ExecutionStatus::Partial
        };

        // Update aggregated counters
        let status_label = match batch_status {
            ExecutionStatus::Success => "success",
            ExecutionStatus::Error => "error",
            ExecutionStatus::Partial => "partial",
            _ => "unknown",
        };
        REQUESTS_TOTAL
            .with_label_values(&[RUNTIME_LABEL, "ExecuteQueryBatch", status_label])
            .inc();
        CACHE_HITS_TOTAL
            .with_label_values(&[RUNTIME_LABEL, "plan_cache"])
            .inc_by(0);
        if failure_count > 0 {
            ERRORS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, "batch", "ExecuteQueryBatch"])
                .inc();
        }

        if let Some(timer) = batch_timer.take() {
            timer.observe();
        }

        Ok(Response::new(CypherBatchResponse {
            responses,
            batch_status: batch_status as i32,
            total_execution_time_ms: batch_start.elapsed().as_millis() as i32,
            success_count,
            failure_count,
        }))
    }

    async fn health_check(
        &self,
        request: Request<HealthCheckRequest>,
    ) -> Result<Response<HealthCheckResponse>, Status> {
        info!(service = %request.get_ref().service, "HealthCheck request");
        let mut timer = Some(RequestTimer::new());

        let db_status = match self.pool.get_client().await {
            Ok(client) => {
                drop(client);
                REQUESTS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "HealthCheck", "success"])
                    .inc();
                HealthStatus::Healthy
            }
            Err(error) => {
                error!(?error, "health check database connection failed");
                REQUESTS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "HealthCheck", "error"])
                    .inc();
                ERRORS_TOTAL
                    .with_label_values(&[RUNTIME_LABEL, "connection", "HealthCheck"])
                    .inc();
                if let Some(metric_timer) = timer.take() {
                    metric_timer.observe();
                }
                return Err(Status::unavailable(format!(
                    "database health check failed: {error}"
                )));
            }
        };

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;

        let response = HealthCheckResponse {
            status: db_status as i32,
            database: Some(ComponentStatus {
                name: "database".to_string(),
                status: db_status as i32,
                error_message: String::new(),
                last_check_timestamp: now,
            }),
            age_extension: Some(ComponentStatus {
                name: "age_extension".to_string(),
                status: HealthStatus::Healthy as i32,
                error_message: String::new(),
                last_check_timestamp: now,
            }),
            uptime_seconds: SystemTime::now()
                .duration_since(self.service_start_time)
                .unwrap()
                .as_secs() as i64,
            version: env!("CARGO_PKG_VERSION").to_string(),
            details: HashMap::new(),
        };

        if let Some(metric_timer) = timer.take() {
            metric_timer.observe();
        }
        Ok(Response::new(response))
    }

    async fn get_metrics(
        &self,
        _request: Request<MetricsRequest>,
    ) -> Result<Response<MetricsResponse>, Status> {
        info!("GetMetrics request");
        let mut timer = Some(RequestTimer::new());

        metrics::update_memory_metrics();

        let total_success = REQUESTS_TOTAL
            .with_label_values(&[RUNTIME_LABEL, "ExecuteQuery", "success"])
            .get()
            + REQUESTS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, "ExecuteQueryBatch", "success"])
                .get();

        let total_errors = REQUESTS_TOTAL
            .with_label_values(&[RUNTIME_LABEL, "ExecuteQuery", "error"])
            .get()
            + REQUESTS_TOTAL
                .with_label_values(&[RUNTIME_LABEL, "ExecuteQueryBatch", "error"])
                .get();

        let memory_usage = metrics::get_memory_usage() as i64;
        let active_connections = DB_CONNECTIONS_ACTIVE
            .with_label_values(&[RUNTIME_LABEL, "primary"])
            .get() as i32;

        let response = MetricsResponse {
            total_queries: (total_success + total_errors) as i64,
            successful_queries: total_success as i64,
            failed_queries: total_errors as i64,
            p50_latency_ms: 0.0, // TODO: derive from histogram once histogram quantiles wired in
            p95_latency_ms: 0.0,
            p99_latency_ms: 0.0,
            avg_execution_time_ms: 0.0,
            memory_usage_bytes: memory_usage,
            active_connections,
        };

        REQUESTS_TOTAL
            .with_label_values(&[RUNTIME_LABEL, "GetMetrics", "success"])
            .inc();
        if let Some(metric_timer) = timer.take() {
            metric_timer.observe();
        }

        Ok(Response::new(response))
    }
}
