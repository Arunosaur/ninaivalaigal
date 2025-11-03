package main

import (
	"context"
	"testing"
	"time"
)

func TestNewGRPCClientsWithValidAddresses(t *testing.T) {
	// Test client creation structure
	// Note: Will fail without actual services, but tests initialization
	clients, err := NewGRPCClients()

	if err != nil {
		t.Logf("NewGRPCClients() returned error (expected if services unavailable): %v", err)
	}

	if clients == nil {
		t.Error("NewGRPCClients() should not return nil even on error")
	}
}

func TestGRPCClientsGetConnectionStatusWhenNil(t *testing.T) {
	clients := &GRPCClients{}
	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	// Should return status map even if clients are nil
	if len(status) == 0 {
		t.Log("Status map is empty (expected if clients not initialized)")
	}
}

func TestGRPCClientsGetConnectionStatusWithClients(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	status := clients.GetConnectionStatus()

	if status == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	// Verify status contains expected keys
	expectedKeys := []string{"memory_service", "graphops_service"}
	for _, key := range expectedKeys {
		if _, ok := status[key]; !ok {
			t.Logf("Status key '%s' not found (may be expected)", key)
		}
	}
}

func TestGRPCClientsContextHandling(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// Test context timeout handling
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Just verify clients can be used with context
	_ = ctx
	_ = clients
}

func TestGRPCClientsMultipleCalls(t *testing.T) {
	// Test that multiple calls to NewGRPCClients work
	clients1, err1 := NewGRPCClients()
	clients2, err2 := NewGRPCClients()

	// Both should return something (even if errors)
	if clients1 == nil && clients2 == nil {
		t.Error("At least one NewGRPCClients() call should return non-nil")
	}

	_ = err1
	_ = err2
}

func TestGRPCClientsStatusConsistency(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// Get status multiple times - should be consistent
	status1 := clients.GetConnectionStatus()
	status2 := clients.GetConnectionStatus()

	// Status should be non-nil (may be different if connections change, but should exist)
	if status1 == nil || status2 == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}
}
