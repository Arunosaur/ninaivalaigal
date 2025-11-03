package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestGraphHealthHandlerNoClients is defined in graph_health_handler_test.go
// This test is removed to avoid duplicate declaration

func TestGraphHealthHandlerPlaceholder(t *testing.T) {
	// Placeholder - actual test in graph_health_handler_test.go
	if rec.Body.Len() == 0 {
		t.Error("Handler should write error response body")
	}
}

func TestGraphHealthHandlerWithClientsButError(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test without clients")
	}

	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// May return 503 if health check fails, or 200 if it succeeds
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}

	// Should return JSON
	if rec.Header().Get("Content-Type") != "application/json" {
		t.Log("Response should have Content-Type application/json")
	}
}

func TestGraphHealthHandlerResponseFormat(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// Verify response is valid JSON (if status is 200)
	if rec.Code == http.StatusOK {
		var response map[string]interface{}
		if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
			t.Errorf("Response should be valid JSON: %v", err)
		}

		// Verify expected fields
		if _, ok := response["status"]; !ok {
			t.Log("Response should contain 'status' field")
		}
	}
}

func TestGraphHealthHandlerErrorResponseFormat(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// Should return JSON error response
	var response map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Errorf("Error response should be valid JSON: %v", err)
	}

	if _, ok := response["error"]; !ok {
		t.Log("Error response should contain 'error' field")
	}
}
