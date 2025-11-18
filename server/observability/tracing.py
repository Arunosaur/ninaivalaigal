#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# OpenTelemetry Distributed Tracing Configuration
# Task #84: Implement OpenTelemetry Distributed Tracing
"""
OpenTelemetry distributed tracing configuration for FastAPI services.

This module provides automatic instrumentation for FastAPI applications with:
- OTLP exporter for Jaeger
- FastAPI endpoint tracing
- HTTP client instrumentation (HTTPX)
- Database instrumentation (PostgreSQL via psycopg2)
- Redis cache instrumentation
- W3C trace context propagation
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for OpenTelemetry tracing"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        jaeger_endpoint: str = "http://localhost:14317",  # Updated to use OTEL collector
        enable_console_export: bool = False,
        sample_rate: float = 1.0,
    ):
        """Initialize tracing configuration.

        Args:
            service_name: Name of the service for identification in traces
            service_version: Version of the service
            jaeger_endpoint: OTLP gRPC endpoint for Jaeger
            enable_console_export: Enable console output for debugging
            sample_rate: Sampling rate (0.0-1.0)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.jaeger_endpoint = jaeger_endpoint
        self.enable_console_export = enable_console_export
        self.sample_rate = sample_rate


def init_tracing(
    app: FastAPI,
    config: Optional[TracingConfig] = None,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry distributed tracing for FastAPI application

    Args:
        app: FastAPI application instance
        config: Tracing configuration (optional)

    Returns:
        Tracer instance for manual instrumentation

    Example:
        ```python
        from fastapi import FastAPI
        from observability.tracing import init_tracing, TracingConfig

        app = FastAPI()

        # Initialize tracing
        config = TracingConfig(
            service_name="ninaivalaigal-core-api",
            service_version="1.0.0"
        )
        tracer = init_tracing(app, config)
        ```
    """
    # Use default config if not provided
    if config is None:
        service_name = os.getenv("OTEL_SERVICE_NAME", "ninaivalaigal-api")
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:14317")
        config = TracingConfig(service_name=service_name, jaeger_endpoint=otlp_endpoint)

    # Create resource with service information
    resource = Resource(
        attributes={
            SERVICE_NAME: config.service_name,
            SERVICE_VERSION: config.service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            "service.namespace": "ninaivalaigal",
        }
    )

    # Create tracer provider with resource
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter for Jaeger
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=config.jaeger_endpoint,
            insecure=True,  # Use insecure for local development
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Configured OTLP exporter for {config.service_name} -> {config.jaeger_endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure OTLP exporter: {e}")
        logger.warning("Tracing will be disabled")

    # Optional console exporter for debugging
    if config.enable_console_export:
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console span exporter enabled for debugging")

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Get tracer for manual instrumentation
    tracer = trace.get_tracer(__name__)

    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    logger.info(f"FastAPI instrumentation enabled for {config.service_name}")

    # Instrument HTTP clients
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX client instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")

    # Instrument PostgreSQL
    try:
        Psycopg2Instrumentor().instrument()
        logger.info("PostgreSQL (psycopg2) instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument psycopg2: {e}")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")

    logger.info(
        f"✅ OpenTelemetry tracing initialized for {config.service_name} " f"(endpoint: {config.jaeger_endpoint})"
    )

    return tracer


def get_current_span() -> Optional[trace.Span]:
    """Get the current active span for manual instrumentation"""
    return trace.get_current_span()


def add_span_attribute(key: str, value: any) -> None:
    """Add attribute to current span"""
    span = get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[dict] = None) -> None:
    """Add event to current span"""
    span = get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes=attributes or {})


def record_exception(exception: Exception) -> None:
    """Record exception in current span"""
    span = get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# Example usage in endpoints:
"""
from observability.tracing import add_span_attribute, add_span_event, record_exception

@app.get("/api/memory/{memory_id}")
async def get_memory(memory_id: str):
    # Add custom attributes
    add_span_attribute("memory.id", memory_id)
    add_span_attribute("user.id", current_user_id)

    try:
        memory = await db.get_memory(memory_id)
        add_span_event("memory.retrieved", {"size": len(memory.content)})
        return memory
    except Exception as e:
        record_exception(e)
        raise
"""
