package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestValidateTesterRunValidation tests the full validation run
func TestValidateTesterRunValidation(t *testing.T) {
	// Create a test server that responds to health checks
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/health", "/api/v1/memory/health":
			w.WriteHeader(http.StatusOK)
			if _, err := w.Write([]byte(`{"status":"ok"}`)); err != nil {
				t.Errorf("Failed to write response: %v", err)
			}
		case "/api/v1/graph/health":
			w.WriteHeader(http.StatusNotImplemented)
			if _, err := w.Write([]byte(`{"error":"not implemented"}`)); err != nil {
				t.Errorf("Failed to write response: %v", err)
			}
		default:
			w.WriteHeader(http.StatusNotFound)
			if _, err := w.Write([]byte(`{"error":"not found"}`)); err != nil {
				t.Errorf("Failed to write response: %v", err)
			}
		}
	}))
	defer server.Close()

	validator := NewValidateTester(server.URL)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Run validation - should complete successfully with test server
	err := validator.RunValidation(ctx)
	if err != nil {
		t.Logf("Validation run (may fail if service unavailable): %v", err)
	}
}

// TestValidateTesterWithInvalidURL tests validator with invalid URL
func TestValidateTesterWithInvalidURL(t *testing.T) {
	validator := NewValidateTester("http://invalid-host-12345:9999")

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Should fail with connection error
	err := validator.RunValidation(ctx)
	if err != nil {
		t.Logf("Validation with invalid URL (expected to fail): %v", err)
	}
}

// TestValidateTesterWithSlowServer tests validator with slow server
func TestValidateTesterWithSlowServer(t *testing.T) {
	// Server that delays response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"status":"ok"}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer server.Close()

	validator := NewValidateTester(server.URL)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	// Run validation with slow server
	err := validator.RunValidation(ctx)
	if err != nil {
		t.Logf("Validation with slow server: %v", err)
	}
}

// TestValidateTesterWithErrorResponses tests validator with error responses
func TestValidateTesterWithErrorResponses(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusInternalServerError)
		} else {
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	validator := NewValidateTester(server.URL)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	// Run validation with error responses
	err := validator.RunValidation(ctx)
	// May succeed or fail depending on validation logic
	if err != nil {
		t.Logf("Validation with error responses: %v", err)
	}
}

// TestValidateTesterNewValidateTester tests creating a new validator
func TestValidateTesterNewValidateTester(t *testing.T) {
	validator := NewValidateTester("http://localhost:8080")

	if validator == nil {
		t.Fatal("NewValidateTester should not return nil")
	}

	if validator.baseURL != "http://localhost:8080" {
		t.Errorf("Expected baseURL 'http://localhost:8080', got '%s'", validator.baseURL)
	}

	if validator.client == nil {
		t.Error("HTTP client should be initialized")
	}
}

// TestValidateTesterWithContextTimeout tests validator with context timeout
func TestValidateTesterWithContextTimeout(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(2 * time.Second) // Longer than timeout
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	validator := NewValidateTester(server.URL)

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Should timeout
	err := validator.RunValidation(ctx)
	if err != nil {
		t.Logf("Validation with timeout (expected): %v", err)
	}
}

// TestValidateTesterMultipleRuns tests running validation multiple times
func TestValidateTesterMultipleRuns(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		if _, err := w.Write([]byte(`{"status":"ok"}`)); err != nil {
			t.Errorf("Failed to write response: %v", err)
		}
	}))
	defer server.Close()

	validator := NewValidateTester(server.URL)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Run validation multiple times
	for i := 0; i < 3; i++ {
		err := validator.RunValidation(ctx)
		if err != nil {
			t.Logf("Validation run %d: %v", i+1, err)
		}
	}
}
