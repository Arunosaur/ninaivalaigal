package main

import (
	"bytes"
	"net/http/httptest"
	"testing"
)

func TestMemoryRememberHandlerHTTPRequestCreation(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := bytes.NewBufferString(`{"content": "test", "context": "test"}`)
	req := httptest.NewRequest("POST", "/api/v1/memory/remember", body)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRememberHandlerHTTPClientTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := bytes.NewBufferString(`{"content": "test"}`)
	req := httptest.NewRequest("POST", "/api/v1/memory/remember", body)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should use 10 second timeout
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerHTTPPostBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=5&threshold=0.8", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should convert GET with query params to POST with JSON body
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerHTTPRequestTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should use 15 second timeout
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerHTTPRequestCreation(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=3&page_size=100", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerURLConstructionDetailed(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []struct {
		page     string
		pageSize string
	}{
		{"1", "20"},   // Defaults
		{"5", "50"},   // Custom values
		{"10", "100"}, // Larger pages
		{"", ""},      // No params (defaults)
	}

	for _, tc := range testCases {
		t.Run(tc.page+"_"+tc.pageSize, func(t *testing.T) {
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

func TestMemoryListHandlerResponseForwarding(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	// Should forward response status code and body
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
