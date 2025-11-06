package main

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// TestGRPCTesterBuildOptionsEnhanced tests buildOptions with various configurations
func TestGRPCTesterBuildOptionsEnhanced(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.Timeout = 5 * time.Second

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	// Test with TotalRequests set
	config.TotalRequests = 100
	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}

	// Test with Duration instead of TotalRequests
	config.TotalRequests = 0
	config.Duration = 30 * time.Second
	options, err = tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error with duration: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options with duration")
	}
}

// TestGRPCTesterBuildOptionsWithRateLimit tests buildOptions with rate limiting
func TestGRPCTesterBuildOptionsWithRateLimit(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.RateLimit = 50

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsWithProtoFile tests buildOptions with proto file
func TestGRPCTesterBuildOptionsWithProtoFile(t *testing.T) {
	// Create a temporary proto file
	tmpDir, err := os.MkdirTemp("", "grpc-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer func() {
		if err := os.RemoveAll(tmpDir); err != nil {
			t.Logf("Failed to remove temp dir: %v", err)
		}
	}()

	protoFile := filepath.Join(tmpDir, "test.proto")
	err = os.WriteFile(protoFile, []byte(`syntax = "proto3"; package test;`), 0644)
	if err != nil {
		t.Fatalf("Failed to write proto file: %v", err)
	}

	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.ProtoFile = protoFile

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsWithBody tests buildOptions with body data
func TestGRPCTesterBuildOptionsWithBody(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.Body = `{"key": "value"}`

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsWithBodyFile tests buildOptions with body file
func TestGRPCTesterBuildOptionsWithBodyFile(t *testing.T) {
	// Create a temporary body file
	tmpDir, err := os.MkdirTemp("", "grpc-body-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer func() {
		if err := os.RemoveAll(tmpDir); err != nil {
			t.Logf("Failed to remove temp dir: %v", err)
		}
	}()

	bodyFile := filepath.Join(tmpDir, "body.json")
	err = os.WriteFile(bodyFile, []byte(`{"key": "value"}`), 0644)
	if err != nil {
		t.Fatalf("Failed to write body file: %v", err)
	}

	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.BodyFile = bodyFile

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsWithHeaders tests buildOptions with headers
func TestGRPCTesterBuildOptionsWithHeaders(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.Headers = []string{"Authorization: Bearer token123", "Content-Type: application/json"}

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsWithInvalidHeader tests buildOptions with invalid header format
func TestGRPCTesterBuildOptionsWithInvalidHeader(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.Headers = []string{"InvalidHeader"} // Missing colon

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err == nil {
		t.Error("buildOptions should return error for invalid header format")
	}
	_ = options // May be nil
}

// TestGRPCTesterBuildOptionsWithEmptyDurationAndRequests tests error case
func TestGRPCTesterBuildOptionsWithEmptyDurationAndRequests(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 0
	config.Duration = 0 // Invalid: both are zero

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err == nil {
		t.Error("buildOptions should return error when both TotalRequests and Duration are zero")
	}
	_ = options // May be nil
}

// TestGRPCTesterBuildOptionsWithGRPCPlaintext tests buildOptions with plaintext
func TestGRPCTesterBuildOptionsWithGRPCPlaintext(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.GRPCPlaintext = true

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}

// TestGRPCTesterBuildOptionsCombined tests buildOptions with multiple options
func TestGRPCTesterBuildOptionsCombined(t *testing.T) {
	config := NewLoadTestConfig()
	config.Concurrency = 10
	config.TotalRequests = 100
	config.RateLimit = 50
	config.Body = `{"key": "value"}`
	config.Headers = []string{"Authorization: Bearer token123"}

	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	options, err := tester.buildOptions()
	if err != nil {
		t.Fatalf("buildOptions should not return error: %v", err)
	}
	if len(options) == 0 {
		t.Error("buildOptions should return options")
	}
}
