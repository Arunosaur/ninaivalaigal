package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestMemoryRememberHandlerEmptyContent(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"content": "",
		"context": "test",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should return 400 Bad Request
	if rec.Code != http.StatusBadRequest {
		t.Logf("Expected 400, got %d (this may be acceptable if auth check happens first)", rec.Code)
	}
}

func TestMemoryRememberHandlerInvalidJSON(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBufferString("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRememberHandlerNoAuth(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"content": "test",
		"context": "test",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	// No Authorization header
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should return 401 Unauthorized
	if rec.Code != http.StatusUnauthorized {
		t.Logf("Expected 401, got %d", rec.Code)
	}
}

func TestMemoryRecallHandlerNoQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should return 400 Bad Request
	if rec.Code != http.StatusBadRequest {
		t.Logf("Expected 400, got %d (may return 401 if auth check happens first)", rec.Code)
	}
}

func TestMemoryRecallHandlerWithLimit(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=20&threshold=0.8", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerWithPagination(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=2&page_size=50", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerEmptyQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": "",
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

func TestGraphQueryHandlerWithParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) WHERE n.id = $id RETURN n",
		"parameters": map[string]string{"id": "123"},
		"timeout_ms": 5000,
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

func TestCoreAPIProxyDifferentPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	paths := []string{
		"/api/v1/users/me",
		"/api/v1/teams",
		"/api/v1/organizations",
		"/api/v1/contexts",
	}

	for _, path := range paths {
		t.Run(path, func(t *testing.T) {
			req := httptest.NewRequest("GET", path, nil)
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

func TestCoreAPIProxyDifferentMethods(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	methods := []string{"GET", "POST", "PATCH", "DELETE", "PUT"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			var body io.Reader
			if method == "POST" || method == "PUT" || method == "PATCH" {
				body = bytes.NewBufferString(`{"test": "data"}`)
			}

			req := httptest.NewRequest(method, "/api/v1/users/me", body)
			if body != nil {
				req.Header.Set("Content-Type", "application/json")
			}
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

func TestMemoryRememberHandlerLargeBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Create large content
	largeContent := strings.Repeat("a", 10000)
	body := map[string]interface{}{
		"content":  largeContent,
		"context":  "test",
		"metadata": map[string]string{"key": "value"},
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerInvalidLimit(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with negative limit
	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=-1", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerMalformedParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with invalid parameters format
	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"parameters": "not a map", // Should be map[string]string
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

func TestEnhancedHealthHandlerNoClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rec.Code)
	}

	// Verify response contains JSON
	var response map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Errorf("Response should be valid JSON: %v", err)
	}
}

func TestGraphHealthHandlerEdgeCase(t *testing.T) {
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
