package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	graphopspb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/graphopspb"
)

// Enhanced Gateway with gRPC clients
type EnhancedGateway struct {
	*Gateway
	grpcClients *GRPCClients
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
	// Extract user ID from JWT token (placeholder for now)
	userID := gw.extractUserID(r)
	if userID == "" {
		http.Error(w, `{"error": "Authentication required"}`, http.StatusUnauthorized)
		return
	}

	// Parse request body
	var req MemoryRememberRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Invalid request body: %s"}`, err.Error()),
			http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Content == "" {
		http.Error(w, `{"error": "Content is required"}`, http.StatusBadRequest)
		return
	}

	// Memory Service is HTTP/REST (not gRPC) - proxy HTTP request
	memoryURL := fmt.Sprintf("http://%s/memory/remember", MemoryAddr)

	// Prepare HTTP request body
	httpReqBody, err := json.Marshal(map[string]interface{}{
		"content":  req.Content,
		"context":  req.Context,
		"metadata": req.Metadata,
	})
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Failed to marshal request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Create HTTP request
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	httpReq, err := http.NewRequestWithContext(ctx, "POST", memoryURL, bytes.NewBuffer(httpReqBody))
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Failed to create request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Copy Authorization header from original request
	if auth := r.Header.Get("Authorization"); auth != "" {
		httpReq.Header.Set("Authorization", auth)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	// Execute HTTP request
	httpClient := &http.Client{Timeout: 10 * time.Second}
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

func (gw *EnhancedGateway) memoryRecallHandler(w http.ResponseWriter, r *http.Request) {
	userID := gw.extractUserID(r)
	if userID == "" {
		http.Error(w, `{"error": "Authentication required"}`, http.StatusUnauthorized)
		return
	}

	// Parse query parameters
	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, `{"error": "Query parameter 'q' is required"}`, http.StatusBadRequest)
		return
	}

	limit := 10 // default limit
	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 {
			limit = parsed
		}
	}

	threshold := float32(0.7) // default similarity threshold
	if t := r.URL.Query().Get("threshold"); t != "" {
		if parsed, err := strconv.ParseFloat(t, 32); err == nil {
			threshold = float32(parsed)
		}
	}

	// Memory Service is HTTP/REST (not gRPC) - proxy HTTP request
	memoryURL := fmt.Sprintf("http://%s/memory/recall", MemoryAddr)

	// Prepare HTTP request body (Memory Service expects POST with JSON body)
	httpReqBody, err := json.Marshal(map[string]interface{}{
		"query":     query,
		"limit":     limit,
		"threshold": threshold,
	})
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Failed to marshal request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Create HTTP request
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	httpReq, err := http.NewRequestWithContext(ctx, "POST", memoryURL, bytes.NewBuffer(httpReqBody))
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Failed to create request: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Copy Authorization header from original request
	if auth := r.Header.Get("Authorization"); auth != "" {
		httpReq.Header.Set("Authorization", auth)
	}
	httpReq.Header.Set("Content-Type", "application/json")

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

func (gw *EnhancedGateway) graphQueryHandler(w http.ResponseWriter, r *http.Request) {
	userID := gw.extractUserID(r)
	if userID == "" {
		http.Error(w, `{"error": "Authentication required"}`, http.StatusUnauthorized)
		return
	}

	// Parse request body
	var req GraphQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf(`{"error": "Invalid request body: %s"}`, err.Error()),
			http.StatusBadRequest)
		return
	}

	// Validate Cypher query
	if req.Query == "" {
		http.Error(w, `{"error": "Query is required"}`, http.StatusBadRequest)
		return
	}

	// Set default timeout
	if req.TimeoutMs <= 0 {
		req.TimeoutMs = 30000 // 30 seconds default
	}

	// Call GraphOps Service gRPC
	if gw.grpcClients == nil || gw.grpcClients.GraphOpsClient == nil {
		http.Error(w, `{"error": "GraphOps service not available"}`, http.StatusServiceUnavailable)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(req.TimeoutMs)*time.Millisecond)
	defer cancel()

	grpcReq := &graphopspb.ExecuteQueryRequest{
		Query:      req.Query,
		Parameters: req.Parameters,
		UserId:     userID,
		TimeoutMs:  int32(req.TimeoutMs),
	}

	grpcResp, err := gw.grpcClients.GraphOpsClient.ExecuteQuery(ctx, grpcReq)
	if err != nil {
		log.Printf("⚠️ GraphOps service gRPC error: %v", err)
		http.Error(w, fmt.Sprintf(`{"error": "GraphOps service error: %s"}`, err.Error()),
			http.StatusInternalServerError)
		return
	}

	// Convert gRPC response to REST response
	results := make([]QueryResult, len(grpcResp.Results))
	for i, result := range grpcResp.Results {
		columns := make([]QueryColumn, len(result.Columns))
		for j, col := range result.Columns {
			columns[j] = QueryColumn{Name: col.Name, Type: col.Type}
		}

		rows := make([]QueryRow, len(result.Rows))
		for j, row := range result.Rows {
			values := make([]interface{}, len(row.Values))
			for k, val := range row.Values {
				// Convert protobuf oneof to interface{}
				switch v := val.Value.(type) {
				case *graphopspb.QueryValue_StringValue:
					values[k] = v.StringValue
				case *graphopspb.QueryValue_IntValue:
					values[k] = v.IntValue
				case *graphopspb.QueryValue_DoubleValue:
					values[k] = v.DoubleValue
				case *graphopspb.QueryValue_BoolValue:
					values[k] = v.BoolValue
				case *graphopspb.QueryValue_JsonValue:
					values[k] = json.RawMessage(v.JsonValue)
				default:
					values[k] = nil
				}
			}
			rows[j] = QueryRow{Values: values}
		}

		results[i] = QueryResult{Columns: columns, Rows: rows}
	}

	resp := GraphQueryResponse{
		Results: results,
		Metadata: QueryMeta{
			RowsAffected:    int(grpcResp.Metadata.RowsAffected),
			ExecutionTimeMs: int(grpcResp.Metadata.ExecutionTimeMs),
			QueryPlan:       grpcResp.Metadata.QueryPlan,
			Warnings:        grpcResp.Metadata.Warnings,
		},
		Status: grpcResp.Status,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("⚠️ Failed to encode response: %v", err)
		return
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
	memoryURL := fmt.Sprintf("http://%s/memory/memories?page=%d&page_size=%d", MemoryAddr, page, pageSize)

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

	grpcReq := &graphopspb.HealthCheckRequest{}
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
		"status":    grpcResp.Status,
		"version":   grpcResp.Version,
		"timestamp": grpcResp.Timestamp.AsTime().Format(time.RFC3339),
		"database": map[string]interface{}{
			"connected":          grpcResp.Database.Connected,
			"active_connections": grpcResp.Database.ActiveConnections,
			"idle_connections":   grpcResp.Database.IdleConnections,
			"max_connections":    grpcResp.Database.MaxConnections,
		},
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

	// Execute request
	resp, err := client.Do(proxyReq)
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
