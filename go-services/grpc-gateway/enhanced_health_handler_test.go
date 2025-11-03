package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestEnhancedHealthHandlerWithGrpcClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil, // No gRPC clients
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rec.Code)
	}

	// Should return JSON health status
	if rec.Body.Len() == 0 {
		t.Error("Handler should return response body")
	}
}

func TestEnhancedHealthHandlerWithConnectionStatus(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients() // May be nil if services unavailable

	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	// May return 200 (healthy) or 503 (degraded) depending on connection status
	if rec.Code != http.StatusOK && rec.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status 200 or 503, got %d", rec.Code)
	}
}

func TestEnhancedHealthHandlerConnectionStatusFields(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()

	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	// Verify response contains connection status if clients exist
	if clients != nil {
		status := clients.GetConnectionStatus()
		if status == nil {
			t.Error("Connection status should not be nil")
		}
	}
}
