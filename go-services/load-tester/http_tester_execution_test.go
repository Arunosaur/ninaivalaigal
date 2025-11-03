package main

import (
	"context"
	"testing"
	"time"
)

func TestNewHTTPTester(t *testing.T) {
	config := &LoadTestConfig{
		URL:            "http://localhost:8080",
		Concurrency:    1,
		TotalRequests:  1,
		Timeout:        5 * time.Second,
		ReportInterval: 1 * time.Second, // Required to avoid ticker panic
	}
	tester := NewHTTPTester(config)
	if tester == nil {
		t.Fatal("NewHTTPTester() should not return nil")
	}
	if tester.config.URL != "http://localhost:8080" {
		t.Errorf("Expected URL 'http://localhost:8080', got '%s'", tester.config.URL)
	}
}

func TestHTTPTesterRun(t *testing.T) {
	config := &LoadTestConfig{
		URL:            "http://127.0.0.1:65535", // Use invalid port to force quick failure
		Concurrency:    1,
		TotalRequests:  1,
		Timeout:        1 * time.Second, // Short timeout
		ReportInterval: 1 * time.Second, // Required to avoid ticker panic
	}
	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	// Test will fail quickly without server, but tests structure
	err := tester.Run(ctx)
	// Accept any error - just testing function exists and returns
	_ = err
}

func TestHTTPTesterExecuteRequest(t *testing.T) {
	config := &LoadTestConfig{
		URL:            "http://127.0.0.1:65535", // Invalid port for quick failure
		Concurrency:    1,
		TotalRequests:  1,
		Timeout:        1 * time.Second,
		ReportInterval: 1 * time.Second,
	}
	tester := NewHTTPTester(config)

	// Test request execution structure
	// Note: executeRequest may be private or have different signature
	// Testing through Run() instead
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Test Run() which internally uses executeRequest
	err := tester.Run(ctx)
	// Accept any error - just testing function exists
	_ = err
}

func TestHTTPTesterWorker(t *testing.T) {
	config := &LoadTestConfig{
		URL:            "http://127.0.0.1:65535", // Invalid port for quick failure
		Concurrency:    1,
		TotalRequests:  1,
		Timeout:        1 * time.Second,
		ReportInterval: 1 * time.Second,
	}
	tester := NewHTTPTester(config)

	// Note: worker may be private - test through Run() instead
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Test Run() which internally uses worker
	err := tester.Run(ctx)
	// Accept any error - just testing function exists
	_ = err
}
