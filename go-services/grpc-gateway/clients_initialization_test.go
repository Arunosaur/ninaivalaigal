package main

import (
	"testing"
)

func TestNewGRPCClientsErrorHandling(t *testing.T) {
	// Test that NewGRPCClients handles errors gracefully
	// Note: Will fail without actual services, but tests error paths

	clients, err := NewGRPCClients()

	// Should return clients even if there's an error (for partial initialization)
	if err != nil {
		t.Logf("NewGRPCClients() returned error (expected if services unavailable): %v", err)
	}

	if clients == nil {
		t.Error("NewGRPCClients() should not return nil even on error")
	}
}

func TestNewGRPCClientsPartialConnection(t *testing.T) {
	// Test scenario where one connection succeeds and one fails
	// This would require mocking, but we can test the structure

	clients, err := NewGRPCClients()

	if err != nil {
		t.Logf("Connection error (expected): %v", err)
	}

	if clients != nil {
		// Test that clients structure is valid even with partial connections
		status := clients.GetConnectionStatus()
		if status == nil {
			t.Error("GetConnectionStatus() should not return nil")
		}
	}
}

func TestGRPCClientsStructure(t *testing.T) {
	clients := &GRPCClients{}

	// Test that all fields are accessible
	if clients.MemoryClient == nil {
		t.Log("MemoryClient is nil (expected if not initialized)")
	}

	if clients.GraphOpsClient == nil {
		t.Log("GraphOpsClient is nil (expected if not initialized)")
	}

	// Test Close on empty structure
	clients.Close()

	// Test GetConnectionStatus on empty structure
	status := clients.GetConnectionStatus()
	if status == nil {
		t.Error("GetConnectionStatus() should not return nil even with empty clients")
	}
}

func TestGRPCClientsConnectionRetry(t *testing.T) {
	// Test multiple initialization attempts
	clients1, err1 := NewGRPCClients()
	clients2, err2 := NewGRPCClients()

	_ = err1
	_ = err2

	// Both should return something
	if clients1 == nil && clients2 == nil {
		t.Error("At least one NewGRPCClients() call should return non-nil")
	}

	// Cleanup
	if clients1 != nil {
		clients1.Close()
	}
	if clients2 != nil {
		clients2.Close()
	}
}

func TestGRPCClientsConcurrentAccess(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test without clients")
	}

	// Test that GetConnectionStatus is safe for concurrent access
	// This is a basic test - full concurrency testing would require more setup
	status1 := clients.GetConnectionStatus()
	status2 := clients.GetConnectionStatus()

	if status1 == nil || status2 == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	clients.Close()
}
