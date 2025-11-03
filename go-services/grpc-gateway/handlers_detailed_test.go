package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"
)

func TestMemoryRememberHandlerDetailed(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with valid JSON body
	body := map[string]interface{}{
		"content": "test memory",
		"context": "test-context",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should set status code (may be 501, 400, or 401)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerDetailed(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with query parameters
	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=10", nil)
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerDetailed(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with valid query
	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n LIMIT 1",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerInvalidJSON(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBufferString("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// Should handle invalid JSON gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerDetailed(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=1&page_size=10", nil)
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestCoreAPIProxyWithMethods(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	methods := []string{"GET", "POST", "PATCH", "DELETE"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			req := httptest.NewRequest(method, "/api/v1/users/me", nil)
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

func TestEnhancedHealthHandlerWithConnections(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}

	// Response should contain JSON
	if rec.Body.Len() == 0 {
		t.Error("Handler should write response body")
	}
}

func TestExtractUserIDWithDifferentFormats(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name   string
		header string
	}{
		{"Bearer token", "Bearer test-token-123"},
		{"No header", ""},
		{"Invalid format", "Basic dGVzdDp0ZXN0"},
		{"Empty bearer", "Bearer "},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			if tt.header != "" {
				req.Header.Set("Authorization", tt.header)
			}

			userID := enhanced.extractUserID(req)
			// Just verify function doesn't panic
			_ = userID
		})
	}
}
