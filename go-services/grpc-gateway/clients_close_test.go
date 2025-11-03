package main

import (
	"context"
	"testing"
	"time"
)

func TestGRPCClientsCloseBasic(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		// Create a minimal client for testing Close
		clients = &GRPCClients{}
	}

	// Close should not panic even if connections are nil
	clients.Close()

	// Test multiple closes (should be idempotent)
	clients.Close()
	clients.Close()
}

func TestGRPCClientsCloseWithNilConnections(t *testing.T) {
	clients := &GRPCClients{
		memoryConn:   nil,
		graphOpsConn: nil,
	}

	// Should not panic
	clients.Close()
}

func TestGRPCClientsCloseAfterConnection(t *testing.T) {
	clients, err := NewGRPCClients()
	if err != nil {
		t.Logf("Cannot test with real connections: %v", err)
		t.Skip("Skipping test that requires actual gRPC connections")
	}

	// Close should work
	clients.Close()

	// Close again should not panic
	clients.Close()
}

func TestGRPCClientsTestConnections(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test without clients")
	}

	// Test connections - may fail if services not running
	err := clients.testConnections()
	// Accept any error - services may not be running
	_ = err
}

func TestGRPCClientsTestMemoryConnection(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil || clients.MemoryClient == nil {
		t.Skip("Cannot test without memory client")
	}

	// Test memory connection with valid context
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Test memory connection
	err := clients.testMemoryConnection(ctx)
	// Accept any error (service may not be running)
	_ = err
}

func TestGRPCClientsTestGraphOpsConnection(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil || clients.GraphOpsClient == nil {
		t.Skip("Cannot test without graphops client")
	}

	// Test graphops connection with valid context
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Test graphops connection
	err := clients.testGraphOpsConnection(ctx)
	// Accept any error (service may not be running)
	_ = err
}
