package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNewGateway(t *testing.T) {
	gateway := NewGateway()

	if gateway == nil {
		t.Fatal("Expected gateway to be created, got nil")
	}

	if gateway.router == nil {
		t.Error("Expected router to be initialized")
	}

	if gateway.grpcConns == nil {
		t.Error("Expected grpcConns map to be initialized")
	}
}

func TestHealthHandler(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	gateway.healthHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, rec.Code)
	}

	contentType := rec.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type 'application/json', got '%s'", contentType)
	}

	body := rec.Body.String()
	if body == "" {
		t.Error("Expected non-empty response body")
	}

	// Check response contains expected fields
	expectedFields := []string{"status", "service", "version"}
	for _, field := range expectedFields {
		if !contains(body, field) {
			t.Errorf("Expected response body to contain '%s'", field)
		}
	}
}

func TestCorsMiddleware(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("OPTIONS", "/health", nil)
	rec := httptest.NewRecorder()

	handler := corsMiddleware(gateway.router)
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status code %d for OPTIONS, got %d", http.StatusOK, rec.Code)
	}

	// Check CORS headers
	corsHeaders := map[string]string{
		"Access-Control-Allow-Origin":  "*",
		"Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
		"Access-Control-Allow-Headers": "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization",
	}

	for header, expectedValue := range corsHeaders {
		actualValue := rec.Header().Get(header)
		if actualValue != expectedValue {
			t.Errorf("Expected CORS header '%s' to be '%s', got '%s'", header, expectedValue, actualValue)
		}
	}
}

func TestLoggingMiddleware(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	handler := loggingMiddleware(gateway.router)
	handler.ServeHTTP(rec, req)

	// Middleware should not affect response
	if rec.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, rec.Code)
	}
}

func TestMemoryRememberHandler(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", nil)
	rec := httptest.NewRecorder()

	gateway.memoryRememberHandler(rec, req)

	// Handler currently returns 501 Not Implemented
	if rec.Code != http.StatusNotImplemented {
		t.Errorf("Expected status code %d, got %d", http.StatusNotImplemented, rec.Code)
	}
}

func TestMemoryRecallHandler(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	rec := httptest.NewRecorder()

	gateway.memoryRecallHandler(rec, req)

	// Handler currently returns 501 Not Implemented
	if rec.Code != http.StatusNotImplemented {
		t.Errorf("Expected status code %d, got %d", http.StatusNotImplemented, rec.Code)
	}
}

func TestGraphQueryHandler(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("POST", "/api/v1/graph/query", nil)
	rec := httptest.NewRecorder()

	gateway.graphQueryHandler(rec, req)

	// Handler currently returns 501 Not Implemented
	if rec.Code != http.StatusNotImplemented {
		t.Errorf("Expected status code %d, got %d", http.StatusNotImplemented, rec.Code)
	}
}

func TestSetupRoutes(t *testing.T) {
	gateway := NewGateway()

	// Test health route exists
	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()
	gateway.router.ServeHTTP(rec, req)

	if rec.Code == http.StatusNotFound {
		t.Error("Expected /health route to exist")
	}

	// Test API v1 routes exist with appropriate methods
	// Note: Memory routes may not be registered if gRPC clients unavailable
	apiRoutes := []struct {
		path      string
		method    string
		mustExist bool
	}{
		{"/api/v1/graph/query", "POST", true}, // Always exists
		{"/api/v1/graph/health", "GET", true}, // Always exists
		{"/api/v1/users/me", "GET", true},     // Core API proxy
		{"/api/v1/auth/login", "POST", true},  // Core API proxy
		// Memory routes may not exist if gRPC clients not initialized
		{"/api/v1/memory/remember", "POST", false},
		{"/api/v1/memory/recall", "GET", false},
	}

	for _, route := range apiRoutes {
		req := httptest.NewRequest(route.method, route.path, nil)
		rec := httptest.NewRecorder()
		gateway.router.ServeHTTP(rec, req)

		// Route should exist (even if it returns 501 or 405 Method Not Allowed)
		if route.mustExist && rec.Code == http.StatusNotFound {
			t.Errorf("Expected route '%s' with method '%s' to exist, got 404", route.path, route.method)
		}
		// For optional routes, just verify they don't cause a panic
		if !route.mustExist && rec.Code == http.StatusNotFound {
			t.Logf("Optional route '%s' not registered (this is OK if gRPC clients not available)", route.path)
		}
	}
}

// Helper function to check if string contains substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && containsHelper(s, substr)
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
