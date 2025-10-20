// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 Medhasys LLC
//
// OpenTelemetry Distributed Tracing for Go Services
// Task #84: Implement OpenTelemetry Distributed Tracing

package tracing

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.20.0"
)

// InitTracing initializes OpenTelemetry distributed tracing for Go services
//
// Parameters:
//   - serviceName: Name of the service for identification in traces
//   - jaegerEndpoint: OTLP gRPC endpoint (e.g., "localhost:4317")
//
// Returns:
//   - Cleanup function to call on shutdown
//   - Error if initialization fails
//
// Example:
//
//	cleanup, err := tracing.InitTracing("ninaivalaigal-grpc-gateway", "localhost:4317")
//	if err != nil {
//	    log.Fatal(err)
//	}
//	defer cleanup()
func InitTracing(serviceName, jaegerEndpoint string) (func(), error) {
	ctx := context.Background()

	// Create OTLP gRPC exporter
	exporter, err := otlptracegrpc.New(
		ctx,
		otlptracegrpc.WithEndpoint(jaegerEndpoint),
		otlptracegrpc.WithInsecure(), // Use TLS in production
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
	}

	// Create resource with service information
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
			semconv.ServiceNamespace("ninaivalaigal"),
			attribute.String("deployment.environment", getEnvironment()),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	// Create tracer provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
	)

	// Set global tracer provider
	otel.SetTracerProvider(tp)

	// Set global propagator for context propagation (W3C Trace Context)
	otel.SetTextMapPropagator(
		propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		),
	)

	log.Printf("✅ OpenTelemetry tracing initialized: %s -> %s\n", serviceName, jaegerEndpoint)

	// Return cleanup function
	return func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := tp.Shutdown(ctx); err != nil {
			log.Printf("⚠️  Error shutting down tracer provider: %v\n", err)
		}
	}, nil
}

// getEnvironment returns the deployment environment from env var or defaults to "development"
func getEnvironment() string {
	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		return "development"
	}
	return env
}
