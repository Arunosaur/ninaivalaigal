package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/arunosaur/ninaivalaigal/grpc-gateway/tracing"
	"github.com/gorilla/mux"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"google.golang.org/grpc"
)

type Gateway struct {
	router    *mux.Router
	grpcConns map[string]*grpc.ClientConn
}

func NewGateway() *Gateway {
	gw := &Gateway{
		router:    mux.NewRouter(),
		grpcConns: make(map[string]*grpc.ClientConn),
	}

	gw.setupRoutes()
	return gw
}

func (gw *Gateway) setupRoutes() {
	// Health check endpoint
	gw.router.HandleFunc("/health", gw.healthHandler).Methods("GET")

	// API v1 routes - translate REST to gRPC
	api := gw.router.PathPrefix("/api/v1").Subrouter()

	// Memory service routes
	api.HandleFunc("/memory/remember", gw.memoryRememberHandler).Methods("POST")
	api.HandleFunc("/memory/recall", gw.memoryRecallHandler).Methods("GET")
	api.HandleFunc("/memory/memories", gw.memoryListHandler).Methods("GET")

	// GraphOps service routes
	api.HandleFunc("/graph/query", gw.graphQueryHandler).Methods("POST")
	api.HandleFunc("/graph/health", gw.graphHealthHandler).Methods("GET")

	// Core API proxy routes (direct HTTP for now, will migrate to gRPC later)
	api.HandleFunc("/users/me", gw.coreAPIProxy).Methods("GET", "PATCH")
	api.HandleFunc("/auth/login", gw.coreAPIProxy).Methods("POST")

	// Add CORS middleware
	gw.router.Use(corsMiddleware)
	gw.router.Use(loggingMiddleware)
}

func (gw *Gateway) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := fmt.Fprintf(w, `{
		"status": "healthy",
		"service": "grpc-gateway",
		"version": "1.0.0",
		"timestamp": "%s",
		"connections": {
			"memory_service": "%s",
			"graphops_service": "%s",
			"core_api": "%s"
		}
	}`, time.Now().UTC().Format(time.RFC3339), MemoryAddr, GraphOpsAddr, CoreAPIAddr); err != nil {
		log.Printf("⚠️ Failed to write health response: %v", err)
	}
}

// Placeholder handlers - will implement gRPC calls
func (gw *Gateway) memoryRememberHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gRPC call to memory service
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "Memory service gRPC integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

func (gw *Gateway) memoryRecallHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gRPC call to memory service
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "Memory service gRPC integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

func (gw *Gateway) memoryListHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gRPC call to memory service
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "Memory service gRPC integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

func (gw *Gateway) graphQueryHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gRPC call to graphops service
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "GraphOps service gRPC integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

func (gw *Gateway) graphHealthHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gRPC call to GraphOps service
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "GraphOps service gRPC integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

func (gw *Gateway) coreAPIProxy(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement HTTP proxy to Core API (temporary until gRPC migration)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	if _, err := fmt.Fprintf(w, `{"error": "Core API proxy integration pending", "task": "Developer A Task #36"}`); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
	}
}

// Middleware
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
		w.Header().Set("Access-Control-Allow-Headers", "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("[%s] %s %s %v", r.Method, r.URL.Path, r.RemoteAddr, time.Since(start))
	})
}

func main() {
	log.Println("🚀 Starting gRPC Gateway for ninaivalaigal")

	// Initialize distributed tracing (Task #84)
	serviceName := os.Getenv("OTEL_SERVICE_NAME")
	if serviceName == "" {
		serviceName = "ninaivalaigal-grpc-gateway"
	}
	jaegerEndpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if jaegerEndpoint == "" {
		jaegerEndpoint = "localhost:4317"
	}
	tracingEnabled := os.Getenv("OTEL_TRACING_ENABLED")
	if tracingEnabled == "" {
		tracingEnabled = "true"
	}

	var cleanupTracing func()
	if tracingEnabled == "true" {
		var err error
		cleanupTracing, err = tracing.InitTracing(serviceName, jaegerEndpoint)
		if err != nil {
			log.Printf("⚠️  Failed to initialize OpenTelemetry tracing: %v", err)
			log.Println("ℹ️  Continuing without distributed tracing")
		} else {
			defer cleanupTracing()
		}
	}

	log.Printf("📡 Gateway will listen on %s", GatewayAddr)
	log.Printf("🌐 External access via %s", GatewayPublicURL)
	log.Printf("🔗 Backend services: Memory=%s, GraphOps=%s, CoreAPI=%s",
		MemoryAddr, GraphOpsAddr, CoreAPIAddr)

	// Initialize gRPC clients
	grpcClients, err := NewGRPCClients()
	if err != nil {
		log.Printf("⚠️  Failed to initialize gRPC clients: %v", err)
		log.Println("📡 Starting gateway without gRPC integration (development mode)")
	}

	gateway := NewGateway()
	enhancedGateway := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: grpcClients,
	}

	// Update handlers to use enhanced versions
	if grpcClients != nil {
		gateway.router.HandleFunc("/health", enhancedGateway.enhancedHealthHandler).Methods("GET")
		api := gateway.router.PathPrefix("/api/v1").Subrouter()
		api.HandleFunc("/memory/remember", enhancedGateway.memoryRememberHandler).Methods("POST")
		api.HandleFunc("/memory/recall", enhancedGateway.memoryRecallHandler).Methods("GET")
		api.HandleFunc("/graph/query", enhancedGateway.graphQueryHandler).Methods("POST")
		log.Println("✅ Enhanced handlers with gRPC integration enabled")
	}

	// Wrap router with OpenTelemetry HTTP instrumentation (Task #84)
	var handler http.Handler = gateway.router
	if cleanupTracing != nil {
		handler = otelhttp.NewHandler(gateway.router, "grpc-gateway")
	}

	server := &http.Server{
		Addr:         GatewayAddr,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Printf("✅ gRPC Gateway started on %s", GatewayAddr)
		log.Printf("🏥 Health check: curl %s/health", GatewayPublicURL)

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("❌ Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("🛑 Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Close gRPC connections
	if enhancedGateway.grpcClients != nil {
		enhancedGateway.grpcClients.Close()
	}
	for service, conn := range gateway.grpcConns {
		log.Printf("🔌 Closing gRPC connection to %s", service)
		if err := conn.Close(); err != nil {
			log.Printf("⚠️ Failed to close connection to %s: %v", service, err)
		}
	}

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("❌ Server forced to shutdown: %v", err)
	}

	log.Println("✅ Server gracefully stopped")
}
