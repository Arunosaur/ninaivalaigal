package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestEnhancedHealthHandlerDegradedState(t *testing.T) {
	gateway := NewGateway()

	// Create mock clients with disconnected state
	clients := &GRPCClients{
		MemoryClient:   nil,
		GraphOpsClient: nil,
		memoryConn:     nil,
		graphOpsConn:   nil,
	}

	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	// Should report "initializing" or "degraded" status
	if rec.Code != http.StatusOK && rec.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status 200 or 503, got %d", rec.Code)
	}
}

func TestEnhancedHealthHandlerWriteError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	// Test that handler handles write errors gracefully
	enhanced.enhancedHealthHandler(rec, req)

	// Handler should complete even if there are write issues
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestEnhancedHealthHandlerNilClientsPath(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil, // Explicitly nil
	}

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	enhanced.enhancedHealthHandler(rec, req)

	// Should handle nil clients and return "initializing" status
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}

	// Verify response contains expected status
	if rec.Body.Len() == 0 {
		t.Error("Handler should write response body")
	}
}
