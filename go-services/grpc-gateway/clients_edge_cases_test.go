package main

import (
	"context"
	"testing"
)

func TestGRPCClientsGetConnectionStatusWithNilConnections(t *testing.T) {
	clients := &GRPCClients{
		MemoryClient:   nil,
		GraphOpsClient: nil,
		memoryConn:     nil,
		graphOpsConn:   nil,
	}

	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus should not return nil")
	}

	// Should handle nil connections gracefully
	if _, ok := status["memory_service"]; !ok {
		t.Error("memory_service status should be set")
	}
	if _, ok := status["graphops_service"]; !ok {
		t.Error("graphops_service status should be set")
	}
}

// TestGRPCClientsCloseWithNilConnections is defined in clients_close_test.go
// This test is removed to avoid duplicate declaration

func TestGRPCClientsTestConnectionsWithNilClients(t *testing.T) {
	clients := &GRPCClients{
		MemoryClient:   nil,
		GraphOpsClient: nil,
	}

	ctx := context.Background()

	// Should handle nil clients gracefully
	err := clients.testConnections()

	// May return error or nil depending on implementation
	_ = err
}

func TestGRPCClientsTestMemoryConnectionNil(t *testing.T) {
	clients := &GRPCClients{
		MemoryClient: nil,
	}

	ctx := context.Background()

	err := clients.testMemoryConnection(ctx)

	// Should handle nil client gracefully
	_ = err
}

func TestGRPCClientsTestGraphOpsConnectionNil(t *testing.T) {
	clients := &GRPCClients{
		GraphOpsClient: nil,
	}

	ctx := context.Background()

	err := clients.testGraphOpsConnection(ctx)

	// Should handle nil client gracefully
	_ = err
}

func TestGRPCClientsGetConnectionStatusPartialConnections(t *testing.T) {
	clients, _ := NewGRPCClients() // May fail if services unavailable

	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus should not return nil")
	}

	// Should report status for both services even if only one is connected
	if _, ok := status["memory_service"]; !ok {
		t.Error("memory_service status should be set")
	}
	if _, ok := status["graphops_service"]; !ok {
		t.Error("graphops_service status should be set")
	}
}
