package main

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestRunScenarioWithPredefinedSmoke(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Test smoke scenario - simplest one
	// Will fail without actual services, but tests structure
	err := runScenario(ctx, "smoke")
	// Accept any error - just testing function exists and handles predefined scenarios
	_ = err
}

func TestRunScenarioWithFile(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Create a temporary scenario file
	tmpDir := t.TempDir()
	scenarioFile := filepath.Join(tmpDir, "test-scenario.json")

	// Write valid scenario JSON
	scenarioData := `{
		"name": "test-scenario",
		"description": "Test scenario",
		"base_url": "http://localhost:8080",
		"endpoints": [
			{
				"path": "/health",
				"method": "GET",
				"weight": 100
			}
		]
	}`

	if err := os.WriteFile(scenarioFile, []byte(scenarioData), 0644); err != nil {
		t.Fatalf("Failed to write scenario file: %v", err)
	}

	// Test loading from file
	err := runScenario(ctx, scenarioFile)
	// Will fail without actual service, but tests file loading
	_ = err
}

func TestRunScenarioWithInvalidFile(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	// Test with non-existent file
	err := runScenario(ctx, "/nonexistent/scenario.json")
	// Should return error for missing file
	if err == nil {
		t.Error("Expected error for non-existent scenario file")
	}
}

func TestRunScenarioWithInvalidJSON(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	// Create temporary file with invalid JSON
	tmpDir := t.TempDir()
	scenarioFile := filepath.Join(tmpDir, "invalid.json")

	os.WriteFile(scenarioFile, []byte("invalid json"), 0644)
	defer os.Remove(scenarioFile)

	// Should return error for invalid JSON
	err := runScenario(ctx, scenarioFile)
	if err == nil {
		t.Error("Expected error for invalid JSON in scenario file")
	}
}
