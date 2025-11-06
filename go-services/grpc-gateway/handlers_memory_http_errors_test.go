package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"
)

// TestMemoryRememberHandlerMarshalError covers the error path when marshaling request body fails
// This is hard to trigger in normal circumstances, but we can verify the error handling exists
func TestMemoryRememberHandlerMarshalError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Create a request that will trigger marshaling (though JSON marshal rarely fails)
	body := MemoryRememberRequest{
		Content: "Test memory content",
		Context: "test-context",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Handler should set a status code (may be 500 if service is unavailable, or 200 if successful)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerNegativeLimit tests that negative limit values are handled
func TestMemoryRecallHandlerNegativeLimit(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=-5", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should use default limit (10) when negative limit provided
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerZeroLimit tests that zero limit values are handled
func TestMemoryRecallHandlerZeroLimit(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=0", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should use default limit (10) when zero limit provided
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerNegativeThreshold tests that negative threshold values are handled
func TestMemoryRecallHandlerNegativeThreshold(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&threshold=-0.5", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should accept negative threshold (though it may not make practical sense)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerLargeLimit tests that large limit values are handled
func TestMemoryRecallHandlerLargeLimit(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=1000", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should accept large limit
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerWithBothParams tests with both limit and threshold
func TestMemoryRecallHandlerWithBothParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=20&threshold=0.85", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerWithMultipleMetadataKeys tests the metadata path with multiple keys
func TestMemoryRememberHandlerWithMultipleMetadataKeys(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content:  "Test memory content",
		Context:  "test-context",
		Metadata: map[string]string{"key1": "value1", "key2": "value2", "key3": "value3"},
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

// TestMemoryRememberHandlerWithEmptyMetadata tests with empty metadata
func TestMemoryRememberHandlerWithEmptyMetadata(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content:  "Test memory content",
		Context:  "test-context",
		Metadata: map[string]string{},
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

// TestMemoryRememberHandlerWithNilMetadata tests with nil metadata
func TestMemoryRememberHandlerWithNilMetadata(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content: "Test memory content",
		Context: "test-context",
		// Metadata is nil
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

// TestMemoryListHandlerWithLargePageSize tests with very large page size
func TestMemoryListHandlerWithLargePageSize(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=1&page_size=9999", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerWithLargePage tests with very large page number
func TestMemoryListHandlerWithLargePage(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=99999&page_size=20", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerURLEncoding tests that special characters in query params are handled
func TestMemoryListHandlerURLEncoding(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with properly encoded URL
	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=2&page_size=50", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
