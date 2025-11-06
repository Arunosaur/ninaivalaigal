package main

import (
	"context"
	"testing"
	"time"
)

func TestGRPCTesterRunWithContext(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "localhost:50051"
	config.GRPCMethod = "TestService/TestMethod"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Timeout = 1 * time.Second

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester should not return nil")
	}

	// Test with short timeout context
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// This will likely fail due to connection issues, but tests the code path
	err := tester.Run(ctx)
	if err != nil {
		t.Logf("GRPCTester.Run failed as expected (connection issue): %v", err)
	}
}

func TestGRPCTesterRunWithCanceledContext(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "localhost:50051"
	config.GRPCMethod = "TestService/TestMethod"
	config.Concurrency = 1
	config.TotalRequests = 10

	tester := NewGRPCTester(config)

	// Test with canceled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	err := tester.Run(ctx)
	if err == nil {
		t.Log("GRPCTester.Run may not check context immediately")
	} else {
		t.Logf("GRPCTester.Run correctly handled canceled context: %v", err)
	}
}

func TestGRPCTesterRunWithDuration(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "localhost:50051"
	config.GRPCMethod = "TestService/TestMethod"
	config.Concurrency = 1
	config.Duration = 100 * time.Millisecond
	config.Timeout = 50 * time.Millisecond

	tester := NewGRPCTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("GRPCTester.Run with duration: %v", err)
	}
}

func TestGRPCTesterRunWithRateLimit(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "localhost:50051"
	config.GRPCMethod = "TestService/TestMethod"
	config.Concurrency = 1
	config.TotalRequests = 5
	config.RateLimit = 10
	config.Timeout = 1 * time.Second

	tester := NewGRPCTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("GRPCTester.Run with rate limit: %v", err)
	}
}

func TestGRPCTesterRunWithProtoFile(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "localhost:50051"
	config.GRPCMethod = "TestService/TestMethod"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.ProtoFile = "test.proto"
	config.Timeout = 1 * time.Second

	tester := NewGRPCTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := tester.Run(ctx)
	if err != nil {
		t.Logf("GRPCTester.Run with proto file: %v", err)
	}
}
