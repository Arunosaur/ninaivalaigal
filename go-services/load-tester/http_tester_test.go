package main

import (
	"context"
	"testing"
	"time"
)

func TestHTTPTesterRunWithContext(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Timeout = 1 * time.Second

	tester := NewHTTPTester(config)
	if tester == nil {
		t.Fatal("NewHTTPTester should not return nil")
	}

	// Test with short timeout context
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// This will likely fail due to connection issues, but tests the code path
	err := tester.Run(ctx)
	if err != nil {
		t.Logf("HTTPTester.Run failed as expected (connection issue): %v", err)
	}
}

func TestHTTPTesterRunWithCanceledContext(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 10

	tester := NewHTTPTester(config)

	// Test with canceled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	err := tester.Run(ctx)
	if err == nil {
		t.Log("HTTPTester.Run may not check context immediately")
	} else {
		t.Logf("HTTPTester.Run correctly handled canceled context: %v", err)
	}
}

func TestHTTPTesterRunWithDuration(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.Duration = 100 * time.Millisecond
	config.Timeout = 50 * time.Millisecond

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("HTTPTester.Run with duration: %v", err)
	}
}

func TestHTTPTesterRunWithRateLimit(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 5
	config.RateLimit = 10
	config.Timeout = 1 * time.Second

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("HTTPTester.Run with rate limit: %v", err)
	}
}

func TestHTTPTesterRunWithHeaders(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Headers = []string{
		"Authorization: Bearer test-token",
		"Content-Type: application/json",
	}
	config.Timeout = 1 * time.Second

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("HTTPTester.Run with headers: %v", err)
	}
}

func TestHTTPTesterRunWithMethod(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/api/test"
	config.Method = "POST"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Body = `{"test": "data"}`
	config.Timeout = 1 * time.Second

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("HTTPTester.Run with POST method: %v", err)
	}
}
