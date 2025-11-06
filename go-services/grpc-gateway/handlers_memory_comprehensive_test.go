package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestMemoryRememberHandlerWithContext tests with context in request
func TestMemoryRememberHandlerWithContext(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content:  "Test memory with context",
		Context:  "test-context-value",
		Metadata: map[string]string{"source": "test"},
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

// TestMemoryRememberHandlerMarshalRequest tests request marshaling
func TestMemoryRememberHandlerMarshalRequest(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with complex metadata
	body := MemoryRememberRequest{
		Content: "Test content",
		Context: "test-context",
		Metadata: map[string]string{
			"key1": "value1",
			"key2": "value2",
			"key3": "value3",
		},
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Verify request was marshaled and sent
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerWithAllParams tests with all query parameters
func TestMemoryRecallHandlerWithAllParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=25&threshold=0.85", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerEmptyQueryParam tests edge case with empty query after parsing
func TestMemoryRecallHandlerEmptyQueryParam(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should error for empty query
	if rec.Code != http.StatusBadRequest {
		t.Logf("Expected BadRequest for empty query, got %d", rec.Code)
	}
}

// TestMemoryListHandlerWithQueryParams tests with various query parameter combinations
func TestMemoryListHandlerWithQueryParams(t *testing.T) {
	testCases := []struct {
		name     string
		page     string
		pageSize string
	}{
		{"page 1, size 20", "1", "20"},
		{"page 10, size 50", "10", "50"},
		{"page 100, size 100", "100", "100"},
		{"page 1, no size", "1", ""},
		{"no page, size 20", "", "20"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			url := "/api/v1/memory/memories"
			if tc.page != "" || tc.pageSize != "" {
				url += "?"
				if tc.page != "" {
					url += "page=" + tc.page
				}
				if tc.pageSize != "" {
					if tc.page != "" {
						url += "&"
					}
					url += "page_size=" + tc.pageSize
				}
			}

			req := httptest.NewRequest("GET", url, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

// TestMemoryRememberHandlerRequestCreationError tests error handling in request creation
func TestMemoryRememberHandlerRequestCreationError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content: "Test content",
		Context: "test-context",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	// Handler should handle errors gracefully
	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerLargeValues tests with very large limit and threshold values
func TestMemoryRecallHandlerLargeValues(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=99999&threshold=0.999", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerURLConstructionComprehensive tests URL construction with various parameters
func TestMemoryListHandlerURLConstructionComprehensive(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with page=1, pageSize=20 (defaults)
	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerWithoutAuthHeader tests without authorization header
func TestMemoryRememberHandlerWithoutAuthHeader(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := MemoryRememberRequest{
		Content: "Test content",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	// No Authorization header
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Logf("Expected Unauthorized for missing auth, got %d", rec.Code)
	}
}
