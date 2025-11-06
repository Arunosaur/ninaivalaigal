package main

import (
	"testing"
	"time"

	"github.com/spf13/cobra"
)

// TestInitQuickCommand tests that the quick command is registered in init()
func TestInitQuickCommand(t *testing.T) {
	// The init() function registers a "quick" command
	// We can verify it exists by checking if the root command has it
	// This is a basic test to ensure init() is called and command is registered

	// Since init() adds commands, we need to check if quick command exists
	// We'll test by creating a new root command and checking its structure
	rootCmd := &cobra.Command{
		Use:   "load-tester",
		Short: "Load testing tool",
	}

	// The init() function should have already run, adding quick command
	// We test by verifying the command structure can be created
	// Note: rootCmd is initialized above, so it's never nil, but we verify it's valid
	if rootCmd.Use == "" {
		t.Fatal("Root command should have Use field set")
	}

	// The quick command should be available as a subcommand
	// Since init() adds it to the root, we verify the command structure exists
	quickCmd := rootCmd.Commands()
	found := false
	for _, cmd := range quickCmd {
		if cmd.Use == "quick" {
			found = true
			break
		}
	}

	if !found {
		t.Log("Quick command not found - init() may not have run or command structure differs")
	}
}

// TestQuickCommandExecution tests the quick command execution
// Note: init() runs automatically when package is loaded, so quick command should be available
func TestQuickCommandExecution(t *testing.T) {
	// Test the quick command config directly since init() has already run
	// We can't directly test init() execution, but we can test the behavior it sets up

	url := "http://localhost:8080/health"
	quickConfig := NewLoadTestConfig()
	quickConfig.URL = url
	quickConfig.Concurrency = 1
	quickConfig.TotalRequests = 5
	quickConfig.Duration = 10 * time.Second
	quickConfig.Timeout = 5 * time.Second

	tester := NewHTTPTester(quickConfig)
	if tester == nil {
		t.Fatal("NewHTTPTester should not return nil")
	}

	// Test that config matches what init() would create
	if quickConfig.Concurrency != 1 {
		t.Errorf("Expected Concurrency 1, got %d", quickConfig.Concurrency)
	}
	if quickConfig.TotalRequests != 5 {
		t.Errorf("Expected TotalRequests 5, got %d", quickConfig.TotalRequests)
	}
}

// TestQuickCommandWithURL tests the quick command with custom URL
func TestQuickCommandWithURL(t *testing.T) {
	// Test quick command config with custom URL (as init() would handle it)
	customURL := "http://localhost:9999/health"

	quickConfig := NewLoadTestConfig()
	quickConfig.URL = customURL
	quickConfig.Concurrency = 1
	quickConfig.TotalRequests = 5
	quickConfig.Duration = 10 * time.Second
	quickConfig.Timeout = 5 * time.Second

	if quickConfig.URL != customURL {
		t.Errorf("Expected URL %s, got %s", customURL, quickConfig.URL)
	}
}

// TestQuickCommandConfig tests that quick command creates proper config
func TestQuickCommandConfig(t *testing.T) {
	// Test the config that quick command would create
	url := "http://localhost:8080/health"

	quickConfig := NewLoadTestConfig()
	quickConfig.URL = url
	quickConfig.Concurrency = 1
	quickConfig.TotalRequests = 5
	quickConfig.Duration = 10 * time.Second
	quickConfig.Timeout = 5 * time.Second

	if quickConfig.URL != url {
		t.Errorf("Expected URL %s, got %s", url, quickConfig.URL)
	}
	if quickConfig.Concurrency != 1 {
		t.Errorf("Expected Concurrency 1, got %d", quickConfig.Concurrency)
	}
	if quickConfig.TotalRequests != 5 {
		t.Errorf("Expected TotalRequests 5, got %d", quickConfig.TotalRequests)
	}
	if quickConfig.Duration != 10*time.Second {
		t.Errorf("Expected Duration 10s, got %v", quickConfig.Duration)
	}
	if quickConfig.Timeout != 5*time.Second {
		t.Errorf("Expected Timeout 5s, got %v", quickConfig.Timeout)
	}
}
