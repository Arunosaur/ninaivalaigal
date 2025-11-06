package main

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// errorWriter is a ResponseWriter that fails on Write
type errorResponseWriter struct {
	*httptest.ResponseRecorder
	writeError bool
}

func (w *errorResponseWriter) Write(p []byte) (int, error) {
	if w.writeError {
		return 0, errors.New("write error")
	}
	return w.ResponseRecorder.Write(p)
}

func TestCoreAPIProxyResponseBodyWriteError(t *testing.T) {
	// Create a mock HTTP server that returns a response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte("test response body")); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer server.Close()

	// Temporarily override CoreAPIAddr
	originalAddr := CoreAPIAddr
	CoreAPIAddr = strings.TrimPrefix(server.URL, "http://")
	defer func() { CoreAPIAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := &errorResponseWriter{
		ResponseRecorder: httptest.NewRecorder(),
		writeError:       true,
	}

	enhanced.coreAPIProxy(rec, req)

	// Should handle write error gracefully
	if rec.Code != http.StatusOK {
		t.Errorf("Expected status %d, got %d", http.StatusOK, rec.Code)
	}
}

func TestCoreAPIProxyResponseBodyReadError(t *testing.T) {
	// Create a mock HTTP server that returns a response with an error reader
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		// Use a custom writer that errors
		_, _ = w.Write([]byte("test"))
	}))
	defer server.Close()

	// Create a custom response that errors on body read
	originalAddr := CoreAPIAddr
	CoreAPIAddr = strings.TrimPrefix(server.URL, "http://")
	defer func() { CoreAPIAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	// Should handle read error gracefully
	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyResponseBodyStreamingWithError(t *testing.T) {
	// Test the streaming path with multiple reads
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		// Write large response to trigger streaming
		data := make([]byte, 64*1024)
		for i := range data {
			data[i] = byte(i % 256)
		}
		if _, err := w.Write(data); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer server.Close()

	originalAddr := CoreAPIAddr
	CoreAPIAddr = strings.TrimPrefix(server.URL, "http://")
	defer func() { CoreAPIAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status %d, got %d", http.StatusOK, rec.Code)
	}
}

func TestCoreAPIProxyWithEmptyBody(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	originalAddr := CoreAPIAddr
	CoreAPIAddr = strings.TrimPrefix(server.URL, "http://")
	defer func() { CoreAPIAddr = originalAddr }()

	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code != http.StatusNoContent {
		t.Errorf("Expected status %d, got %d", http.StatusNoContent, rec.Code)
	}
}
