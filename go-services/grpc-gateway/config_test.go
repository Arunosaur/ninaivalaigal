package main

import (
	"os"
	"testing"
)

func TestGetEnvDefault(t *testing.T) {
	// Test with default value
	value := getEnv("NONEXISTENT_VAR", "default-value")
	if value != "default-value" {
		t.Errorf("Expected 'default-value', got '%s'", value)
	}
}

func TestGetEnvFromEnvironment(t *testing.T) {
	// Set environment variable
	if err := os.Setenv("TEST_VAR", "test-value"); err != nil {
		t.Fatalf("Failed to set env var: %v", err)
	}
	defer func() {
		if err := os.Unsetenv("TEST_VAR"); err != nil {
			t.Fatalf("Failed to unset env var: %v", err)
		}
	}()

	value := getEnv("TEST_VAR", "default-value")
	if value != "test-value" {
		t.Errorf("Expected 'test-value', got '%s'", value)
	}
}

func TestSanitizePortValid(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"8080", "8080"},
		{"13390", "13390"},
		{"0", "0"},
		{"65535", "65535"},
	}

	for _, tt := range tests {
		result := sanitizePort(tt.input)
		if result != tt.expected {
			t.Errorf("sanitizePort(%s) = %s, expected %s", tt.input, result, tt.expected)
		}
	}
}

func TestSanitizePortInvalid(t *testing.T) {
	// Invalid ports should return default or sanitized value
	invalidPorts := []string{"", "abc", "-1", "65536", "99999"}

	for _, port := range invalidPorts {
		result := sanitizePort(port)
		// Should return some valid port or default
		if result == "" {
			t.Errorf("sanitizePort(%s) returned empty string", port)
		}
	}
}

func TestSanitizePortSpecialCharacters(t *testing.T) {
	// Test with special characters
	specialPorts := []string{"8080:8081", "8080 ", " 8080 ", "8080\n"}

	for _, port := range specialPorts {
		result := sanitizePort(port)
		// Should sanitize and return valid port
		if result == "" {
			t.Errorf("sanitizePort(%s) returned empty string", port)
		}
	}
}

func TestConfigVariablesSet(t *testing.T) {
	// Verify config variables are initialized
	if GatewayAddr == "" {
		t.Error("GatewayAddr should be set")
	}
	if GatewayPublicURL == "" {
		t.Error("GatewayPublicURL should be set")
	}
	if MemoryAddr == "" {
		t.Error("MemoryAddr should be set")
	}
	if GraphOpsAddr == "" {
		t.Error("GraphOpsAddr should be set")
	}
	if CoreAPIAddr == "" {
		t.Error("CoreAPIAddr should be set")
	}
}
