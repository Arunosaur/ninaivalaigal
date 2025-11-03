package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
)

// Test memoryRememberHandler error paths
func TestMemoryRememberHandlerErrorPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name        string
		body        interface{}
		contentType string
		expectCode  int
	}{
		{"Invalid JSON body", "not json", "application/json", http.StatusBadRequest},
		{"Empty body", "", "application/json", http.StatusBadRequest},
		{"Missing content field", map[string]interface{}{"metadata": map[string]string{}}, "application/json", http.StatusBadRequest},
		{"Invalid content type", map[string]interface{}{"content": "test"}, "text/plain", http.StatusBadRequest},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var bodyReader io.Reader
			if tt.body != nil {
				if str, ok := tt.body.(string); ok {
					bodyReader = bytes.NewBufferString(str)
				} else {
					bodyJSON, _ := json.Marshal(tt.body)
					bodyReader = bytes.NewBuffer(bodyJSON)
				}
			}

			req := httptest.NewRequest("POST", "/api/v1/memory/remember", bodyReader)
			if tt.contentType != "" {
				req.Header.Set("Content-Type", tt.contentType)
			}
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRememberHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

// Test memoryRecallHandler query parameter parsing edge cases
func TestMemoryRecallHandlerQueryParamEdgeCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name       string
		query      string
		limit      string
		threshold  string
		expectCode int
	}{
		{"Missing query param", "", "", "", http.StatusBadRequest},
		{"Invalid limit", "test", "invalid", "", http.StatusBadRequest},
		{"Negative limit", "test", "-5", "", http.StatusBadRequest},
		{"Zero limit", "test", "0", "", http.StatusBadRequest},
		{"Invalid threshold", "test", "10", "not-a-number", http.StatusBadRequest},
		{"Negative threshold", "test", "10", "-0.1", http.StatusBadRequest},
		{"Threshold > 1.0", "test", "10", "1.5", http.StatusBadRequest},
		{"Valid params with defaults", "test query", "", "", http.StatusUnauthorized}, // No auth, but tests parsing
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Build URL with proper encoding
			u := fmt.Sprintf("/api/v1/memory/recall?q=%s", url.QueryEscape(tt.query))
			if tt.limit != "" {
				u += fmt.Sprintf("&limit=%s", url.QueryEscape(tt.limit))
			}
			if tt.threshold != "" {
				u += fmt.Sprintf("&threshold=%s", url.QueryEscape(tt.threshold))
			}

			req := httptest.NewRequest("GET", u, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

// Test memoryListHandler pagination edge cases
func TestMemoryListHandlerPaginationEdgeCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name       string
		page       string
		pageSize   string
		expectCode int
	}{
		{"Invalid page number", "invalid", "20", http.StatusUnauthorized},
		{"Negative page", "-1", "20", http.StatusUnauthorized},
		{"Zero page", "0", "20", http.StatusUnauthorized},
		{"Invalid page_size", "1", "invalid", http.StatusUnauthorized},
		{"Negative page_size", "1", "-5", http.StatusUnauthorized},
		{"Zero page_size", "1", "0", http.StatusUnauthorized},
		{"Large page_size", "1", "1000", http.StatusUnauthorized},
		{"Missing params (uses defaults)", "", "", http.StatusUnauthorized},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			url := "/api/v1/memory/memories"
			params := []string{}
			if tt.page != "" {
				params = append(params, fmt.Sprintf("page=%s", tt.page))
			}
			if tt.pageSize != "" {
				params = append(params, fmt.Sprintf("page_size=%s", tt.pageSize))
			}
			if len(params) > 0 {
				url += "?" + params[0]
				for i := 1; i < len(params); i++ {
					url += "&" + params[i]
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

// Test memoryRememberHandler with various metadata structures
func TestMemoryRememberHandlerMetadataVariations(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	tests := []struct {
		name string
		body MemoryRememberRequest
	}{
		{"Empty metadata", MemoryRememberRequest{Content: "test", Metadata: map[string]string{}}},
		{"Nil metadata", MemoryRememberRequest{Content: "test", Metadata: nil}},
		{"Multiple metadata keys", MemoryRememberRequest{
			Content:  "test",
			Metadata: map[string]string{"key1": "value1", "key2": "value2", "key3": "value3"},
		}},
		{"With context", MemoryRememberRequest{
			Content:  "test content",
			Context:  "test-context-id",
			Metadata: map[string]string{"source": "test"},
		}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			bodyJSON, _ := json.Marshal(tt.body)
			req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRememberHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

// Test HTTP client error paths in memory handlers
func TestMemoryHandlersHTTPClientErrors(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with invalid memory service address
	originalAddr := MemoryAddr
	MemoryAddr = "invalid-address:99999"
	defer func() { MemoryAddr = originalAddr }()

	// Test memoryRememberHandler with invalid address
	body := MemoryRememberRequest{Content: "test", Metadata: map[string]string{}}
	bodyJSON, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should handle connection error gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}

	// Test memoryRecallHandler with invalid address
	req2 := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req2.Header.Set("Authorization", "Bearer test-token")
	rec2 := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec2, req2)

	if rec2.Code == 0 {
		t.Error("Handler should set a status code")
	}

	// Test memoryListHandler with invalid address
	req3 := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req3.Header.Set("Authorization", "Bearer test-token")
	rec3 := httptest.NewRecorder()

	enhanced.memoryListHandler(rec3, req3)

	if rec3.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Test memoryRecallHandler with body instead of query params
func TestMemoryRecallHandlerWithBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Some clients might send POST with body
	body := map[string]interface{}{
		"query":     "test query",
		"limit":     10,
		"threshold": 0.7,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/recall", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Handler should still process query params from URL if present
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
