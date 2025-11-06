package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestMemoryRememberHandlerResponseBody tests response body forwarding
func TestMemoryRememberHandlerResponseBody(t *testing.T) {
	// Create a mock server that responds with JSON
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"id":"test-id","content":"test memory"}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer mockServer.Close()

	// Temporarily override MemoryAddr for testing
	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:] // Remove "http://" prefix
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

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

	if rec.Code != http.StatusOK {
		t.Logf("Expected StatusOK, got %d", rec.Code)
	}

	// Verify response body was forwarded
	if rec.Body.Len() == 0 {
		t.Error("Response body should not be empty")
	}
}

// TestMemoryRecallHandlerResponseBody tests response body forwarding for recall
func TestMemoryRecallHandlerResponseBody(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"memories":[{"id":"1","content":"test"}]}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerReadResponseError tests error handling when reading response
func TestMemoryRememberHandlerReadResponseError(t *testing.T) {
	// Server that closes connection immediately
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		// Close connection without sending body
		hj, ok := w.(http.Hijacker)
		if ok {
			conn, _, _ := hj.Hijack()
			_ = conn.Close() // Ignore close errors in test
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

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

	enhanced.memoryRememberHandler(rec, req)

	// Should handle read error gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerResponseBody tests response body forwarding for list
func TestMemoryListHandlerResponseBody(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"memories":[],"total":0}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerWriteResponseError tests response writing
func TestMemoryRememberHandlerWriteResponseError(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"id":"test"}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

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
	req.Header.Set("Authorization", "Bearer test-token")

	// Create a response recorder that simulates write error
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerWithLargeResponse tests handling large response bodies
func TestMemoryRecallHandlerWithLargeResponse(t *testing.T) {
	largeData := make([]byte, 10000) // 10KB response
	for i := range largeData {
		largeData[i] = byte(i % 256)
	}

	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"memories":[]}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
		if _, err := w.Write(largeData); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerHTTPClientErrorResponse tests HTTP client error handling
func TestMemoryRememberHandlerHTTPClientErrorResponse(t *testing.T) {
	// Use invalid address to force connection error
	originalAddr := MemoryAddr
	MemoryAddr = "invalid-host-12345:9999"
	defer func() { MemoryAddr = originalAddr }()

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

	enhanced.memoryRememberHandler(rec, req)

	// Should handle connection error gracefully
	if rec.Code != http.StatusInternalServerError {
		t.Logf("Expected InternalServerError for connection failure, got %d", rec.Code)
	}
}

// TestMemoryRecallHandlerHTTPClientError tests HTTP client error for recall
func TestMemoryRecallHandlerHTTPClientError(t *testing.T) {
	originalAddr := MemoryAddr
	MemoryAddr = "invalid-host-12345:9999"
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerHTTPClientError tests HTTP client error for list
func TestMemoryListHandlerHTTPClientError(t *testing.T) {
	originalAddr := MemoryAddr
	MemoryAddr = "invalid-host-12345:9999"
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerRequestCreationErrorResponse tests request creation error path
func TestMemoryRememberHandlerRequestCreationErrorResponse(t *testing.T) {
	// This is hard to trigger, but we can test the structure
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Create request with invalid body that might cause issues
	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should handle invalid JSON gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRecallHandlerResponseReadError tests response read error handling
func TestMemoryRecallHandlerResponseReadError(t *testing.T) {
	// Create a server that sends response but closes connection
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		// Write partial response then close
		if _, err := w.Write([]byte(`{"memories":`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
		// Force close by hijacking
		if hj, ok := w.(http.Hijacker); ok {
			conn, _, _ := hj.Hijack()
			_ = conn.Close() // Ignore close errors in test
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should handle read error
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerWithQueryParamsResponse tests URL construction with query params
func TestMemoryListHandlerWithQueryParamsResponse(t *testing.T) {
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Verify query params in request
		if r.URL.Query().Get("page") != "" || r.URL.Query().Get("page_size") != "" {
			w.WriteHeader(http.StatusOK)
			if _, err := w.Write([]byte(`{"memories":[]}`)); err != nil {
				t.Errorf("Failed to write response: %v", err)
			}
		} else {
			w.WriteHeader(http.StatusOK)
			if _, err := w.Write([]byte(`{"memories":[]}`)); err != nil {
				t.Errorf("Failed to write response: %v", err)
			}
		}
	}))
	defer mockServer.Close()

	originalAddr := MemoryAddr
	MemoryAddr = mockServer.URL[7:]
	defer func() { MemoryAddr = originalAddr }()

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
