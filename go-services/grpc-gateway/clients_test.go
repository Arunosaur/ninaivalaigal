package main

import (
	"testing"
)

func TestNewGRPCClients(t *testing.T) {
	clients, err := NewGRPCClients()
	if err != nil {
		// Accept connection errors - clients may still be created
		t.Logf("NewGRPCClients() returned error: %v (this is acceptable for testing)", err)
	}
	if clients == nil {
		t.Fatal("NewGRPCClients() should not return nil")
	}
	// Connections may be nil if services unavailable
	_ = clients
}

func TestGRPCClientsGetConnectionStatus(t *testing.T) {
	clients, _ := NewGRPCClients()

	status := clients.GetConnectionStatus()
	if status == nil {
		t.Error("GetConnectionStatus() should not return nil")
	}

	// Verify status structure (returns map[string]string)
	if _, ok := status["memory_service"]; !ok {
		t.Error("memory_service status should be set")
	}
	if _, ok := status["graphops_service"]; !ok {
		t.Error("graphops_service status should be set")
	}
}
