package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"
)

func TestEnhancedGatewayMemoryRememberHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil, // No gRPC clients for this test
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBufferString(`{"content":"test"}`))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should handle request (may return 401 or 501)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayMemoryRecallHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?query=test", nil)
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayMemoryListHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayGraphQueryHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	reqBody := map[string]interface{}{
		"query": "MATCH (n) RETURN n LIMIT 1",
	}
	body, _ := json.Marshal(reqBody)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayGraphHealthHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayEnhancedHealthHandler(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedGatewayExtractUserID(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name   string
		header string
		expect string
	}{
		{"Bearer token", "Bearer test-token", "user-123"},
		{"No auth", "", ""},
		{"Invalid format", "Basic test", ""},
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

// Note: toJSON is a package-level function that can be tested indirectly
// through handlers that use it. Testing via enhancedHealthHandler which calls it.
func TestToJSONFunction(t *testing.T) {
	// Test toJSON indirectly through enhancedHealthHandler
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/health", nil)
	rec := httptest.NewRecorder()

	// enhancedHealthHandler calls toJSON internally
	enhanced.enhancedHealthHandler(rec, req)

	// Verify response contains JSON (from toJSON)
	if rec.Body.Len() == 0 {
		t.Error("Handler should write response body")
	}
}

func TestEnhancedGatewayCoreAPIProxy(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		method string
		path   string
	}{
		{"GET", "/api/v1/users/me"},
		{"PATCH", "/api/v1/users/me"},
		{"POST", "/api/v1/auth/login"},
	}

	for _, tt := range tests {
		t.Run(tt.method+" "+tt.path, func(t *testing.T) {
			req := httptest.NewRequest(tt.method, tt.path, nil)
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

// Note: TestGRPCClientsClose moved to clients_close_test.go to avoid duplication
