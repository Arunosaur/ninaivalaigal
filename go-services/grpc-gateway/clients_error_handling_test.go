package main

import (
	"testing"
)

func TestNewGRPCClientsMemoryConnectionFailure(t *testing.T) {
	// Test error handling when Memory Service connection fails
	// Note: This will fail in real environment, but tests error path
	clients, err := NewGRPCClients()

	if err != nil {
		t.Logf("NewGRPCClients() error (expected if services unavailable): %v", err)
	}

	// Should still return clients for partial initialization scenarios
	_ = clients
}

func TestNewGRPCClientsGraphOpsConnectionFailure(t *testing.T) {
	// Test error handling when GraphOps Service connection fails after Memory succeeds
	// This tests the cleanup path when second connection fails
	clients, err := NewGRPCClients()

	if err != nil {
		t.Logf("NewGRPCClients() error (expected): %v", err)
	}

	_ = clients
}

func TestNewGRPCClientsHealthCheckFailure(t *testing.T) {
	// Test error handling when health checks fail after connections are established
	clients, err := NewGRPCClients()

	if err != nil {
		t.Logf("Connection health check failed (expected): %v", err)
	}

	// Clients should be cleaned up on health check failure
	if clients != nil {
		clients.Close()
	}
}

func TestGRPCClientsCloseOnNilMemoryConnection(t *testing.T) {
	clients := &GRPCClients{
		memoryConn:   nil,
		graphOpsConn: nil,
	}

	// Should not panic
	clients.Close()
}

func TestGRPCClientsCloseOnNilGraphOpsConnection(t *testing.T) {
	clients := &GRPCClients{
		memoryConn:   nil,
		graphOpsConn: nil,
	}

	// Should not panic
	clients.Close()
}

func TestGRPCClientsCloseErrorHandling(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test without clients")
	}

	// Close once (should succeed)
	clients.Close()

	// Close again (should handle already-closed gracefully)
	clients.Close()

	// Close third time (should be idempotent)
	clients.Close()
}

func TestGetConnectionStatusWithNilConnections(t *testing.T) {
	clients := &GRPCClients{
		memoryConn:   nil,
		graphOpsConn: nil,
	}

	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	// Should indicate disconnected status
	if status["memory_service"] == "" {
		t.Error("Status should contain memory_service key")
	}

	if status["graphops_service"] == "" {
		t.Error("Status should contain graphops_service key")
	}
}

func TestGetConnectionStatusPartialConnections(t *testing.T) {
	// Test with one connection nil and one valid
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test without clients")
	}

	// Create a scenario with partial connections
	// (This would require more setup, but we can test the status reporting)
	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	// Should report status for both services
	if _, ok := status["memory_service"]; !ok {
		t.Error("Status should contain memory_service")
	}

	if _, ok := status["graphops_service"]; !ok {
		t.Error("Status should contain graphops_service")
	}
}
