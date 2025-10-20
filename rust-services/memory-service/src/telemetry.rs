// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// OpenTelemetry Distributed Tracing for Rust Services
// Task #84: Implement OpenTelemetry Distributed Tracing

use opentelemetry::global;
use opentelemetry::KeyValue;
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::runtime;
use opentelemetry_sdk::Resource;
use tracing_subscriber::fmt;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::EnvFilter;

/// Initialize OpenTelemetry distributed tracing for Rust services
///
/// # Arguments
/// * `service_name` - Name of the service for identification in traces
/// * `jaeger_endpoint` - OTLP gRPC endpoint (e.g., "http://localhost:4317")
///
/// # Example
/// ```
/// init_tracing("ninaivalaigal-graphops", "http://localhost:4317")?;
/// ```
pub fn init_tracing(
    service_name: &str,
    jaeger_endpoint: Option<&str>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let endpoint = jaeger_endpoint.unwrap_or("http://localhost:4317");

    // Create OTLP exporter
    let exporter = opentelemetry_otlp::new_exporter()
        .tonic()
        .with_endpoint(endpoint);

    // Build tracer provider with resource attributes
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(exporter)
        .with_trace_config(
            opentelemetry_sdk::trace::config().with_resource(Resource::new(vec![
                KeyValue::new("service.name", service_name.to_string()),
                KeyValue::new("service.namespace", "ninaivalaigal"),
                KeyValue::new("deployment.environment", get_environment()),
            ])),
        )
        .install_batch(runtime::Tokio)?;

    // Create OpenTelemetry tracing layer
    let telemetry_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    // Create env filter (defaults to INFO)
    let env_filter = EnvFilter::try_from_default_env()
        .or_else(|_| EnvFilter::try_new("info"))
        .unwrap();

    // Create formatting layer with JSON output
    let fmt_layer = fmt::layer()
        .json()
        .with_target(true)
        .with_thread_ids(true)
        .with_level(true);

    // Combine layers
    tracing_subscriber::registry()
        .with(env_filter)
        .with(telemetry_layer)
        .with(fmt_layer)
        .try_init()?;

    tracing::info!(
        service = service_name,
        endpoint = endpoint,
        "✅ OpenTelemetry tracing initialized"
    );

    Ok(())
}

/// Shutdown OpenTelemetry gracefully
pub fn shutdown_tracing() {
    global::shutdown_tracer_provider();
}

/// Get deployment environment from env var or default to "development"
fn get_environment() -> String {
    std::env::var("ENVIRONMENT").unwrap_or_else(|_| "development".to_string())
}

/// Initialize simple tracing without OpenTelemetry (fallback)
pub fn init_simple_tracing() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let fmt_layer = fmt::layer().json().with_target(true);

    let env_filter = EnvFilter::try_from_default_env()
        .or_else(|_| EnvFilter::try_new("info"))
        .unwrap();

    tracing_subscriber::registry()
        .with(env_filter)
        .with(fmt_layer)
        .try_init()?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_environment() {
        let env = get_environment();
        assert!(!env.is_empty());
    }
}
