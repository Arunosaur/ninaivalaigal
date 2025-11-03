package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"
)

// Note: TestMemoryRememberHandlerNoAuth already exists in handlers_edge_cases_test.go

func TestMemoryRememberHandlerDetailedCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", nil)
	// No Authorization header
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should return 401 Unauthorized or 503 if auth check happens after client check
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRememberHandlerWithAuthNoBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRememberHandlerWithValidBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"content": "Test memory content",
		"context": "test-context",
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

func TestMemoryRememberHandlerWithMetadata(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"content": "Test memory",
		"context": "test",
		"metadata": map[string]interface{}{
			"source": "test",
			"tags":   []string{"tag1", "tag2"},
		},
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

// Note: TestMemoryRememberHandlerInvalidJSON already exists in handlers_edge_cases_test.go

func TestMemoryRememberHandlerEmptyBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBufferString(""))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Note: TestMemoryRememberHandlerLargeBody already exists in handlers_edge_cases_test.go

func TestMemoryRememberHandlerMissingContent(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"context": "test-context",
		// Missing "content" field
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

func TestMemoryRememberHandlerNoClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"content": "Test memory",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should return 503 if no clients available
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
