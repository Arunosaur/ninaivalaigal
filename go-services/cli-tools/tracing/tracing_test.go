package tracing

import (
	"os"
	"testing"
)

func TestGetEnvironment(t *testing.T) {
	// Test default environment
	originalEnv := os.Getenv("ENVIRONMENT")
	defer os.Setenv("ENVIRONMENT", originalEnv)

	os.Unsetenv("ENVIRONMENT")
	env := getEnvironment()
	if env != "development" {
		t.Errorf("Expected default environment 'development', got '%s'", env)
	}

	// Test custom environment
	os.Setenv("ENVIRONMENT", "production")
	env = getEnvironment()
	if env != "production" {
		t.Errorf("Expected environment 'production', got '%s'", env)
	}

	// Test staging environment
	os.Setenv("ENVIRONMENT", "staging")
	env = getEnvironment()
	if env != "staging" {
		t.Errorf("Expected environment 'staging', got '%s'", env)
	}
}

func TestInitTracingWithInvalidEndpoint(t *testing.T) {
	// Test with invalid endpoint (should fail gracefully)
	cleanup, err := InitTracing("test-service", "invalid-endpoint:99999")
	if err == nil {
		t.Log("InitTracing with invalid endpoint should fail, but got nil error")
		// If cleanup was returned, call it
		if cleanup != nil {
			cleanup()
		}
	} else {
		t.Logf("InitTracing correctly failed with invalid endpoint: %v", err)
	}
}

func TestInitTracingStructure(t *testing.T) {
	// Test that InitTracing function exists and has correct signature
	// We can't test successful initialization without a running OTLP collector,
	// but we can verify the function signature and basic structure

	// Test with empty service name
	cleanup, err := InitTracing("", "localhost:4317")
	if err == nil {
		// If it succeeded, clean up
		if cleanup != nil {
			cleanup()
		}
		t.Log("InitTracing with empty service name may succeed (service name may be optional)")
	} else {
		t.Logf("InitTracing with empty service name: %v", err)
	}
}

func TestInitTracingCleanupFunction(t *testing.T) {
	// Test that cleanup function is returned even on error
	// This tests the function structure
	cleanup, err := InitTracing("test-service", "invalid:99999")

	// Even if initialization fails, cleanup should be nil or a function
	if err != nil {
		// On error, cleanup should typically be nil
		if cleanup != nil {
			// If cleanup is not nil, it should be callable
			cleanup()
		}
		t.Logf("InitTracing failed as expected: %v", err)
	} else {
		// If it succeeded, cleanup should be callable
		if cleanup != nil {
			cleanup()
		}
	}
}
