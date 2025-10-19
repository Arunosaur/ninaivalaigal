package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"
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

	// TODO: Call Memory Service gRPC after protocol buffer generation
	/*
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		grpcReq := &memorypb.RememberRequest{
			UserId:   userID,
			Content:  req.Content,
			Context:  req.Context,
			Metadata: req.Metadata,
		}

		grpcResp, err := gw.grpcClients.MemoryClient.Remember(ctx, grpcReq)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "Memory service error: %s"}`, err.Error()),
				http.StatusInternalServerError)
			return
		}

		resp := MemoryRememberResponse{
			MemoryID:  grpcResp.MemoryId,
			Status:    grpcResp.Status,
			CreatedAt: grpcResp.CreatedAt.AsTime().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	*/

	// Placeholder response until gRPC is implemented
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	if _, err := fmt.Fprintf(w, `{
		"memory_id": "placeholder-id-123",
		"status": "accepted",
		"created_at": "%s",
		"note": "gRPC integration pending - Task #36 in progress"
	}`, time.Now().UTC().Format(time.RFC3339)); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
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

	_ = 10 // default limit (unused for now)
	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 {
			_ = parsed // Will be used when gRPC integration is complete
		}
	}

	_ = float32(0.7) // default similarity threshold (unused for now)
	if t := r.URL.Query().Get("threshold"); t != "" {
		if parsed, err := strconv.ParseFloat(t, 32); err == nil {
			_ = float32(parsed) // Will be used when gRPC integration is complete
		}
	}

	// TODO: Call Memory Service gRPC after protocol buffer generation
	/*
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()

		grpcReq := &memorypb.RecallRequest{
			UserId:    userID,
			Query:     query,
			Limit:     int32(limit),
			Threshold: threshold,
		}

		grpcResp, err := gw.grpcClients.MemoryClient.Recall(ctx, grpcReq)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error": "Memory service error: %s"}`, err.Error()),
				http.StatusInternalServerError)
			return
		}

		// Convert gRPC response to REST response
		memories := make([]MemoryItem, len(grpcResp.Memories))
		for i, mem := range grpcResp.Memories {
			memories[i] = MemoryItem{
				ID:             mem.Id,
				Content:        mem.Content,
				Context:        mem.Context,
				Metadata:       mem.Metadata,
				CreatedAt:      mem.CreatedAt.AsTime().Format(time.RFC3339),
				UpdatedAt:      mem.UpdatedAt.AsTime().Format(time.RFC3339),
				RelevanceScore: mem.RelevanceScore,
			}
		}

		resp := MemoryRecallResponse{
			Memories:   memories,
			TotalCount: int(grpcResp.TotalCount),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	*/

	// Placeholder response
	w.Header().Set("Content-Type", "application/json")
	if _, err := fmt.Fprintf(w, `{
		"memories": [
			{
				"id": "placeholder-memory-1",
				"content": "Sample memory matching query: %s",
				"context": "test context",
				"created_at": "%s",
				"relevance_score": 0.95
			}
		],
		"total_count": 1,
		"note": "gRPC integration pending - Task #36 in progress"
	}`, query, time.Now().UTC().Format(time.RFC3339)); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
		http.Error(w, `{"error": "Failed to write response"}`, http.StatusInternalServerError)
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

	// TODO: Call GraphOps Service gRPC after protocol buffer generation
	/*
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
		json.NewEncoder(w).Encode(resp)
	*/

	// Placeholder response
	w.Header().Set("Content-Type", "application/json")
	if _, err := fmt.Fprintf(w, `{
		"results": [
			{
				"columns": [{"name": "n", "type": "node"}],
				"rows": [
					{"values": ["Sample graph node for query: %s"]}
				]
			}
		],
		"metadata": {
			"rows_affected": 1,
			"execution_time_ms": 25,
			"query_plan": "MATCH (n) RETURN n LIMIT 1"
		},
		"status": "success",
		"note": "gRPC integration pending - Task #36 in progress"
	}`, req.Query); err != nil {
		log.Printf("⚠️ Failed to write response: %v", err)
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
		"grpc_integration": "Task #36 in progress"
	}`, status, time.Now().UTC().Format(time.RFC3339), toJSON(connections)); err != nil {
		log.Printf("⚠️ Failed to write health response: %v", err)
	}
}

// Helper function to convert map to JSON
func toJSON(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
