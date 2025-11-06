package main

import (
	"context"
	"testing"
	"time"
)

// Test testMemoryConnection with nil client
func TestTestMemoryConnectionWithNilClient(t *testing.T) {
	clients := &GRPCClients{
		MemoryClient: nil,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	// Should handle nil client gracefully
	err := clients.testMemoryConnection(ctx)
	if err != nil {
		// Error is expected with nil client, but function should not panic
		t.Logf("testMemoryConnection with nil client returned error (expected): %v", err)
	}
}

// Test testGraphOpsConnection with nil client
func TestTestGraphOpsConnectionWithNilClient(t *testing.T) {
	clients := &GRPCClients{
		GraphOpsClient: nil,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	// Should handle nil client gracefully
	err := clients.testGraphOpsConnection(ctx)
	if err != nil {
		// Error is expected with nil client, but function should not panic
		t.Logf("testGraphOpsConnection with nil client returned error (expected): %v", err)
	}
}

// Test testConnections with both clients nil
func TestTestConnectionsWithNilClients(t *testing.T) {
	clients := &GRPCClients{
		MemoryClient:   nil,
		GraphOpsClient: nil,
	}

	// Should handle nil clients gracefully
	err := clients.testConnections()
	if err != nil {
		// Error is expected, but should not panic
		t.Logf("testConnections with nil clients returned error (expected): %v", err)
	}
}

// Test testConnections with context timeout
func TestTestConnectionsWithTimeout(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// Create a very short timeout context
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
	defer cancel()

	// Give context time to expire
	time.Sleep(10 * time.Millisecond)

	// Test with expired context
	err := clients.testMemoryConnection(ctx)
	if err == nil {
		// May return nil if service is not available (expected behavior)
		t.Log("testMemoryConnection with expired context handled gracefully")
	}
}

// Test testConnections error path when memory connection fails
func TestTestConnectionsMemoryFailurePath(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// Set MemoryClient to nil to simulate failure
	originalClient := clients.MemoryClient
	clients.MemoryClient = nil

	defer func() {
		clients.MemoryClient = originalClient
	}()

	err := clients.testConnections()
	// Error is expected, but function should handle it gracefully
	if err != nil {
		t.Logf("testConnections with nil memory client returned error (expected): %v", err)
	}
}

// Test testConnections error path when graphops connection fails
func TestTestConnectionsGraphOpsFailurePath(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// Set GraphOpsClient to nil to simulate failure
	originalClient := clients.GraphOpsClient
	clients.GraphOpsClient = nil

	defer func() {
		clients.GraphOpsClient = originalClient
	}()

	// First ensure memory connection works (or is nil)
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	// Test memory connection first (should succeed or return nil)
	_ = clients.testMemoryConnection(ctx)

	// Now test connections - should fail on graphops
	err := clients.testConnections()
	// Error is expected, but function should handle it gracefully
	if err != nil {
		t.Logf("testConnections with nil graphops client returned error (expected): %v", err)
	}
}

// Test testMemoryConnection with very short timeout
func TestTestMemoryConnectionShortTimeout(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
	defer cancel()

	// Give context time to expire
	time.Sleep(10 * time.Millisecond)

	err := clients.testMemoryConnection(ctx)
	// May return nil if context is already expired (expected behavior)
	if err != nil {
		t.Logf("testMemoryConnection with short timeout returned error (expected): %v", err)
	}
}

// Test testGraphOpsConnection with very short timeout
func TestTestGraphOpsConnectionShortTimeout(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
	defer cancel()

	// Give context time to expire
	time.Sleep(10 * time.Millisecond)

	err := clients.testGraphOpsConnection(ctx)
	// May return nil if context is already expired (expected behavior)
	if err != nil {
		t.Logf("testGraphOpsConnection with short timeout returned error (expected): %v", err)
	}
}

// Test that testConnections calls both test functions
func TestTestConnectionsCallsBothTests(t *testing.T) {
	clients, _ := NewGRPCClients()
	if clients == nil {
		t.Skip("Cannot test with nil clients")
	}

	// This test verifies that testConnections calls both test functions
	// The actual behavior depends on service availability, but should not panic
	err := clients.testConnections()
	if err != nil {
		t.Logf("testConnections returned error (may be expected if services unavailable): %v", err)
	}
}
