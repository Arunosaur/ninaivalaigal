package main

import (
	"fmt"
	"os"
	"strings"
)

var (
	// GatewayHost is the address the HTTP server binds to (default 0.0.0.0).
	GatewayHost string
	// GatewayPort is the port portion (prefixed with :) used by ListenAndServe.
	GatewayPort string
	// GatewayAddr is the host:port combination used by the HTTP server.
	GatewayAddr string
	// GatewayPublicHost is the advertised host for curl samples.
	GatewayPublicHost string
	// GatewayPublicPort is the advertised public port value.
	GatewayPublicPort string
	// GatewayPublicURL is the friendly URL shown in logs and docs.
	GatewayPublicURL string
	// CoreAPIAddr is the upstream HTTP endpoint for the core API.
	CoreAPIAddr string
	// MemoryAddr is the upstream HTTP endpoint for the memory service (HTTP/REST, not gRPC).
	MemoryAddr string
	// GraphOpsAddr is the upstream gRPC endpoint for GraphOps.
	GraphOpsAddr string
)

func init() {
	GatewayHost = getEnv("GATEWAY_HOST", "0.0.0.0")
	// Standard: gRPC gateway binds to canonical port 13395 inside container
	// See: config/ports.nv.yaml and docs/standards/CONTAINERIZATION_STANDARD.md
	port := sanitizePort(getEnv("GATEWAY_PORT", "13395"))
	GatewayPort = ":" + port
	GatewayAddr = fmt.Sprintf("%s:%s", GatewayHost, port)

	GatewayPublicHost = getEnv("GATEWAY_PUBLIC_HOST", "localhost")
	GatewayPublicPort = sanitizePort(getEnv("GATEWAY_PUBLIC_PORT", "13395"))
	GatewayPublicURL = fmt.Sprintf("http://%s:%s", GatewayPublicHost, GatewayPublicPort)

	CoreAPIAddr = getEnv("CORE_API_ADDR", "localhost:13390")
	MemoryAddr = getEnv("MEMORY_SERVICE_ADDR", "localhost:13393")
	GraphOpsAddr = getEnv("GRAPHOPS_SERVICE_ADDR", "localhost:50051")
}

func getEnv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func sanitizePort(port string) string {
	trimmed := strings.TrimSpace(port)
	trimmed = strings.TrimPrefix(trimmed, ":")
	if trimmed == "" {
		return "13395"
	}
	return trimmed
}
