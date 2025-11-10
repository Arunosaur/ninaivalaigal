package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	graphopsv1 "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto"
	memorypb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/memorypb"
)

// Enhanced Gateway with gRPC clients
type EnhancedGateway struct {
	*Gateway
	grpcClients       *GRPCClients
	config            *GatewayConfig         // YAML configuration
	translator        *ProtocolTranslator    // Protocol translation layer
	circuitBreakerMgr *CircuitBreakerManager // Circuit breaker manager
}

// Request/Response types for REST API
type MemoryRememberRequest struct {
	Content  string            `json:"content"`
	Context  string            `json:"context"`
	Metadata map[string]string `json:"metadata"`
}

type MemoryRememberResponse struct {
	MemoryID  string `json:"memory_id"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

type MemoryRecallRequest struct {
	Query     string  `json:"query"`
	Limit     int     `json:"limit"`
	Threshold float32 `json:"threshold"`
}

type MemoryRecallResponse struct {
	Memories   []MemoryItem `json:"memories"`
	TotalCount int          `json:"total_count"`
}

type MemoryItem struct {
	ID             string            `json:"id"`
	Content        string            `json:"content"`
	Context        string            `json:"context"`
	Metadata       map[string]string `json:"metadata"`
	CreatedAt      string            `json:"created_at"`
	UpdatedAt      string            `json:"updated_at"`
	RelevanceScore float32           `json:"relevance_score,omitempty"`
}

type GraphQueryRequest struct {
	Query      string            `json:"query"`
	Parameters map[string]string `json:"parameters"`
	TimeoutMs  int               `json:"timeout_ms"`
}

type GraphQueryResponse struct {
	Results  []QueryResult `json:"results"`
	Metadata QueryMeta     `json:"metadata"`
	Status   string        `json:"status"`
}

type QueryResult struct {
	Columns []QueryColumn `json:"columns"`
	Rows    []QueryRow    `json:"rows"`
}

type QueryColumn struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type QueryRow struct {
	Values []interface{} `json:"values"`
}

type QueryMeta struct {
	RowsAffected    int      `json:"rows_affected"`
	ExecutionTimeMs int      `json:"execution_time_ms"`
	QueryPlan       string   `json:"query_plan,omitempty"`
	Warnings        []string `json:"warnings,omitempty"`
}

// Enhanced handlers with actual gRPC integration
func (gw *EnhancedGateway) memoryRememberHandler(w http.ResponseWriter, r *http.Request) {
	// Check gateway mode and protocol
	backendProtocol := gw.GetBackendProtocol("memory")

	// If backend is REST, use HTTP proxy
	if backendProtocol == "rest" {
		memoryURL := fmt.Sprintf("http://%s/memory/remember", MemoryAddr)
		gw.translator.ProxyRESTRequest(w, r, memoryURL)
		return
	}

	// If backend is gRPC, use translation
	if backendProtocol == "grpc" && gw.grpcClients != nil && gw.grpcClients.MemoryClient != nil {
		gw.translator.TranslateRESTToGRPC(
			w, r, "memory",
			func(ctx context.Context, req interface{}) (interface{}, error) {
				grpcReq := req.(*memorypb.RememberRequest)
				return gw.grpcClients.MemoryClient.Remember(ctx, grpcReq)
			},
			ConvertMemoryRememberRESTToGRPC,
			ConvertMemoryRememberGRPCToREST,
		)
		return
	}

	// Fallback: HTTP proxy (if translator not available)
	memoryURL := fmt.Sprintf("http://%s/api/v1/memories", MemoryAddr)
	if gw.translator != nil {
		gw.translator.ProxyRESTRequest(w, r, memoryURL)
	} else {
		http.Error(w, `{"error": "Protocol translation not available"}`, http.StatusServiceUnavailable)
	}
}

func (gw *EnhancedGateway) memoryRecallHandler(w http.ResponseWriter, r *http.Request) {
	backendProtocol := gw.GetBackendProtocol("memory")

	// If backend is REST, use HTTP proxy
	if backendProtocol == "rest" {
		memoryURL := fmt.Sprintf("http://%s/api/v1/memories", MemoryAddr) // Note: recall uses query params
		gw.translator.ProxyRESTRequest(w, r, memoryURL)
		return
	}

	// If backend is gRPC, use translation
	if backendProtocol == "grpc" && gw.grpcClients != nil && gw.grpcClients.MemoryClient != nil {
		gw.translator.TranslateRESTToGRPC(
			w, r, "memory",
			func(ctx context.Context, req interface{}) (interface{}, error) {
				grpcReq := req.(*memorypb.RecallRequest)
				return gw.grpcClients.MemoryClient.Recall(ctx, grpcReq)
			},
			ConvertMemoryRecallRESTToGRPC,
			ConvertMemoryRecallGRPCToREST,
		)
		return
	}

	// Fallback: HTTP proxy
	memoryURL := fmt.Sprintf("http://%s/api/v1/memories", MemoryAddr) // Note: recall uses query params
	if gw.translator != nil {
		gw.translator.ProxyRESTRequest(w, r, memoryURL)
	} else {
		http.Error(w, `{"error": "Protocol translation not available"}`, http.StatusServiceUnavailable)
	}
}

func (gw *EnhancedGateway) graphQueryHandler(w http.ResponseWriter, r *http.Request) {
	backendProtocol := gw.GetBackendProtocol("graphops")

	// GraphOps is always gRPC, use translation
	if backendProtocol == "grpc" && gw.grpcClients != nil && gw.grpcClients.GraphOpsClient != nil {
		gw.translator.TranslateRESTToGRPC(
			w, r, "graphops",
			func(ctx context.Context, req interface{}) (interface{}, error) {
				grpcReq := req.(*graphopsv1.CypherRequest)
				return gw.grpcClients.GraphOpsClient.ExecuteQuery(ctx, grpcReq)
			},
			ConvertGraphQueryRESTToGRPC,
			ConvertGraphQueryGRPCToREST,
		)
		return
	}

	// Fallback: error if gRPC not available
	http.Error(w, `{"error": "GraphOps service not available"}`, http.StatusServiceUnavailable)
}

// Graph/AI Service HTTP proxy handler
func (gw *EnhancedGateway) graphServiceProxy(w http.ResponseWriter, r *http.Request) {
	// Graph/AI Service is HTTP/REST - proxy HTTP request
	// Remove /api/v1/graph prefix and forward to Graph Service
	path := r.URL.Path
	// Remove /api/v1/graph prefix if present
	if strings.HasPrefix(path, "/api/v1/graph") {
		path = strings.TrimPrefix(path, "/api/v1/graph")
		if path == "" {
			path = "/"
		}
	}

	// Construct target URL
	targetURL := fmt.Sprintf("http://%s/api/v1/graph%s", GraphServiceAddr, path)
	if r.URL.RawQuery != "" {
		targetURL += "?" + r.URL.RawQuery
	}

	// Create HTTP request
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	httpReq, err := http.NewRequestWithContext(ctx, r.Method, targetURL, r.Body)
	if err != nil {
		log.Printf("⚠️ Failed to create Graph Service proxy request: %v", err)
		http.Error(w, fmt.Sprintf(`{"error": "Failed to create proxy request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Copy headers from original request
	for key, values := range r.Header {
		for _, value := range values {
			httpReq.Header.Add(key, value)
		}
	}

	// Execute HTTP request
	httpClient := &http.Client{Timeout: 30 * time.Second}
	httpResp, err := httpClient.Do(httpReq)
	if err != nil {
		log.Printf("⚠️ Graph Service proxy error: %v", err)
		http.Error(w, fmt.Sprintf(`{"error": "Graph Service proxy error: %s"}`, err.Error()),
			http.StatusBadGateway)
		return
	}
	defer func() {
		if err := httpResp.Body.Close(); err != nil {
			log.Printf("⚠️ Failed to close Graph Service response body: %v", err)
		}
	}()

	// Copy response headers
	for key, values := range httpResp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Copy status code and body
	w.WriteHeader(httpResp.StatusCode)
	if _, err := io.Copy(w, httpResp.Body); err != nil {
		log.Printf("⚠️ Failed to copy Graph Service response body: %v", err)
	}
}

// Extract user ID from JWT token (placeholder implementation)
func (gw *EnhancedGateway) extractUserID(r *http.Request) string {
	// TODO: Implement JWT token validation
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}

	// For now, extract from Bearer token (placeholder)
	if strings.HasPrefix(authHeader, "Bearer ") {
		token := strings.TrimPrefix(authHeader, "Bearer ")
		token = strings.TrimSpace(token)
		// Return empty if token is empty
		if token == "" {
			return ""
		}
		// In real implementation, decode and validate JWT
		return "user-123" // placeholder user ID
	}

	return ""
}

