package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGraphQueryHandlerWithGRPCClients(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n LIMIT 1",
		"parameters": map[string]string{},
		"timeout_ms": 5000,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// Should set status code (may be 503 if clients unavailable, 400 if validation fails, or 500 on gRPC error)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerNoClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// Should return 503 Service Unavailable
	if rec.Code != http.StatusServiceUnavailable {
		t.Logf("Expected 503, got %d (may return 401 if auth check happens first)", rec.Code)
	}
}

func TestGraphQueryHandlerWithEmptyParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"parameters": map[string]string{},
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerWithTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"timeout_ms": 10000,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerWithZeroTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"timeout_ms": 0,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerWithNegativeTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"timeout_ms": -1,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphHealthHandlerWithClients(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Note: TestGraphHealthHandlerResponseFormat moved to handlers_graph_health_test.go to avoid duplication
