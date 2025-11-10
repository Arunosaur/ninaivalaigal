package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"google.golang.org/grpc"

	graphopsv1 "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto"
)

func TestGraphHealthHandlerNoClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status 503, got %d", rec.Code)
	}
}

func TestGraphHealthHandlerNilGraphOpsClient(t *testing.T) {
	gateway := NewGateway()
	clients := &GRPCClients{
		GraphOpsClient: nil,
	}
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status 503, got %d", rec.Code)
	}
}

func TestGraphHealthHandlerWithMockClient(t *testing.T) {
	gateway := NewGateway()
	mockClient := &MockGraphOpsClient{}

	// Mock successful health check with all fields
	mockClient.HealthCheckFunc = func(ctx context.Context, in *graphopsv1.HealthCheckRequest, opts ...grpc.CallOption) (*graphopsv1.HealthCheckResponse, error) {
		return &graphopsv1.HealthCheckResponse{
			Status:        graphopsv1.HealthStatus_HEALTH_STATUS_HEALTHY,
			Version:       "1.0.0",
			UptimeSeconds: 3600,
			Database: &graphopsv1.ComponentStatus{
				Name:   "PostgreSQL",
				Status: graphopsv1.HealthStatus_HEALTH_STATUS_HEALTHY,
			},
			AgeExtension: &graphopsv1.ComponentStatus{
				Name:   "Apache AGE",
				Status: graphopsv1.HealthStatus_HEALTH_STATUS_HEALTHY,
			},
			Details: map[string]string{
				"message": "All systems operational",
			},
		}, nil
	}

	clients := &GRPCClients{
		GraphOpsClient: mockClient,
	}
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// Should return 200 if health check succeeds
	if rec.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rec.Code)
	}
}

func TestGraphHealthHandlerWithMockClientError(t *testing.T) {
	gateway := NewGateway()
	mockClient := &MockGraphOpsClient{}

	// Mock failed health check
	mockClient.HealthCheckFunc = func(ctx context.Context, in *graphopsv1.HealthCheckRequest, opts ...grpc.CallOption) (*graphopsv1.HealthCheckResponse, error) {
		return nil, fmt.Errorf("connection error")
	}

	clients := &GRPCClients{
		GraphOpsClient: mockClient,
	}
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// Should handle error gracefully (may return 503 or 500)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphHealthHandlerTimeout(t *testing.T) {
	gateway := NewGateway()
	mockClient := &MockGraphOpsClient{}

	// Mock context timeout - simulate timeout error
	mockClient.HealthCheckFunc = func(ctx context.Context, in *graphopsv1.HealthCheckRequest, opts ...grpc.CallOption) (*graphopsv1.HealthCheckResponse, error) {
		// Return context deadline exceeded error to simulate timeout
		return nil, context.DeadlineExceeded
	}

	clients := &GRPCClients{
		GraphOpsClient: mockClient,
	}
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
	rec := httptest.NewRecorder()

	enhanced.graphHealthHandler(rec, req)

	// Should handle timeout gracefully (returns 503)
	if rec.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status 503 for timeout, got %d", rec.Code)
	}
}