// Enhanced health handler with gRPC connection status
func (gw *EnhancedGateway) enhancedHealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	status := "healthy"
	statusCode := http.StatusOK

	// Check gRPC connections if available
	var connections map[string]string
	if gw.grpcClients != nil {
		connections = gw.grpcClients.GetConnectionStatus()

		// Check if any connections are down
		for _, connStatus := range connections {
			if strings.Contains(connStatus, "disconnected") ||
				strings.Contains(connStatus, "TRANSIENT_FAILURE") {
				status = "degraded"
				statusCode = http.StatusServiceUnavailable
			}
		}
	} else {
		connections = map[string]string{
			"memory_service":   "not_initialized",
			"graphops_service": "not_initialized",
		}
		status = "initializing"
	}

	w.WriteHeader(statusCode)
	if _, err := fmt.Fprintf(w, `{
		"status": "%s",
		"service": "grpc-gateway",
		"version": "1.0.0",
		"timestamp": "%s",
		"connections": %s,
		"grpc_integration": "Complete - Developer F"
	}`, status, time.Now().UTC().Format(time.RFC3339), toJSON(connections)); err != nil {
		log.Printf("⚠️ Failed to write health response: %v", err)
	}
}

// Helper function to convert map to JSON
func toJSON(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}

// Memory list handler - List all memories for a user
func (gw *EnhancedGateway) memoryListHandler(w http.ResponseWriter, r *http.Request) {
	userID := gw.extractUserID(r)
	if userID == "" {
		http.Error(w, `{"error": "Authentication required"}`, http.StatusUnauthorized)
		return
	}

	// Parse query parameters
	page := int32(1)
	if p := r.URL.Query().Get("page"); p != "" {
		if parsed, err := strconv.Atoi(p); err == nil && parsed > 0 {
			page = int32(parsed)
		}
	}

	pageSize := int32(20)
	if ps := r.URL.Query().Get("page_size"); ps != "" {
		if parsed, err := strconv.Atoi(ps); err == nil && parsed > 0 {
			pageSize = int32(parsed)
		}
	}

	// Memory Service is HTTP/REST (not gRPC) - proxy HTTP request
	memoryURL := fmt.Sprintf("http://%s/api/v1/memories?page=%d&page_size=%d", MemoryAddr, page, pageSize)

	// Create HTTP request
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	httpReq, err := http.NewRequestWithContext(ctx, "GET", memoryURL, nil)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Failed to create request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Copy Authorization header from original request
	if auth := r.Header.Get("Authorization"); auth != "" {
		httpReq.Header.Set("Authorization", auth)
	}

	// Execute HTTP request
	httpClient := &http.Client{Timeout: 15 * time.Second}
	httpResp, err := httpClient.Do(httpReq)
	if err != nil {
		log.Printf("⚠️ Memory service HTTP error: %v", err)
		http.Error(w, fmt.Sprintf(`{"error": "Memory service error: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}
	defer func() {
		if err := httpResp.Body.Close(); err != nil {
			log.Printf("⚠️ Failed to close response body: %v", err)
		}
	}()

	// Read response body
	respBody, err := io.ReadAll(httpResp.Body)
	if err != nil {
		log.Printf("⚠️ Failed to read memory service response: %v", err)
		http.Error(w, `{"error": "Failed to read response from memory service"}`,
			http.StatusInternalServerError)
		return
	}

	// Forward response status and body
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(httpResp.StatusCode)
	if _, err := w.Write(respBody); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
		return
	}
}

// GraphOps health handler
func (gw *EnhancedGateway) graphHealthHandler(w http.ResponseWriter, r *http.Request) {
	// Call GraphOps Service gRPC health check
	if gw.grpcClients == nil || gw.grpcClients.GraphOpsClient == nil {
		http.Error(w, `{"error": "GraphOps service not available"}`, http.StatusServiceUnavailable)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	grpcReq := &graphopsv1.HealthCheckRequest{}
	grpcResp, err := gw.grpcClients.GraphOpsClient.HealthCheck(ctx, grpcReq)
	if err != nil {
		log.Printf("⚠️ GraphOps health check error: %v", err)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		if err := json.NewEncoder(w).Encode(map[string]interface{}{
			"status":  "unhealthy",
			"error":   err.Error(),
			"service": "graphops",
		}); err != nil {
			log.Printf("⚠️ Failed to encode error response: %v", err)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(map[string]interface{}{
		"status":         grpcResp.Status.String(),
		"version":        grpcResp.Version,
		"uptime_seconds": grpcResp.UptimeSeconds,
		"database": map[string]interface{}{
			"name":   grpcResp.Database.Name,
			"status": grpcResp.Database.Status.String(),
		},
		"age_extension": map[string]interface{}{
			"name":   grpcResp.AgeExtension.Name,
			"status": grpcResp.AgeExtension.Status.String(),
		},
		"details": grpcResp.Details,
	}); err != nil {
		log.Printf("⚠️ Failed to encode response: %v", err)
		return
	}
}

// Core API HTTP proxy
func (gw *EnhancedGateway) coreAPIProxy(w http.ResponseWriter, r *http.Request) {
	// HTTP proxy to Core API (temporary until gRPC migration)
	// Forward the request to Core API
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	// Construct target URL
	targetURL := fmt.Sprintf("http://%s%s", CoreAPIAddr, r.URL.Path)
	if r.URL.RawQuery != "" {
		targetURL += "?" + r.URL.RawQuery
	}

	// Create request to Core API
	proxyReq, err := http.NewRequest(r.Method, targetURL, r.Body)
	if err != nil {
		log.Printf("⚠️ Failed to create proxy request: %v", err)
		http.Error(w, `{"error": "Failed to create proxy request"}`, http.StatusInternalServerError)
		return
	}

	// Copy headers
	for key, values := range r.Header {
		for _, value := range values {
			proxyReq.Header.Add(key, value)
		}
	}

	// Get retry policy from config if available
	var retryPolicy *RetryPolicy
	if gw.config != nil && gw.config.Backends.CoreAPI != nil && gw.config.Backends.CoreAPI.Retry.Enabled {
		retryPolicy = BuildRetryPolicyFromConfig(&gw.config.Backends.CoreAPI.Retry)
	}

	// Execute request with retry logic
	var resp *http.Response
	if retryPolicy != nil {
		retryClient := NewRetryClient(client, retryPolicy)
		resp, err = retryClient.DoWithContext(r.Context(), proxyReq)
	} else {
		resp, err = client.Do(proxyReq)
	}
	if err != nil {
		log.Printf("⚠️ Core API proxy error: %v", err)
		http.Error(w, fmt.Sprintf(`{"error": "Core API proxy error: %s"}`, err.Error()),
			http.StatusBadGateway)
		return
	}
	defer func() {
		if err := resp.Body.Close(); err != nil {
			log.Printf("⚠️ Failed to close response body: %v", err)
		}
	}()

	// Copy response headers
	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Copy status code and body
	w.WriteHeader(resp.StatusCode)

	// Copy response body
	buf := make([]byte, 32*1024) // 32KB buffer
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			if _, writeErr := w.Write(buf[:n]); writeErr != nil {
				log.Printf("⚠️ Failed to write proxy response body: %v", writeErr)
				break
			}
		}
		if err != nil {
			if err != io.EOF {
				log.Printf("⚠️ Error reading proxy response: %v", err)
			}
			break
		}
	}
}
