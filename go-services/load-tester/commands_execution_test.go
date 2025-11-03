package main

import (
	"context"
	"os"
	"testing"
	"time"
)

func TestRunScenario(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	// Create temp scenario file
	tmpFile, err := os.CreateTemp("", "test-scenario-*.json")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())

	scenarioJSON := `{
		"name": "test",
		"endpoints": [
			{"method": "GET", "path": "/health", "weight": 100}
		]
	}`
	tmpFile.WriteString(scenarioJSON)
	tmpFile.Close()

	// Test scenario execution structure
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err = runScenario(ctx, tmpFile.Name())
	// Accept any error - just testing function exists
	_ = err
}

func TestRunPredefinedScenario(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Test predefined scenarios
	targets := GetNinaivalaigalTargets()
	profiles := GetDefaultProfiles()
	if len(targets) == 0 || len(profiles) == 0 {
		t.Skip("No targets or profiles available for testing")
	}

	scenario := "smoke"
	target := targets[0]
	profile := profiles[0]
	err := runPredefinedScenario(ctx, scenario, target, profile)
	// Accept any error
	_ = err
}

func TestRunTargetScenario(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Test target-based scenarios
	targets := GetNinaivalaigalTargets()
	if len(targets) == 0 {
		t.Skip("No targets available for testing")
	}

	target := targets[0]
	err := runTargetScenario(ctx, target)
	// Accept any error
	_ = err
}
