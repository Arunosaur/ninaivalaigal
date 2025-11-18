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
	"github.com/prometheus/client_golang/prometheus/promhttp"
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

	// Prometheus metrics endpoint
	gw.router.Handle("/metrics", promhttp.Handler()).Methods("GET")

	// API v1 routes - translate REST to gRPC
	api := gw.router.PathPrefix("/api/v1").Subrouter()

	// Memory service routes
	// Memory service routes (handled by enhanced gateway)
	// These will be set up below if gRPC clients are available

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
			"graph_service": "%s",
			"core_api": "%s"
		}
	}`, time.Now().UTC().Format(time.RFC3339), MemoryAddr, GraphOpsAddr, GraphServiceAddr, CoreAPIAddr); err != nil {
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

	// Load YAML configuration file if specified
	configFile := os.Getenv("GATEWAY_CONFIG_FILE")
	var yamlConfig *GatewayConfig

	// Try to find config file if not explicitly specified
	if configFile == "" {
		if fileExists("./gateway.yaml") {
			configFile = "./gateway.yaml"
		} else if fileExists("./config/gateway.yaml") {
			configFile = "./config/gateway.yaml"
		}
	}

	if configFile != "" {
		var err error
		yamlConfig, err = LoadConfigFromFile(configFile)
		if err != nil {
			log.Printf("⚠️  Failed to load YAML config: %v", err)
			log.Println("ℹ️  Continuing with environment variable configuration")
		} else {
			log.Printf("✅ Loaded configuration from YAML file: %s", configFile)
			// Apply YAML config to global variables
			if err := yamlConfig.ApplyConfig(); err != nil {
				log.Printf("⚠️  Failed to apply YAML config: %v", err)
			} else {
				log.Printf("📋 Gateway mode: %s", yamlConfig.Gateway.Mode)
			}
		}
	} else {
		log.Println("ℹ️  No YAML config file found, using environment variables")
	}

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
		Gateway:           gateway,
		grpcClients:       grpcClients,
		config:            yamlConfig, // Store config for protocol detection
		translator:        nil,        // Will be initialized below
		circuitBreakerMgr: nil,        // Will be initialized below
	}

	// Initialize protocol translator
	enhancedGateway.translator = NewProtocolTranslator(enhancedGateway)

	// Initialize circuit breaker manager
	if yamlConfig != nil && yamlConfig.CircuitBreaker.Enabled {
		enhancedGateway.circuitBreakerMgr = NewCircuitBreakerManager(yamlConfig)
		log.Println("✅ Circuit breaker manager initialized")
	}

	// Initialize rate limiting middleware
	var rateLimitMiddleware *RateLimitMiddleware
	if yamlConfig != nil && yamlConfig.RateLimit.Enabled {
		rateLimitMiddleware = NewRateLimitMiddleware(yamlConfig)
		if rateLimitMiddleware != nil {
			log.Println("✅ Rate limiting middleware initialized")
		}
	} else {
		log.Println("ℹ️  Rate limiting middleware disabled")
	}

	// Initialize authentication middleware
	var authMiddleware *AuthMiddleware
	if yamlConfig != nil {
		authMiddleware = NewAuthMiddleware(yamlConfig)
		log.Println("✅ Authentication middleware initialized")
	}

	// Initialize cache
	var cache *Cache
	var cacheMiddleware *CacheMiddleware
	if yamlConfig != nil && yamlConfig.Cache.Enabled {
		cacheConfig := buildCacheConfig(yamlConfig)
		var err error
		cache, err = NewCache(cacheConfig)
		if err != nil {
			log.Printf("⚠️  Failed to initialize cache: %v", err)
			log.Println("ℹ️  Continuing without caching")
		} else {
			cacheMiddleware = NewCacheMiddleware(cache)
			log.Println("✅ Cache middleware initialized")
		}
	} else {
		log.Println("ℹ️  Cache middleware disabled")
	}

	// Initialize transformation middleware
	var transformationMiddleware *TransformationMiddleware
	if yamlConfig != nil && yamlConfig.Transformation.Enabled {
		transformationMiddleware = NewTransformationMiddleware(&yamlConfig.Transformation)
		if transformationMiddleware != nil {
			log.Println("✅ Transformation middleware initialized")
		}
	} else {
		log.Println("ℹ️  Transformation middleware disabled")
	}

	// Initialize WAF middleware
	var wafMiddleware *WAFMiddleware
	if yamlConfig != nil && yamlConfig.WAF.Enabled {
		wafMiddleware = NewWAFMiddleware(&yamlConfig.WAF)
		if wafMiddleware != nil {
			log.Println("✅ WAF middleware initialized")
		}
	} else {
		log.Println("ℹ️  WAF middleware disabled")
	}

	// Apply middleware to router (order matters: waf -> cache -> transformation -> auth -> rate limit)
	// WAF should run first to block malicious requests early
	// Transformation should run early to modify requests/responses
	// Auth must run before rate limit so user ID is available for per-user rate limiting
	if wafMiddleware != nil {
		gateway.router.Use(wafMiddleware.Middleware)
	}
	if cacheMiddleware != nil {
		gateway.router.Use(cacheMiddleware.Middleware)
	}
	if transformationMiddleware != nil {
		gateway.router.Use(transformationMiddleware.Middleware)
	}
	if authMiddleware != nil {
		gateway.router.Use(authMiddleware.Middleware)
	}
	if rateLimitMiddleware != nil {
		gateway.router.Use(rateLimitMiddleware.Middleware)
	}

	// Register enhanced handlers - always register routes, handlers will use REST proxy if gRPC unavailable
	// Enhanced handlers support both REST proxy and gRPC translation based on backend protocol
	gateway.router.HandleFunc("/health", enhancedGateway.enhancedHealthHandler).Methods("GET")
	api := gateway.router.PathPrefix("/api/v1").Subrouter()
	// Memory service routes - handlers support REST proxy and gRPC translation
	api.HandleFunc("/memory/remember", enhancedGateway.memoryRememberHandler).Methods("POST")
	api.HandleFunc("/memory/recall", enhancedGateway.memoryRecallHandler).Methods("GET")
	api.HandleFunc("/memory/memories", enhancedGateway.memoryListHandler).Methods("GET")
	// GraphOps service routes - always register, handlers will return proper errors if gRPC unavailable
	api.HandleFunc("/graph/query", enhancedGateway.graphQueryHandler).Methods("POST")
	api.HandleFunc("/graph/health", enhancedGateway.graphHealthHandler).Methods("GET")
	if grpcClients != nil && grpcClients.GraphOpsClient != nil {
		log.Println("✅ GraphOps gRPC routes registered (gRPC clients available)")
	} else {
		log.Println("✅ GraphOps routes registered (will return errors if gRPC clients unavailable)")
	}
	// Graph/AI Service HTTP proxy routes - proxy all /api/v1/graph/* requests to Graph Service
	api.PathPrefix("/graph").HandlerFunc(enhancedGateway.graphServiceProxy)
	log.Println("✅ Graph/AI Service HTTP proxy routes registered")
	// Core API proxy routes - always use HTTP proxy
	api.HandleFunc("/users/me", enhancedGateway.coreAPIProxy).Methods("GET", "PATCH")
	api.HandleFunc("/auth/login", enhancedGateway.coreAPIProxy).Methods("POST")

	if grpcClients != nil {
		log.Println("✅ Enhanced handlers with gRPC integration enabled")
	} else {
		log.Println("✅ Enhanced handlers registered (REST proxy mode - gRPC clients unavailable)")
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

	// Close cache connection
	if cache != nil {
		if err := cache.Close(); err != nil {
			log.Printf("⚠️  Failed to close cache connection: %v", err)
		} else {
			log.Println("🔌 Cache connection closed")
		}
	}

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

// fileExists checks if a file exists
func fileExists(filename string) bool {
	info, err := os.Stat(filename)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}
